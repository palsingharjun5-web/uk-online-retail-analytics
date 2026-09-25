import streamlit as st
import pandas as pd
import textwrap

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
        ("month", "month")
    ):
        value = filters.get(key)

        if value is not None:
            clauses.append(f"{column} = %s")
            params.append(value)

    where_clause = (
        "WHERE " + " AND ".join(clauses)
        if clauses
        else ""
    )

    return where_clause, tuple(params)


# --------------------------------------------------
# NUMBER FORMATTING
# --------------------------------------------------

def _compact(value, currency=False, decimals=2):
    value = float(value or 0)

    if abs(value) >= 1_000_000:
        result = f"{value / 1_000_000:,.{decimals}f}M"

    elif abs(value) >= 1_000:
        result = f"{value / 1_000:,.2f}K"

    else:
        result = (
            f"{value:,.{decimals}f}"
            if currency
            else f"{value:,.0f}"
        )

    return f"£{result}" if currency else result


# --------------------------------------------------
# TRANSACTION FILTER
# --------------------------------------------------

def _transaction_filter(filters):
    clauses = []
    params = []

    for key, column in (
        ("country", "country"),
        ("year", "year"),
        ("month", "month")
    ):
        value = filters.get(key)

        if value is not None:
            clauses.append(f"{column} = %s")
            params.append(value)

    where_clause = (
        "WHERE " + " AND ".join(clauses)
        if clauses
        else ""
    )

    return where_clause, tuple(params)


# --------------------------------------------------
# SALES ANALYSIS PAGE
# --------------------------------------------------

