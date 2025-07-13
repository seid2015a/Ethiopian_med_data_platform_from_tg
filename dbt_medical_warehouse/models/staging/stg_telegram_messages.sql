.
{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        (message ->> 'id')::BIGINT AS message_id,
        channel_name,
        (message ->> 'date')::TIMESTAMP AS message_date,
        message ->> 'message' AS message_text,
        message ->> 'image_path' AS image_path, -- Path to downloaded image
        CASE
            WHEN message -> 'media' IS NOT NULL AND message -> 'media' ->> '_' LIKE '%Photo%' THEN TRUE
            ELSE FALSE
        END AS has_image,
        message AS raw_message_json, -- Keep original JSON for debugging/future fields
        scraped_at
    FROM {{ source('raw', 'telegram_messages') }}
)
SELECT
    message_id,
    channel_name,
    message_date,
    message_text,
    image_path,
    has_image,
    raw_message_json,
    scraped_at
FROM source_data
WHERE message_text IS NOT NULL OR has_image = TRUE -- Filter out empty messages