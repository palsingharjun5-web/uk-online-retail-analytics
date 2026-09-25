import streamlit as st
import pandas as pd

from db_connection import get_connection

from Components.theme import apply_theme
from Components.sidebar import render_sidebar_navigation
from Components.kpi_cards import render_kpi_card
from Components.charts import render_chart
from Components.filters import render_overview_filters
from Pages_Views.sales import render_sales_page
from Pages_Views.customers import render_customers_page
from Pages_Views.products import render_products_page
from Pages_Views.geography import render_geography_page
from Pages_Views.operations import render_operations_page
from Pages_Views.findings import render_findings_page


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="UK Retail Analytics",
    page_icon="🌿",
    layout="wide"
)

apply_theme()


# ==================================================
# DATABASE FUNCTION
# ==================================================

@st.cache_data(ttl=300)
def load_data(query, params=()):

    conn = get_connection()

    try:
        return pd.read_sql_query(
            query,
            conn,
            params=params
        )

    finally:
        conn.close()


# ==================================================
# SQL FILTER BUILDER
# ==================================================

def build_where(filters, sales_only=True, include_type=False):

    conditions = []
    params = []

    if sales_only:
        conditions.append("transaction_type = 'Sale'")

    if filters["country"] is not None:
        conditions.append("country = %s")
        params.append(filters["country"])

    if filters["year"] is not None:
        conditions.append("year = %s")
        params.append(filters["year"])

    if filters["month"] is not None:
        conditions.append("month = %s")
        params.append(filters["month"])

    if include_type and filters["transaction_type"] is not None:
        conditions.append("transaction_type = %s")
        params.append(filters["transaction_type"])

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    return where_clause, tuple(params)


# ==================================================
# KPI DATA
# ==================================================

def get_kpi_data(filters):

    where_clause, params = build_where(
        filters,
        sales_only=True
    )

    query = f"""
        SELECT
            COALESCE(SUM(revenue), 0) AS total_revenue,

            COUNT(DISTINCT invoice) AS total_orders,

            COUNT(DISTINCT customer_id) AS total_customers,

            COALESCE(SUM(quantity), 0) AS total_units,

            COALESCE(
                SUM(revenue) /
                NULLIF(COUNT(DISTINCT invoice), 0),
                0
            ) AS average_order_value

        FROM analytics.base_sales

        {where_clause};
    """

    df = load_data(query, params)

    return df.iloc[0].to_dict()


# ==================================================
# MONTHLY REVENUE
# ==================================================

def get_monthly_revenue(filters):

    where_clause, params = build_where(
        filters,
        sales_only=True
    )

    query = f"""
        SELECT
            DATE_TRUNC('month', invoice_date) AS month_start,

            TO_CHAR(
                DATE_TRUNC('month', invoice_date),
                'Mon YYYY'
            ) AS month_name,

            SUM(revenue) AS revenue

        FROM analytics.base_sales

        {where_clause}

        GROUP BY DATE_TRUNC('month', invoice_date)

        ORDER BY month_start;
    """

    return load_data(query, params)


# ==================================================
# TRANSACTION OVERVIEW
# ==================================================

def get_transaction_data(filters):

    where_clause, params = build_where(
        filters,
        sales_only=False,
        include_type=True
    )

    query = f"""
        SELECT
            transaction_type,

            COUNT(*) AS transaction_rows

        FROM transactions

        {where_clause}

        GROUP BY transaction_type

        ORDER BY transaction_rows DESC;
    """

    return load_data(query, params)


# ==================================================
# TOP 10 COUNTRIES
# ==================================================

def get_country_data(filters):

    where_clause, params = build_where(
        filters,
        sales_only=True
    )

    query = f"""
        SELECT
            country,

            SUM(revenue) AS revenue

        FROM analytics.base_sales

        {where_clause}

        GROUP BY country

        ORDER BY revenue DESC

        LIMIT 10;
    """

    return load_data(query, params)


# ==================================================
# TOP 10 PRODUCTS
# ==================================================

def get_product_data(filters):

    where_clause, params = build_where(
        filters,
        sales_only=True
    )

    query = f"""
        SELECT
            product_id::text AS product_id,

            SUM(revenue) AS revenue

        FROM analytics.base_sales

        {where_clause}

        GROUP BY product_id

        ORDER BY revenue DESC

        LIMIT 10;
    """

    return load_data(query, params)


