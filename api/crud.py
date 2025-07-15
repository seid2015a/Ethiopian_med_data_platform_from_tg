from sqlalchemy.orm import Session
from sqlalchemy import text, func, distinct
from typing import List, Dict, Any
from .schemas import TopProduct, ChannelActivity, MessageSearchResult

def get_top_products(db: Session, limit: int = 10) -> List[TopProduct]:
    # This query assumes you have extracted product names in dbt or can do so here
    # For now, a placeholder assuming keywords are extracted or found in message_text
    # In a real scenario, you'd have a more sophisticated NLP step for product extraction.
    query = text(f"""
        SELECT
            LOWER(SUBSTRING(message_text, '(?i)(?:drug|product|medication|medicine|pill|cream|ointment|tablet|syringe|vaccine|mask|sanitizer|gloves|stethoscope|bandages|thermometer|kit|syrup|capsule|ampoule|vial|drops|sprays|inhaler|gel|patch|suppository|powder|granules|suspension|emulsion|liniment|lotion|spray|aerosol|solution|elixir|tincture|paste|plaster|implant|lozenge|troche|film|disk|strip|wafer|implant|insert|bougie|pessary|device|instrument|equipment|supply)\s*([a-zA-Z0-9\s-]+)')) AS product_name,
            COUNT(*) AS mention_count
        FROM fct_messages
        WHERE message_text ILIKE ANY(ARRAY['%drug%', '%product%', '%medication%', '%medicine%', '%pill%', '%cream%', '%ointment%', '%tablet%', '%syringe%', '%vaccine%', '%mask%', '%sanitizer%', '%gloves%', '%stethoscope%', '%bandages%', '%thermometer%', '%kit%', '%syrup%', '%capsule%', '%ampoule%', '%vial%', '%drops%', '%sprays%', '%inhaler%', '%gel%', '%patch%', '%suppository%', '%powder%', '%granules%', '%suspension%', '%emulsion%', '%liniment%', '%lotion%', '%spray%', '%aerosol%', '%solution%', '%elixir%', '%tincture%', '%paste%', '%plaster%', '%implant%', '%lozenge%', '%troche%', '%film%', '%disk%', '%strip%', '%wafer%', '%implant%', '%insert%', '%bougie%', '%pessary%', '%device%', '%instrument%', '%equipment%', '%supply%']) -- Basic keyword search
        GROUP BY 1
        ORDER BY mention_count DESC
        LIMIT :limit
    """)
    result = db.execute(query, {'limit': limit}).fetchall()
    return [TopProduct(product_name=row[0], mention_count=row[1]) for row in result if row[0] is not None]


def get_channel_activity(db: Session, channel_name: str) -> List[ChannelActivity]:
    query = text("""
        SELECT
            dd.full_date AS date,
            COUNT(fm.message_id) AS posting_volume
        FROM fct_messages fm
        JOIN dim_channels dc ON fm.channel_id = dc.channel_id
        JOIN dim_dates dd ON fm.date_key = dd.date_key
        WHERE dc.channel_name ILIKE :channel_name
        GROUP BY dd.full_date
        ORDER BY dd.full_date ASC
    """)
    result = db.execute(query, {'channel_name': channel_name}).fetchall()
    return [ChannelActivity(date=row[0], posting_volume=row[1]) for row in result]

def search_messages(db: Session, query_str: str) -> List[MessageSearchResult]:
    search_query = f"%{query_str}%"
    sql_query = text("""
        SELECT
            fm.message_id,
            dc.channel_name,
            fm.message_date,
            fm.message_text,
            fm.has_image,
            fm.image_path,
            ARRAY_AGG(fid.detected_object_class) FILTER (WHERE fid.detected_object_class IS NOT NULL) AS detected_objects
        FROM fct_messages fm
        JOIN dim_channels dc ON fm.channel_id = dc.channel_id
        LEFT JOIN fct_image_detections fid ON fm.message_id = fid.message_id
        WHERE fm.message_text ILIKE :search_query
        GROUP BY fm.message_id, dc.channel_name, fm.message_date, fm.message_text, fm.has_image, fm.image_path
        ORDER BY fm.message_date DESC
        LIMIT 100 -- Limit for search results
    """)
    result = db.execute(sql_query, {'search_query': search_query}).fetchall()
    return [
        MessageSearchResult(
            message_id=row[0],
            channel_name=row[1],
            message_date=row[2],
            message_text=row[3],
            has_image=row[4],
            image_path=row[5],
            detected_objects=row[6] if row[6] and row[6] != [None] else []
        )
        for row in result
    ]