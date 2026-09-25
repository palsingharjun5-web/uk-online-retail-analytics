import streamlit as st


def render_sidebar_navigation():

    with st.sidebar:

        st.markdown(
            """
            <div class="brand">
                <div class="brand-mark">UK</div>
                <div>
                    <div class="brand-title">UK Retail</div>
                    <div class="brand-sub">Analytics Dashboard</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="nav-label">MENU</div>', unsafe_allow_html=True)

        pages = [
            "Overview",
            "Sales",
            "Customers",
            "Products",
            "Geography",
            "Operations",
            "Findings"
        ]

        labels = {
            "Overview": "▦  Overview",
            "Sales": "↗  Sales",
            "Customers": "☺  Customers",
            "Products": "▣  Products",
            "Geography": "◎  Geography",
            "Operations": "⚙  Operations",
            "Findings": "★  Findings"
        }

        selected_page = st.radio(
            "Navigation",
            pages,
            index=0,
            key="sidebar_navigation",
            format_func=lambda page: labels[page],
            label_visibility="collapsed"
        )

        st.markdown(
            """
            <div class="sidebar-foot">
                UK Online Retail<br/>
                Business Intelligence
            </div>
            """,
            unsafe_allow_html=True
        )

    return selected_page
