from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services.databricks_service import run_query
from services.metadata_service import load_etf_metadata


# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------

st.set_page_config(
    page_title="ETF Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

GREEN = "#22C55E"
RED = "#EF4444"
BLUE = "#3B82F6"
AMBER = "#F59E0B"
PURPLE = "#8B5CF6"
SLATE = "#94A3B8"

PLOTLY_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

MONTH_ORDER = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1500px;
            padding-top: 1.4rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }

        .dashboard-hero {
            padding: 1.25rem 1.4rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 16px;
            background: linear-gradient(
                120deg,
                rgba(59, 130, 246, 0.14),
                rgba(34, 197, 94, 0.06)
            );
        }

        .dashboard-hero h1 {
            margin: 0;
            font-size: 2.25rem;
            line-height: 1.15;
        }

        .dashboard-hero p {
            margin: 0.55rem 0 0;
            color: #94A3B8;
            font-size: 1rem;
        }

        .status-badge {
            display: inline-block;
            margin-bottom: 0.65rem;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            color: #86EFAC;
            background: rgba(34, 197, 94, 0.14);
            border: 1px solid rgba(34, 197, 94, 0.35);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.04em;
        }

        section[data-testid="stSidebar"] {
            width: 370px !important;
            min-width: 370px !important;
        }

        .etf-highlight-card {
            min-height: 165px;
            padding: 1rem 1.05rem;
            border: 1px solid rgba(148, 163, 184, 0.28);
            border-radius: 12px;
            background: rgba(15, 23, 42, 0.20);
        }

        .etf-highlight-label {
            margin-bottom: 0.45rem;
            color: #CBD5E1;
            font-size: 0.83rem;
            font-weight: 700;
        }

        .etf-highlight-name {
            min-height: 3.1rem;
            color: #F8FAFC;
            font-size: 1.05rem;
            font-weight: 700;
            line-height: 1.3;
            overflow-wrap: anywhere;
        }

        .etf-highlight-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            margin-top: 0.85rem;
        }

        .etf-highlight-symbol {
            color: #93C5FD;
            font-size: 1.35rem;
            font-weight: 800;
        }

        .etf-highlight-positive,
        .etf-highlight-neutral {
            padding: 0.2rem 0.5rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            white-space: nowrap;
        }

        .etf-highlight-positive {
            color: #86EFAC;
            background: rgba(34, 197, 94, 0.16);
        }

        .etf-highlight-neutral {
            color: #CBD5E1;
            background: rgba(148, 163, 184, 0.15);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------

def format_pct(value: object, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):,.{decimals}f}%"


def format_price(value: object) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"${float(value):,.2f}"


def format_date(value: object, month_only: bool = False) -> str:
    if value is None or pd.isna(value):
        return "—"

    timestamp = pd.Timestamp(value)
    date_format = "%b %Y" if month_only else "%d %b %Y"
    return timestamp.strftime(date_format)


