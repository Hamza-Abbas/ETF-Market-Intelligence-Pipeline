SELECT
    symbol,
    price_date,
    COUNT(*) AS row_count

FROM {{ ref('etf_prices_raw') }}

GROUP BY
    symbol,
    price_date

HAVING COUNT(*) > 1