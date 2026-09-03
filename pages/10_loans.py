import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from utils.formatting import format_currency, t
from utils.theme import apply_theme

st.set_page_config(page_title="BizMetrics - Loans & EMI", layout="wide")
apply_theme()
render_sidebar()
render_header("Loans & EMI", "Manage your loans, EMI schedules, and debt risk.")

if "raw_data" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

df = st.session_state["raw_data"]
loan_df = df[df['Record_Type'].str.lower() == 'loan'].copy()

if loan_df.empty:
    st.info("No loan records are currently available.")
    st.stop()

total_principal = pd.to_numeric(loan_df['Principal_Amount'], errors='coerce').sum()
total_emi = pd.to_numeric(loan_df['Monthly_EMI'], errors='coerce').sum()
total_outstanding = pd.to_numeric(loan_df['Outstanding_Principal'], errors='coerce').sum()

c1, c2, c3 = st.columns(3)
with c1: kpi_card("Total Principal", format_currency(total_principal))
with c2: kpi_card("Monthly EMI", format_currency(total_emi))
with c3: kpi_card("Outstanding Principal", format_currency(total_outstanding))

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)
st.markdown("### Loan Portfolio")

display_cols = []
for col in ['Loan_Provider', 'Principal_Amount', 'Interest_Rate', 'Tenure_Months', 'Monthly_EMI', 'Outstanding_Principal', 'Next_Due_Date']:
    if col in loan_df.columns:
        display_cols.append(col)
        
if display_cols:
    st.dataframe(loan_df[display_cols], width="stretch", hide_index=True)
else:
    st.dataframe(loan_df, width="stretch", hide_index=True)

