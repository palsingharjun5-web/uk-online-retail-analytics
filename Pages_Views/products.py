import streamlit as st
import pandas as pd

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


# --------------------------------------------------
# PRODUCTS ANALYSIS PAGE
# --------------------------------------------------

def render_products_page():
    st.markdown(
        """
        <div class="page-kicker">Product Intelligence</div>
        <div class="page-title">Product Analysis</div>
        <div class="page-sub">
            Explore product revenue, sales volume, and performance
            to understand which products drive the business.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    filters = render_overview_filters()
    where, params = _where(filters, sales_only=True)

    try:
        # --------------------------------------------------
        # 1. PRODUCT KPIs
        # --------------------------------------------------
        kpi = _query(
            f"""
            SELECT
                COUNT(DISTINCT product_id) AS products,
                COALESCE(SUM(quantity), 0) AS units,
                COALESCE(SUM(revenue), 0) AS revenue,
                COALESCE(SUM(revenue) / NULLIF(COUNT(DISTINCT product_id), 0), 0)
                    AS revenue_per_product,
                COALESCE(SUM(revenue) / NULLIF(SUM(quantity), 0), 0)
                    AS revenue_per_unit
            FROM analytics.base_sales
            {where};
            """,
            params,
        ).iloc[0]

        total_products = int(kpi["products"] or 0)
        total_units = float(kpi["units"] or 0)
        total_revenue = float(kpi["revenue"] or 0)
        revenue_per_product = float(kpi["revenue_per_product"] or 0)
        revenue_per_unit = float(kpi["revenue_per_unit"] or 0)

        # --------------------------------------------------
        # 2. PRODUCT PERFORMANCE DATA
        # --------------------------------------------------
        product_perf = _query(
            f"""
            SELECT
                product_id::text AS product_id,
                SUM(quantity) AS units_sold,
                SUM(revenue) AS revenue,
                COUNT(DISTINCT invoice) AS orders,
                COUNT(DISTINCT customer_id) FILTER (
                    WHERE customer_id IS NOT NULL
                ) AS customers,
                SUM(revenue) / NULLIF(SUM(quantity), 0) AS revenue_per_unit
            FROM analytics.base_sales
            {where}
            GROUP BY product_id
            ORDER BY revenue DESC;
            """,
            params,
        )

        # --------------------------------------------------
        # 3. MONTHLY PRODUCT REVENUE
        # --------------------------------------------------
        monthly = _query(
            f"""
            SELECT
                DATE_TRUNC('month', invoice_date)::date AS month_start,
                SUM(revenue) AS revenue,
                SUM(quantity) AS units_sold
            FROM analytics.base_sales
            {where}
            GROUP BY month_start
            ORDER BY month_start;
            """,
            params,
        )

        # --------------------------------------------------
        # 4. CHART DATA PREPARATION
        # --------------------------------------------------
        top_revenue = product_perf.nlargest(10, "revenue").copy()
        top_volume = product_perf.nlargest(10, "units_sold").copy()
        top_efficiency = product_perf.nlargest(10, "revenue_per_unit").copy()

        # Avoid charting zero/negative unit rows in revenue-per-unit ranking.
        top_efficiency = top_efficiency[
            top_efficiency["revenue_per_unit"].notna()
            & (top_efficiency["units_sold"] > 0)
        ]

        # Convert large values for chart readability.
        for frame in (top_revenue, top_volume):
            frame["revenue_k"] = frame["revenue"].astype(float) / 1000

        product_scatter = product_perf[
            (product_perf["units_sold"] > 0)
            & (product_perf["revenue"] > 0)
        ].copy()
        product_scatter["revenue_k"] = product_scatter["revenue"] / 1000

        monthly_plot = monthly.copy()
        monthly_plot["revenue_m"] = monthly_plot["revenue"].astype(float) / 1_000_000

        # --------------------------------------------------
        # 5. KPI CARDS — MATCH SALES/CUSTOMERS STYLE
        # --------------------------------------------------
        st.markdown(
            '<div class="section-title">Product Overview</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card(
                "Products Sold",
                f"{total_products:,}",
                "Distinct products in selected sales",
                featured=True,
            )
        with c2:
            render_kpi_card(
                "Units Sold",
                f"{total_units:,.0f}",
                "Total quantity across sales",
            )
        with c3:
            render_kpi_card(
                "Revenue per Product",
                f"£{revenue_per_product:,.2f}",
                "Revenue / distinct products",
            )
        with c4:
            render_kpi_card(
                "Revenue per Unit",
                f"£{revenue_per_unit:,.2f}",
                "Average revenue per item sold",
            )

        st.write("")

        # --------------------------------------------------
        # 6. PRODUCT PERFORMANCE CHARTS
        # --------------------------------------------------
        st.markdown(
            '<div class="section-title">Product Performance</div>',
            unsafe_allow_html=True,
        )

        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                st.markdown('<div class="card-title">Top 10 Products by Revenue</div>', unsafe_allow_html=True)
                st.markdown('<div class="card-sub">Highest revenue-generating products (£K)</div>', unsafe_allow_html=True)
                render_chart(
                    top_revenue, "bar", "product_id", "revenue_k",
                    x_label="Product ID", y_label="Revenue (£K)", height=360,
                )

        with right:
            with st.container(border=True):
                st.markdown('<div class="card-title">Top 10 Products by Volume</div>', unsafe_allow_html=True)
                st.markdown('<div class="card-sub">Products ranked by total units sold</div>', unsafe_allow_html=True)
                render_chart(
                    top_volume, "bar", "product_id", "units_sold",
                    x_label="Product ID", y_label="Units Sold", height=360,
                )

        st.write("")

        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                st.markdown('<div class="card-title">Revenue vs Sales Volume</div>', unsafe_allow_html=True)
                st.markdown('<div class="card-sub">Each point represents a product; revenue shown in £K</div>', unsafe_allow_html=True)
                render_chart(
                    product_scatter, "scatter", "units_sold", "revenue_k",
                    x_label="Units Sold", y_label="Revenue (£K)", height=360,
                )

        with right:
            with st.container(border=True):
                st.markdown('<div class="card-title">Top 10 Products by Revenue per Unit</div>', unsafe_allow_html=True)
                st.markdown('<div class="card-sub">Products ranked by average revenue per unit (£)</div>', unsafe_allow_html=True)
                render_chart(
                    top_efficiency, "bar", "product_id", "revenue_per_unit",
                    x_label="Product ID", y_label="Revenue per Unit (£)", height=360,
                )

        st.write("")

        # --------------------------------------------------
        # 7. THREE INSIGHT CARDS
        # --------------------------------------------------
        st.markdown(
            '<div class="section-title">Product Performance Insights</div>',
            unsafe_allow_html=True,
        )

        if not product_perf.empty:
            best_revenue = product_perf.loc[product_perf["revenue"].idxmax()]
            best_volume = product_perf.loc[product_perf["units_sold"].idxmax()]
            top10_revenue_sum = float(product_perf.nlargest(10, "revenue")["revenue"].sum())
            top10_share = 100 * top10_revenue_sum / total_revenue if total_revenue else 0
            best_rev_id = str(best_revenue["product_id"])
            best_rev_value = float(best_revenue["revenue"] or 0)
            best_vol_id = str(best_volume["product_id"])
            best_vol_value = float(best_volume["units_sold"] or 0)
        else:
            best_rev_id = best_vol_id = "—"
            best_rev_value = best_vol_value = top10_share = 0

        insight_html = f"""
        <div class="insight-grid">
            <div class="insight-card">
                <div class="card-title">Revenue Leader</div>
                <div class="card-sub">Product with the highest sales revenue</div>
                <div class="signal-item"><span>Top product ID</span><span class="signal-status">{best_rev_id}</span></div>
                <div class="signal-item"><span>Product revenue</span><span class="signal-status">£{best_rev_value:,.2f}</span></div>
                <div class="signal-item"><span>Revenue per product</span><span class="signal-status">£{revenue_per_product:,.2f}</span></div>
            </div>

            <div class="insight-card">
                <div class="card-title">Volume Leader</div>
                <div class="card-sub">Product with the highest quantity sold</div>
                <div class="signal-item"><span>Top product ID</span><span class="signal-status">{best_vol_id}</span></div>
                <div class="signal-item"><span>Units sold</span><span class="signal-status">{best_vol_value:,.0f}</span></div>
                <div class="signal-item"><span>Total products sold</span><span class="signal-status">{total_products:,}</span></div>
            </div>

            <div class="insight-card accent">
                <div class="card-title">Product Concentration</div>
                <div class="card-sub">Revenue contribution from leading products</div>
                <div class="signal-item"><span>Top 10 product revenue share</span><span class="signal-status">{top10_share:.1f}%</span></div>
                <div class="signal-item"><span>Total sales revenue</span><span class="signal-status">£{total_revenue:,.2f}</span></div>
                <div class="signal-item"><span>Revenue per unit</span><span class="signal-status">£{revenue_per_unit:,.2f}</span></div>
            </div>
        </div>
        """
        st.html(insight_html)

    except Exception as e:
        st.error("Unable to load Product Analysis data from PostgreSQL.")
        st.exception(e)
