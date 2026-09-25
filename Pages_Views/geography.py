import streamlit as st
import pandas as pd
from html import escape

from Components.filters import render_overview_filters
from Components.kpi_cards import render_kpi_card
from Components.charts import render_chart
from db_connection import get_connection


# --------------------------------------------------
# DATABASE QUERY HELPER
# --------------------------------------------------

@st.cache_data(ttl=300)
def _query(sql, params=()):
    conn = get_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


# --------------------------------------------------
# FILTER HELPER
# --------------------------------------------------

def _where(filters, sales_only=True):
    clauses = []
    params = []

    if sales_only:
        clauses.append("transaction_type = 'Sale'")

    for key, column in (
        ("country", "country"),
        ("year", "year"),
        ("month", "month"),
    ):
        value = filters.get(key)
        if value is not None:
            clauses.append(f"{column} = %s")
            params.append(value)

    return ("WHERE " + " AND ".join(clauses) if clauses else ""), tuple(params)


def _compact(value, currency=False, decimals=2):
    value = float(value or 0)
    if abs(value) >= 1_000_000:
        result = f"{value / 1_000_000:,.{decimals}f}M"
    elif abs(value) >= 1_000:
        result = f"{value / 1_000:,.2f}K"
    else:
        result = f"{value:,.{decimals}f}" if currency else f"{value:,.0f}"
    return f"£{result}" if currency else result


# --------------------------------------------------
# GEOGRAPHY ANALYSIS PAGE
# --------------------------------------------------

