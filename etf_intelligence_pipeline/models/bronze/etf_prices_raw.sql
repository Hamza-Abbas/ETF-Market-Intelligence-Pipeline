{{
    config(
        materialized='incremental',
        incremental_strategy='merge',
        unique_key=['symbol', 'price_date'],
        file_format='delta',
        on_schema_change='fail',
        full_refresh=false
    )
}}

WITH latest_data AS (

    SELECT
        CAST(symbol AS STRING) AS symbol,
        CAST(price_date AS DATE) AS price_date,
        CAST(open AS DOUBLE) AS open,
        CAST(high AS DOUBLE) AS high,
        CAST(low AS DOUBLE) AS low,
        CAST(close AS DOUBLE) AS close,
        CAST(adjusted_close AS DOUBLE) AS adjusted_close,
        CAST(volume AS BIGINT) AS volume,
        CAST(source_provider AS STRING) AS source_provider,
        CAST(load_type AS STRING) AS load_type,
        CAST(batch_id AS STRING) AS batch_id,
        CAST(ingested_at_utc AS TIMESTAMP) AS ingested_at_utc

    FROM {{ ref('etf_prices_incremental') }}

),

new_records AS (

    SELECT *
    FROM latest_data

    {% if is_incremental() %}

        WHERE price_date > (
            SELECT MAX(price_date)
            FROM {{ this }}
        )

    {% endif %}

)

SELECT *
FROM new_records