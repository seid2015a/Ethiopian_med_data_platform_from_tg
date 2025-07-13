
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors.rpcerrorlist import ChannelPrivateError
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
import asyncio

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

# List of channels to scrape
CHANNELS = {
    'Chemed': 'https://t.me/CheMed123', 
    'Lobelia4Cosmetics': 'https://t.me/lobelia4cosmetics',
    'TikvahPharma': 'https://t.me/tikvahpharma',
    # Add more channels from et.tgstat.com/medicine here
    'HealthIssue': 'https://et.tgstat.com/medicine', 
}

RAW_DATA_DIR = "data/raw/telegram_messages"
RAW_IMAGE_DIR = "data/raw/telegram_images"

async def scrape_channel(client, channel_name, channel_entity):
    logging.info(f"Scraping channel: {channel_name}")
    offset_id = 0
    limit = 100 # Fetch 100 messages at a time
    all_messages = []
    total_messages = 0

    today_str = datetime.now().strftime("%Y-%m-%d")
    channel_dir = os.path.join(RAW_DATA_DIR, today_str)
    os.makedirs(channel_dir, exist_ok=True)
    channel_image_dir = os.path.join(RAW_IMAGE_DIR, today_str, channel_name)
    os.makedirs(channel_image_dir, exist_ok=True)

    while True:
        try:
            history = await client(GetHistoryRequest(
                peer=channel_entity,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))
            messages = history.messages
            if not messages:
                break

            for message in messages:
                message_dict = message.to_dict()
                message_dict['channel_name'] = channel_name # Add channel name to the message

                # Check for media (image) and download
                if message.media and hasattr(message.media, 'photo'):
                    try:
                        image_filename = f"{message.id}.jpg"
                        image_path = os.path.join(channel_image_dir, image_filename)
                        await client.download_media(message.media, file=image_path)
                        message_dict['image_path'] = image_path # Store path in message metadata
                        logging.info(f"Downloaded image from message {message.id} to {image_path}")
                    except Exception as e:
                        logging.warning(f"Could not download image from message {message.id} in {channel_name}: {e}")

                all_messages.append(message_dict)
                total_messages += 1

            offset_id = messages[-1].id

            # Save incrementally to avoid losing data on interruption
            with open(os.path.join(channel_dir, f"{channel_name}_{datetime.now().strftime('%H%M%S')}.json"), 'w', encoding='utf-8') as f:
                json.dump(all_messages, f, ensure_ascii=False, indent=4)
            all_messages = [] # Clear for next batch

            logging.info(f"Scraped {total_messages} messages from {channel_name}. Last message ID: {offset_id}")

        except ChannelPrivateError:
            logging.error(f"Cannot access private channel: {channel_name}. Please ensure the channel is public or you have appropriate permissions.")
            break
        except Exception as e:
            logging.error(f"Error scraping channel {channel_name}: {e}")
            break

async def main():
    client = TelegramClient('telegram_scraper', API_ID, API_HASH)
    await client.start()

    for channel_name, channel_link in CHANNELS.items():
        try:
            # Resolve channel entity from link or ID
            entity = await client.get_entity(channel_link)
            await scrape_channel(client, channel_name, entity)
        except Exception as e:
            logging.error(f"Could not get entity for channel {channel_name} ({channel_link}): {e}")

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())