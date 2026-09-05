import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from components.charts import create_bar_chart, create_donut_chart
from utils.formatting import format_currency
from utils.theme import apply_theme, get_colors
from customer_qr_bills import render_customer_qr_and_bills

st.set_page_config(page_title="BizMetrics - Customers", layout="wide")

apply_theme()
render_sidebar()
render_header("Customer Intelligence", "Understand customer behavior, value, activity and purchasing patterns.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]
raw_data = st.session_state.get("raw_data", pd.DataFrame())
c = result.get("customers", {})
customers_list = c.get("customers", [])
colors = get_colors()

# KPI Cards
c1, c2, c3, c4 = st.columns(4)
with c1: kpi_card("Total Customers", f"{c.get('total_customers', 0)}")
with c2: kpi_card("Active Customers", f"{c.get('active_customers', 0)}")
with c3: kpi_card("High-Value Customers", f"{c.get('high_value_customers', 0)}")
with c4: kpi_card("New Customers", f"{c.get('new_customers', 0)}")

c5, c6, c7, c8 = st.columns(4)
with c5: kpi_card("Total Customer Revenue", format_currency(c.get('total_revenue', 0)))
with c6: kpi_card("Average Order Value", format_currency(c.get('aov', 0)))
with c7: 
    # Repeat Customer Rate
    repeat_custs = sum(1 for x in customers_list if x['Total_Orders'] > 1)
    repeat_rate = (repeat_custs / c.get('total_customers', 1)) * 100 if c.get('total_customers', 0) > 0 else 0
    kpi_card("Repeat Customer Rate", f"{repeat_rate:.1f}%")
with c8: kpi_card("Total Orders", f"{c.get('total_orders', 0)}")

st.divider()

if not customers_list:
    st.info("No customer records found.")
    st.stop()

df_cust = pd.DataFrame(customers_list)

def normalize_mobile(value):
    if pd.isna(value):
        return ""
    mobile = str(value).strip()
    if mobile.endswith(".0"):
        mobile = mobile[:-2]
    mobile = "".join(character for character in mobile if character.isdigit())
    return mobile if len(mobile) == 10 and mobile[0] in "6789" else ""


mobile_source = next((column for column in ("Mobile_Number", "Phone", "contact_number", "Mobile") if column in df_cust.columns), None)
df_cust["Mobile_Number"] = df_cust[mobile_source].apply(normalize_mobile) if mobile_source else ""
df_cust["Mobile Number"] = df_cust["Mobile_Number"].replace("", "Not Available")

# Customer data normalization
for col in ['customer_type', 'Customer', 'customer_name', 'business_name', 'Segment', 'status']:
    if col in df_cust.columns:
        df_cust[col] = (
            df_cust[col]
            .fillna('Unknown')
            .astype(str)
            .str.strip()
        )

col_charts1, col_charts2 = st.columns(2)

with col_charts1:
    st.markdown("### Revenue by Segment")
    segment_rev = df_cust.groupby('Segment')['Total_Spent'].sum().reset_index()
    if not segment_rev.empty and segment_rev['Total_Spent'].sum() > 0:
        fig1 = create_donut_chart(segment_rev, 'Segment', 'Total_Spent', "")
        st.plotly_chart(fig1, width="stretch")
    else:
        st.info("No revenue data available by segment.")

with col_charts2:
    st.markdown("### Top 5 Customers by Spending")
    top_custs = df_cust.nlargest(5, 'Total_Spent')
    if not top_custs.empty and top_custs['Total_Spent'].sum() > 0:
        # Use reversed order for horizontal bar chart so largest is at the top
        top_custs = top_custs.iloc[::-1]
        fig2 = create_bar_chart(top_custs, 'Total_Spent', 'business_name', "", colors.get('primary', '#9B493C'), orientation='h')
        st.plotly_chart(fig2, width="stretch")
    else:
        st.info("No spending data available.")

st.divider()

st.markdown("### CRM Database")

# Filters
f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    search_term = st.text_input("Search Customer/Business Name", "")
with f_col2:
    status_filter = st.selectbox("status", ["All"] + sorted(df_cust['status'].unique().tolist()))
with f_col3:
    type_filter = st.selectbox("Type", ["All"] + sorted(df_cust['customer_type'].unique().tolist()))

filtered_df = df_cust.copy()
if search_term:
    filtered_df = filtered_df[
        filtered_df['customer_name'].astype(str).str.contains(search_term, case=False, na=False) |
        filtered_df['business_name'].astype(str).str.contains(search_term, case=False, na=False) |
        filtered_df['customer_id'].astype(str).str.contains(search_term, case=False, na=False) |
        filtered_df['Mobile_Number'].astype(str).str.contains(normalize_mobile(search_term) or search_term.strip(), case=False, na=False)
    ]
if status_filter != "All":
    filtered_df = filtered_df[filtered_df['status'] == status_filter]
if type_filter != "All":
    filtered_df = filtered_df[filtered_df['customer_type'] == type_filter]

# Display columns
display_cols = ['business_name', 'customer_id', 'Mobile Number', 'customer_type', 'Total_Spent', 'Total_Orders', 'AOV', 'Last_Purchase_Date']
formatted_df = filtered_df[display_cols].copy()
formatted_df.columns = ['Customer', 'Customer ID', 'Mobile Number', 'Type', 'Total Spent', 'Orders', 'AOV', 'Last Purchase']

# Formatting for table display
formatted_df['Total Spent'] = formatted_df['Total Spent'].apply(lambda x: format_currency(x))
formatted_df['AOV'] = formatted_df['AOV'].apply(lambda x: format_currency(x))

# Streamlit-compatible styling for the table (light text on dark background)
st.dataframe(formatted_df, width="stretch", hide_index=True)

st.divider()

st.markdown("### Customer Profile Details")
if not filtered_df.empty:
    selected_customer_id = st.selectbox("Select a customer to view details:", filtered_df['customer_id'].tolist())
    
    if selected_customer_id:
        prof = filtered_df[filtered_df['customer_id'] == selected_customer_id].iloc[0]
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.subheader(f"🏢 {prof.get('business_name', 'Unknown')}")
            st.caption(f"**Customer ID:** {prof.get('customer_id', 'N/A')} | **Name:** {prof.get('customer_name', 'N/A')}")
            st.markdown(f"**Mobile Number:** {prof.get('Mobile Number', 'Not Available')} | **Type:** {prof.get('customer_type', 'N/A')} | **Status:** {prof.get('status', 'N/A')}")
            st.markdown(f"**Total Spent:** {format_currency(prof.get('Total_Spent', 0))} | **Total Orders:** {prof.get('Total_Orders', 0)} | **Average Order Value:** {format_currency(prof.get('AOV', 0))}")
            st.markdown(f"**Last Purchase:** {prof.get('Last_Purchase_Date', 'N/A')} | **Most Purchased Product:** {prof.get('Most_Purchased_Product', 'N/A')}")
            
            # Use get to avoid KeyErrors if not in dataframe
            email = prof.get('email', 'N/A')
            st.markdown(f"**Email:** {email}")
        with c2:
            st.metric("Rating", f"{prof.get('customer_rating', 0):.1f} ★")
        with c3:
            st.metric("Total Spent", format_currency(prof.get('Total_Spent', 0)))

        st.divider()
        
        render_customer_qr_and_bills(str(prof.get('customer_id', '')))
else:
    st.info("No customers match the given filters.")
