import streamlit as st
import base64
from pathlib import Path

def apply_theme():
        # Load background image and convert it to Base64
    image_path = Path(__file__).resolve().parent.parent / "assets" / "bg.png"

    with open(image_path, "rb") as image_file:
        bg_base64 = base64.b64encode(image_file.read()).decode()

    bg_data = f"data:image/png;base64,{bg_base64}"
    st.html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        :root {
            --bg-outer: #E8EBE6;
            --bg-main: #F3F6F1;
            --bg-sidebar: #FFFFFF;
            --card-bg: #FFFFFF;
            --green-primary: #1F7A4D;
            --green-dark: #14603B;
            --green-deep: #0F4F30;
            --green-light: #E3F3EA;
            --mint: #BFE6D0;
            --text-main: #1A2B22;
            --text-muted: #7A877F;
            --border: #E6EDE7;
            --shadow: 0 8px 28px rgba(22, 48, 34, 0.06);
            --radius: 22px;
        }
        html, body, [class*="css"], .stApp, .stMarkdown, p, label, input {
    font-family: "Plus Jakarta Sans", sans-serif !important;
}

/* Fix Streamlit icons */
[data-testid="stIconMaterial"] {
    font-family: "Material Symbols Rounded" !important;
    font-weight: normal !important;
    font-style: normal !important;
}

        .stApp {
    background: url("__MINT_BG__") center center / cover fixed no-repeat;
    color: var(--text-main);
}

        [data-testid="stHeader"] {
            background: transparent;
        }

      /* Hide unnecessary Streamlit UI */
       #MainMenu,
       footer,
       .stAppDeployButton,
       [data-testid="stDecoration"] {
          display: none !important;
          visibility: hidden;
         }

/* Keep the header and sidebar expand control accessible */
[data-testid="stHeader"] {
    display: block !important;
    visibility: visible !important;
    background: transparent !important;
}

