WITH source AS (

SELECT
    symbol
    ,price_date
    ,adjusted_closing_price
    ,CAST(date_trunc('month', price_date) AS DATE) AS month_start_date
FROM {{ ref('etf_prices_cleaned') }}

)
,monthly_dates AS (
    SELECT 
        symbol
        ,month_start_date
        ,MIN(price_date) AS first_trading_date_of_month
        ,MAX(price_date) AS last_trading_date_of_month
    FROM source
    GROUP BY symbol,month_start_date
)
,first_monthly_prices AS (
    SELECT s.symbol
    ,s.month_start_date
    ,m.first_trading_date_of_month 
    ,s.adjusted_closing_price AS first_adjusted_closing_price
    FROM source s
    JOIN monthly_dates m ON s.symbol = m.symbol 
        AND s.month_start_date=m.month_start_date 
        AND s.price_date = m.first_trading_date_of_month 
)
,last_monthly_prices AS (
    SELECT s.symbol
    ,s.month_start_date
    ,m.last_trading_date_of_month
    ,s.adjusted_closing_price AS last_adjusted_closing_price
    FROM source s
    JOIN monthly_dates m ON s.symbol = m.symbol 
    AND s.month_start_date=m.month_start_date 
    AND s.price_date = m.last_trading_date_of_month
)
,monthly_trading_days AS (

    SELECT
        symbol,
        month_start_date,
        COUNT(*) AS trading_days_count
    FROM source
    GROUP BY symbol, month_start_date

)
,final AS (

    SELECT
        f.symbol,
        f.month_start_date,
        f.first_trading_date_of_month,
        l.last_trading_date_of_month,
        f.first_adjusted_closing_price,
        l.last_adjusted_closing_price,

        l.last_adjusted_closing_price
            - f.first_adjusted_closing_price AS monthly_return,

        CASE
            WHEN f.first_adjusted_closing_price = 0 THEN NULL
            ELSE (
                (l.last_adjusted_closing_price / f.first_adjusted_closing_price) - 1
            ) * 100
        END AS monthly_return_pct,

        t.trading_days_count,

        current_timestamp() AS gold_created_at_utc

    FROM first_monthly_prices f

    INNER JOIN last_monthly_prices l
        ON f.symbol = l.symbol
       AND f.month_start_date = l.month_start_date

    INNER JOIN monthly_trading_days t
        ON f.symbol = t.symbol
       AND f.month_start_date = t.month_start_date

)

SELECT *
FROM final
ORDER BY symbol,month_start_date