# ==================================================
# CUSTOMER INSIGHTS
# ==================================================

def get_insight_data(filters):

    where_clause, params = build_where(
        filters,
        sales_only=True
    )

    extra = ""
    if where_clause:
        extra = where_clause + " AND customer_id IS NOT NULL"
    else:
        extra = "WHERE customer_id IS NOT NULL"

    query = f"""
        WITH customer_orders AS (
            SELECT
                customer_id,
                COUNT(DISTINCT invoice) AS orders
            FROM analytics.base_sales
            {extra}
            GROUP BY customer_id
        )
        SELECT
            COUNT(*) AS known_customers,
            COUNT(*) FILTER (WHERE orders >= 2) AS repeat_customers,
            COALESCE(
                100.0 * COUNT(*) FILTER (WHERE orders >= 2)
                / NULLIF(COUNT(*), 0),
                0
            ) AS repeat_customer_rate_pct
        FROM customer_orders;
    """

    df = load_data(query, params)

    return df.iloc[0].to_dict()


def format_compact_number(value):

    value = float(value)

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"

    return f"{int(value):,}"


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

selected_page = render_sidebar_navigation()


# ==================================================
# OVERVIEW PAGE
# ==================================================

if selected_page == "Overview":

    st.markdown(
        """
        <div class="page-kicker">Dashboard</div>
        <div class="page-title">UK Online Retail</div>
        <div class="page-sub">
            Plan, review, and explore retail performance at a glance.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    filters = render_overview_filters()

    st.write("")

    try:

        kpi = get_kpi_data(filters)

        monthly_df = get_monthly_revenue(filters)

        transaction_df = get_transaction_data(filters)

        country_df = get_country_data(filters)

        product_df = get_product_data(filters)

        insights = get_insight_data(filters)

        st.markdown(
            '<div class="section-title">Business Performance</div>',
            unsafe_allow_html=True
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            render_kpi_card(
                "Total Revenue",
                f"£{format_compact_number(kpi['total_revenue'])}",
                "Increased from filtered sales",
                featured=True
            )

        with col2:
            render_kpi_card(
                "Total Orders",
                f"{int(kpi['total_orders']):,}",
                "Unique invoices"
            )

        with col3:
            render_kpi_card(
                "Total Customers",
                f"{int(kpi['total_customers']):,}",
                "Known customer IDs"
            )

        with col4:
            render_kpi_card(
                "Units Sold",
                format_compact_number(kpi["total_units"]),
                "Items sold"
            )

        with col5:
            render_kpi_card(
                "Average Order Value",
                f"£{float(kpi['average_order_value']):,.2f}",
                "Revenue per invoice"
            )

        st.write("")

        col1, col2 = st.columns([1.7, 1])

        with col1:

            with st.container(border=True):

                st.markdown(
                    """
                    <div class="card-head">
                        <div>
                            <div class="card-title">Monthly Revenue Trend</div>
                            <div class="card-sub">Sales revenue over time</div>
                        </div>
                        <div class="card-pill">Sales</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                render_chart(
                    df=monthly_df,
                    chart_type="line",
                    x="month_start",
                    y="revenue",
                    title="",
                    x_label="Month",
                    y_label="Revenue (£)",
                    height=340
                )

        with col2:

            with st.container(border=True):

                st.markdown(
                    """
                    <div class="card-head">
                        <div>
                            <div class="card-title">Transaction Overview</div>
                            <div class="card-sub">Rows by transaction type</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                render_chart(
                    df=transaction_df,
                    chart_type="bar",
                    x="transaction_type",
                    y="transaction_rows",
                    title="",
                    x_label="Type",
                    y_label="Number of Rows",
                    height=340
                )

        st.write("")

        col1, col2 = st.columns(2)

        with col1:

            with st.container(border=True):

                st.markdown(
                    """
                    <div class="card-head">
                        <div>
                            <div class="card-title">Top 10 Countries</div>
                            <div class="card-sub">Ranked by sales revenue</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                render_chart(
                    df=country_df,
                    chart_type="bar",
                    x="country",
                    y="revenue",
                    title="",
                    x_label="Revenue (£)",
                    y_label="Country",
                    height=400
                )

        with col2:

            with st.container(border=True):

                st.markdown(
                    """
                    <div class="card-head">
                        <div>
                            <div class="card-title">Top 10 Products</div>
                            <div class="card-sub">Ranked by sales revenue</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                render_chart(
                    df=product_df,
                    chart_type="bar",
                    x="product_id",
                    y="revenue",
                    title="",
                    x_label="Revenue (£)",
                    y_label="Product ID",
                    height=400
                )

        st.write("")

        repeat_pct = float(insights["repeat_customer_rate_pct"])
        repeat_customers = int(insights["repeat_customers"])
        known_customers = int(insights["known_customers"])

        sale_rows = 0
        cancel_rows = 0

        if transaction_df is not None and not transaction_df.empty:

            sales_match = transaction_df[
                transaction_df["transaction_type"] == "Sale"
            ]
            cancel_match = transaction_df[
                transaction_df["transaction_type"].str.contains(
                    "Cancel",
                    case=False,
                    na=False
                )
            ]

            if not sales_match.empty:
                sale_rows = int(sales_match["transaction_rows"].sum())

            if not cancel_match.empty:
                cancel_rows = int(cancel_match["transaction_rows"].sum())

        cancel_pct = 0
        if sale_rows:
            cancel_pct = 100.0 * cancel_rows / sale_rows

        top_country = "—"
        top_country_share = 0

        if country_df is not None and not country_df.empty:
            top_country = str(country_df.iloc[0]["country"])
            total_top10 = float(country_df["revenue"].sum())
            if total_top10:
                top_country_share = (
                    100.0 * float(country_df.iloc[0]["revenue"]) / total_top10
                )

        st.markdown(
            '<div class="section-title">Customer & Operational Insights</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="insight-grid">
                <div class="insight-card">
                    <div class="card-title">Repeat Customers</div>
                    <div class="card-sub">Share of customers with 2+ orders</div>
                    <div class="donut-wrap">
                        <div class="donut" style="background: conic-gradient(#1F7A4D 0% {repeat_pct:.1f}%, #E4F0E8 {repeat_pct:.1f}% 100%);">
                            <div class="donut-inner">{repeat_pct:.0f}%</div>
                        </div>
                        <div>
                            <div class="legend-row"><span class="dot" style="background:#1F7A4D"></span> Repeat · {repeat_customers:,}</div>
                            <div class="legend-row"><span class="dot" style="background:#E4F0E8"></span> One-time · {max(known_customers - repeat_customers, 0):,}</div>
                        </div>
                    </div>
                </div>
                <div class="insight-card">
                    <div class="card-title">Cancellations</div>
                    <div class="card-sub">Cancellation rows vs sales rows</div>
                    <div class="kpi-value" style="font-size:34px;margin-top:28px;">{cancel_pct:.1f}%</div>
                    <div class="kpi-hint">{cancel_rows:,} cancellation rows against {sale_rows:,} sales rows</div>
                </div>
                <div class="insight-card accent">
                    <div class="card-title">Key Signals</div>
                    <div class="card-sub">High-level retail takeaways</div>
                    <div class="signal-item"><span>Top market</span><span class="signal-status">{top_country}</span></div>
                    <div class="signal-item"><span>Top-10 country share</span><span class="signal-status">{top_country_share:.0f}%</span></div>
                    <div class="signal-item"><span>Repeat buyers</span><span class="signal-status">{repeat_pct:.0f}%</span></div>
                    <div class="signal-item"><span>AOV</span><span class="signal-status">£{float(kpi['average_order_value']):,.0f}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:

        st.error("Unable to load Overview dashboard data.")

        st.exception(e)


# ==================================================
# OTHER DASHBOARD PAGES
# ==================================================

elif selected_page == "Sales":

    render_sales_page()

elif selected_page == "Customers":

    render_customers_page()

elif selected_page == "Products":

    render_products_page()

elif selected_page == "Geography":

    render_geography_page()

elif selected_page == "Operations":

    render_operations_page()

elif selected_page == "Findings":

    render_findings_page()