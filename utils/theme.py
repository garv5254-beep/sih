import streamlit as st

def apply_theme():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
            
            /* Background & Global Fonts */
            .stApp {
                background-color: #EDE5D0;
            }

            [data-baseweb="select"] > div,
            [data-testid="stTextInput"] input,
            [data-testid="stNumberInput"] input,
            [data-testid="stDateInput"] input,
            [data-testid="stMultiSelect"] input {
                background-color: #FFFFFF !important;
                color: #292622 !important;
                border-color: rgba(41, 38, 34, .2) !important;
            }

            [data-baseweb="select"] span,
            [data-baseweb="select"] div,
            [data-testid="stTextInput"] label,
            [data-testid="stNumberInput"] label,
            [data-testid="stDateInput"] label,
            [data-testid="stMultiSelect"] label {
                color: #292622 !important;
            }

            [data-baseweb="select"] > div:focus-within,
            [data-testid="stTextInput"] input:focus,
            [data-testid="stNumberInput"] input:focus,
            [data-testid="stDateInput"] input:focus {
                border-color: #9B493C !important;
                box-shadow: 0 0 0 1px #9B493C !important;
            }
            * {
                font-family: 'Inter', sans-serif;
            }
            
            /* Apply dark text to typography and labels */
            .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, label, li {
                color: #292622;
            }
            
            /* Headings */
            h1, h2, h3 {
                font-family: 'Playfair Display', serif !important;
                color: #292622;
                font-weight: 600;
            }
            
            /* Metric / Value text */
            [data-testid="stMetricValue"] {
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                color: #292622;
            }
            
            /* Sidebar */
            [data-testid="stSidebar"] {
                background-color: #EDE5D0;
                border-right: 1px solid rgba(41, 38, 34, .14);
            }

            [data-testid="stSidebar"] [data-baseweb="select"] > div {
                background-color: #FFFFFF !important;
            }
            
            /* Remove default header space */
            header {visibility: hidden;}
            
            /* Premium Cards */
            .ep-card {
                background-color: #FFFFFF;
                padding: 1.5rem;
                border-radius: 8px;
                border: 1px solid rgba(41, 38, 34, .12);
                border-radius: 14px;
                box-shadow: 0 6px 18px rgba(41, 38, 34, .08);
                margin-bottom: 1rem;
            }
            
            .ep-card-title {
                color: #78805B;
                font-size: 0.875rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.5rem;
            }
            
            .ep-card-value {
                font-size: 2rem;
                font-weight: 600;
                color: #292622;
                margin: 0;
            }
            
            /* Global Streamlit buttons */
            .stButton > button,
            .stDownloadButton > button,
            .stLinkButton > a,
            [data-testid="stFormSubmitButton"] > button {
                color: #FFFFFF !important;
                background-color: #9B493C !important;
                border: 1px solid #9B493C !important;
                border-radius: 6px !important;
                font-weight: 700 !important;
            }

            .stButton > button *,
            .stDownloadButton > button *,
            .stLinkButton > a *,
            [data-testid="stFormSubmitButton"] > button * {
                color: #FFFFFF !important;
                fill: #FFFFFF !important;
                stroke: #FFFFFF !important;
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover,
            .stLinkButton > a:hover,
            [data-testid="stFormSubmitButton"] > button:hover {
                color: #FFFFFF !important;
                background-color: #78372F !important;
                border-color: #78372F !important;
            }

            .stButton > button:focus,
            .stButton > button:active,
            .stDownloadButton > button:focus,
            .stDownloadButton > button:active,
            .stLinkButton > a:focus,
            .stLinkButton > a:active,
            [data-testid="stFormSubmitButton"] > button:focus,
            [data-testid="stFormSubmitButton"] > button:active {
                color: #FFFFFF !important;
                background-color: #9B493C !important;
                border-color: #9B493C !important;
                box-shadow: 0 0 0 2px rgba(155, 73, 60, 0.35) !important;
            }

            .stButton > button:disabled,
            .stDownloadButton > button:disabled,
            .stLinkButton > a[aria-disabled="true"],
            [data-testid="stFormSubmitButton"] > button:disabled {
                color: #FFFFFF !important;
                background-color: #9B493C !important;
                opacity: 0.65 !important;
            }
            
            /* Insight Cards */
            .ep-insight {
                background-color: #EDE5D0;
                border-left: 4px solid #9B493C;
                padding: 1rem;
                border-radius: 0 8px 8px 0;
                margin-bottom: 1rem;
            }
            .ep-insight-title {
                font-weight: 600;
                color: #9B493C;
                margin-bottom: 0.25rem;
                font-size: 0.9rem;
            }
            .ep-insight-text {
                font-size: 0.9rem;
                color: #292622;
            }
        </style>
    """, unsafe_allow_html=True)

def get_colors():
    return {
        "terracotta": "#9B493C",
        "deep_rust": "#78372F",
        "olive": "#78805B",
        "limestone": "#EDE5D0",
        "bg": "#EDE5D0",
        "white": "#FFFFFF",
        "primary": "#9B493C",
        "secondary": "#78805B",
        "background": "#EDE5D0",
        "surface": "#FFFFFF",
        "text": "#292622",
    }
