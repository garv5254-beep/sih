import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from components.charts import create_bar_chart, create_donut_chart
from utils.formatting import format_currency
from utils.theme import apply_theme, get_colors

st.set_page_config(page_title="BizMetrics - Customers", layout="wide")

# Fix Customer CRM text visibility (Scoped CSS)
st.markdown("""
<style>
    /* 1. CUSTOMER DATABASE / TABLE */
    [data-testid="stDataFrame"] span,
    [data-testid="stDataFrame"] div,
    [data-testid="stDataFrame"] {
        color: #FFFFFF !important;
    }
    
    /* 2 & 3. SEARCH & FILTER INPUTS */
    [data-testid="stTextInput"] input {
        color: #FFFFFF !important;
        background-color: #1F2937 !important;
        border-color: #374151 !important;
    }
    [data-testid="stTextInput"] input::placeholder {
        color: #9CA3AF !important;
    }
    [data-baseweb="select"] > div {
        background-color: #1F2937 !important;
        border-color: #374151 !important;
    }
    [data-baseweb="select"] span,
    [data-baseweb="select"] div {
        color: #FFFFFF !important;
    }
    
    /* 4. DROPDOWN MENUS */
    [data-baseweb="popover"] [data-baseweb="menu"] {
        background-color: #1F2937 !important;
    }
    [data-baseweb="menu"] span,
    [data-baseweb="menu"] li {
        color: #FFFFFF !important;
    }
    [data-baseweb="menu"] li:hover,
    [data-baseweb="menu"] li[aria-selected="true"] {
        background-color: #374151 !important;
    }
</style>
""", unsafe_allow_html=True)

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

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)

if not customers_list:
    st.info("No customer records found.")
    st.stop()

df_cust = pd.DataFrame(customers_list)

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
        fig2 = create_bar_chart(top_custs, 'Total_Spent', 'Business_Name', "", colors.get('primary', '#C65D47'), orientation='h')
        st.plotly_chart(fig2, width="stretch")
    else:
        st.info("No spending data available.")

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)

st.markdown("### CRM Database")

# Filters
f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    search_term = st.text_input("Search Customer/Business Name", "")
with f_col2:
    status_filter = st.selectbox("Status", ["All"] + sorted(list(df_cust['Status'].unique())))
with f_col3:
    type_filter = st.selectbox("Type", ["All"] + sorted(list(df_cust['Customer_Type'].unique())))

filtered_df = df_cust.copy()
if search_term:
    filtered_df = filtered_df[
        filtered_df['Customer_Name'].str.contains(search_term, case=False, na=False) |
        filtered_df['Business_Name'].str.contains(search_term, case=False, na=False)
    ]
if status_filter != "All":
    filtered_df = filtered_df[filtered_df['Status'] == status_filter]
if type_filter != "All":
    filtered_df = filtered_df[filtered_df['Customer_Type'] == type_filter]

# Display columns
display_cols = ['Customer_ID', 'Business_Name', 'City', 'Status', 'Segment', 'Total_Orders', 'Total_Spent', 'AOV', 'Last_Purchase_Date', 'Customer_Rating']
formatted_df = filtered_df[display_cols].copy()

# Formatting for table display
formatted_df['Total_Spent'] = formatted_df['Total_Spent'].apply(lambda x: format_currency(x))
formatted_df['AOV'] = formatted_df['AOV'].apply(lambda x: format_currency(x))
formatted_df['Customer_Rating'] = formatted_df['Customer_Rating'].apply(lambda x: f"{x:.1f} ★" if x > 0 else "N/A")

# Streamlit-compatible styling for the table (light text on dark background)
styled_df = formatted_df.style.set_properties(**{
    'background-color': '#1F2937',
    'color': '#F9FAFB',
    'border-color': '#374151'
})

st.dataframe(styled_df, width="stretch", hide_index=True)

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)

st.markdown("### Customer Profile Details")
if not filtered_df.empty:
    selected_customer_name = st.selectbox("Select a customer to view details:", filtered_df['Business_Name'].tolist())
    
    if selected_customer_name:
        prof = filtered_df[filtered_df['Business_Name'] == selected_customer_name].iloc[0]
        
        st.subheader(prof['Business_Name'])
        st.caption(f"{prof['City']} • {prof['Status']} • {prof['Customer_Type']}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Purchase History")
        
        if not raw_data.empty:
            sales_raw = raw_data[raw_data['Record_Type'] == 'Sale']
            cust_sales = sales_raw[sales_raw['Customer_ID'] == prof['Customer_ID']].copy()
            
            if not cust_sales.empty:
                hist_cols = ['Date', 'Product_ID', 'Quantity', 'Selling_Price', 'Discount_Percent', 'Total_Amount']
                available_cols = [col for col in hist_cols if col in cust_sales.columns]
                # Streamlit-compatible styling for the table
                styled_hist = cust_sales[available_cols].sort_values('Date', ascending=False).style.set_properties(**{
                    'background-color': '#1F2937',
                    'color': '#F9FAFB',
                    'border-color': '#374151'
                })
                st.dataframe(styled_hist, width="stretch", hide_index=True)
            else:
                st.info("No transaction records found for this customer.")
else:
    st.info("No customers match the given filters.")
