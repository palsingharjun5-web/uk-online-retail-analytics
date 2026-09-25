import streamlit as st


def render_kpi_card(label, value, hint="", featured=False):

    card_class = "kpi-card featured" if featured else "kpi-card"

    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="kpi-label">
                <span>{label}</span>
                <span class="kpi-arrow">↗</span>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-hint">{hint}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