def render_etf_highlight_card(
    *,
    label: str,
    symbol: object,
    name: object,
    metric_value: object,
    neutral: bool = False,
) -> None:
    """
    Render a compact ETF KPI card without truncating the ETF name.
    """
    symbol_text = "—" if symbol is None or pd.isna(symbol) else str(symbol)
    name_text = "—" if name is None or pd.isna(name) else str(name)
    metric_text = (
        "—"
        if metric_value is None or pd.isna(metric_value)
        else format_pct(metric_value)
    )
    badge_class = (
        "etf-highlight-neutral"
        if neutral
        else "etf-highlight-positive"
    )
    badge_prefix = "" if neutral else "↑ "

    st.markdown(
        f"""
        <div class="etf-highlight-card">
            <div class="etf-highlight-label">{label}</div>
            <div class="etf-highlight-name">{name_text}</div>
            <div class="etf-highlight-footer">
                <div class="etf-highlight-symbol">{symbol_text}</div>
                <div class="{badge_class}">
                    {badge_prefix}{metric_text}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def convert_dates(
    dataframe: pd.DataFrame,
    columns: Iterable[str],
) -> pd.DataFrame:
    result = dataframe.copy()

    for column in columns:
        if column in result.columns:
            result[column] = pd.to_datetime(
                result[column],
                errors="coerce",
            )

    return result


def convert_numbers(
    dataframe: pd.DataFrame,
    columns: Iterable[str],
) -> pd.DataFrame:
    result = dataframe.copy()

    for column in columns:
        if column in result.columns:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    return result


def style_figure(
    figure: go.Figure,
    *,
    height: int = 420,
    hovermode: str | None = None,
) -> go.Figure:
    figure.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=55, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        hovermode=hovermode,
    )

    figure.update_xaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.12)",
    )
    figure.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.12)",
    )

    return figure


def require_columns(
    dataframe: pd.DataFrame,
    required_columns: Iterable[str],
    table_name: str,
) -> None:
    missing = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            f"{table_name} is missing expected columns: "
            f"{', '.join(missing)}"
        )


def dataframe_to_csv(dataframe: pd.DataFrame) -> bytes:
    return dataframe.to_csv(index=False).encode("utf-8")


def load_gold_data() -> dict[str, pd.DataFrame]:
    """
    Read the five existing dashboard-facing Gold tables.

    run_query() already caches each SQL result for five minutes.
    """
    return {
        "long_term": run_query(
            "SELECT * FROM etf_long_term_performance"
        ),
        "monthly": run_query(
            "SELECT * FROM etf_month_by_month_performance"
        ),
        "market": run_query(
            "SELECT * FROM etf_monthly_market_summary"
        ),
        "risk": run_query(
            "SELECT * FROM etf_risk_summary"
        ),
        "alerts": run_query(
            "SELECT * FROM etf_alert_candidates"
        ),
    }


# -------------------------------------------------------------------
# Load, clean, and validate Gold data
# -------------------------------------------------------------------

try:
    data = load_gold_data()
    metadata = load_etf_metadata()

    long_term = convert_dates(
        data["long_term"],
        ["start_date", "end_date", "gold_created_at_utc"],
    )
    long_term = convert_numbers(
        long_term,
        [
            "first_adjusted_closing_price",
            "latest_adjusted_closing_price",
            "total_return",
            "total_return_pct",
        ],
    )

    monthly = convert_dates(
        data["monthly"],
        [
            "month_start_date",
            "first_trading_date_of_month",
            "last_trading_date_of_month",
            "gold_created_at_utc",
        ],
    )
    monthly = convert_numbers(
        monthly,
        [
            "first_adjusted_closing_price",
            "last_adjusted_closing_price",
            "monthly_return",
            "monthly_return_pct",
            "trading_days_count",
        ],
    )

    market = convert_dates(
        data["market"],
        ["month_start_date", "gold_created_at_utc"],
    )
    market = convert_numbers(
        market,
        [
            "total_etfs_count",
            "positive_etfs_count",
            "negative_etfs_count",
            "flat_etfs_count",
            "avg_monthly_return_pct",
            "best_monthly_return_pct",
            "worst_monthly_return_pct",
            "best_performing_etf_return_pct",
        ],
    )

    risk = convert_dates(
        data["risk"],
        ["gold_created_at_utc"],
    )
    risk = convert_numbers(
        risk,
        [
            "total_months_count",
            "positive_months_count",
            "negative_months_count",
            "flat_months_count",
            "avg_monthly_return_pct",
            "best_monthly_return_pct",
            "worst_monthly_return_pct",
            "monthly_volatility_pct",
            "positive_month_ratio_pct",
        ],
    )

    alerts = convert_dates(
        data["alerts"],
        ["month_start_date", "gold_created_at_utc"],
    )
    alerts = convert_numbers(
        alerts,
        ["monthly_return_pct"],
    )

    require_columns(
        long_term,
        [
            "symbol",
            "start_date",
            "end_date",
            "latest_adjusted_closing_price",
            "total_return_pct",
        ],
        "etf_long_term_performance",
    )

    require_columns(
        monthly,
        [
            "symbol",
            "month_start_date",
            "last_adjusted_closing_price",
            "monthly_return_pct",
        ],
        "etf_month_by_month_performance",
    )

    require_columns(
        market,
        [
            "month_start_date",
            "total_etfs_count",
            "positive_etfs_count",
            "negative_etfs_count",
            "flat_etfs_count",
            "avg_monthly_return_pct",
            "best_monthly_return_pct",
            "worst_monthly_return_pct",
            "best_performing_etf",
            "best_performing_etf_return_pct",
        ],
        "etf_monthly_market_summary",
    )

    require_columns(
        risk,
        [
            "symbol",
            "avg_monthly_return_pct",
            "monthly_volatility_pct",
            "positive_month_ratio_pct",
        ],
        "etf_risk_summary",
    )

    require_columns(
        alerts,
        [
            "symbol",
            "month_start_date",
            "monthly_return_pct",
            "alert_type",
            "alert_severity",
            "alert_message",
        ],
        "etf_alert_candidates",
    )

    metadata_name_map = (
        metadata.set_index("symbol")["name"].to_dict()
    )
    metadata_label_map = (
        metadata.set_index("symbol")["etf_label"].to_dict()
    )

    data_symbols = (
        set(long_term["symbol"].dropna().astype(str))
        | set(monthly["symbol"].dropna().astype(str))
        | set(risk["symbol"].dropna().astype(str))
        | set(alerts["symbol"].dropna().astype(str))
    )

    missing_metadata_symbols = sorted(
        data_symbols.difference(metadata_name_map)
    )

    if missing_metadata_symbols:
        raise ValueError(
            "ETF metadata is missing symbols: "
            + ", ".join(missing_metadata_symbols)
        )

    def etf_name(symbol: object) -> str:
        symbol_text = str(symbol)
        return metadata_name_map.get(symbol_text, symbol_text)

    def etf_label(symbol: object) -> str:
        symbol_text = str(symbol)
        return metadata_label_map.get(symbol_text, symbol_text)

    for dataframe in [long_term, monthly, risk, alerts]:
        dataframe["etf_name"] = (
            dataframe["symbol"]
            .astype(str)
            .map(metadata_name_map)
            .fillna(dataframe["symbol"].astype(str))
        )
        dataframe["etf_label"] = (
            dataframe["symbol"]
            .astype(str)
            .map(metadata_label_map)
            .fillna(dataframe["symbol"].astype(str))
        )

    market["best_performing_etf_name"] = (
        market["best_performing_etf"]
        .astype(str)
        .map(metadata_name_map)
        .fillna(market["best_performing_etf"].astype(str))
    )
    market["best_performing_etf_label"] = (
        market["best_performing_etf"]
        .astype(str)
        .map(metadata_label_map)
        .fillna(market["best_performing_etf"].astype(str))
    )

except Exception as error:
    st.error("The dashboard could not load the Databricks Gold tables.")

    with st.expander("Show technical error"):
        st.exception(error)

    st.stop()


if long_term.empty or monthly.empty or market.empty or risk.empty:
    st.warning("One or more required Gold tables are empty.")
    st.stop()


# -------------------------------------------------------------------
# Shared controls
# -------------------------------------------------------------------

symbols = sorted(
    set(long_term["symbol"].dropna().astype(str))
    | set(monthly["symbol"].dropna().astype(str))
)

available_months = (
    monthly["month_start_date"]
    .dropna()
    .drop_duplicates()
    .sort_values()
)

if available_months.empty:
    st.error("No valid monthly history was found.")
    st.stop()

date_options = [
    timestamp.date()
    for timestamp in available_months
]

default_comparison_symbols = (
    long_term
    .sort_values("total_return_pct", ascending=False)
    .head(min(5, len(long_term)))["symbol"]
    .tolist()
)

refresh_candidates: list[pd.Timestamp] = []

for dataframe in [long_term, monthly, market, risk, alerts]:
    if "gold_created_at_utc" not in dataframe.columns:
        continue

    latest_value = pd.to_datetime(
        dataframe["gold_created_at_utc"],
        errors="coerce",
    ).max()

    if pd.notna(latest_value):
        refresh_candidates.append(pd.Timestamp(latest_value))

latest_gold_refresh = (
    max(refresh_candidates)
    if refresh_candidates
    else None
)


with st.sidebar:
    st.header("Dashboard controls")

    st.caption(
        "Data source: "
        "`etf_market_intelligence.gold`"
    )

    if st.button(
        "Refresh from Databricks",
        type="primary",
        width="stretch",
    ):
        st.cache_data.clear()
        st.rerun()

    selected_date_range = st.select_slider(
        "Analysis period",
        options=date_options,
        value=(date_options[0], date_options[-1]),
        format_func=lambda value: value.strftime("%b %Y"),
    )

    start_date, end_date = selected_date_range
    start_timestamp = pd.Timestamp(start_date)
    end_timestamp = pd.Timestamp(end_date)

    selected_symbol = st.selectbox(
        "ETF Explorer",
        options=symbols,
        format_func=etf_label,
    )

    comparison_symbols = st.multiselect(
        "Comparison universe",
        options=symbols,
        default=default_comparison_symbols,
        max_selections=8,
        help=(
            "Ticker symbols are kept compact here. "
            "The complete ETF names are listed below."
        ),
    )

    if comparison_symbols:
        with st.expander(
            "Selected ETF names",
            expanded=False,
        ):
            for comparison_symbol in comparison_symbols:
                st.markdown(
                    f"**{comparison_symbol}** — "
                    f"{etf_name(comparison_symbol)}"
                )

    st.divider()

    st.markdown("**Gold layer status**")
    st.write(f"ETFs: **{len(symbols)}**")
    st.write(
        "Latest trading date: "
        f"**{format_date(long_term['end_date'].max())}**"
    )
    st.write(
        "Last Gold refresh: "
        f"**{format_date(latest_gold_refresh)}**"
    )

    st.caption(
        "Query results are cached for five minutes. "
        "Use Refresh after a new dbt run."
    )


monthly_filtered = monthly.loc[
    monthly["month_start_date"].between(
        start_timestamp,
        end_timestamp,
        inclusive="both",
    )
].copy()

market_filtered = market.loc[
    market["month_start_date"].between(
        start_timestamp,
        end_timestamp,
        inclusive="both",
    )
].copy()

alerts_filtered = alerts.loc[
    alerts["month_start_date"].between(
        start_timestamp,
        end_timestamp,
        inclusive="both",
    )
].copy()


# -------------------------------------------------------------------
# Header and navigation
# -------------------------------------------------------------------

st.markdown(
    f"""
    <div class="dashboard-hero">
        <div class="status-badge">DATABRICKS GOLD CONNECTED</div>
        <h1>ETF Market Intelligence</h1>
        <p>
            Long-term performance, monthly history, risk analytics,
            and alert monitoring for {len(symbols)} exchange-traded funds.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

overview_tab, explorer_tab, risk_tab, market_tab, alerts_tab = st.tabs(
    [
        "Overview",
        "ETF Explorer",
        "Risk & Return",
        "Market History",
        "Alerts",
    ]
)


# -------------------------------------------------------------------
# Tab 1: Overview
# -------------------------------------------------------------------

with overview_tab:
    latest_market_row = (
        market_filtered
        .sort_values("month_start_date")
        .tail(1)
    )

    best_long_term_row = (
        long_term
        .sort_values("total_return_pct", ascending=False)
        .head(1)
    )

    lowest_volatility_row = (
        risk
        .dropna(subset=["monthly_volatility_pct"])
        .sort_values("monthly_volatility_pct")
        .head(1)
    )

    latest_month = (
        latest_market_row.iloc[0]["month_start_date"]
        if not latest_market_row.empty
        else pd.NaT
    )

    summary_metric_columns = st.columns(3)

    summary_metric_columns[0].metric(
        "ETFs tracked",
        f"{len(symbols)}",
        border=True,
    )

    summary_metric_columns[1].metric(
        "Latest trading date",
        format_date(long_term["end_date"].max()),
        border=True,
    )

    summary_metric_columns[2].metric(
        "Latest market month",
        format_date(latest_month, month_only=True),
        border=True,
    )

    highlight_columns = st.columns(3)

    with highlight_columns[0]:
        if not latest_market_row.empty:
            latest_row = latest_market_row.iloc[0]
            render_etf_highlight_card(
                label="Monthly leader",
                symbol=latest_row["best_performing_etf"],
                name=latest_row["best_performing_etf_name"],
                metric_value=latest_row[
                    "best_performing_etf_return_pct"
                ],
            )
        else:
            render_etf_highlight_card(
                label="Monthly leader",
                symbol=None,
                name=None,
                metric_value=None,
            )

    with highlight_columns[1]:
        if not best_long_term_row.empty:
            best_row = best_long_term_row.iloc[0]
            render_etf_highlight_card(
                label="Best long-term ETF",
                symbol=best_row["symbol"],
                name=best_row["etf_name"],
                metric_value=best_row["total_return_pct"],
            )
        else:
            render_etf_highlight_card(
                label="Best long-term ETF",
                symbol=None,
                name=None,
                metric_value=None,
            )

    with highlight_columns[2]:
        if not lowest_volatility_row.empty:
            low_risk_row = lowest_volatility_row.iloc[0]
            render_etf_highlight_card(
                label="Lowest monthly volatility",
                symbol=low_risk_row["symbol"],
                name=low_risk_row["etf_name"],
                metric_value=low_risk_row[
                    "monthly_volatility_pct"
                ],
                neutral=True,
            )
        else:
            render_etf_highlight_card(
                label="Lowest monthly volatility",
                symbol=None,
                name=None,
                metric_value=None,
                neutral=True,
            )

    left_column, right_column = st.columns([1.15, 0.85])

    with left_column:
        long_term_chart_data = (
            long_term
            .dropna(subset=["total_return_pct"])
            .sort_values("total_return_pct")
            .tail(12)
        )

        long_term_figure = px.bar(
            long_term_chart_data,
            x="total_return_pct",
            y="etf_label",
            orientation="h",
            color="total_return_pct",
            color_continuous_scale=[
                [0.0, RED],
                [0.5, AMBER],
                [1.0, GREEN],
            ],
            text="total_return_pct",
            title="Top long-term performers",
            labels={
                "total_return_pct": "Total return (%)",
                "etf_label": "ETF",
            },
        )

        long_term_figure.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            cliponaxis=False,
        )
        long_term_figure.update_layout(coloraxis_showscale=False)
        style_figure(long_term_figure, height=470)

        st.plotly_chart(
            long_term_figure,
            width="stretch",
            config=PLOTLY_CONFIG,
        )

    with right_column:
        if not latest_market_row.empty:
            breadth = latest_market_row.iloc[0]

            breadth_figure = go.Figure(
                go.Pie(
                    labels=["Positive", "Negative", "Flat"],
                    values=[
                        breadth["positive_etfs_count"],
                        breadth["negative_etfs_count"],
                        breadth["flat_etfs_count"],
                    ],
                    hole=0.65,
                    marker_colors=[GREEN, RED, SLATE],
                    textinfo="label+value",
                )
            )

            breadth_figure.update_layout(
                title=(
                    "Latest market breadth — "
                    f"{format_date(latest_month, month_only=True)}"
                ),
                annotations=[
                    dict(
                        text=str(int(breadth["total_etfs_count"])),
                        x=0.5,
                        y=0.5,
                        font_size=24,
                        showarrow=False,
                    )
                ],
            )

            style_figure(breadth_figure, height=470)

            st.plotly_chart(
                breadth_figure,
                width="stretch",
                config=PLOTLY_CONFIG,
            )

    left_column, right_column = st.columns(2)

    with left_column:
        risk_return_data = risk.dropna(
            subset=[
                "monthly_volatility_pct",
                "avg_monthly_return_pct",
                "positive_month_ratio_pct",
            ]
        )

        risk_return_figure = px.scatter(
            risk_return_data,
            x="monthly_volatility_pct",
            y="avg_monthly_return_pct",
            size="positive_month_ratio_pct",
            color="avg_monthly_return_pct",
            text="etf_name",
            hover_name="etf_label",
            color_continuous_scale=[
                [0.0, RED],
                [0.5, AMBER],
                [1.0, GREEN],
            ],
            title="Monthly return versus volatility",
            labels={
                "monthly_volatility_pct": "Monthly volatility (%)",
                "avg_monthly_return_pct": "Average monthly return (%)",
                "positive_month_ratio_pct": "Positive months (%)",
            },
        )

        risk_return_figure.update_traces(textposition="top center")
        risk_return_figure.update_layout(coloraxis_showscale=False)
        style_figure(risk_return_figure, height=450)

        st.plotly_chart(
            risk_return_figure,
            width="stretch",
            config=PLOTLY_CONFIG,
        )

    with right_column:
        market_line_data = market_filtered.sort_values(
            "month_start_date"
        )

        market_line_figure = px.line(
            market_line_data,
            x="month_start_date",
            y="avg_monthly_return_pct",
            markers=True,
            title="Average ETF return by month",
            labels={
                "month_start_date": "Month",
                "avg_monthly_return_pct": "Average monthly return (%)",
            },
        )

        market_line_figure.add_hline(
            y=0,
            line_dash="dash",
            line_color=SLATE,
        )
        market_line_figure.update_traces(line_color=BLUE)
        style_figure(
            market_line_figure,
            height=450,
            hovermode="x unified",
        )

        st.plotly_chart(
            market_line_figure,
            width="stretch",
            config=PLOTLY_CONFIG,
        )

    st.subheader("Long-term performance table")

    overview_table = (
        long_term[
            [
                "etf_name",
                "symbol",
                "start_date",
                "end_date",
                "latest_adjusted_closing_price",
                "total_return_pct",
            ]
        ]
        .sort_values("total_return_pct", ascending=False)
        .reset_index(drop=True)
    )

    st.dataframe(
        overview_table,
        width="stretch",
        hide_index=True,
        column_config={
            "etf_name": st.column_config.TextColumn(
                "ETF name",
                width="large",
            ),
            "symbol": st.column_config.TextColumn("Ticker"),
            "start_date": st.column_config.DateColumn(
                "Start date",
                format="DD MMM YYYY",
            ),
            "end_date": st.column_config.DateColumn(
                "Latest date",
                format="DD MMM YYYY",
            ),
            "latest_adjusted_closing_price": (
                st.column_config.NumberColumn(
                    "Latest adjusted close",
                    format="$%.2f",
                )
            ),
            "total_return_pct": st.column_config.NumberColumn(
                "Total return",
                format="%.2f%%",
            ),
        },
    )


