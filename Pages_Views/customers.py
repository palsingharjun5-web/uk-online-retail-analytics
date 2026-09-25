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

    where_clause = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where_clause, tuple(params)


# --------------------------------------------------
# CUSTOMERS ANALYSIS PAGE
# --------------------------------------------------

def render_customers_page():
    st.markdown(
        """
        <div class="page-kicker">Customer Intelligence</div>
        <div class="page-title">Customer Analysis</div>
        <div class="page-sub">
            Explore customer loyalty, purchasing behaviour,
            revenue contribution, and engagement patterns.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    filters = render_overview_filters()
    where, params = _where(filters, sales_only=True)
    customer_where = (
        where + (" AND " if where else "WHERE ") + "customer_id IS NOT NULL"
    )

    try:
        # --------------------------------------------------
        # 1. CUSTOMER KPIs
        # --------------------------------------------------
        kpi = _query(
            f"""
            WITH customer_orders AS (
                SELECT
                    customer_id,
                    COUNT(DISTINCT invoice) AS order_count,
                    SUM(revenue) AS customer_revenue
                FROM analytics.base_sales
                {customer_where}
                GROUP BY customer_id
            )
            SELECT
                COUNT(*) AS customers,
                COALESCE(SUM(customer_revenue), 0) AS revenue,
                COALESCE(SUM(order_count), 0) AS orders,
                COUNT(*) FILTER (WHERE order_count >= 2) AS repeat_customers,
                COALESCE(AVG(order_count), 0) AS avg_orders
            FROM customer_orders;
            """,
            params,
        ).iloc[0]

        total_customers = int(kpi["customers"] or 0)
        total_revenue = float(kpi["revenue"] or 0)
        total_orders = int(kpi["orders"] or 0)
        repeat_customers = int(kpi["repeat_customers"] or 0)
        avg_orders = float(kpi["avg_orders"] or 0)

        repeat_rate = (
            100 * repeat_customers / total_customers
            if total_customers else 0
        )
        revenue_per_customer = (
            total_revenue / total_customers
            if total_customers else 0
        )

        # --------------------------------------------------
        # 2. CUSTOMER ORDER FREQUENCY
        # --------------------------------------------------
        frequency = _query(
            f"""
            WITH customer_orders AS (
                SELECT customer_id, COUNT(DISTINCT invoice) AS order_count
                FROM analytics.base_sales
                {customer_where}
                GROUP BY customer_id
            )
            SELECT
                CASE
                    WHEN order_count = 1 THEN '1 Order'
                    WHEN order_count BETWEEN 2 AND 4 THEN '2–4 Orders'
                    WHEN order_count BETWEEN 5 AND 9 THEN '5–9 Orders'
                    WHEN order_count BETWEEN 10 AND 19 THEN '10–19 Orders'
                    ELSE '20+ Orders'
                END AS frequency_group,
                CASE
                    WHEN order_count = 1 THEN 1
                    WHEN order_count BETWEEN 2 AND 4 THEN 2
                    WHEN order_count BETWEEN 5 AND 9 THEN 3
                    WHEN order_count BETWEEN 10 AND 19 THEN 4
                    ELSE 5
                END AS sort_order,
                COUNT(*) AS customers
            FROM customer_orders
            GROUP BY frequency_group, sort_order
            ORDER BY sort_order;
            """,
            params,
        )

        # --------------------------------------------------
        # 3. CUSTOMER REVENUE DISTRIBUTION
        # --------------------------------------------------
        revenue_distribution = _query(
            f"""
            SELECT customer_id::text AS customer_id, SUM(revenue) AS revenue
            FROM analytics.base_sales
            {customer_where}
            GROUP BY customer_id
            ORDER BY revenue DESC;
            """,
            params,
        )

        # --------------------------------------------------
        # 4. CUSTOMER RECENCY
        # --------------------------------------------------
        recency = _query(
            f"""
            WITH customer_last_purchase AS (
                SELECT customer_id, MAX(invoice_date)::date AS last_purchase
                FROM analytics.base_sales
                {customer_where}
                GROUP BY customer_id
            ),
            reference_date AS (
                SELECT MAX(invoice_date)::date AS max_date
                FROM analytics.base_sales
                {where}
            ),
            customer_recency AS (
                SELECT c.customer_id, (r.max_date - c.last_purchase) AS days_since_purchase
                FROM customer_last_purchase c
                CROSS JOIN reference_date r
            )
            SELECT
                CASE
                    WHEN days_since_purchase BETWEEN 0 AND 30 THEN '0–30 Days'
                    WHEN days_since_purchase BETWEEN 31 AND 90 THEN '31–90 Days'
                    WHEN days_since_purchase BETWEEN 91 AND 180 THEN '91–180 Days'
                    WHEN days_since_purchase BETWEEN 181 AND 365 THEN '181–365 Days'
                    ELSE '365+ Days'
                END AS recency_group,
                CASE
                    WHEN days_since_purchase BETWEEN 0 AND 30 THEN 1
                    WHEN days_since_purchase BETWEEN 31 AND 90 THEN 2
                    WHEN days_since_purchase BETWEEN 91 AND 180 THEN 3
                    WHEN days_since_purchase BETWEEN 181 AND 365 THEN 4
                    ELSE 5
                END AS sort_order,
                COUNT(*) AS customers
            FROM customer_recency
            GROUP BY recency_group, sort_order
            ORDER BY sort_order;
            """,
            params,
        )

        # --------------------------------------------------
        # 5. MONTHLY ACTIVE CUSTOMERS
        # --------------------------------------------------
        monthly_customers = _query(
            f"""
            SELECT
                DATE_TRUNC('month', invoice_date)::date AS month_start,
                COUNT(DISTINCT customer_id) AS customers
            FROM analytics.base_sales
            {customer_where}
            GROUP BY month_start
            ORDER BY month_start;
            """,
            params,
        )

        # --------------------------------------------------
        # 6. KPI CARDS (MATCH SALES PAGE STYLE)
        # --------------------------------------------------
        st.markdown(
            '<div class="section-title">Customer Overview</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card(
                "Identified Customers",
                f"{total_customers:,}",
                "Unique customers in selected data",
                featured=True,
            )
        with c2:
            render_kpi_card(
                "Repeat Customer Rate",
                f"{repeat_rate:.1f}%",
                "Customers with 2+ orders",
            )
        with c3:
            render_kpi_card(
                "Revenue per Customer",
                f"£{revenue_per_customer:,.2f}",
                "Revenue / identified customers",
            )
        with c4:
            render_kpi_card(
                "Avg Orders per Customer",
                f"{avg_orders:.2f}",
                "Orders per identified customer",
            )

        # --------------------------------------------------
        # 7. CUSTOMER BEHAVIOUR CHARTS
        # --------------------------------------------------
        st.write("")
        st.markdown(
            '<div class="section-title">Customer Behaviour</div>',
            unsafe_allow_html=True,
        )

        frequency_plot = frequency.copy()
        recency_plot = recency.copy()
        revenue_plot = revenue_distribution.head(10).copy()
        monthly_plot = monthly_customers.copy()
        if not revenue_plot.empty:
            revenue_plot["revenue_k"] = revenue_plot["revenue"] / 1000

        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                st.markdown(
                    '<div class="card-title">Purchase Frequency</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="card-sub">Customers grouped by number of distinct orders</div>',
                    unsafe_allow_html=True,
                )
                if not frequency_plot.empty:
                    render_chart(
                        frequency_plot, "bar", "frequency_group", "customers",
                        x_label="Order Frequency", y_label="Customers", height=350,
                    )
                else:
                    st.info("No customer frequency data available.")

        with right:
            with st.container(border=True):
                st.markdown(
                    '<div class="card-title">Purchase Recency</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="card-sub">Time since each customer last purchased</div>',
                    unsafe_allow_html=True,
                )
                if not recency_plot.empty:
                    render_chart(
                        recency_plot, "bar", "recency_group", "customers",
                        x_label="Days Since Last Purchase", y_label="Customers", height=350,
                    )
                else:
                    st.info("No customer recency data available.")

        st.write("")
        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                st.markdown(
                    '<div class="card-title">Top 10 Customers by Revenue</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="card-sub">Highest revenue-contributing identified customers</div>',
                    unsafe_allow_html=True,
                )
                if not revenue_plot.empty:
                    render_chart(
                        revenue_plot, "bar", "customer_id", "revenue_k",
                        x_label="Customer ID", y_label="Revenue (£K)", height=350,
                    )
                else:
                    st.info("No customer revenue data available.")

        with right:
            with st.container(border=True):
                st.markdown(
                    '<div class="card-title">Monthly Active Customers</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="card-sub">Distinct identified customers making purchases each month</div>',
                    unsafe_allow_html=True,
                )
                if not monthly_plot.empty:
                    render_chart(
                        monthly_plot, "line", "month_start", "customers",
                        x_label="Month", y_label="Active Customers", height=350,
                    )
                else:
                    st.info("No monthly customer data available.")

        # --------------------------------------------------
        # 8. THREE CUSTOMER INSIGHT CARDS
        # --------------------------------------------------
        one_time_customers = 0
        if not frequency.empty:
            one_time_row = frequency[frequency["frequency_group"] == "1 Order"]
            if not one_time_row.empty:
                one_time_customers = int(one_time_row.iloc[0]["customers"])

        one_time_rate = 100 * one_time_customers / total_customers if total_customers else 0

        recent_customers = 0
        if not recency.empty:
            recent_rows = recency[recency["recency_group"].isin(["0–30 Days", "31–90 Days"])]
            recent_customers = int(recent_rows["customers"].sum())

        recent_customer_rate = 100 * recent_customers / total_customers if total_customers else 0
        top10_revenue = float(revenue_distribution.head(10)["revenue"].sum()) if not revenue_distribution.empty else 0
        top10_share = 100 * top10_revenue / total_revenue if total_revenue else 0
        top_customer_id = str(revenue_distribution.iloc[0]["customer_id"]) if not revenue_distribution.empty else "—"
        top_customer_revenue = float(revenue_distribution.iloc[0]["revenue"]) if not revenue_distribution.empty else 0

        st.write("")
        st.markdown(
            '<div class="section-title">Customer Performance Insights</div>',
            unsafe_allow_html=True,
        )

        insight_html = f"""
        <div class="insight-grid">
            <div class="insight-card">
                <div class="card-title">Customer Loyalty</div>
                <div class="card-sub">Repeat purchase behaviour</div>
                <div class="signal-item"><span>Repeat customer rate</span><span class="signal-status">{repeat_rate:.1f}%</span></div>
                <div class="signal-item"><span>Repeat customers</span><span class="signal-status">{repeat_customers:,}</span></div>
                <div class="signal-item"><span>One-time customers</span><span class="signal-status">{one_time_customers:,}</span></div>
                <div class="signal-item"><span>One-time customer share</span><span class="signal-status">{one_time_rate:.1f}%</span></div>
            </div>

            <div class="insight-card">
                <div class="card-title">Customer Engagement</div>
                <div class="card-sub">Recency and activity signals</div>
                <div class="signal-item"><span>Purchased in last 90 days</span><span class="signal-status">{recent_customers:,}</span></div>
                <div class="signal-item"><span>Recent customer share</span><span class="signal-status">{recent_customer_rate:.1f}%</span></div>
                <div class="signal-item"><span>Monthly active customers</span><span class="signal-status">{int(monthly_customers['customers'].iloc[-1]) if not monthly_customers.empty else 0:,}</span></div>
                <div class="signal-item"><span>Avg orders per customer</span><span class="signal-status">{avg_orders:.2f}</span></div>
            </div>

            <div class="insight-card accent">
                <div class="card-title">Customer Value</div>
                <div class="card-sub">Revenue contribution concentration</div>
                <div class="signal-item"><span>Top customer ID</span><span class="signal-status">{top_customer_id}</span></div>
                <div class="signal-item"><span>Top customer revenue</span><span class="signal-status">£{top_customer_revenue:,.0f}</span></div>
                <div class="signal-item"><span>Top 10 customer revenue share</span><span class="signal-status">{top10_share:.1f}%</span></div>
                <div class="signal-item"><span>Revenue per customer</span><span class="signal-status">£{revenue_per_customer:,.2f}</span></div>
            </div>
        </div>
        """
        st.html(insight_html)

    except Exception as e:
        st.error("Unable to load Customer Analysis data from PostgreSQL.")
        st.exception(e)
