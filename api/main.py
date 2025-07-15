from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from . import crud, schemas
from .database import get_db

app = FastAPI(title="Ethiopian Medical Business Data API", version="1.0.0")

@app.get("/api/reports/top-products", response_model=List[schemas.TopProduct])
def read_top_products(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    """
    Returns the top N most frequently mentioned medical products or drugs.
    """
    products = crud.get_top_products(db, limit=limit)
    return products

@app.get("/api/channels/{channel_name}/activity", response_model=List[schemas.ChannelActivity])
def read_channel_activity(channel_name: str, db: Session = Depends(get_db)):
    """
    Returns the daily posting activity for a specific channel.
    """
    activity = crud.get_channel_activity(db, channel_name=channel_name)
    if not activity:
        raise HTTPException(status_code=404, detail="Channel not found or no activity.")
    return activity

@app.get("/api/search/messages", response_model=List[schemas.MessageSearchResult])
def search_messages_api(query: str = Query(..., min_length=2, description="Keyword to search for in messages"), db: Session = Depends(get_db)):
    """
    Searches for messages containing a specific keyword.
    """
    messages = crud.search_messages(db, query_str=query)
    if not messages:
        raise HTTPException(status_code=404, detail="No messages found for the given query.")
    return messages

# You might add more endpoints, e.g., for image content analysis:
@app.get("/api/channels/{channel_name}/visual-content", response_model=Dict[str, Any])
def get_channel_visual_content(channel_name: str, db: Session = Depends(get_db)):
    """
    Analyzes and returns insights on visual content for a specific channel,
    e.g., counts of image detections by class.
    """
    # This would require a new CRUD function and a more specific dbt model or direct query
    # to aggregate object detection results per channel.
    # Example placeholder:
    query = text("""
        SELECT
            fid.detected_object_class,
            COUNT(DISTINCT fm.message_id) AS message_count,
            COUNT(fid.detection_id) AS detection_count
        FROM fct_messages fm
        JOIN dim_channels dc ON fm.channel_id = dc.channel_id
        JOIN fct_image_detections fid ON fm.message_id = fid.message_id
        WHERE dc.channel_name ILIKE :channel_name
        GROUP BY fid.detected_object_class
        ORDER BY detection_count DESC
    """)
    result = db.execute(query, {'channel_name': channel_name}).fetchall()

    if not result:
        raise HTTPException(status_code=404, detail="Channel not found or no visual content processed.")

    response = {
        "channel_name": channel_name,
        "visual_content_summary": [
            {"object_class": row[0], "message_count": row[1], "detection_count": row[2]} for row in result
        ]
    }
    return response