# -------------------------------------------------------------------
# Tab 2: ETF Explorer
# -------------------------------------------------------------------

with explorer_tab:
    symbol_long_term = long_term.loc[
        long_term["symbol"].eq(selected_symbol)
    ].head(1)

    symbol_risk = risk.loc[
        risk["symbol"].eq(selected_symbol)
    ].head(1)

    symbol_monthly = (
        monthly_filtered.loc[
            monthly_filtered["symbol"].eq(selected_symbol)
        ]
        .sort_values("month_start_date")
        .copy()
    )

    st.subheader(f"{etf_label(selected_symbol)} Explorer")

    st.caption(
        f"Analysis period: "
        f"{format_date(start_timestamp, month_only=True)} to "
        f"{format_date(end_timestamp, month_only=True)}"
    )

    explorer_metrics = st.columns(6)

    if not symbol_long_term.empty:
        long_row = symbol_long_term.iloc[0]

        explorer_metrics[0].metric(
            "Latest adjusted close",
            format_price(long_row["latest_adjusted_closing_price"]),
            border=True,
        )
        explorer_metrics[1].metric(
            "Total return",
            format_pct(long_row["total_return_pct"]),
            border=True,
        )
        explorer_metrics[2].metric(
            "History begins",
            format_date(long_row["start_date"]),
            border=True,
        )

    if not symbol_risk.empty:
        risk_row = symbol_risk.iloc[0]

        explorer_metrics[3].metric(
            "Average monthly return",
            format_pct(risk_row["avg_monthly_return_pct"]),
            border=True,
        )
        explorer_metrics[4].metric(
            "Monthly volatility",
            format_pct(risk_row["monthly_volatility_pct"]),
            border=True,
        )
        explorer_metrics[5].metric(
            "Positive months",
            format_pct(risk_row["positive_month_ratio_pct"]),
            border=True,
        )

    if symbol_monthly.empty:
        st.info(
            "No monthly records exist for this ETF "
            "in the selected period."
        )
    else:
        symbol_monthly["return_direction"] = np.where(
            symbol_monthly["monthly_return_pct"].ge(0),
            "Positive",
            "Negative",
        )

        growth_multiplier = (
            1
            + symbol_monthly["monthly_return_pct"].fillna(0) / 100
        ).cumprod()

        symbol_monthly["growth_of_100"] = (
            100
            * growth_multiplier
            / growth_multiplier.iloc[0]
        )

        left_column, right_column = st.columns(2)

        with left_column:
            price_figure = px.line(
                symbol_monthly,
                x="month_start_date",
                y="last_adjusted_closing_price",
                markers=True,
                title=f"{etf_name(selected_symbol)} adjusted closing price",
                labels={
                    "month_start_date": "Month",
                    "last_adjusted_closing_price": (
                        "Adjusted close ($)"
                    ),
                },
            )

            price_figure.update_traces(
                line_color=BLUE,
                fill="tozeroy",
                fillcolor="rgba(59,130,246,0.10)",
            )

            style_figure(
                price_figure,
                height=430,
                hovermode="x unified",
            )

            st.plotly_chart(
                price_figure,
                width="stretch",
                config=PLOTLY_CONFIG,
            )

        with right_column:
            return_figure = px.bar(
                symbol_monthly,
                x="month_start_date",
                y="monthly_return_pct",
                color="return_direction",
                color_discrete_map={
                    "Positive": GREEN,
                    "Negative": RED,
                },
                title=f"{etf_name(selected_symbol)} monthly returns",
                labels={
                    "month_start_date": "Month",
                    "monthly_return_pct": "Monthly return (%)",
                },
            )

            return_figure.add_hline(
                y=0,
                line_dash="dash",
                line_color=SLATE,
            )

            style_figure(return_figure, height=430)

            st.plotly_chart(
                return_figure,
                width="stretch",
                config=PLOTLY_CONFIG,
            )

        left_column, right_column = st.columns([0.85, 1.15])

        with left_column:
            growth_figure = px.line(
                symbol_monthly,
                x="month_start_date",
                y="growth_of_100",
                title="Growth of a normalized $100",
                labels={
                    "month_start_date": "Month",
                    "growth_of_100": "Portfolio value ($)",
                },
            )

            growth_figure.update_traces(
                line_color=GREEN,
                line_width=3,
            )

            style_figure(
                growth_figure,
                height=430,
                hovermode="x unified",
            )

            st.plotly_chart(
                growth_figure,
                width="stretch",
                config=PLOTLY_CONFIG,
            )

        with right_column:
            heatmap_data = symbol_monthly[
                ["month_start_date", "monthly_return_pct"]
            ].copy()

            heatmap_data["year"] = (
                heatmap_data["month_start_date"].dt.year
            )
            heatmap_data["month"] = (
                heatmap_data["month_start_date"].dt.strftime("%b")
            )

            heatmap_pivot = (
                heatmap_data
                .pivot_table(
                    index="year",
                    columns="month",
                    values="monthly_return_pct",
                    aggfunc="first",
                )
                .reindex(columns=MONTH_ORDER)
                .sort_index()
            )

            heatmap_text = heatmap_pivot.map(
                lambda value: (
                    ""
                    if pd.isna(value)
                    else f"{value:.1f}%"
                )
            )

            heatmap_figure = go.Figure(
                go.Heatmap(
                    z=heatmap_pivot.values,
                    x=heatmap_pivot.columns,
                    y=heatmap_pivot.index.astype(str),
                    text=heatmap_text.values,
                    texttemplate="%{text}",
                    zmid=0,
                    colorscale=[
                        [0.0, "#7F1D1D"],
                        [0.5, "#111827"],
                        [1.0, "#14532D"],
                    ],
                    colorbar=dict(title="Return %"),
                    hovertemplate=(
                        "Year %{y}<br>"
                        "Month %{x}<br>"
                        "Return %{z:.2f}%"
                        "<extra></extra>"
                    ),
                )
            )

            heatmap_figure.update_layout(
                title="Monthly return heatmap"
            )

            style_figure(
                heatmap_figure,
                height=max(
                    430,
                    28 * len(heatmap_pivot) + 150,
                ),
            )

            st.plotly_chart(
                heatmap_figure,
                width="stretch",
                config=PLOTLY_CONFIG,
            )

        st.subheader("Recent monthly observations")

        recent_months = (
            symbol_monthly[
                [
                    "month_start_date",
                    "first_trading_date_of_month",
                    "last_trading_date_of_month",
                    "first_adjusted_closing_price",
                    "last_adjusted_closing_price",
                    "monthly_return_pct",
                    "trading_days_count",
                ]
            ]
            .sort_values(
                "month_start_date",
                ascending=False,
            )
            .head(18)
        )

        st.dataframe(
            recent_months,
            width="stretch",
            hide_index=True,
            column_config={
                "month_start_date": st.column_config.DateColumn(
                    "Month",
                    format="MMM YYYY",
                ),
                "first_trading_date_of_month": (
                    st.column_config.DateColumn(
                        "First trading date",
                        format="DD MMM YYYY",
                    )
                ),
                "last_trading_date_of_month": (
                    st.column_config.DateColumn(
                        "Last trading date",
                        format="DD MMM YYYY",
                    )
                ),
                "first_adjusted_closing_price": (
                    st.column_config.NumberColumn(
                        "Opening adjusted close",
                        format="$%.2f",
                    )
                ),
                "last_adjusted_closing_price": (
                    st.column_config.NumberColumn(
                        "Closing adjusted close",
                        format="$%.2f",
                    )
                ),
                "monthly_return_pct": (
                    st.column_config.NumberColumn(
                        "Monthly return",
                        format="%.2f%%",
                    )
                ),
                "trading_days_count": (
                    st.column_config.NumberColumn(
                        "Trading days",
                        format="%d",
                    )
                ),
            },
        )

        st.download_button(
            label=(
                f"Download {selected_symbol} monthly history"
            ),
            data=dataframe_to_csv(symbol_monthly),
            file_name=(
                f"{selected_symbol.lower()}_monthly_history.csv"
            ),
            mime="text/csv",
        )


