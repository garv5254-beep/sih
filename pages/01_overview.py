import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card, insight_card
from components.charts import create_line_chart, create_donut_chart, get_base_layout
from utils.formatting import format_currency, t
from utils.theme import apply_theme, get_colors

st.set_page_config(page_title="BizMetrics - Overview", layout="wide")
apply_theme()
render_sidebar()
render_header("Good morning 👋", "Business Overview - Understand your business performance at a glance.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]
raw_data = st.session_state["raw_data"]
f = result.get("financial", {})
r = result.get("receivables", {})
inv = result.get("inventory", {})
risks = result.get("risks", [])
business = result.get("business", {})
colors = get_colors()

# Top KPI Cards
c1, c2, c3, c4, c5 = st.columns(5)
with c1: kpi_card("Revenue", format_currency(f.get('total_revenue', 0)), "Total recorded sales")
with c2: kpi_card("Expenses", format_currency(f.get('total_expenses', 0)), "Total recorded expenses")
with c3: kpi_card("Net Profit", format_currency(f.get('net_profit', 0)), "Overall margin")
with c4: kpi_card("Outstanding Receivables", format_currency(r.get('total_outstanding', 0)), "Pending payments")
with c5: kpi_card("Inventory Value", format_currency(inv.get('total_value', 0) if inv.get('total_value') else inv.get('dead_stock_value', 0)), "Current stock")

st.markdown("<br>", unsafe_allow_html=True)

# Main Charts Area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Revenue & Profit Trend")
    # Generate trend from raw data if Sale/Expense dates exist, else fallback
    # For now, let's create a clean bar/line chart grouping by Date if possible.
    try:
        sales = raw_data[raw_data['Record_Type'].str.lower() == 'sale'].copy()
        if not sales.empty and 'Date' in sales.columns:
            sales['Date'] = pd.to_datetime(sales['Date'], errors='coerce')
            monthly_sales = sales.groupby(sales['Date'].dt.to_period('M'))['Amount'].sum().reset_index()
            monthly_sales['Date'] = monthly_sales['Date'].astype(str)
            fig = create_line_chart(monthly_sales, 'Date', 'Amount', '', color=colors['terracotta'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Trend data currently unavailable based on dataset dates.")
    except Exception:
        st.info("Trend data currently unavailable.")

with col2:
    st.markdown("### Business Health")
    score = result.get("health_score", 70)
    health_color = colors['olive'] if score >= 70 else colors['terracotta'] if score > 40 else colors['deep_rust']
    
    st.markdown(
        f"""
        <div class="ep-card" style="text-align: center;">
            <h1 style="font-size: 5rem; color: {health_color}; margin: 0;">{score}</h1>
            <p style="color: #4B5563; font-size: 1.2rem; font-weight: 500;">Healthy</p>
        </div>
        """, unsafe_allow_html=True
    )
    st.markdown("<p style='font-size: 0.9rem; color: #4B5563;'>Factors analyzed:</p>", unsafe_allow_html=True)
    st.markdown(f"• Financial Health<br>• Sales Performance<br>• Inventory Health<br>• Receivables<br>• Debt", unsafe_allow_html=True)

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)

# Business Snapshot
st.markdown("### Business Snapshot")
b_c1, b_c2, b_c3, b_c4, b_c5 = st.columns(5)
b_c1.markdown(f"**Business Name**<br>{business.get('Shop_Name', 'Not available')}", unsafe_allow_html=True)
b_c2.markdown(f"**Location**<br>{business.get('Village_City', 'Not available')}", unsafe_allow_html=True)
b_c3.markdown(f"**Sector**<br>{business.get('Business_Type', 'Not available')}", unsafe_allow_html=True)
b_c4.markdown(f"**Employees**<br>{business.get('Employees', 'Not available')}", unsafe_allow_html=True)
b_c5.markdown(f"**Started**<br>{business.get('Years_in_Operation', 'Not available')} years ago", unsafe_allow_html=True)

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)

# Quick Insights
st.markdown("### Quick Insights")
i_c1, i_c2, i_c3 = st.columns(3)
with i_c1:
    if risks:
        insight_card("Risk Alert", risks[0].get('risk', 'Attention required.'))
    else:
        insight_card("All Clear", "No critical risks detected.")
        
with i_c2:
    if inv.get('reorder_items'):
        insight_card("Inventory Alert", f"{len(inv['reorder_items'])} items are below reorder level.")
    else:
        insight_card("Inventory Status", "Stock levels are healthy.")
        
with i_c3:
    if r.get('total_outstanding', 0) > 0:
        insight_card("Receivables", f"₹{r.get('total_outstanding', 0)} remains outstanding.")
    else:
        insight_card("Receivables", "No pending collections.")

