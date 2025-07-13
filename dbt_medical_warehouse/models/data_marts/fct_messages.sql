{{ config(materialized='incremental', unique_key='message_id', on_schema_change='sync_all_columns') }}

SELECT
    stm.message_id,
    dc.channel_id,
    dd.date_key,
    stm.message_text,
    stm.has_image,
    stm.image_path,
    LENGTH(stm.message_text) AS message_length,
    stm.message_date,
    stm.raw_message_json
FROM {{ ref('stg_telegram_messages') }} stm
JOIN {{ ref('dim_channels') }} dc
    ON stm.channel_name = dc.channel_name
JOIN {{ ref('dim_dates') }} dd
    ON stm.message_date::date = dd.full_date

{% if is_incremental() %}
WHERE stm.message_date > (SELECT MAX(message_date) FROM {{ this }})
{% endif %}
