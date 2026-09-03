import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from utils.formatting import format_currency, t
from utils.theme import apply_theme

st.set_page_config(page_title="BizMetrics - Customers", layout="wide")
apply_theme()
render_sidebar()
render_header("Customers", "Manage your customers, outstanding receivables, and collection periods.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]
raw_data = st.session_state.get("raw_data", pd.DataFrame())
r = result.get("receivables", {})

c1, c2, c3 = st.columns(3)
with c1: kpi_card("Total Outstanding", format_currency(r.get('total_outstanding', 0)))
with c2: kpi_card("Overdue Amount", format_currency(r.get('overdue', 0)))
with c3: kpi_card("Days Sales Outstanding", f"{r.get('days_sales_outstanding', 0)} days")

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)

if not raw_data.empty:
    rec_df = raw_data[raw_data['Record_Type'].str.lower() == 'receivable'].copy()
    if not rec_df.empty:
        st.markdown("### Customer Receivables Table")
        
        display_cols = []
        if 'Customer_Name' in rec_df.columns: display_cols.append('Customer_Name')
        elif 'Party_Name' in rec_df.columns: display_cols.append('Party_Name')
        
        if 'Outstanding_Amount' in rec_df.columns: display_cols.append('Outstanding_Amount')
        if 'Due_Date' in rec_df.columns: display_cols.append('Due_Date')
        if 'Days_Overdue' in rec_df.columns: display_cols.append('Days_Overdue')
        if 'Payment_Status' in rec_df.columns: display_cols.append('Payment_Status')
        
        if display_cols:
            st.dataframe(rec_df[display_cols], width="stretch", hide_index=True)
        else:
            st.dataframe(rec_df, width="stretch", hide_index=True)
    else:
        st.info("No receivable records found.")
else:
    st.info("Raw data not available for detailed tables.")

