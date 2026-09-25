import streamlit as st
import pandas as pd

from db_connection import get_connection


# ==================================================
# LOAD FILTER OPTIONS FROM POSTGRESQL
# ==================================================

@st.cache_data(ttl=300)
def get_filter_options():

    conn = get_connection()

    try:
        countries = pd.read_sql_query("""
            SELECT DISTINCT country
            FROM analytics.base_sales
            WHERE country IS NOT NULL
            ORDER BY country;
        """, conn)

        years = pd.read_sql_query("""
            SELECT DISTINCT year
            FROM analytics.base_sales
            WHERE year IS NOT NULL
            ORDER BY year DESC;
        """, conn)

        months = pd.read_sql_query("""
            SELECT DISTINCT month, month_name
            FROM analytics.base_sales
            WHERE month IS NOT NULL
            ORDER BY month;
        """, conn)

        transaction_types = pd.read_sql_query("""
    SELECT DISTINCT transaction_type
    FROM transactions
    WHERE transaction_type IS NOT NULL
    ORDER BY transaction_type;
""", conn)

        return {
            "countries": countries["country"].tolist(),
            "years": years["year"].tolist(),
            "months": months.to_dict("records"),
            "transaction_types": transaction_types[
                "transaction_type"
            ].tolist()
        }

    finally:
        conn.close()


# ==================================================
# RESET FILTERS
# ==================================================

def reset_filters():

    st.session_state["filter_country"] = "All Countries"
    st.session_state["filter_year"] = "All Years"
    st.session_state["filter_month"] = "All Months"
    st.session_state["filter_transaction_type"] = "All Types"


# ==================================================
# RENDER OVERVIEW FILTERS
# ==================================================

def render_overview_filters():
    get_filter_options.clear()
    st.markdown(
        '<div class="section-title">Dashboard Filters</div>',
        unsafe_allow_html=True
    )

    try:
        options = get_filter_options()

    except Exception as e:

        st.error("Unable to load filter options from PostgreSQL.")
        st.exception(e)

        return {
            "country": None,
            "year": None,
            "month": None,
            "transaction_type": None
        }

    # ------------------------------------------------
    # FILTER OPTIONS
    # ------------------------------------------------

    country_options = ["All Countries"] + options["countries"]

    year_options = ["All Years"] + [
        int(year) for year in options["years"]
    ]

    month_labels = {
        f"{int(m['month']):02d} - {m['month_name']}": int(m["month"])
        for m in options["months"]
    }

    month_options = ["All Months"] + list(month_labels.keys())

    type_options = ["All Types"] + options["transaction_types"]

    # ------------------------------------------------
    # INITIAL VALUES
    # ------------------------------------------------

    st.session_state.setdefault("filter_country", "All Countries")
    st.session_state.setdefault("filter_year", "All Years")
    st.session_state.setdefault("filter_month", "All Months")
    st.session_state.setdefault("filter_transaction_type", "All Types")

    # ------------------------------------------------
    # FILTER LAYOUT
    # ------------------------------------------------

    with st.container(border=True):

        col1, col2, col3, col4, col5 = st.columns(
            [1.3, 0.8, 1, 1.5, 0.8]
        )

        with col1:
            country = st.selectbox(
                "🌍 Country",
                country_options,
                key="filter_country"
            )

        with col2:
            year = st.selectbox(
                "📅 Year",
                year_options,
                key="filter_year"
            )

        with col3:
            month = st.selectbox(
                "🗓️ Month",
                month_options,
                key="filter_month"
            )

        with col4:
            transaction_type = st.selectbox(
                "🛒 Transaction Type",
                type_options,
                key="filter_transaction_type"
            )

        with col5:
            st.markdown("<div style='height: 28px'></div>",
                        unsafe_allow_html=True)

            st.button(
                "↺ Reset",
                key="reset_overview_filters",
                use_container_width=True,
                on_click=reset_filters
            )

    # ------------------------------------------------
    # RETURN FILTER VALUES
    # ------------------------------------------------

    return {
        "country": (
            None if country == "All Countries"
            else country
        ),

        "year": (
            None if year == "All Years"
            else int(year)
        ),

        "month": (
            None if month == "All Months"
            else month_labels[month]
        ),

        "transaction_type": (
            None if transaction_type == "All Types"
            else transaction_type
        )
    }