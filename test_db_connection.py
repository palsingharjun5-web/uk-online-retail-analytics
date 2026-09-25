import streamlit as st
import pandas as pd

from db_connection import get_connection
from Components.charts import render_chart

st.set_page_config(
    page_title="Real Data Chart Tests - Batch 2",
    layout="wide"
)

st.title("📊 Real Data Chart Gallery — Batch 2")
st.write("Final corrected tests using actual PostgreSQL columns.")


@st.cache_data(ttl=300)
def load_data(query):
    conn = get_connection()
    try:
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def show_chart(title, query, chart_type, x, y=None, **kwargs):
    st.subheader(title)

    try:
        df = load_data(query)

        if df.empty:
            st.warning("No data returned.")
            return

        render_chart(
            df=df,
            chart_type=chart_type,
            x=x,
            y=y,
            title=title,
            **kwargs
        )

        st.success(f"Passed — {len(df):,} rows loaded.")

    except Exception as e:
        st.error(f"Test failed: {e}")


# -----------------------------------
# 1. Top 10 Products by Units Sold
# -----------------------------------

show_chart(
    title="1. Top 10 Products by Units Sold",
    query="""
        SELECT stock_code, units_sold
        FROM analytics.product_volume
        ORDER BY units_sold DESC
        LIMIT 10;
    """,
    chart_type="bar",
    x="stock_code",
    y="units_sold",
    x_label="Product",
    y_label="Units Sold"
)


# -----------------------------------
# 2. Return Analysis by Transaction Type
# -----------------------------------

show_chart(
    title="2. Return Analysis by Transaction Type",
    query="""
        SELECT transaction_type, return_rows
        FROM analytics.return_analysis
        ORDER BY return_rows DESC;
    """,
    chart_type="bar",
    x="transaction_type",
    y="return_rows",
    x_label="Transaction Type",
    y_label="Return Rows"
)


# -----------------------------------
# 3. Return Rate Metrics
# -----------------------------------

st.subheader("3. Return Rate Metrics")

try:
    rate_df = load_data("""
        SELECT
            sales_orders,
            return_orders,
            return_order_rate_percent
        FROM analytics.return_rate;
    """)

    st.dataframe(rate_df, use_container_width=True)

    rate_chart_df = pd.DataFrame({
        "metric": [
            "Sales Orders",
            "Return Orders",
            "Return Order Rate (%)"
        ],
        "value": [
            rate_df.iloc[0]["sales_orders"],
            rate_df.iloc[0]["return_orders"],
            rate_df.iloc[0]["return_order_rate_percent"]
        ]
    })

    render_chart(
        df=rate_chart_df,
        chart_type="bar",
        x="metric",
        y="value",
        title="Return Rate Metrics",
        x_label="Metric",
        y_label="Value"
    )

    st.success("Passed — Return Rate")

except Exception as e:
    st.error(f"Return Rate failed: {e}")


# -----------------------------------
# 4. Top 10 Countries by Return Orders
# -----------------------------------

show_chart(
    title="4. Top 10 Countries by Return Orders",
    query="""
        SELECT country, return_orders
        FROM analytics.country_returns
        ORDER BY return_orders DESC
        LIMIT 10;
    """,
    chart_type="bar",
    x="country",
    y="return_orders",
    x_label="Country",
    y_label="Return Orders"
)


# -----------------------------------
# 5. Special Transaction Breakdown
# -----------------------------------

show_chart(
    title="5. Special Transaction Breakdown",
    query="""
        SELECT transaction_type, "rows"
        FROM analytics.special_transactions
        ORDER BY "rows" DESC;
    """,
    chart_type="pie",
    x="transaction_type",
    y="rows"
)


st.success("Batch 2 testing completed!")