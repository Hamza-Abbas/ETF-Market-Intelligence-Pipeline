SELECT
    symbol,
    price_date,
    COUNT(*) AS duplicate_count
FROM {{ ref('etf_prices_cleaned') }}
GROUP BY
    symbol,
    price_date
HAVING COUNT(*) > 1
