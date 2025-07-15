import os
from ultralytics import YOLO
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging
from datetime import datetime
import json

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = "db"
DB_PORT = "5432"

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)

RAW_IMAGE_DIR = "data/raw/telegram_images"
# Path where YOLO saves its results (optional, we'll extract directly)
YOLO_OUTPUT_DIR = "data/processed/yolo_results"
os.makedirs(YOLO_OUTPUT_DIR, exist_ok=True)

# Load a pre-trained YOLOv8 model
# You might want to specify a smaller model for faster inference if resources are limited (e.g., 'yolov8n.pt')
model = YOLO('yolov8n.pt') # yolov8n.pt (nano), yolov8s.pt (small), yolov8m.pt (medium), yolov8l.pt (large), yolov8x.pt (extra large)

def create_image_detection_table():
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS public.fct_image_detections (
                detection_id SERIAL PRIMARY KEY,
                message_id BIGINT NOT NULL,
                image_path TEXT NOT NULL,
                detected_object_class TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                detection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (message_id, detected_object_class, confidence_score) -- To prevent duplicate detections for the same message
            );
        """))
        connection.commit()
    logging.info("fct_image_detections table ensured to exist.")


def get_unprocessed_image_paths():
    unprocessed_images = []
    with engine.connect() as connection:
        # Get all images that exist in raw.telegram_messages but not in fct_image_detections (or where processing failed)
        result = connection.execute(text("""
            SELECT
                t.id,
                t.message ->> 'image_path' AS image_path
            FROM raw.telegram_messages t
            LEFT JOIN public.fct_image_detections fid ON t.id = fid.message_id
            WHERE t.message ->> 'image_path' IS NOT NULL
            AND fid.message_id IS NULL; -- Only select messages not yet processed by YOLO
        """))
        for row in result:
            if row.image_path and os.path.exists(row.image_path): # Verify file exists on disk
                unprocessed_images.append({'message_id': row.id, 'image_path': row.image_path})
    return unprocessed_images

def run_object_detection():
    create_image_detection_table()
    images_to_process = get_unprocessed_image_paths()
    logging.info(f"Found {len(images_to_process)} images to process.")

    if not images_to_process:
        logging.info("No new images to process for object detection.")
        return

    for img_info in images_to_process:
        message_id = img_info['message_id']
        image_path = img_info['image_path']
        logging.info(f"Processing image: {image_path} for message_id: {message_id}")
        try:
            results = model(image_path) # Run inference

            detections = []
            for r in results:
                for box in r.boxes:
                    class_id = int(box.cls)
                    object_class = model.names[class_id]
                    confidence = float(box.conf)
                    detections.append({
                        "message_id": message_id,
                        "image_path": image_path,
                        "detected_object_class": object_class,
                        "confidence_score": confidence
                    })

            if detections:
                with engine.connect() as connection:
                    for d in detections:
                        connection.execute(text("""
                            INSERT INTO public.fct_image_detections (message_id, image_path, detected_object_class, confidence_score)
                            VALUES (:message_id, :image_path, :detected_object_class, :confidence_score)
                            ON CONFLICT (message_id, detected_object_class, confidence_score) DO NOTHING;
                        """), d)
                    connection.commit()
                logging.info(f"Inserted {len(detections)} detections for message {message_id}.")
            else:
                logging.info(f"No objects detected in image for message {message_id}.")

        except Exception as e:
            logging.error(f"Error processing image {image_path} for message {message_id}: {e}")

if __name__ == "__main__":
    run_object_detection()