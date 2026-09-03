import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from utils.formatting import format_currency
from utils.theme import apply_theme

st.set_page_config(page_title="BizMetrics - Receivables", layout="wide")
apply_theme()
render_sidebar()
render_header("Receivables", "Track and manage outstanding payments.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]
raw_data = st.session_state.get("raw_data", pd.DataFrame())
receivables = result.get("receivables", {})

if not raw_data.empty:
    rec_df = raw_data[raw_data['Record_Type'].str.lower() == 'receivable'].copy()
else:
    rec_df = pd.DataFrame()

# KPIs
st.markdown("### Outstanding Summary")
c1, c2, c3 = st.columns(3)

total_outstanding = receivables.get('total_outstanding', 0.0)
overdue = receivables.get('overdue', 0.0)
dso = receivables.get('days_sales_outstanding', 0)

with c1: kpi_card("Total Outstanding", format_currency(total_outstanding))
with c2: kpi_card("Overdue Payments", format_currency(overdue))
with c3: kpi_card("Days Sales Outstanding (DSO)", f"{dso} days")

st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)

st.markdown("### Outstanding Invoices")

if not rec_df.empty:
    display_cols = [col for col in ['Date', 'Customer_ID', 'Total_Amount', 'Due_Date', 'Status'] if col in rec_df.columns]
    
    if 'Status' in rec_df.columns:
        # Simple color formatting for status
        def color_status(val):
            color = 'red' if val.lower() == 'overdue' else 'orange' if val.lower() == 'pending' else 'green'
            return f'color: {color}'
        st.dataframe(rec_df[display_cols].style.map(color_status, subset=['Status']))
    else:
        st.dataframe(rec_df[display_cols])
else:
    st.info("No receivables data found in the current dataset.")
