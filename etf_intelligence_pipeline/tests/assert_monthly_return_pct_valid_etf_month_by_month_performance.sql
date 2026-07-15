SELECT
    symbol,
    month_start_date,
    first_adjusted_closing_price,
    last_adjusted_closing_price,
    monthly_return_pct,
    ((last_adjusted_closing_price / first_adjusted_closing_price) - 1) * 100 AS recalculated_monthly_return_pct
FROM {{ ref('etf_month_by_month_performance') }}
WHERE first_adjusted_closing_price != 0
  AND ABS(
        monthly_return_pct
        - (((last_adjusted_closing_price / first_adjusted_closing_price) - 1) * 100)
      ) > 0.01