import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card, insight_card
from components.charts import create_line_chart, create_bar_chart, create_donut_chart
from utils.formatting import format_currency
from utils.theme import apply_theme, get_colors

st.set_page_config(page_title="BizMetrics - Financial", layout="wide")
apply_theme()
render_sidebar()
render_header("Financial Performance", "Revenue, profitability, expenses and reconciliation")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]
raw_data = st.session_state.get("raw_data", pd.DataFrame())
f = result.get("financial", {})
r = result.get("receivables", {})
colors = get_colors()

# KPI Cards
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: kpi_card("Total Revenue", format_currency(f.get('total_revenue', 0)))
with c2: kpi_card("COGS", format_currency(f.get('cogs', 0)))
with c3: kpi_card("Gross Profit", format_currency(f.get('gross_profit', 0)))
with c4: kpi_card("Operating Expenses", format_currency(f.get('total_expenses', 0)))
with c5: kpi_card("Net Profit", format_currency(f.get('net_profit', 0)))
with c6: kpi_card("Net Margin", f"{f.get('profit_margin', 0):.2f}%")

st.markdown("<br>", unsafe_allow_html=True)

col_stmt, col_debug = st.columns([1, 1])

with col_stmt:
    st.markdown("### Income Statement")
    st.markdown(f"""
    <div style='background: {colors.get('background', '#FAF9F6')}; padding: 20px; border-radius: 8px; border: 1px solid #E5E7EB;'>
        <div style='display:flex; justify-content:space-between; margin-bottom:8px;'><span>Revenue</span> <span>{format_currency(f.get('total_revenue', 0))}</span></div>
        <div style='display:flex; justify-content:space-between; margin-bottom:8px;'><span>- Cost of Goods Sold</span> <span>{format_currency(f.get('cogs', 0))}</span></div>
        <hr style='margin: 8px 0; border: none; border-top: 1px solid #D1D5DB;'>
        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-weight:bold;'><span>Gross Profit</span> <span>{format_currency(f.get('gross_profit', 0))}</span></div>
        <br>
        <div style='display:flex; justify-content:space-between; margin-bottom:8px;'><span>- Operating Expenses</span> <span>{format_currency(f.get('total_expenses', 0))}</span></div>
        <hr style='margin: 8px 0; border: none; border-top: 1px solid #D1D5DB;'>
        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-weight:bold;'><span>Operating Profit</span> <span>{format_currency(f.get('operating_profit', 0))}</span></div>
        <br>
        <div style='display:flex; justify-content:space-between; margin-bottom:8px;'><span>- Interest Expense</span> <span>{format_currency(f.get('interest_expense', 0))}</span></div>
        <hr style='margin: 8px 0; border: none; border-top: 1px solid #D1D5DB;'>
        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-weight:bold;'><span>Profit Before Tax</span> <span>{format_currency(f.get('profit_before_tax', 0))}</span></div>
        <br>
        <div style='display:flex; justify-content:space-between; margin-bottom:8px;'><span>- Estimated Tax</span> <span>{format_currency(f.get('taxes', 0))}</span></div>
        <hr style='margin: 8px 0; border: none; border-top: 2px solid #111827;'>
        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-weight:bold; font-size:1.1em;'><span>Net Profit</span> <span>{format_currency(f.get('net_profit', 0))}</span></div>
    </div>
    """, unsafe_allow_html=True)

with col_debug:
    # Calculations
    exp_gp = f.get('total_revenue', 0) - f.get('cogs', 0)
    exp_op = f.get('gross_profit', 0) - f.get('total_expenses', 0)
    exp_pbt = f.get('operating_profit', 0) - f.get('interest_expense', 0)
    exp_np = f.get('profit_before_tax', 0) - f.get('taxes', 0)
    
    diff_gp = abs(exp_gp - f.get('gross_profit', 0))
    diff_op = abs(exp_op - f.get('operating_profit', 0))
    diff_pbt = abs(exp_pbt - f.get('profit_before_tax', 0))
    diff_np = abs(exp_np - f.get('net_profit', 0))
    
    is_reconciled = (diff_gp < 0.01) and (diff_op < 0.01) and (diff_pbt < 0.01) and (diff_np < 0.01)
    
    with st.expander("Financial Reconciliation", expanded=True):
        if is_reconciled:
            st.success("✓ Financials Reconciled")
        else:
            st.error("⚠ Financial Reconciliation Error")
            
        st.markdown(f"""
| Check | Expected | Actual | Difference | Status |
|---|---|---|---|---|
| Gross Profit | {format_currency(exp_gp)} | {format_currency(f.get('gross_profit', 0))} | {format_currency(diff_gp)} | {'✓' if diff_gp < 0.01 else '⚠'} |
| Operating Profit | {format_currency(exp_op)} | {format_currency(f.get('operating_profit', 0))} | {format_currency(diff_op)} | {'✓' if diff_op < 0.01 else '⚠'} |
| Profit Before Tax | {format_currency(exp_pbt)} | {format_currency(f.get('profit_before_tax', 0))} | {format_currency(diff_pbt)} | {'✓' if diff_pbt < 0.01 else '⚠'} |
| Net Profit | {format_currency(exp_np)} | {format_currency(f.get('net_profit', 0))} | {format_currency(diff_np)} | {'✓' if diff_np < 0.01 else '⚠'} |
        """)

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)

if not raw_data.empty:
    sales_df = raw_data[raw_data['Record_Type'].str.lower() == 'sale'].copy()
    exp_df = raw_data[raw_data['Record_Type'].str.lower() == 'expense'].copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Revenue Trend")
        if 'Date' in sales_df.columns and 'Total_Amount' in sales_df.columns:
            sales_df['Date'] = pd.to_datetime(sales_df['Date'], errors='coerce')
            sales_trend = sales_df.groupby('Date')['Total_Amount'].sum().reset_index()
            fig = create_line_chart(sales_trend, 'Date', 'Total_Amount', "", colors.get('terracotta', '#C65D47'))
            st.plotly_chart(fig, use_container_width=True)
        elif 'Date' in sales_df.columns and 'Amount' in sales_df.columns:
            sales_df['Date'] = pd.to_datetime(sales_df['Date'], errors='coerce')
            sales_trend = sales_df.groupby('Date')['Amount'].sum().reset_index()
            fig = create_line_chart(sales_trend, 'Date', 'Amount', "", colors.get('terracotta', '#C65D47'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Time-series data for Revenue not available.")
            
    with col2:
        st.markdown("### Expense Breakdown")
        if 'Category' in exp_df.columns and 'Amount' in exp_df.columns:
            exp_breakdown = exp_df.groupby('Category')['Amount'].sum().reset_index()
            fig = create_donut_chart(exp_breakdown, 'Category', 'Amount', "")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Category breakdown for Expenses not available.")
            
    st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)
    st.markdown("### Financial Health Summary")
    ic1, ic2, ic3, ic4 = st.columns(4)
    with ic1: insight_card("Revenue Health", "Tracking steady." if f.get('total_revenue', 0) > 0 else "Needs attention.")
    with ic2: insight_card("Expense Health", "Managed." if f.get('total_expenses', 0) < f.get('total_revenue', 0) else "Expenses exceed revenue.")
    with ic3: insight_card("Profitability", f"{f.get('profit_margin', 0):.1f}% margin.")
    with ic4: insight_card("Liquidity", "Monitor outstanding receivables." if r.get('total_outstanding', 0) > 0 else "Cash flow is healthy.")
else:
    st.info("Raw data not available for detailed charting.")
