import json
import os
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import JSONB
from dotenv import load_dotenv
import logging
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = "db" # Service name in docker-compose
DB_PORT = "5432"

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)

RAW_DATA_DIR = "data/raw/telegram_messages"

def create_raw_table():
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE SCHEMA IF NOT EXISTS raw;
            CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                id BIGINT PRIMARY KEY,
                channel_name TEXT,
                message JSONB,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        connection.commit()
    logging.info("raw.telegram_messages table ensured to exist.")

def load_data_to_postgres():
    create_raw_table()
    for date_dir in os.listdir(RAW_DATA_DIR):
        full_date_dir = os.path.join(RAW_DATA_DIR, date_dir)
        if os.path.isdir(full_date_dir):
            for channel_file in os.listdir(full_date_dir):
                if channel_file.endswith(".json"):
                    file_path = os.path.join(full_date_dir, channel_file)
                    logging.info(f"Loading data from: {file_path}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f) # This expects a list of messages

                    if not isinstance(data, list):
                        data = [data] # Ensure it's a list even if a single message

                    rows = []
                    for msg in data:
                        # Telethon message IDs are unique within a channel, but not globally.
                        # Combine channel name and message ID for global uniqueness if needed in dbt.
                        # For raw, just storing the original ID and channel_name is fine.
                        rows.append({
                            "id": msg.get("id"),
                            "channel_name": msg.get("channel_name"),
                            "message": msg
                        })

                    if rows:
                        with engine.connect() as connection:
                            try:
                                # Use a temporary table or insert in batches for better performance
                                # For simplicity, direct insert for now.
                                for row in rows:
                                    connection.execute(text("""
                                        INSERT INTO raw.telegram_messages (id, channel_name, message)
                                        VALUES (:id, :channel_name, :message)
                                        ON CONFLICT (id) DO UPDATE SET
                                            message = EXCLUDED.message,
                                            scraped_at = EXCLUDED.scraped_at
                                    """), row)
                                connection.commit()
                                logging.info(f"Successfully loaded {len(rows)} messages from {channel_file}")
                            except Exception as e:
                                connection.rollback()
                                logging.error(f"Error loading data from {file_path}: {e}")
                    else:
                        logging.info(f"No messages found in {file_path}")

if __name__ == "__main__":
    load_data_to_postgres()
