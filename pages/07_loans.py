import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from utils.formatting import format_currency
from utils.theme import apply_theme

st.set_page_config(page_title="BizMetrics - Loans", layout="wide")
apply_theme()
render_sidebar()
render_header("Loan Management", "Track active loans, EMIs, and interest payments")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.stop()

result = st.session_state["pipeline_result"]
loans_data = result.get("loans", {})
loans_list = loans_data.get("loans", [])

# KPI Cards
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: kpi_card("Total Principal", format_currency(loans_data.get('total_principal', 0)))
with c2: kpi_card("Outstanding", format_currency(loans_data.get('outstanding_principal', 0)))
with c3: kpi_card("Monthly EMI", format_currency(loans_data.get('monthly_emi', 0)))
with c4: kpi_card("Monthly Interest", format_currency(loans_data.get('monthly_interest', 0)))
with c5: kpi_card("Total Interest Paid", format_currency(loans_data.get('total_interest_paid', 0)))
with c6: kpi_card("Active Loans", loans_data.get('active_loans', 0))

st.markdown("<br>", unsafe_allow_html=True)

if not loans_list:
    st.info("No loan records available.")
else:
    st.markdown("### Active Loans")
    df = pd.DataFrame(loans_list)
    
    # Format currency columns
    for col in ['Principal', 'Outstanding', 'Monthly_Payment']:
        df[col] = df[col].apply(lambda x: format_currency(x))
        
    df['Interest_Rate'] = df['Interest_Rate'].apply(lambda x: f"{x}%")
    
    st.dataframe(df, use_container_width=True)