# -------------------------------------------------------------------
# Tab 3: Risk & Return
# -------------------------------------------------------------------

with risk_tab:
    st.subheader("Cross-ETF risk and return comparison")

    st.caption(
        "Monthly volatility measures the dispersion of monthly "
        "returns. It is not annualized volatility."
    )

    risk_performance = risk.merge(
        long_term[
            [
                "symbol",
                "latest_adjusted_closing_price",
                "total_return_pct",
            ]
        ],
        on="symbol",
        how="left",
    )

    if comparison_symbols:
        selected_risk = risk_performance.loc[
            risk_performance["symbol"].isin(
                comparison_symbols
            )
        ].copy()
    else:
        selected_risk = risk_performance.copy()

    left_column, right_column = st.columns(2)

    with left_column:
        risk_scatter = px.scatter(
            selected_risk,
            x="monthly_volatility_pct",
            y="avg_monthly_return_pct",
            size="positive_month_ratio_pct",
            color="total_return_pct",
            text="etf_name",
            hover_name="etf_label",
            color_continuous_scale=[
                [0.0, RED],
                [0.5, AMBER],
                [1.0, GREEN],
            ],
            title="Risk-return map",
            labels={
                "monthly_volatility_pct": "Monthly volatility (%)",
                "avg_monthly_return_pct": (
                    "Average monthly return (%)"
                ),
                "positive_month_ratio_pct": (
                    "Positive months (%)"
                ),
                "total_return_pct": "Total return (%)",
            },
        )

        risk_scatter.update_traces(
            textposition="top center"
        )
        style_figure(risk_scatter, height=470)

        st.plotly_chart(
            risk_scatter,
            width="stretch",
            config=PLOTLY_CONFIG,
        )

    with right_column:
        volatility_data = (
            selected_risk
            .dropna(subset=["monthly_volatility_pct"])
            .sort_values("monthly_volatility_pct")
        )

        volatility_figure = px.bar(
            volatility_data,
            x="monthly_volatility_pct",
            y="etf_label",
            orientation="h",
            color="monthly_volatility_pct",
            color_continuous_scale=[
                [0.0, GREEN],
                [0.5, AMBER],
                [1.0, RED],
            ],
            text="monthly_volatility_pct",
            title="Monthly volatility ranking",
            labels={
                "monthly_volatility_pct": (
                    "Monthly volatility (%)"
                ),
                "etf_label": "ETF",
            },
        )

        volatility_figure.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside",
        )
        volatility_figure.update_layout(
            coloraxis_showscale=False
        )
        style_figure(volatility_figure, height=470)

        st.plotly_chart(
            volatility_figure,
            width="stretch",
            config=PLOTLY_CONFIG,
        )

    st.subheader("Risk summary table")

    risk_table_columns = [
        "etf_name",
        "symbol",
        "total_months_count",
        "positive_months_count",
        "negative_months_count",
        "avg_monthly_return_pct",
        "best_monthly_return_pct",
        "worst_monthly_return_pct",
        "monthly_volatility_pct",
        "positive_month_ratio_pct",
        "total_return_pct",
    ]

    risk_table_columns = [
        column
        for column in risk_table_columns
        if column in selected_risk.columns
    ]

    risk_table = (
        selected_risk[risk_table_columns]
        .sort_values(
            [
                "monthly_volatility_pct",
                "avg_monthly_return_pct",
            ],
            ascending=[True, False],
        )
        .reset_index(drop=True)
    )

    st.dataframe(
        risk_table,
        width="stretch",
        hide_index=True,
        column_config={
            "etf_name": st.column_config.TextColumn(
                "ETF name",
                width="large",
            ),
            "symbol": st.column_config.TextColumn("Ticker"),
            "total_months_count": (
                st.column_config.NumberColumn(
                    "Months",
                    format="%d",
                )
            ),
            "positive_months_count": (
                st.column_config.NumberColumn(
                    "Positive months",
                    format="%d",
                )
            ),
            "negative_months_count": (
                st.column_config.NumberColumn(
                    "Negative months",
                    format="%d",
                )
            ),
            "avg_monthly_return_pct": (
                st.column_config.NumberColumn(
                    "Average monthly return",
                    format="%.2f%%",
                )
            ),
            "best_monthly_return_pct": (
                st.column_config.NumberColumn(
                    "Best month",
                    format="%.2f%%",
                )
            ),
            "worst_monthly_return_pct": (
                st.column_config.NumberColumn(
                    "Worst month",
                    format="%.2f%%",
                )
            ),
            "monthly_volatility_pct": (
                st.column_config.NumberColumn(
                    "Monthly volatility",
                    format="%.2f%%",
                )
            ),
            "positive_month_ratio_pct": (
                st.column_config.NumberColumn(
                    "Positive-month ratio",
                    format="%.2f%%",
                )
            ),
            "total_return_pct": (
                st.column_config.NumberColumn(
                    "Total return",
                    format="%.2f%%",
                )
            ),
        },
    )


