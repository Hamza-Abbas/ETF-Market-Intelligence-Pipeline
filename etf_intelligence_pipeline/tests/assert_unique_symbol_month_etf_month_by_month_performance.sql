SELECT
    symbol,
    month_start_date,
    COUNT(*) AS row_count
FROM {{ ref('etf_month_by_month_performance') }}
GROUP BY
    symbol,
    month_start_date
HAVING COUNT(*) > 1