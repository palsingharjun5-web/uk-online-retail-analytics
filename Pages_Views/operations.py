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

def _where(filters):
    clauses = []
    params = []

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
# OPERATIONS ANALYSIS PAGE
# --------------------------------------------------

def render_operations_page():
    st.markdown(
        """
        <div class="page-kicker">Operational Intelligence</div>
        <div class="page-title">Operations Analysis</div>
        <div class="page-sub">
            Track cancellations, returns, and non-standard transactions
            to understand operational activity and potential data-quality signals.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    filters = render_overview_filters()
    where, params = _where(filters)

    try:
        # --------------------------------------------------
        # 1. OPERATIONAL KPIs — RAW TRANSACTION ROWS
        # --------------------------------------------------
        kpi = _query(
            f"""
            SELECT
                COUNT(*) AS total_rows,
                COUNT(*) FILTER (WHERE transaction_type = 'Sale') AS sale_rows,
                COUNT(*) FILTER (WHERE transaction_type = 'Cancellation') AS cancellation_rows,
                COUNT(*) FILTER (WHERE transaction_type = 'Adjustment / Return') AS return_rows,
                COUNT(*) FILTER (
                    WHERE transaction_type IN (
                        'Special / Charge', 'Zero Price', 'Bad Debt'
                    )
                ) AS other_rows,
                COUNT(*) FILTER (
                    WHERE transaction_type <> 'Sale'
                ) AS non_sale_rows
            FROM transactions
            {where};
            """,
            params,
        ).iloc[0]

        total_rows = int(kpi["total_rows"] or 0)
        sale_rows = int(kpi["sale_rows"] or 0)
        cancellation_rows = int(kpi["cancellation_rows"] or 0)
        return_rows = int(kpi["return_rows"] or 0)
        other_rows = int(kpi["other_rows"] or 0)
        non_sale_rows = int(kpi["non_sale_rows"] or 0)

        cancellation_rate = 100 * cancellation_rows / sale_rows if sale_rows else 0
        return_rate = 100 * return_rows / sale_rows if sale_rows else 0
        non_sale_share = 100 * non_sale_rows / total_rows if total_rows else 0

        # --------------------------------------------------
        # 2. TRANSACTION TYPE BREAKDOWN
        # --------------------------------------------------
        type_df = _query(
            f"""
            SELECT transaction_type, COUNT(*) AS transaction_rows
            FROM transactions
            {where}
            GROUP BY transaction_type
            ORDER BY transaction_rows DESC;
            """,
            params,
        )

        # --------------------------------------------------
        # 3. MONTHLY CANCELLATIONS
        # --------------------------------------------------
        monthly_cancellations = _query(
            f"""
            SELECT
                DATE_TRUNC('month', invoice_date)::date AS month_start,
                COUNT(*) AS cancellation_rows
            FROM transactions
            {where + (' AND ' if where else 'WHERE ')}
                transaction_type = 'Cancellation'
            GROUP BY month_start
            ORDER BY month_start;
            """,
            params,
        )

        # --------------------------------------------------
        # 4. MONTHLY RETURNS / ADJUSTMENTS
        # --------------------------------------------------
        monthly_returns = _query(
            f"""
            SELECT
                DATE_TRUNC('month', invoice_date)::date AS month_start,
                COUNT(*) AS return_rows
            FROM transactions
            {where + (' AND ' if where else 'WHERE ')}
                transaction_type = 'Adjustment / Return'
            GROUP BY month_start
            ORDER BY month_start;
            """,
            params,
        )

        # --------------------------------------------------
        # 5. COUNTRIES WITH MOST NON-SALE ROWS
        # --------------------------------------------------
        country_ops = _query(
            f"""
            SELECT
                country,
                COUNT(*) AS non_sale_rows
            FROM transactions
            {where + (' AND ' if where else 'WHERE ')}
                transaction_type <> 'Sale'
            GROUP BY country
            ORDER BY non_sale_rows DESC
            LIMIT 10;
            """,
            params,
        )

        # --------------------------------------------------
        # 6. KPI CARDS
        # --------------------------------------------------
        st.markdown(
            '<div class="section-title">Operations Overview</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card(
                "Transaction Rows",
                f"{total_rows:,}",
                "All transaction types in selected data",
                featured=True,
            )
        with c2:
            render_kpi_card(
                "Cancellation Rate",
                f"{cancellation_rate:.2f}%",
                "Cancellation rows / sale rows",
            )
        with c3:
            render_kpi_card(
                "Return / Adjustment Rate",
                f"{return_rate:.2f}%",
                "Return rows / sale rows",
            )
        with c4:
            render_kpi_card(
                "Non-Sale Transaction Share",
                f"{non_sale_share:.2f}%",
                "Non-sale rows / all transaction rows",
            )

        st.write("")

        # --------------------------------------------------
        # 7. CHARTS — BORDERS MATCH OTHER PAGES
        # --------------------------------------------------
        st.markdown(
            '<div class="section-title">Operational Activity</div>',
            unsafe_allow_html=True,
        )

        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                st.markdown('<div class="card-title">Transaction Type Breakdown</div>', unsafe_allow_html=True)
                st.markdown('<div class="card-sub">Count of rows by transaction classification</div>', unsafe_allow_html=True)
                if not type_df.empty:
                    render_chart(type_df, "bar", "transaction_type", "transaction_rows",
                                 x_label="Transaction Type", y_label="Rows", height=360)
                else:
                    st.info("No transaction-type data for these filters.")

        with right:
            with st.container(border=True):
                st.markdown('<div class="card-title">Monthly Cancellations</div>', unsafe_allow_html=True)
                st.markdown('<div class="card-sub">Cancellation rows over time</div>', unsafe_allow_html=True)
                if not monthly_cancellations.empty:
                    render_chart(monthly_cancellations, "line", "month_start", "cancellation_rows",
                                 x_label="Month", y_label="Cancellation Rows", height=360)
                else:
                    st.info("No cancellation rows for these filters.")

        st.write("")
        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                st.markdown('<div class="card-title">Monthly Returns & Adjustments</div>', unsafe_allow_html=True)
                st.markdown('<div class="card-sub">Adjustment / return rows over time</div>', unsafe_allow_html=True)
                if not monthly_returns.empty:
                    render_chart(monthly_returns, "line", "month_start", "return_rows",
                                 x_label="Month", y_label="Return / Adjustment Rows", height=360)
                else:
                    st.info("No return / adjustment rows for these filters.")

        with right:
            with st.container(border=True):
                st.markdown('<div class="card-title">Markets by Non-Sale Activity</div>', unsafe_allow_html=True)
                st.markdown('<div class="card-sub">Countries with the most non-sale transaction rows</div>', unsafe_allow_html=True)
                if not country_ops.empty:
                    render_chart(country_ops, "bar", "country", "non_sale_rows",
                                 x_label="Country", y_label="Non-Sale Rows", height=360)
                else:
                    st.info("No non-sale activity for these filters.")

        st.write("")

        # --------------------------------------------------
        # 8. THREE INSIGHT CARDS
        # --------------------------------------------------
        st.markdown(
            '<div class="section-title">Operational Insights</div>',
            unsafe_allow_html=True,
        )

        top_type = "—"
        top_type_rows = 0
        if not type_df.empty:
            top_type = str(type_df.iloc[0]["transaction_type"])
            top_type_rows = int(type_df.iloc[0]["transaction_rows"])

        top_country = "—"
        top_country_rows = 0
        if not country_ops.empty:
            top_country = str(country_ops.iloc[0]["country"] or "Unknown")
            top_country_rows = int(country_ops.iloc[0]["non_sale_rows"])

        insight_html = f"""
        <div class="insight-grid">
            <div class="insight-card">
                <div class="card-title">Cancellation Activity</div>
                <div class="card-sub">Cancellation volume relative to sale rows</div>
                <div class="signal-item"><span>Cancellation rows</span><span class="signal-status">{cancellation_rows:,}</span></div>
                <div class="signal-item"><span>Cancellation rate</span><span class="signal-status">{cancellation_rate:.2f}%</span></div>
                <div class="signal-item"><span>Sale rows</span><span class="signal-status">{sale_rows:,}</span></div>
            </div>
            <div class="insight-card">
                <div class="card-title">Returns & Adjustments</div>
                <div class="card-sub">Recorded adjustment / return activity</div>
                <div class="signal-item"><span>Return / adjustment rows</span><span class="signal-status">{return_rows:,}</span></div>
                <div class="signal-item"><span>Rate vs sale rows</span><span class="signal-status">{return_rate:.2f}%</span></div>
                <div class="signal-item"><span>Other transaction rows</span><span class="signal-status">{other_rows:,}</span></div>
            </div>
            <div class="insight-card accent">
                <div class="card-title">Operational Signals</div>
                <div class="card-sub">Non-sale transaction composition</div>
                <div class="signal-item"><span>Most frequent transaction type</span><span class="signal-status">{escape(top_type)}</span></div>
                <div class="signal-item"><span>Rows in leading type</span><span class="signal-status">{top_type_rows:,}</span></div>
                <div class="signal-item"><span>Top market by non-sale rows</span><span class="signal-status">{escape(top_country)}</span></div>
                <div class="signal-item"><span>Non-sale rows in top market</span><span class="signal-status">{top_country_rows:,}</span></div>
            </div>
        </div>
        """
        st.html(insight_html)

    except Exception as e:
        st.error("Unable to load Operations Analysis data from PostgreSQL.")
        st.exception(e)
