import streamlit as st
from utils.theme import apply_theme
from utils.data_loader import refresh_application_data

st.set_page_config(page_title="BizMetrics", layout="wide", initial_sidebar_state="expanded")
apply_theme()

with st.spinner("Loading BizMetrics Dashboard..."):
    if "pipeline_result" not in st.session_state or "raw_data" not in st.session_state:
        try:
            refresh_application_data()
        except FileNotFoundError:
            st.error("BizMetrics dataset could not be found.")
            st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
            
            # Show searched locations to developer
            from pathlib import Path
            PROJECT_ROOT = Path(__file__).resolve().parent
            st.code(f"Searched:\n- {PROJECT_ROOT / 'rural_business_master_data.csv'}\n- {PROJECT_ROOT / 'data' / 'rural_business_master_data.csv'}")
            st.stop()
        except Exception as e:
            st.error(f"Error loading master dataset: {e}")
            st.stop()

# Redirect to the Overview page automatically
st.switch_page("pages/01_dashboard.py")
