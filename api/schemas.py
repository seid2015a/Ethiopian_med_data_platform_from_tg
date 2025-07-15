from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class TopProduct(BaseModel):
    product_name: str
    mention_count: int

class ChannelActivity(BaseModel):
    date: datetime
    posting_volume: int

class MessageSearchResult(BaseModel):
    message_id: int
    channel_name: str
    message_date: datetime
    message_text: str
    has_image: bool
    image_path: Optional[str] = None
    detected_objects: Optional[List[str]] = None # To include YOLO results