def render_geography_page():
    st.markdown(
        """
        <div class="page-kicker">Market Intelligence</div>
        <div class="page-title">Geographic Analysis</div>
        <div class="page-sub">
            Explore market reach, country-level revenue, customer distribution,
            and the balance between UK and international sales.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    filters = render_overview_filters()
    where, params = _where(filters, sales_only=True)
    geo_where = where + (" AND " if where else "WHERE ") + "country IS NOT NULL"

    try:
        # --------------------------------------------------
        # 1. GEOGRAPHY KPIs
        # --------------------------------------------------
        kpi = _query(
            f"""
            SELECT
                COUNT(DISTINCT country) AS countries,
                COALESCE(SUM(revenue), 0) AS revenue,
                COUNT(DISTINCT invoice) AS orders,
                COUNT(DISTINCT customer_id) FILTER (
                    WHERE customer_id IS NOT NULL
                ) AS customers,
                COALESCE(SUM(quantity), 0) AS units,
                COALESCE(
                    SUM(revenue) / NULLIF(COUNT(DISTINCT country), 0), 0
                ) AS revenue_per_country,
                COALESCE(
                    SUM(revenue) FILTER (WHERE country <> 'United Kingdom'), 0
                ) AS international_revenue,
                COALESCE(
                    SUM(revenue) FILTER (WHERE country = 'United Kingdom'), 0
                ) AS uk_revenue
            FROM analytics.base_sales
            {geo_where};
            """,
            params,
        ).iloc[0]

        total_countries = int(kpi["countries"] or 0)
        total_revenue = float(kpi["revenue"] or 0)
        total_orders = int(kpi["orders"] or 0)
        total_customers = int(kpi["customers"] or 0)
        revenue_per_country = float(kpi["revenue_per_country"] or 0)
        international_revenue = float(kpi["international_revenue"] or 0)
        uk_revenue = float(kpi["uk_revenue"] or 0)

        international_share = (
            100 * international_revenue / total_revenue if total_revenue else 0
        )
        uk_share = 100 * uk_revenue / total_revenue if total_revenue else 0

        # --------------------------------------------------
        # 2. COUNTRY PERFORMANCE
        # --------------------------------------------------
        country_perf = _query(
            f"""
            SELECT
                country,
                SUM(revenue) AS revenue,
                COUNT(DISTINCT invoice) AS orders,
                COUNT(DISTINCT customer_id) FILTER (
                    WHERE customer_id IS NOT NULL
                ) AS customers,
                SUM(quantity) AS units
            FROM analytics.base_sales
            {geo_where}
            GROUP BY country
            ORDER BY revenue DESC;
            """,
            params,
        )

        # --------------------------------------------------
        # 3. MONTHLY UK VS INTERNATIONAL REVENUE
        # --------------------------------------------------
        monthly_market = _query(
            f"""
            SELECT
                DATE_TRUNC('month', invoice_date)::date AS month_start,
                CASE
                    WHEN country = 'United Kingdom' THEN 'United Kingdom'
                    ELSE 'International'
                END AS market_group,
                SUM(revenue) / 1000000.0 AS revenue_m
            FROM analytics.base_sales
            {geo_where}
            GROUP BY month_start, market_group
            ORDER BY month_start, market_group;
            """,
            params,
        )

        # --------------------------------------------------
        # 4. KPI CARDS
        # --------------------------------------------------
        st.markdown(
            '<div class="section-title">Geographic Overview</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card(
                "Markets Served",
                f"{total_countries:,}",
                "Countries in selected sales data",
                featured=True,
            )
        with c2:
            render_kpi_card(
                "Total Revenue",
                _compact(total_revenue, currency=True),
                "Sales across selected markets",
            )
        with c3:
            render_kpi_card(
                "Revenue per Market",
                f"£{revenue_per_country:,.0f}",
                "Average revenue per country",
            )
        with c4:
            render_kpi_card(
                "International Revenue Share",
                f"{international_share:.1f}%",
                "Outside the United Kingdom",
            )

        # --------------------------------------------------
        # 5. CHART DATA PREPARATION
        # --------------------------------------------------
        revenue_plot = country_perf.nlargest(10, "revenue").copy()
        orders_plot = country_perf.nlargest(10, "orders").copy()
        customers_plot = country_perf.nlargest(10, "customers").copy()
        monthly_plot = monthly_market.copy()

        for frame in (revenue_plot,):
            if not frame.empty:
                frame["revenue_m"] = frame["revenue"].astype(float) / 1_000_000

        # --------------------------------------------------
        # 6. COUNTRY PERFORMANCE CHARTS
        # --------------------------------------------------
        st.write("")
        st.markdown(
            '<div class="section-title">Market Performance</div>',
            unsafe_allow_html=True,
        )

        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                st.markdown(
                    '<div class="card-title">Top 10 Countries by Revenue</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="card-sub">Highest revenue-contributing markets (£M)</div>',
                    unsafe_allow_html=True,
                )
                if not revenue_plot.empty:
                    render_chart(
                        revenue_plot, "bar", "country", "revenue_m",
                        x_label="Country", y_label="Revenue (£M)", height=360,
                    )
                else:
                    st.info("No country revenue data available.")

        with right:
            with st.container(border=True):
                st.markdown(
                    '<div class="card-title">Top 10 Countries by Orders</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="card-sub">Markets ranked by distinct sales invoices</div>',
                    unsafe_allow_html=True,
                )
                if not orders_plot.empty:
                    render_chart(
                        orders_plot, "bar", "country", "orders",
                        x_label="Country", y_label="Orders", height=360,
                    )
                else:
                    st.info("No country order data available.")

        st.write("")
        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                st.markdown(
                    '<div class="card-title">Top 10 Countries by Identified Customers</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="card-sub">Distinct customers with an available customer ID</div>',
                    unsafe_allow_html=True,
                )
                if not customers_plot.empty:
                    render_chart(
                        customers_plot, "bar", "country", "customers",
                        x_label="Country", y_label="Identified Customers", height=360,
                    )
                else:
                    st.info("No identified-customer data available.")

        with right:
            with st.container(border=True):
                st.markdown(
                    '<div class="card-title">UK vs International Revenue</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="card-sub">Monthly sales trend by domestic and international markets (£M)</div>',
                    unsafe_allow_html=True,
                )
                if not monthly_plot.empty:
                    render_chart(
                        monthly_plot, "line", "month_start", "revenue_m",
                        x_label="Month", y_label="Revenue (£M)",
                        color="market_group", height=360,
                    )
                else:
                    st.info("No monthly market data available.")

        # --------------------------------------------------
        # 7. THREE GEOGRAPHIC INSIGHT CARDS
        # --------------------------------------------------
        if not country_perf.empty:
            top_market = country_perf.iloc[0]
            top_market_name = str(top_market["country"])
            top_market_revenue = float(top_market["revenue"] or 0)
            top_market_orders = int(top_market["orders"] or 0)
            top_market_share = (
                100 * top_market_revenue / total_revenue if total_revenue else 0
            )
            top5_revenue = float(country_perf.head(5)["revenue"].sum())
            top10_revenue = float(country_perf.head(10)["revenue"].sum())
            top5_share = 100 * top5_revenue / total_revenue if total_revenue else 0
            top10_share = 100 * top10_revenue / total_revenue if total_revenue else 0
        else:
            top_market_name = "—"
            top_market_revenue = top_market_orders = 0
            top_market_share = top5_share = top10_share = 0

        st.write("")
        st.markdown(
            '<div class="section-title">Geographic Performance Insights</div>',
            unsafe_allow_html=True,
        )

        safe_top_market = escape(top_market_name)

        insight_html = f"""
        <div class="insight-grid">
            <div class="insight-card">
                <div class="card-title">Leading Market</div>
                <div class="card-sub">Top country by sales revenue</div>
                <div class="signal-item"><span>Top market</span><span class="signal-status">{safe_top_market}</span></div>
                <div class="signal-item"><span>Market revenue</span><span class="signal-status">£{top_market_revenue:,.0f}</span></div>
                <div class="signal-item"><span>Revenue share</span><span class="signal-status">{top_market_share:.1f}%</span></div>
                <div class="signal-item"><span>Distinct orders</span><span class="signal-status">{top_market_orders:,}</span></div>
            </div>

            <div class="insight-card">
                <div class="card-title">Market Concentration</div>
                <div class="card-sub">Revenue contribution from leading countries</div>
                <div class="signal-item"><span>Top 5 country share</span><span class="signal-status">{top5_share:.1f}%</span></div>
                <div class="signal-item"><span>Top 10 country share</span><span class="signal-status">{top10_share:.1f}%</span></div>
                <div class="signal-item"><span>Markets represented</span><span class="signal-status">{total_countries:,}</span></div>
                <div class="signal-item"><span>Revenue per market</span><span class="signal-status">£{revenue_per_country:,.0f}</span></div>
            </div>

            <div class="insight-card accent">
                <div class="card-title">UK vs International</div>
                <div class="card-sub">Domestic and international revenue mix</div>
                <div class="signal-item"><span>UK revenue</span><span class="signal-status">£{uk_revenue:,.0f}</span></div>
                <div class="signal-item"><span>UK revenue share</span><span class="signal-status">{uk_share:.1f}%</span></div>
                <div class="signal-item"><span>International revenue</span><span class="signal-status">£{international_revenue:,.0f}</span></div>
                <div class="signal-item"><span>International share</span><span class="signal-status">{international_share:.1f}%</span></div>
            </div>
        </div>
        """
        st.html(insight_html)

    except Exception as e:
        st.error("Unable to load Geographic Analysis data from PostgreSQL.")
        st.exception(e)
