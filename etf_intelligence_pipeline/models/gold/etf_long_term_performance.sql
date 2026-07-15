WITH source AS (

    SELECT
        symbol,
        price_date,
        adjusted_closing_price
    FROM {{ ref('etf_prices_cleaned') }}

),

first_dates AS (

    SELECT
        symbol,
        MIN(price_date) AS start_date
    FROM source
    GROUP BY symbol

),

first_prices AS (

    SELECT
        s.symbol,
        s.price_date AS start_date,
        s.adjusted_closing_price AS first_adjusted_closing_price
    FROM source s
    INNER JOIN first_dates f
        ON s.symbol = f.symbol
       AND s.price_date = f.start_date

),

latest_dates AS (

    SELECT
        symbol,
        MAX(price_date) AS end_date
    FROM source
    GROUP BY symbol

),

latest_prices AS (

    SELECT
        s.symbol,
        s.price_date AS end_date,
        s.adjusted_closing_price AS latest_adjusted_closing_price
    FROM source s
    INNER JOIN latest_dates l
        ON s.symbol = l.symbol
       AND s.price_date = l.end_date

),

final AS (

    SELECT
        f.symbol,
        f.start_date,
        f.first_adjusted_closing_price,
        l.end_date,
        l.latest_adjusted_closing_price,

        l.latest_adjusted_closing_price
            - f.first_adjusted_closing_price AS total_return,

        CASE
            WHEN f.first_adjusted_closing_price = 0 THEN NULL
            ELSE (
                (l.latest_adjusted_closing_price / f.first_adjusted_closing_price) - 1
            ) * 100
        END AS total_return_pct,

        current_timestamp() AS gold_created_at_utc

    FROM first_prices f
    INNER JOIN latest_prices l
        ON f.symbol = l.symbol

)

SELECT *
FROM final