import streamlit as st
import pandas as pd
import numpy as np
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from utils.formatting import format_currency
from utils.theme import apply_theme

st.set_page_config(page_title="BizMetrics - Receivables", layout="wide")
apply_theme()
render_sidebar()
render_header("Receivables", "Track and manage outstanding payments.")

st.markdown(
    """
    <style>
        /* Receivables information/dialogue styling */
        [data-testid="stAlert"] {
            background: #68705A !important;
            border: 1px solid #68705A !important;
            border-radius: 12px !important;
            color: #FFFFFF !important;
        }

        [data-testid="stAlert"] p,
        [data-testid="stAlert"] span,
        [data-testid="stAlert"] div,
        [data-testid="stAlert"] strong,
        [data-testid="stAlert"] svg {
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
            stroke: #FFFFFF !important;
        }

        /* Receivables tables, controls, and section text */
        [data-testid="stDataFrame"] {
            border: 1px solid #68705A !important;
            border-radius: 10px !important;
            background: #F4EBDD !important;
        }

        [data-testid="stSelectbox"] label,
        [data-testid="stTextInput"] label,
        [data-testid="stMultiSelect"] label,
        [data-testid="stSelectbox"] div,
        [data-testid="stTextInput"] div,
        [data-testid="stMultiSelect"] div {
            color: #263238 !important;
        }

        [data-testid="stSelectbox"] input,
        [data-testid="stTextInput"] input,
        [data-testid="stMultiSelect"] input {
            color: #263238 !important;
            background: #F4EBDD !important;
        }

        [data-testid="stButton"] button,
        [data-testid="stDownloadButton"] button {
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
            stroke: #FFFFFF !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]
raw_data = st.session_state.get("raw_data", pd.DataFrame())
receivables = result.get("receivables", {})

if not raw_data.empty:
    rec_df = raw_data[raw_data['record_type'].astype(str).str.lower() == 'receivable'].copy()
else:
    rec_df = pd.DataFrame()

# ---- KPIs ----
st.markdown("### Outstanding Summary")
c1, c2, c3, c4 = st.columns(4)

total_outstanding = receivables.get('total_outstanding', 0.0)
total_invoiced = receivables.get('total_invoiced', 0.0)
total_paid = receivables.get('total_paid', 0.0)
collection_rate = receivables.get('collection_rate', 0.0)

with c1: kpi_card("Total Receivables (Outstanding)", format_currency(total_outstanding))
with c2: kpi_card("Total Invoiced", format_currency(total_invoiced))
with c3: kpi_card("Total Paid", format_currency(total_paid))
with c4: kpi_card("Collection Rate", f"{collection_rate:.1f}%")

st.write("")
c5, c6, c7 = st.columns(3)
with c5: kpi_card("Overdue", format_currency(receivables.get('overdue', 0.0)))
with c6: kpi_card("Due Soon", format_currency(receivables.get('due_soon', 0.0)))
with c7: kpi_card("Pending", format_currency(receivables.get('pending', 0.0)))

st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)

# ---- Status Formatting ----
def color_status(val):
    if pd.isna(val):
        return ""
    status = str(val).strip().lower()
    if status == "overdue":
        return "color: #9B493C; font-weight: 700;"
    elif status == "due soon":
        return "color: #9B493C; font-weight: 700;"
    elif status in ("paid", "settled", "cleared"):
        return "color: #78805B; font-weight: 700;"
    elif status == "pending":
        return "color: #555555; font-weight: 700;"
    return ""


def readable_receivables_table_styles():
    return [
        {
            "selector": "th",
            "props": [
                ("background-color", "#68705A"),
                ("color", "#FFFFFF"),
                ("font-weight", "700"),
            ],
        },
        {
            "selector": "td",
            "props": [
                ("background-color", "#F4EBDD"),
                ("color", "#263238"),
            ],
        },
    ]

if not rec_df.empty:
    # Build clean invoice table
    inv_df = rec_df.rename(columns={
        'customer_name': 'Customer',
        'sale_id': 'Invoice',
        'total_amount': 'Invoice Amount',
        'total_paid_amount': 'Amount Paid',
        'outstanding_amount': 'Outstanding',
        'date': 'Invoice Date',
        'due_date': 'Due Date',
        'Days_Overdue': 'Days Overdue'
    })
    
    # ---------------------------------------------------------
    # CLEAN RECEIVABLE DATE DATA
    # ---------------------------------------------------------
    
    if 'Due Date' in inv_df.columns:
        inv_df['Due Date'] = pd.to_datetime(
            inv_df['Due Date'],
            errors='coerce'
        )
    
    if 'Payment Date' in inv_df.columns:
        inv_df['Payment Date'] = pd.to_datetime(
            inv_df['Payment Date'],
            errors='coerce'
        )
    
    # Ensure numeric receivable fields are actually numeric
    for col in ['Credit Amount', 'Invoice Amount', 'Amount Paid', 'Outstanding']:
        if col in inv_df.columns:
            inv_df[col] = pd.to_numeric(
                inv_df[col],
                errors='coerce'
            ).fillna(0)
    
    # ---------------------------------------------------------
    # CUSTOMER-LEVEL RECEIVABLE SUMMARY
    # ---------------------------------------------------------
    
    st.markdown("### Customer-Level Receivables")
    
    cust_group = inv_df.groupby('Customer').agg(
        Total_Invoiced=('Invoice Amount', 'sum'),
        Total_Paid=('Amount Paid', 'sum'),
        Outstanding=('Outstanding', 'sum'),
        Oldest_Due_Date=('Due Date', lambda x: x.min() if x.notna().any() else pd.NaT),
        Max_Days_Overdue=('Days Overdue', 'max')
    ).reset_index()
    
    # Determine Customer Status
    def get_cust_status(row):
        if row['Outstanding'] <= 0:
            return "Paid"
        if row['Max_Days_Overdue'] > 0:
            return "Overdue"
        return "Pending"
        
    cust_group['status'] = cust_group.apply(get_cust_status, axis=1)
    cust_group = cust_group.sort_values(by='Outstanding', ascending=False)
    
    st.dataframe(
        cust_group.style.set_table_styles(readable_receivables_table_styles())
                        .map(color_status, subset=['status'])
                        .format({
                            'Total_Invoiced': '₹ {:,.2f}',
                            'Total_Paid': '₹ {:,.2f}',
                            'Outstanding': '₹ {:,.2f}',
                            'Max_Days_Overdue': '{:.0f}'
                        }),
        width="stretch"
    )
    
    st.write("")
    
    # Invoice Level Table
    st.markdown("### Detailed Invoices")
    
    display_cols = ['Customer', 'Invoice', 'Invoice Amount', 'Amount Paid', 'Outstanding', 'Invoice Date', 'Due Date', 'Days Overdue', 'status']
    existing_cols = [c for c in display_cols if c in inv_df.columns]
    
    st.dataframe(
        inv_df[existing_cols].sort_values(by=['Outstanding', 'Days Overdue'], ascending=[False, False])
        .style.set_table_styles(readable_receivables_table_styles())
              .map(color_status, subset=['status'])
              .format({
                  'Invoice Amount': '₹ {:,.2f}',
                  'Amount Paid': '₹ {:,.2f}',
                  'Outstanding': '₹ {:,.2f}',
                  'Days Overdue': '{:.0f}'
              }),
        width="stretch"
    )
else:
    st.info("No receivables data found in the current dataset.")

