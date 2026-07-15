WITH source AS (

    SELECT
        symbol,
        month_start_date,
        monthly_return_pct
    FROM {{ ref('etf_month_by_month_performance') }}

),

monthly_summary AS (

    SELECT
        month_start_date,

        COUNT(*) AS total_etfs_count,

        SUM(
            CASE
                WHEN monthly_return_pct > 0 THEN 1
                ELSE 0
            END
        ) AS positive_etfs_count,

        SUM(
            CASE
                WHEN monthly_return_pct < 0 THEN 1
                ELSE 0
            END
        ) AS negative_etfs_count,

        SUM(
            CASE
                WHEN monthly_return_pct = 0 THEN 1
                ELSE 0
            END
        ) AS flat_etfs_count,

        ROUND(AVG(monthly_return_pct), 2) AS avg_monthly_return_pct,

        ROUND(MAX(monthly_return_pct), 2) AS best_monthly_return_pct,

        ROUND(MIN(monthly_return_pct), 2) AS worst_monthly_return_pct

    FROM source
    GROUP BY month_start_date

),

ranked_best AS (

    SELECT
        symbol,
        month_start_date,
        monthly_return_pct,

        ROW_NUMBER() OVER (
            PARTITION BY month_start_date
            ORDER BY monthly_return_pct DESC, symbol ASC
        ) AS best_rank

    FROM source

),

ranked_worst AS (

    SELECT
        symbol,
        month_start_date,
        monthly_return_pct,

        ROW_NUMBER() OVER (
            PARTITION BY month_start_date
            ORDER BY monthly_return_pct ASC, symbol ASC
        ) AS worst_rank

    FROM source

),

best_etf AS (

    SELECT
        month_start_date,
        symbol AS best_performing_etf,
        ROUND(monthly_return_pct, 2) AS best_performing_etf_return_pct
    FROM ranked_best
    WHERE best_rank = 1

),

worst_etf AS (

    SELECT
        month_start_date,
        symbol AS worst_performing_etf,
        ROUND(monthly_return_pct, 2) AS worst_performing_etf_return_pct
    FROM ranked_worst
    WHERE worst_rank = 1

),

final AS (

    SELECT
        m.month_start_date,
        m.total_etfs_count,
        m.positive_etfs_count,
        m.negative_etfs_count,
        m.flat_etfs_count,
        m.avg_monthly_return_pct,
        m.best_monthly_return_pct,
        m.worst_monthly_return_pct,

        b.best_performing_etf,
        b.best_performing_etf_return_pct,

        w.worst_performing_etf,
        w.worst_performing_etf_return_pct,

        ROUND(m.positive_etfs_count * 100.0 / m.total_etfs_count, 2)
            AS positive_etf_ratio_pct,

        current_timestamp() AS gold_created_at_utc

    FROM monthly_summary m

    INNER JOIN best_etf b
        ON m.month_start_date = b.month_start_date

    INNER JOIN worst_etf w
        ON m.month_start_date = w.month_start_date

)

SELECT *
FROM final