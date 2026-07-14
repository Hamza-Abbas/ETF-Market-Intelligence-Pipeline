WITH source AS (

    SELECT
        symbol,
        month_start_date,
        monthly_return_pct
    FROM {{ ref('etf_month_by_month_performance') }}

),

risk_summary AS (

    SELECT
        symbol,

        COUNT(*) AS total_months_count,

        SUM(
            CASE
                WHEN monthly_return_pct > 0 THEN 1
                ELSE 0
            END
        ) AS positive_months_count,

        SUM(
            CASE
                WHEN monthly_return_pct < 0 THEN 1
                ELSE 0
            END
        ) AS negative_months_count,

        SUM(
            CASE
                WHEN monthly_return_pct = 0 THEN 1
                ELSE 0
            END
        ) AS flat_months_count,

        ROUND(AVG(monthly_return_pct), 2) AS avg_monthly_return_pct,

        ROUND(MAX(monthly_return_pct), 2) AS best_monthly_return_pct,

        ROUND(MIN(monthly_return_pct), 2) AS worst_monthly_return_pct,

        ROUND(STDDEV(monthly_return_pct), 2) AS monthly_volatility_pct,

        ROUND(
            SUM(
                CASE
                    WHEN monthly_return_pct > 0 THEN 1
                    ELSE 0
                END
            ) * 100.0 / COUNT(*),
            2
        ) AS positive_month_ratio_pct

    FROM source
    GROUP BY symbol

),

final AS (

    SELECT
        symbol,
        total_months_count,
        positive_months_count,
        negative_months_count,
        flat_months_count,
        avg_monthly_return_pct,
        best_monthly_return_pct,
        worst_monthly_return_pct,
        monthly_volatility_pct,
        positive_month_ratio_pct,

        CASE
            WHEN monthly_volatility_pct IS NULL
              OR monthly_volatility_pct = 0 THEN NULL
            ELSE ROUND(avg_monthly_return_pct / monthly_volatility_pct, 2)
        END AS return_to_risk_score,

        current_timestamp() AS gold_created_at_utc

    FROM risk_summary

)

SELECT *
FROM final