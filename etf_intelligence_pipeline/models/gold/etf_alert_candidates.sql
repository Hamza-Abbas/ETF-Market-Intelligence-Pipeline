WITH source AS (

    SELECT
        symbol,
        month_start_date,
        monthly_return_pct
    FROM {{ ref('etf_month_by_month_performance') }}

),

alert_rules AS (

    SELECT
        symbol,
        month_start_date,
        monthly_return_pct,

        CASE
            WHEN monthly_return_pct >= 8 THEN 'STRONG_GAIN'
            WHEN monthly_return_pct <= -8 THEN 'SHARP_DROP'
            WHEN monthly_return_pct >= 4 THEN 'POSITIVE_MOMENTUM'
            WHEN monthly_return_pct <= -4 THEN 'NEGATIVE_MOMENTUM'
            ELSE NULL
        END AS alert_type,

        CASE
            WHEN monthly_return_pct >= 8 THEN 'HIGH'
            WHEN monthly_return_pct <= -8 THEN 'HIGH'
            WHEN monthly_return_pct >= 4 THEN 'MEDIUM'
            WHEN monthly_return_pct <= -4 THEN 'MEDIUM'
            ELSE NULL
        END AS alert_severity

    FROM source

),

final AS (

    SELECT
        symbol,
        month_start_date,
        ROUND(monthly_return_pct, 2) AS monthly_return_pct,
        alert_type,
        alert_severity,

        CONCAT(
            symbol,
            ' had a ',
            alert_type,
            ' signal in ',
            CAST(month_start_date AS STRING),
            ' with a monthly return of ',
            CAST(ROUND(monthly_return_pct, 2) AS STRING),
            '%.'
        ) AS alert_message,

        current_timestamp() AS gold_created_at_utc

    FROM alert_rules
    WHERE alert_type IS NOT NULL

)

SELECT *
FROM final
ORDER BY month_start_date DESC