def render_sales_page():

    st.markdown(
        """
        <div class="page-kicker">Performance</div>

        <div class="page-title">
            Sales Analysis
        </div>

        <div class="page-sub">
            Explore revenue trends, order value,
            and sales contribution across markets and products.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # Existing dashboard filters
    filters = render_overview_filters()

    where, params = _where(
        filters,
        sales_only=True
    )

    try:

        # --------------------------------------------------
        # 1. SALES KPIs
        # --------------------------------------------------

        kpi = _query(
            f"""
            SELECT
                COALESCE(SUM(revenue), 0) AS revenue,

                COUNT(DISTINCT invoice) AS orders,

                COALESCE(SUM(quantity), 0) AS units,

                COUNT(DISTINCT invoice_date::date)
                    AS active_days,

                COUNT(DISTINCT customer_id)
                    FILTER (
                        WHERE customer_id IS NOT NULL
                    ) AS customers

            FROM analytics.base_sales

            {where};
            """,
            params
        ).iloc[0]


        # --------------------------------------------------
        # 2. MONTHLY REVENUE
        # --------------------------------------------------

        monthly = _query(
            f"""
            SELECT
                DATE_TRUNC(
                    'month',
                    invoice_date
                )::date AS month_start,

                SUM(revenue) AS revenue

            FROM analytics.base_sales

            {where}

            GROUP BY 1

            ORDER BY 1;
            """,
            params
        )


        # --------------------------------------------------
        # 3. YEARLY REVENUE
        # --------------------------------------------------

        yearly = _query(
            f"""
            SELECT
                year,
                SUM(revenue) AS revenue

            FROM analytics.base_sales

            {where}

            GROUP BY year

            ORDER BY year;
            """,
            params
        )


        # --------------------------------------------------
        # 4. TOP 10 COUNTRIES
        # --------------------------------------------------

        countries = _query(
            f"""
            SELECT
                country,
                SUM(revenue) AS revenue

            FROM analytics.base_sales

            {where}

            GROUP BY country

            ORDER BY revenue DESC

            LIMIT 10;
            """,
            params
        )


        # --------------------------------------------------
        # 5. TOP 10 PRODUCTS
        # --------------------------------------------------

        products = _query(
            f"""
            SELECT
                product_id::text AS product_id,
                SUM(revenue) AS revenue

            FROM analytics.base_sales

            {where}

            GROUP BY product_id

            ORDER BY revenue DESC

            LIMIT 10;
            """,
            params
        )


        # --------------------------------------------------
        # 6. REPEAT CUSTOMER ANALYSIS
        # --------------------------------------------------

        repeat = _query(
            f"""
            WITH customer_orders AS (

                SELECT
                    customer_id,
                    COUNT(DISTINCT invoice) AS order_count

                FROM analytics.base_sales

                {where + (" AND " if where else "WHERE ") + "customer_id IS NOT NULL"}

                GROUP BY customer_id
            )

            SELECT
                COUNT(*) AS known_customers,

                COUNT(*) FILTER (
                    WHERE order_count >= 2
                ) AS repeat_customers

            FROM customer_orders;
            """,
            params
        ).iloc[0]


        # --------------------------------------------------
        # 7. TRANSACTION TYPE ANALYSIS
        # --------------------------------------------------

        tx_where, tx_params = _transaction_filter(filters)

        tx = _query(
            f"""
            SELECT
                transaction_type,
                COUNT(*) AS row_count

            FROM transactions

            {tx_where}

            GROUP BY transaction_type;
            """,
            tx_params
        )


        # --------------------------------------------------
        # 8. KPI CALCULATIONS
        # --------------------------------------------------

        revenue = float(kpi["revenue"] or 0)

        orders = int(kpi["orders"] or 0)

        units = float(kpi["units"] or 0)

        active_days = int(kpi["active_days"] or 0)

        customers = int(kpi["customers"] or 0)


        # Average daily revenue
        avg_daily_revenue = (
            revenue / active_days
            if active_days
            else 0
        )


        # Average items per order
        avg_items_per_order = (
            units / orders
            if orders
            else 0
        )


        # Orders per active day
        orders_per_day = (
            orders / active_days
            if active_days
            else 0
        )


        # Revenue per identified customer
        revenue_per_customer = (
            revenue / customers
            if customers
            else 0
        )


        # --------------------------------------------------
        # 9. REPEAT CUSTOMER & CANCELLATION CALCULATIONS
        # --------------------------------------------------

        repeat_customers = int(
            repeat["repeat_customers"] or 0
        )

        known_customers = int(
            repeat["known_customers"] or 0
        )

        repeat_pct = (
            100 * repeat_customers / known_customers
            if known_customers
            else 0
        )


        sale_rows = 0
        cancel_rows = 0

        if not tx.empty:

            for _, row in tx.iterrows():

                kind = str(
                    row["transaction_type"]
                ).strip().lower()

                if kind == "sale":
                    sale_rows = int(row["row_count"])

                elif "cancel" in kind:
                    cancel_rows += int(row["row_count"])


        cancel_pct = (
            100 * cancel_rows / sale_rows
            if sale_rows
            else 0
        )


        # --------------------------------------------------
        # 10. COUNTRY & PRODUCT INSIGHTS
        # --------------------------------------------------

        total_revenue = revenue

        top_country = (
            str(countries.iloc[0]["country"])
            if not countries.empty
            else "—"
        )

        top_country_revenue = (
            float(countries.iloc[0]["revenue"] or 0)
            if not countries.empty
            else 0
        )

        market_share = (
            100 * top_country_revenue / total_revenue
            if total_revenue
            else 0
        )

        top10_share = (
            100 * float(countries["revenue"].sum())
            / total_revenue
            if total_revenue
            else 0
        )

        top_product = (
            str(products.iloc[0]["product_id"])
            if not products.empty
            else "—"
        )


        # --------------------------------------------------
        # 11. CHART DATA PREPARATION
        # --------------------------------------------------

        monthly_plot = monthly.copy()

        yearly_plot = yearly.copy()

        country_plot = countries.copy()

        product_plot = products.copy()


        # Convert revenue into millions for chart axes
        for frame in (
            monthly_plot,
            yearly_plot,
            country_plot,
            product_plot
        ):

            if "revenue" in frame.columns:

                frame["revenue_m"] = (
                    frame["revenue"].astype(float)
                    / 1_000_000
                )


        # --------------------------------------------------
        # 12. SALES KPI CARDS
        # --------------------------------------------------

        st.markdown(
            '<div class="section-title">Sales Performance</div>',
            unsafe_allow_html=True
        )

        c1, c2, c3, c4 = st.columns(4)


        with c1:

            render_kpi_card(
                "Average Daily Revenue",

                _compact(
                    avg_daily_revenue,
                    currency=True
                ),

                "Revenue per active sales day",

                featured=True
            )


        with c2:

            render_kpi_card(
                "Avg Items per Order",

                f"{avg_items_per_order:,.1f}",

                "Units per unique invoice"
            )


        with c3:

            render_kpi_card(
                "Orders per Active Day",

                _compact(orders_per_day),

                "Average daily order volume"
            )


        with c4:

            render_kpi_card(
                "Revenue per Customer",

                _compact(
                    revenue_per_customer,
                    currency=True
                ),

                "Revenue per identified customer"
            )


        # --------------------------------------------------
        # 13. MONTHLY REVENUE & YEARLY REVENUE CHARTS
        # --------------------------------------------------

        st.write("")

        left, right = st.columns([1.6, 1])


        with left:

            with st.container(border=True):

                st.markdown(
                    '<div class="card-title">Monthly Revenue Trend</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="card-sub">Monthly sales movement in £ millions</div>',
                    unsafe_allow_html=True
                )

                render_chart(
                    monthly_plot,
                    "line",
                    "month_start",
                    "revenue_m",
                    x_label="Month",
                    y_label="Revenue (£M)",
                    height=350
                )


        with right:

            with st.container(border=True):

                st.markdown(
                    '<div class="card-title">Revenue by Year</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="card-sub">Annual sales comparison in £ millions</div>',
                    unsafe_allow_html=True
                )

                render_chart(
                    yearly_plot,
                    "bar",
                    "year",
                    "revenue_m",
                    x_label="Year",
                    y_label="Revenue (£M)",
                    height=350
                )


        # --------------------------------------------------
        # 14. COUNTRY & PRODUCT CHARTS
        # --------------------------------------------------

        st.write("")

        left, right = st.columns(2)


        with left:

            with st.container(border=True):

                st.markdown(
                    '<div class="card-title">Top 10 Countries</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="card-sub">Markets ranked by sales revenue (£M)</div>',
                    unsafe_allow_html=True
                )

                render_chart(
                    country_plot,
                    "bar",
                    "country",
                    "revenue_m",
                    x_label="",
                    y_label="Revenue (£M)",
                    height=380
                )


        with right:

            with st.container(border=True):

                st.markdown(
                    '<div class="card-title">Top 10 Products</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="card-sub">Products ranked by sales revenue (£M)</div>',
                    unsafe_allow_html=True
                )

                render_chart(
                    product_plot,
                    "bar",
                    "product_id",
                    "revenue_m",
                    x_label="",
                    y_label="Revenue (£M)",
                    height=380
                )
                # --------------------------------------------------
        # 15. SALES-SPECIFIC INSIGHT CARDS
        # --------------------------------------------------

        st.write("")

        st.markdown(
            '<div class="section-title">Sales Performance Insights</div>',
            unsafe_allow_html=True
        )

        # --------------------------------------------------
        # A. REVENUE MOMENTUM CALCULATIONS
        # --------------------------------------------------

        monthly_insights = monthly.copy()

        if not monthly_insights.empty:

            monthly_insights["month_start"] = pd.to_datetime(
                monthly_insights["month_start"]
            )

            monthly_insights = monthly_insights.sort_values(
                "month_start"
            )

            # Best revenue month
            best_month_row = monthly_insights.loc[
                monthly_insights["revenue"].idxmax()
            ]

            best_month = best_month_row["month_start"].strftime(
                "%b %Y"
            )

            best_month_revenue = float(
                best_month_row["revenue"] or 0
            )

            # Lowest revenue month
            lowest_month_row = monthly_insights.loc[
                monthly_insights["revenue"].idxmin()
            ]

            lowest_month = lowest_month_row["month_start"].strftime(
                "%b %Y"
            )

            lowest_month_revenue = float(
                lowest_month_row["revenue"] or 0
            )

            # Latest month-over-month change
            if len(monthly_insights) >= 2:

                latest_revenue = float(
                    monthly_insights.iloc[-1]["revenue"] or 0
                )

                previous_revenue = float(
                    monthly_insights.iloc[-2]["revenue"] or 0
                )

                latest_month = monthly_insights.iloc[
                    -1
                ]["month_start"].strftime("%b %Y")

                previous_month = monthly_insights.iloc[
                    -2
                ]["month_start"].strftime("%b %Y")

                if previous_revenue != 0:

                    mom_change = (
                        (latest_revenue - previous_revenue)
                        / abs(previous_revenue)
                    ) * 100

                    mom_text = f"{mom_change:+.1f}%"

                    mom_description = (
                        f"{latest_month} vs {previous_month}"
                    )

                else:
                    mom_text = "N/A"
                    mom_description = (
                        "Previous month's revenue was zero"
                    )

            else:
                mom_text = "N/A"
                mom_description = (
                    "Not enough monthly data to compare"
                )

        else:
            best_month = "N/A"
            best_month_revenue = 0

            lowest_month = "N/A"
            lowest_month_revenue = 0

            mom_text = "N/A"
            mom_description = "No monthly data available"

        # --------------------------------------------------
        # B. PRODUCT PERFORMANCE CALCULATIONS
        # --------------------------------------------------

        top_product_name = (
            str(products.iloc[0]["product_id"])
            if not products.empty
            else "N/A"
        )

        top_product_revenue = (
            float(products.iloc[0]["revenue"] or 0)
            if not products.empty
            else 0
        )

        top10_product_revenue = (
            float(products["revenue"].sum())
            if not products.empty
            else 0
        )

        top10_product_share = (
            100 * top10_product_revenue / total_revenue
            if total_revenue > 0
            else 0
        )

        # --------------------------------------------------
        # C. MARKET PERFORMANCE CALCULATIONS
        # --------------------------------------------------

        remaining_market_share = max(
            0,
            100 - market_share
        )

        # --------------------------------------------------
        # D. BUILD INSIGHT CARDS
        # --------------------------------------------------

        insight_html = f"""
        <div class="insight-grid">

            <!-- REVENUE MOMENTUM -->
            <div class="insight-card">

                <div class="card-title">
                    Revenue Momentum
                </div>

                <div class="card-sub">
                    Monthly revenue performance
                </div>

                <div class="signal-item">
                    <span>Best revenue month</span>
                    <span class="signal-status">
                        {best_month}
                    </span>
                </div>

                <div class="signal-item">
                    <span>Revenue</span>
                    <span class="signal-status">
                        £{best_month_revenue:,.0f}
                    </span>
                </div>

                <div class="signal-item">
                    <span>Lowest revenue month</span>
                    <span class="signal-status">
                        {lowest_month}
                    </span>
                </div>

                <div class="signal-item">
                    <span>Revenue</span>
                    <span class="signal-status">
                        £{lowest_month_revenue:,.0f}
                    </span>
                </div>

                <div class="signal-item">
                    <span>Latest MoM change</span>
                    <span class="signal-status">
                        {mom_text}
                    </span>
                </div>

                <div class="card-sub">
                    {mom_description}
                </div>

            </div>


            <!-- PRODUCT PERFORMANCE -->
            <div class="insight-card">

                <div class="card-title">
                    Product Performance
                </div>

                <div class="card-sub">
                    Revenue contribution by product
                </div>

                <div class="signal-item">
                    <span>Top product ID</span>
                    <span class="signal-status">
                        {top_product_name}
                    </span>
                </div>

                <div class="signal-item">
                    <span>Top product revenue</span>
                    <span class="signal-status">
                        £{top_product_revenue:,.0f}
                    </span>
                </div>

                <div class="signal-item">
                    <span>Top 10 product revenue</span>
                    <span class="signal-status">
                        £{top10_product_revenue:,.0f}
                    </span>
                </div>

                <div class="signal-item">
                    <span>Top 10 product share</span>
                    <span class="signal-status">
                        {top10_product_share:.1f}%
                    </span>
                </div>

                <div class="card-sub">
                    Share of total filtered sales revenue
                </div>

            </div>


            <!-- MARKET PERFORMANCE -->
            <div class="insight-card accent">

                <div class="card-title">
                    Market Performance
                </div>

                <div class="card-sub">
                    Revenue distribution across countries
                </div>

                <div class="signal-item">
                    <span>Top revenue market</span>
                    <span class="signal-status">
                        {top_country}
                    </span>
                </div>

                <div class="signal-item">
                    <span>Top market revenue</span>
                    <span class="signal-status">
                        £{top_country_revenue:,.0f}
                    </span>
                </div>

                <div class="signal-item">
                    <span>Top market share</span>
                    <span class="signal-status">
                        {market_share:.1f}%
                    </span>
                </div>

                <div class="signal-item">
                    <span>Remaining markets</span>
                    <span class="signal-status">
                        {remaining_market_share:.1f}%
                    </span>
                </div>

            </div>

        </div>
        """

        # Render HTML directly (avoids Markdown code-block issue)
        st.html(insight_html)

    # --------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------

    except Exception as e:

        st.error(
            "Unable to load Sales Analysis data from PostgreSQL."
        )

        st.exception(e)