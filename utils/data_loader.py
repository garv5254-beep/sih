import streamlit as st
import pandas as pd
from pathlib import Path
from pipeline import run_pipeline, validate_and_clean

def find_master_csv():
    """Finds the master CSV robustly from the project root."""
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    
    possible_paths = [
        PROJECT_ROOT / "rural_business_master_data.csv",
        PROJECT_ROOT / "data" / "rural_business_master_data.csv",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
            
    return None

@st.cache_data
def load_master_data():
    """Loads the master dataset and caches it."""
    csv_path = find_master_csv()
    
    if csv_path is None:
        raise FileNotFoundError("rural_business_master_data.csv was not found.")
        
    return pd.read_csv(csv_path), csv_path

def refresh_application_data():
    """Refreshes the application data and pipeline results into session state."""
    df, csv_path = load_master_data()
    clean_df = validate_and_clean(df)
    
    st.session_state["pipeline_result"] = run_pipeline(clean_df)
    st.session_state["raw_data"] = clean_df
    st.session_state["dataset_path"] = str(csv_path)