# -------------------------------------------------------------------
# Tab 4: Market History
# -------------------------------------------------------------------

with market_tab:
    st.subheader("Monthly market history")

    market_history = (
        market_filtered
        .sort_values("month_start_date")
        .copy()
    )

    if market_history.empty:
        st.info(
            "No market-summary rows exist "
            "in the selected period."
        )
    else:
        market_history["positive_breadth_pct"] = np.where(
            market_history["total_etfs_count"].gt(0),
            100
            * market_history["positive_etfs_count"]
            / market_history["total_etfs_count"],
            np.nan,
        )

        market_history["negative_breadth_pct"] = np.where(
            market_history["total_etfs_count"].gt(0),
            100
            * market_history["negative_etfs_count"]
            / market_history["total_etfs_count"],
            np.nan,
        )

        market_history["flat_breadth_pct"] = np.where(
            market_history["total_etfs_count"].gt(0),
            100
            * market_history["flat_etfs_count"]
            / market_history["total_etfs_count"],
            np.nan,
        )

        left_column, right_column = st.columns(2)

        with left_column:
            range_figure = go.Figure()

            range_figure.add_trace(
                go.Scatter(
                    x=market_history["month_start_date"],
                    y=market_history[
                        "best_monthly_return_pct"
                    ],
                    name="Best ETF",
                    line=dict(color=GREEN),
                )
            )

            range_figure.add_trace(
                go.Scatter(
                    x=market_history["month_start_date"],
                    y=market_history[
                        "avg_monthly_return_pct"
                    ],
                    name="Market average",
                    line=dict(
                        color=BLUE,
                        width=3,
                    ),
                )
            )

            range_figure.add_trace(
                go.Scatter(
                    x=market_history["month_start_date"],
                    y=market_history[
                        "worst_monthly_return_pct"
                    ],
                    name="Worst ETF",
                    line=dict(color=RED),
                )
            )

            range_figure.add_hline(
                y=0,
                line_dash="dash",
                line_color=SLATE,
            )

            range_figure.update_layout(
                title="Monthly return range",
                xaxis_title="Month",
                yaxis_title="Return (%)",
            )

            style_figure(
                range_figure,
                height=450,
                hovermode="x unified",
            )

            st.plotly_chart(
                range_figure,
                width="stretch",
                config=PLOTLY_CONFIG,
            )

        with right_column:
            breadth_figure = go.Figure()

            breadth_figure.add_trace(
                go.Scatter(
                    x=market_history["month_start_date"],
                    y=market_history["positive_breadth_pct"],
                    name="Positive",
                    stackgroup="one",
                    line=dict(color=GREEN),
                )
            )

            breadth_figure.add_trace(
                go.Scatter(
                    x=market_history["month_start_date"],
                    y=market_history["flat_breadth_pct"],
                    name="Flat",
                    stackgroup="one",
                    line=dict(color=SLATE),
                )
            )

            breadth_figure.add_trace(
                go.Scatter(
                    x=market_history["month_start_date"],
                    y=market_history["negative_breadth_pct"],
                    name="Negative",
                    stackgroup="one",
                    line=dict(color=RED),
                )
            )

            breadth_figure.update_layout(
                title="Market breadth composition",
                xaxis_title="Month",
                yaxis_title="Share of ETFs (%)",
                yaxis_range=[0, 100],
            )

            style_figure(
                breadth_figure,
                height=450,
                hovermode="x unified",
            )

            st.plotly_chart(
                breadth_figure,
                width="stretch",
                config=PLOTLY_CONFIG,
            )

        winners = (
            market_history["best_performing_etf_label"]
            .dropna()
            .astype(str)
            .value_counts()
            .rename_axis("etf_label")
            .reset_index(name="months_won")
            .sort_values("months_won")
        )

        left_column, right_column = st.columns(
            [0.8, 1.2]
        )

        with left_column:
            winners_figure = px.bar(
                winners,
                x="months_won",
                y="etf_label",
                orientation="h",
                color="months_won",
                color_continuous_scale="Blues",
                text="months_won",
                title="Monthly winner leaderboard",
                labels={
                    "months_won": "Months ranked first",
                    "etf_label": "ETF",
                },
            )

            winners_figure.update_layout(
                coloraxis_showscale=False
            )

            style_figure(
                winners_figure,
                height=max(
                    430,
                    30 * len(winners) + 140,
                ),
            )

            st.plotly_chart(
                winners_figure,
                width="stretch",
                config=PLOTLY_CONFIG,
            )

        with right_column:
            st.markdown(
                "#### Recent monthly market summaries"
            )

            market_table = (
                market_history[
                    [
                        "month_start_date",
                        "total_etfs_count",
                        "positive_etfs_count",
                        "negative_etfs_count",
                        "avg_monthly_return_pct",
                        "best_performing_etf_name",
                        "best_performing_etf",
                        "best_performing_etf_return_pct",
                        "worst_monthly_return_pct",
                    ]
                ]
                .sort_values(
                    "month_start_date",
                    ascending=False,
                )
                .head(24)
            )

            st.dataframe(
                market_table,
                width="stretch",
                hide_index=True,
                column_config={
                    "month_start_date": (
                        st.column_config.DateColumn(
                            "Month",
                            format="MMM YYYY",
                        )
                    ),
                    "total_etfs_count": (
                        st.column_config.NumberColumn(
                            "ETFs",
                            format="%d",
                        )
                    ),
                    "positive_etfs_count": (
                        st.column_config.NumberColumn(
                            "Positive",
                            format="%d",
                        )
                    ),
                    "negative_etfs_count": (
                        st.column_config.NumberColumn(
                            "Negative",
                            format="%d",
                        )
                    ),
                    "avg_monthly_return_pct": (
                        st.column_config.NumberColumn(
                            "Average return",
                            format="%.2f%%",
                        )
                    ),
                    "best_performing_etf_name": (
                        st.column_config.TextColumn(
                            "Best ETF name",
                            width="large",
                        )
                    ),
                    "best_performing_etf": (
                        st.column_config.TextColumn(
                            "Ticker"
                        )
                    ),
                    "best_performing_etf_return_pct": (
                        st.column_config.NumberColumn(
                            "Best return",
                            format="%.2f%%",
                        )
                    ),
                    "worst_monthly_return_pct": (
                        st.column_config.NumberColumn(
                            "Worst return",
                            format="%.2f%%",
                        )
                    ),
                },
            )

        st.download_button(
            label="Download filtered market history",
            data=dataframe_to_csv(market_history),
            file_name="etf_monthly_market_history.csv",
            mime="text/csv",
        )


