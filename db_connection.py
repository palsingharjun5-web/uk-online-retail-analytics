import streamlit as st
import psycopg2


def get_connection():
    """
    Creates and returns a PostgreSQL database connection.
    """

    conn = psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        port=st.secrets["postgres"]["port"],
        dbname=st.secrets["postgres"]["dbname"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        sslmode=st.secrets["postgres"]["sslmode"]
    )

    return conn