[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
}

        .main .block-container {
            background: rgba(247, 249, 246, 0.88);
            max-width: 1480px;
            padding: 1.6rem 1.8rem 2.4rem 1.8rem;
            margin: 0.85rem 0.9rem 0.9rem 0.4rem;
            border-radius: 28px;
            box-shadow: var(--shadow);
            border: 1px solid rgba(255,255,255,0.7);
        }

        h1, h2, h3 {
            color: var(--text-main) !important;
            font-weight: 750 !important;
            letter-spacing: -0.6px;
        }

        [data-testid="stCaptionContainer"] {
            color: var(--text-muted) !important;
        }

        hr {
            border: none !important;
            border-top: 1px solid var(--border) !important;
            margin: 0.4rem 0 1rem 0 !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding: 1.4rem 1.05rem 1.6rem 1.05rem;
        }

        [data-testid="stSidebar"] [data-testid="stRadio"] > label {
            display: none;
        }

        [data-testid="stSidebar"] [role="radiogroup"] {
            gap: 0.28rem;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label {
            background: transparent;
            border-radius: 14px;
            padding: 0.62rem 0.85rem !important;
            border: none;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: var(--green-light);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            background: var(--green-light);
            color: var(--green-dark) !important;
            font-weight: 700;
        }

        [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {
            display: none;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0.15rem 0 1.5rem 0.2rem;
        }

        .brand-mark {
            width: 42px;
            height: 42px;
            border-radius: 14px;
            background: linear-gradient(180deg, #2E9A62 0%, #1F7A4D 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 13px;
            box-shadow: 0 8px 16px rgba(31, 122, 77, 0.25);
        }

        .brand-title {
            font-size: 16px;
            font-weight: 800;
            color: var(--text-main);
            line-height: 1.1;
        }

        .brand-sub {
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 3px;
        }

        .nav-label {
            color: #8A958E;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1.6px;
            margin: 0 0 8px 8px;
        }

        .sidebar-foot {
            margin-top: 1.6rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 11px;
            padding-left: 8px;
        }

        /* Header */
        .page-kicker {
            color: var(--green-primary);
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.8px;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .page-title {
            font-size: 34px;
            font-weight: 800;
            letter-spacing: -1.2px;
            color: var(--text-main);
            line-height: 1.1;
            margin: 0;
        }

        .page-sub {
            color: var(--text-muted);
            font-size: 14px;
            margin-top: 8px;
        }

        /* Filters */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--card-bg);
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            box-shadow: var(--shadow);
            padding: 0.35rem 0.2rem;
        }

        .stSelectbox label {
            font-size: 12px !important;
            font-weight: 650 !important;
            color: var(--text-muted) !important;
        }

        .stSelectbox [data-baseweb="select"] > div {
            background: #F4F8F4 !important;
            border-radius: 12px !important;
            border-color: var(--border) !important;
            min-height: 42px;
        }

        .stButton > button {
            background: var(--green-primary);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 700;
            height: 42px;
            box-shadow: 0 8px 16px rgba(31, 122, 77, 0.18);
        }

        .stButton > button:hover {
            background: var(--green-dark);
            color: white;
            border: none;
        }

        /* KPI */
        .kpi-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1.05rem 1.15rem 1rem 1.15rem;
            min-height: 126px;
            box-shadow: var(--shadow);
        }

        .kpi-card.featured {
            background: linear-gradient(180deg, #2A8F58 0%, #1B6B44 100%);
            border: none;
            color: white;
            box-shadow: 0 12px 24px rgba(27, 107, 68, 0.28);
        }

        .kpi-label {
            font-size: 12px;
            font-weight: 650;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .kpi-card.featured .kpi-label {
            color: rgba(255,255,255,0.86);
        }

        .kpi-arrow {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: 1px solid var(--border);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            color: var(--green-primary);
        }

        .kpi-card.featured .kpi-arrow {
            border-color: rgba(255,255,255,0.35);
            color: white;
        }

        .kpi-value {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -1px;
            margin-top: 14px;
            color: var(--text-main);
            line-height: 1.1;
        }

        .kpi-card.featured .kpi-value {
            color: white;
        }

        .kpi-hint {
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 8px;
        }

        .kpi-card.featured .kpi-hint {
            color: rgba(255,255,255,0.78);
        }

        /* Chart / insight cards */
        .card-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 4px;
        }

        .card-title {
            font-size: 16px;
            font-weight: 800;
            color: var(--text-main);
        }

        .card-sub {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        .card-pill {
            background: var(--green-light);
            color: var(--green-dark);
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 11px;
            font-weight: 700;
            white-space: nowrap;
        }

        [data-testid="stPlotlyChart"] {
            background: transparent;
            border: none;
            padding: 0;
        }

        .insight-grid {
            display: grid;
            grid-template-columns: 1.1fr 1fr 1.2fr;
            gap: 14px;
        }

        .insight-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 1.15rem 1.2rem;
            min-height: 210px;
        }

        .insight-card.accent {
            background: linear-gradient(180deg, #1F7A4D 0%, #155C3A 100%);
            color: white;
            border: none;
        }

        .insight-card.accent .card-title,
        .insight-card.accent .card-sub {
            color: white;
        }

        .insight-card.accent .card-sub {
            opacity: 0.8;
        }

        .donut-wrap {
            display: flex;
            align-items: center;
            gap: 18px;
            margin-top: 18px;
        }

        .donut {
            width: 118px;
            height: 118px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .donut-inner {
            width: 78px;
            height: 78px;
            border-radius: 50%;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 20px;
            color: var(--text-main);
        }

        .legend-row {
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }

        .signal-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.16);
            font-size: 13px;
        }

        .signal-item:last-child {
            border-bottom: none;
        }

        .signal-status {
            font-size: 11px;
            font-weight: 700;
            background: rgba(255,255,255,0.16);
            border-radius: 999px;
            padding: 4px 8px;
        }

        .section-title {
            font-size: 18px;
            font-weight: 800;
            color: var(--text-main);
            margin: 0.2rem 0 0.85rem 0;
        }
        </style>
                """.replace("__MINT_BG__", bg_data)
    )
    
