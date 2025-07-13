{{ config(materialized='table', unique_key='date_key') }}

SELECT
    TO_CHAR(date, 'YYYYMMDD')::INT AS date_key,
    date AS full_date,
    EXTRACT(YEAR FROM date) AS year,
    EXTRACT(MONTH FROM date) AS month,
    TO_CHAR(date, 'Month') AS month_name,
    EXTRACT(DAY FROM date) AS day_of_month,
    EXTRACT(DOW FROM date) AS day_of_week, -- 0 = Sunday, 6 = Saturday
    TO_CHAR(date, 'Day') AS day_name,
    EXTRACT(DOY FROM date) AS day_of_year,
    EXTRACT(WEEK FROM date) AS week_of_year,
    EXTRACT(QUARTER FROM date) AS quarter
FROM (
    SELECT GENERATE_SERIES(MIN(message_date)::date, MAX(message_date)::date, '1 day'::interval)::date AS date
    FROM {{ ref('stg_telegram_messages') }}
) AS dates.
