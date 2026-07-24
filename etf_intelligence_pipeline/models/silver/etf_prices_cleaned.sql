WITH source AS (

    SELECT
        symbol,
        price_date,
        open AS opening_price,
        high AS high_price,
        low AS low_price,
        close AS closing_price,
        adjusted_close AS adjusted_closing_price,
        volume,
        source_provider,
        load_type AS data_loaded_as,
        batch_id,
        ingested_at_utc,
        current_timestamp() AS silver_created_at_utc
    FROM {{ source('bronze', 'etf_prices_raw') }}
    WHERE symbol IS NOT NULL
      AND price_date IS NOT NULL
      AND adjusted_close IS NOT NULL
      AND volume IS NOT NULL
      AND high >= low

),

with_previous_price AS (

    SELECT
        *,
        lag(adjusted_closing_price) OVER (
            PARTITION BY symbol
            ORDER BY price_date
        ) AS previous_adjusted_closing_price,

        lag(adjusted_closing_price,5) OVER (
            PARTITION BY symbol
            ORDER BY price_date
        ) AS adjusted_close_5d_ago
    FROM source

),

final AS (

    SELECT
        symbol,
        row_number() over (
        partition by symbol
        order by price_date
        ) as trading_day_number,
        price_date,
        opening_price,
        high_price,
        low_price,
        closing_price,
        adjusted_closing_price,
        previous_adjusted_closing_price,
        adjusted_close_5d_ago,

        CASE
            WHEN previous_adjusted_closing_price IS NULL THEN NULL
            WHEN previous_adjusted_closing_price = 0 THEN NULL
            ELSE ((adjusted_closing_price - previous_adjusted_closing_price) / previous_adjusted_closing_price)
        END AS daily_return,

        CASE
            WHEN previous_adjusted_closing_price IS NULL THEN NULL
            WHEN previous_adjusted_closing_price = 0 THEN NULL
            ELSE ROUND(
                ((adjusted_closing_price - previous_adjusted_closing_price) / previous_adjusted_closing_price) * 100,
                4
            )
        END AS daily_return_pct,

        CASE
            WHEN adjusted_close_5d_ago IS NULL THEN NULL
            WHEN adjusted_close_5d_ago = 0 THEN NULL
            ELSE ((adjusted_closing_price - adjusted_close_5d_ago) / adjusted_close_5d_ago)
        END AS return_5d,

        CASE
            WHEN adjusted_close_5d_ago IS NULL THEN NULL
            WHEN adjusted_close_5d_ago = 0 THEN NULL
            ELSE ROUND(
                ((adjusted_closing_price -  adjusted_close_5d_ago) / adjusted_close_5d_ago) * 100,
                4
            )
        END AS return_5d_pct,

        volume,
        source_provider,
        data_loaded_as,
        batch_id,
        ingested_at_utc,
        silver_created_at_utc

    FROM with_previous_price

)

SELECT *
FROM final