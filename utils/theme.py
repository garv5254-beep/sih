import streamlit as st

def apply_theme():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
            
            /* Background & Global Fonts */
            .stApp {
                background-color: #FAF9F6;
            }
            * {
                font-family: 'Inter', sans-serif;
                color: #111827;
            }
            
            /* Headings */
            h1, h2, h3 {
                font-family: 'Playfair Display', serif !important;
                color: #111827;
                font-weight: 600;
            }
            
            /* Metric / Value text */
            [data-testid="stMetricValue"] {
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                color: #111827;
            }
            
            /* Sidebar */
            [data-testid="stSidebar"] {
                background-color: #F4F1DE;
                border-right: 1px solid #E5E7EB;
            }
            
            /* Remove default header space */
            header {visibility: hidden;}
            
            /* Premium Cards */
            .ep-card {
                background-color: #FFFFFF;
                padding: 1.5rem;
                border-radius: 8px;
                border: 1px solid #E5E7EB;
                box-shadow: 0 1px 3px rgba(0,0,0,0.02);
                margin-bottom: 1rem;
            }
            
            .ep-card-title {
                color: #4B5563;
                font-size: 0.875rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.5rem;
            }
            
            .ep-card-value {
                font-size: 2rem;
                font-weight: 600;
                color: #111827;
                margin: 0;
            }
            
            /* Buttons */
            .stButton>button {
                background-color: #C65D47 !important;
                color: #FFFFFF !important;
                border: none !important;
                border-radius: 6px !important;
                font-weight: 500 !important;
            }
            .stButton>button:hover {
                background-color: #9D4330 !important;
            }
            
            /* Insight Cards */
            .ep-insight {
                background-color: #F4F1DE;
                border-left: 4px solid #C65D47;
                padding: 1rem;
                border-radius: 0 8px 8px 0;
                margin-bottom: 1rem;
            }
            .ep-insight-title {
                font-weight: 600;
                color: #9D4330;
                margin-bottom: 0.25rem;
                font-size: 0.9rem;
            }
            .ep-insight-text {
                font-size: 0.9rem;
                color: #374151;
            }
        </style>
    """, unsafe_allow_html=True)

def get_colors():
    return {
        "terracotta": "#C65D47",
        "deep_rust": "#9D4330",
        "olive": "#6B705C",
        "limestone": "#F4F1DE",
        "bg": "#FAF9F6",
        "white": "#FFFFFF",
        "primary": "#C65D47",
        "secondary": "#6B705C",
        "background": "#FAF9F6",
        "surface": "#FFFFFF",
        "text": "#1F2937",
    }
