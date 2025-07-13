{{ config(materialized='table', unique_key='channel_id') }}

SELECT
    DISTINCT md5(channel_name) AS channel_id, -- Generate a consistent ID
    channel_name
FROM {{ ref('stg_telegram_messages') }}