# -------------------------------------------------------------------
# Tab 5: Alerts
# -------------------------------------------------------------------

with alerts_tab:
    st.subheader("ETF alert monitoring")

    st.caption(
        "Alert business logic comes from the dbt Gold model. "
        "Streamlit only filters and visualizes it."
    )

    alert_severities = sorted(
        alerts_filtered["alert_severity"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    alert_types = sorted(
        alerts_filtered["alert_type"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    filter_column_1, filter_column_2 = st.columns(2)

    with filter_column_1:
        selected_severities = st.multiselect(
            "Alert severity",
            options=alert_severities,
            default=alert_severities,
        )

    with filter_column_2:
        selected_alert_types = st.multiselect(
            "Alert type",
            options=alert_types,
            default=alert_types,
        )

    displayed_alerts = alerts_filtered.copy()

    if selected_severities:
        displayed_alerts = displayed_alerts.loc[
            displayed_alerts[
                "alert_severity"
            ].astype(str).isin(selected_severities)
        ]
    else:
        displayed_alerts = displayed_alerts.iloc[0:0]

    if selected_alert_types:
        displayed_alerts = displayed_alerts.loc[
            displayed_alerts[
                "alert_type"
            ].astype(str).isin(selected_alert_types)
        ]
    else:
        displayed_alerts = displayed_alerts.iloc[0:0]

    alert_metrics = st.columns(4)

    alert_metrics[0].metric(
        "Filtered alerts",
        f"{len(displayed_alerts):,}",
        border=True,
    )
    alert_metrics[1].metric(
        "ETFs affected",
        f"{displayed_alerts['symbol'].nunique():,}",
        border=True,
    )
    alert_metrics[2].metric(
        "Alert types",
        f"{displayed_alerts['alert_type'].nunique():,}",
        border=True,
    )
    alert_metrics[3].metric(
        "Latest alert month",
        format_date(
            displayed_alerts["month_start_date"].max(),
            month_only=True,
        ),
        border=True,
    )

    if displayed_alerts.empty:
        st.info("No alerts match the selected filters.")
    else:
        left_column, right_column = st.columns(2)

        with left_column:
            severity_counts = (
                displayed_alerts["alert_severity"]
                .astype(str)
                .value_counts()
                .rename_axis("alert_severity")
                .reset_index(name="alert_count")
            )

            severity_figure = px.bar(
                severity_counts,
                x="alert_severity",
                y="alert_count",
                color="alert_severity",
                title="Alerts by severity",
                labels={
                    "alert_severity": "Severity",
                    "alert_count": "Alerts",
                },
            )

            style_figure(severity_figure, height=390)

            st.plotly_chart(
                severity_figure,
                width="stretch",
                config=PLOTLY_CONFIG,
            )

        with right_column:
            type_counts = (
                displayed_alerts["alert_type"]
                .astype(str)
                .value_counts()
                .rename_axis("alert_type")
                .reset_index(name="alert_count")
                .sort_values("alert_count")
            )

            type_figure = px.bar(
                type_counts,
                x="alert_count",
                y="alert_type",
                orientation="h",
                color="alert_count",
                color_continuous_scale="Oranges",
                title="Alerts by type",
                labels={
                    "alert_type": "Alert type",
                    "alert_count": "Alerts",
                },
            )

            type_figure.update_layout(
                coloraxis_showscale=False
            )

            style_figure(
                type_figure,
                height=max(
                    390,
                    35 * len(type_counts) + 140,
                ),
            )

            st.plotly_chart(
                type_figure,
                width="stretch",
                config=PLOTLY_CONFIG,
            )

        alert_table = (
            displayed_alerts[
                [
                    "month_start_date",
                    "etf_name",
                    "symbol",
                    "monthly_return_pct",
                    "alert_type",
                    "alert_severity",
                    "alert_message",
                ]
            ]
            .sort_values(
                ["month_start_date", "symbol"],
                ascending=[False, True],
            )
            .head(200)
        )

        st.dataframe(
            alert_table,
            width="stretch",
            hide_index=True,
            column_config={
                "month_start_date": (
                    st.column_config.DateColumn(
                        "Month",
                        format="MMM YYYY",
                    )
                ),
                "etf_name": st.column_config.TextColumn(
                    "ETF name",
                    width="large",
                ),
                "symbol": st.column_config.TextColumn("Ticker"),
                "monthly_return_pct": (
                    st.column_config.NumberColumn(
                        "Monthly return",
                        format="%.2f%%",
                    )
                ),
                "alert_type": (
                    st.column_config.TextColumn(
                        "Alert type"
                    )
                ),
                "alert_severity": (
                    st.column_config.TextColumn(
                        "Severity"
                    )
                ),
                "alert_message": (
                    st.column_config.TextColumn(
                        "Message",
                        width="large",
                    )
                ),
            },
        )

        st.download_button(
            label="Download filtered alerts",
            data=dataframe_to_csv(displayed_alerts),
            file_name="etf_alerts.csv",
            mime="text/csv",
        )


st.divider()

st.caption(
    "ETF Market Intelligence Pipeline · "
    "Python · Databricks · dbt · Streamlit"
)