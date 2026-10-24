"""Academic styling and refined typography for the Timetable Scheduler.

Implements the 'Premium Academic' design system:
- Palette: Warm off-white (#F7F6F0), Deep Forest Green (#285943), Deep Charcoal (#252B25),
  Muted Sage (#82977A), Soft Cream (#EEE9D8), Light Warm Gray (#E3E2D9).
- Typography: Manrope for headings, Inter for body text.
"""

import streamlit as st


def apply_academic_theme():
    """Inject the Premium Academic theme CSS."""
    css = """
    <style>
    /* 1. Google Fonts: Manrope for Headings, Inter for Body */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #252B25;
    }

    /* Overall page background */
    .stApp {
        background-color: #F7F6F0;
    }

    /* Centered content container with balanced, comfortable padding */
    .block-container {
        padding-top: 1.25rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 880px !important;
    }

    /* 2. Headings Hierarchy */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #252B25 !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    /* Header styling - Top Centered */
    .academic-header {
        text-align: center;
        padding-top: 0.5rem;
        padding-bottom: 1.25rem;
        border-bottom: 1px solid #E3E2D9;
        margin-bottom: 1.5rem;
    }

    .academic-title {
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 2.35rem;
        font-weight: 800;
        color: #285943;
        margin: 0;
        line-height: 1.15;
        letter-spacing: -0.03em;
        text-align: center;
    }

    .academic-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        color: #73796F;
        margin-top: 0.45rem;
        margin-bottom: 0;
        line-height: 1.5;
        text-align: center;
    }

    /* Section Headings without numbering */
    .section-header {
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 1.12rem;
        font-weight: 700;
        color: #252B25;
        margin-top: 1.25rem;
        margin-bottom: 0.6rem;
        letter-spacing: -0.015em;
    }

    /* Subtle Dividers */
    hr {
        border: none;
        border-top: 1px solid #E3E2D9;
        margin: 1.35rem 0;
    }

    /* 3. Streamlit Input Controls & Surfaces */
    /* File uploader container */
    [data-testid="stFileUploader"] {
        background-color: #FFFFFF;
        border: 1px solid #E3E2D9;
        border-radius: 6px;
        padding: 0.75rem;
    }

    [data-testid="stFileUploader"] section {
        background-color: #F7F6F0 !important;
        border: 1px dashed #D0CFBF !important;
        border-radius: 5px !important;
        padding: 1rem 0.5rem !important;
    }

    /* Selectbox, Text input, Number input */
    .stSelectbox div[data-baseweb="select"] > div,
    .stNumberInput input,
    .stTextInput input {
        background-color: #FFFFFF !important;
        border: 1px solid #E3E2D9 !important;
        color: #252B25 !important;
        border-radius: 6px !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stSelectbox div[data-baseweb="select"] > div:focus-within,
    .stNumberInput input:focus,
    .stTextInput input:focus {
        border-color: #285943 !important;
        box-shadow: 0 0 0 1px #285943 !important;
    }

    /* 4. Buttons Styling */
    /* Primary Action: Deep Forest Green (Full Width) */
    button[kind="primary"] {
        background-color: #285943 !important;
        color: #FFFFFF !important;
        font-family: 'Manrope', 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.98rem !important;
        border-radius: 6px !important;
        border: 1px solid #204735 !important;
        padding: 0.65rem 1.4rem !important;
        transition: background-color 0.15s ease, border-color 0.15s ease !important;
        box-shadow: none !important;
    }

    button[kind="primary"]:hover {
        background-color: #1F4735 !important;
        border-color: #173729 !important;
        color: #FFFFFF !important;
    }

    /* Secondary Action: Clean White with warm-gray border */
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #252B25 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        border-radius: 6px !important;
        border: 1px solid #E3E2D9 !important;
        padding: 0.5rem 1rem !important;
        transition: background-color 0.15s ease, border-color 0.15s ease !important;
        box-shadow: none !important;
    }

    button[kind="secondary"]:hover {
        background-color: #EEE9D8 !important;
        border-color: #D5CEBA !important;
        color: #252B25 !important;
    }

    /* Download Buttons */
    .stDownloadButton > button {
        background-color: #FFFFFF !important;
        color: #285943 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        border: 1px solid #82977A !important;
        border-radius: 6px !important;
        padding: 0.55rem 1.15rem !important;
        transition: background-color 0.15s ease !important;
    }

    .stDownloadButton > button:hover {
        background-color: #EBF2ED !important;
        border-color: #285943 !important;
        color: #1F4735 !important;
    }

    /* 5. Alerts & Notifications */
    .academic-alert {
        border-radius: 6px;
        padding: 0.65rem 0.9rem;
        font-size: 0.86rem;
        line-height: 1.45;
        margin-top: 0.5rem;
        margin-bottom: 0.75rem;
        border: 1px solid transparent;
    }

    .academic-alert-success {
        background-color: #EBF2ED;
        color: #285943;
        border-color: #C6D8CC;
    }

    .academic-alert-warning {
        background-color: #FAF4E6;
        color: #8A5B18;
        border-color: #EDE0C2;
    }

    .academic-alert-error {
        background-color: #FBEFEF;
        color: #8B2626;
        border-color: #EDCECE;
    }

    .academic-alert-info {
        background-color: #F5F4ED;
        color: #475549;
        border-color: #E3E0D1;
    }

    /* 6. Expanders */
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E3E2D9 !important;
        border-radius: 6px !important;
    }

    /* 7. Timetable Grid Styling */
    .academic-tt-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-top: 0.65rem;
        margin-bottom: 1rem;
        background-color: #FFFFFF;
        border: 1px solid #E3E2D9;
        border-radius: 6px;
        overflow: hidden;
    }

    .academic-tt-table th {
        background-color: #285943;
        color: #FFFFFF;
        padding: 8px 10px;
        font-family: 'Manrope', sans-serif;
        font-size: 0.82rem;
        font-weight: 700;
        text-align: center;
        letter-spacing: 0.02em;
        border-right: 1px solid #366b53;
    }

    .academic-tt-table th:last-child {
        border-right: none;
    }

    .academic-tt-table td {
        padding: 6px 8px;
        border-right: 1px solid #EBEAE2;
        border-bottom: 1px solid #EBEAE2;
        font-size: 0.8rem;
        vertical-align: top;
        min-height: 55px;
        background-color: #FFFFFF;
    }

    .academic-tt-table tr:last-child td {
        border-bottom: none;
    }

    .academic-tt-table td:last-child {
        border-right: none;
    }

    .academic-tt-period-col {
        font-family: 'Manrope', sans-serif;
        font-weight: 700;
        text-align: center;
        background-color: #F7F6F0 !important;
        color: #252B25 !important;
        width: 70px;
        vertical-align: middle !important;
    }

    .academic-session-cell {
        background-color: #FBFBF9;
        border: 1px solid #E3E2D9;
        border-left: 3px solid #285943;
        border-radius: 4px;
        padding: 5px 7px;
    }

    .academic-session-subj {
        font-family: 'Manrope', sans-serif;
        font-weight: 700;
        color: #252B25;
        font-size: 0.82rem;
    }

    .academic-session-meta {
        font-size: 0.72rem;
        color: #73796F;
        margin-top: 2px;
        line-height: 1.3;
    }

    .academic-lab-badge {
        font-size: 0.66rem;
        background-color: #EEE9D8;
        color: #285943;
        font-weight: 600;
        padding: 1px 4px;
        border-radius: 3px;
        display: inline-block;
        margin-left: 4px;
    }

    .academic-break-cell {
        background-color: #F7F6F0;
        border: 1px dashed #D5CEBA;
        border-radius: 4px;
        padding: 6px 4px;
        text-align: center;
        color: #73796F;
        font-size: 0.76rem;
        font-style: italic;
    }

    .academic-lunch-cell {
        background-color: #FAF4E6;
        border: 1px dashed #EDE0C2;
        border-radius: 4px;
        padding: 6px 4px;
        text-align: center;
        color: #8A5B18;
        font-size: 0.76rem;
        font-weight: 500;
    }

    .academic-empty-cell {
        color: #B5B9B0;
        text-align: center;
        padding: 6px 0;
        font-size: 0.78rem;
    }

    /* 8. Status Badges */
    .badge {
        display: inline-block;
        padding: 0.18rem 0.5rem;
        font-size: 0.72rem;
        font-weight: 600;
        border-radius: 4px;
        letter-spacing: 0.02em;
    }
    .badge-success {
        background-color: #EBF2ED;
        color: #285943;
        border: 1px solid #C6D8CC;
    }
    .badge-danger {
        background-color: #FBEFEF;
        color: #8B2626;
        border: 1px solid #EDCECE;
    }
    .badge-warning {
        background-color: #FAF4E6;
        color: #8A5B18;
        border: 1px solid #EDE0C2;
    }
    .badge-neutral {
        background-color: #F2EFE6;
        color: #73796F;
        border: 1px solid #E3E2D9;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_badge(text: str, badge_type: str = "neutral") -> str:
    """Return HTML string for a styled status badge."""
    valid_types = {"success", "danger", "warning", "info", "neutral"}
    b_type = badge_type if badge_type in valid_types else "neutral"
    return f'<span class="badge badge-{b_type}">{text}</span>'


def render_kpi_card(title: str, value: str | int, subtitle: str = ""):
    """Render a compact metric card (retained for backward compatibility)."""
    sub_html = f'<div style="font-size:0.75rem; color:#73796F;">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid #E3E2D9; border-radius:6px; padding:10px 14px; margin-bottom:8px;">
            <div style="font-size:0.75rem; color:#73796F; font-weight:600; text-transform:uppercase;">{title}</div>
            <div style="font-size:1.45rem; font-weight:700; color:#285943; font-family:'Manrope',sans-serif;">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
