import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from utils.formatting import format_currency
from utils.theme import apply_theme

st.set_page_config(page_title="BizMetrics - Inventory", layout="wide")
apply_theme()
render_sidebar()
render_header("Inventory Intelligence", "ML-powered demand forecasting and stock recommendations.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]
raw_data = st.session_state.get("raw_data", pd.DataFrame())
inv = result.get("inventory", {})

if not raw_data.empty:
    inv_df = raw_data[raw_data['Record_Type'].str.lower() == 'inventory'].copy()
    sales_df = raw_data[raw_data['Record_Type'].str.lower() == 'sale'].copy()
else:
    inv_df = pd.DataFrame()
    sales_df = pd.DataFrame()

if inv_df.empty:
    st.info("No inventory records found.")
    st.stop()

# Ensure numeric types
inv_df['Current_Stock'] = pd.to_numeric(inv_df.get('Current_Stock', 0), errors='coerce').fillna(0)
inv_df['Purchase_Price'] = pd.to_numeric(inv_df.get('Purchase_Price', 0).astype(str).str.replace('₹','').str.replace(',',''), errors='coerce').fillna(0)

total_skus = inv.get('total_skus', len(inv_df))
total_value = inv.get('total_value', (inv_df['Current_Stock'] * inv_df['Purchase_Price']).sum())
low_stock = inv.get('low_stock_items', 0)
fast_moving = inv.get('fast_moving', 0)
slow_moving = inv.get('slow_moving', 0)
dead_stock_value = inv.get('dead_stock_value', 0)
avg_turnover = inv.get('avg_turnover', 0)
avg_days = inv.get('avg_days_remaining', 0)

# ==========================================
# KPIs
# ==========================================
st.markdown("### Inventory Health")
c1, c2, c3, c4 = st.columns(4)
with c1: kpi_card("Total SKUs", str(total_skus))
with c2: kpi_card("Total Inventory Value", format_currency(total_value))
with c3: kpi_card("Low Stock Items", str(low_stock))
with c4: kpi_card("Dead Stock Value", format_currency(dead_stock_value))

st.markdown("<br>", unsafe_allow_html=True)
c5, c6, c7, c8 = st.columns(4)
with c5: kpi_card("Fast Moving SKUs", str(fast_moving))
with c6: kpi_card("Slow Moving SKUs", str(slow_moving))
with c7: kpi_card("Avg Inventory Turnover (30d)", f"{avg_turnover:.1f} units/SKU")
with c8: kpi_card("Est. Days of Stock", f"{avg_days:.1f} days")

st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)

# ==========================================
# CHARTS
# ==========================================
ml_recs = inv.get("ml_recommendations", [])
diagnostics = inv.get("ml_diagnostics", {})

# ML Diagnostics Debug Panel
if diagnostics:
    with st.expander("🛠️ ML Diagnostics (Debug Panel)"):
        st.write("This panel exposes internal ML variables for pipeline debugging.")
        d1, d2, d3 = st.columns(3)
        d1.metric("Inventory SKUs", diagnostics.get('unique_inv_skus', 0))
        d2.metric("Sales SKUs", diagnostics.get('unique_sales_skus', 0))
        d3.metric("Training Rows", diagnostics.get('training_rows', 0))
        
        st.markdown(f"**Date Range:** {diagnostics.get('date_range', 'Unknown')}")
        st.markdown(f"**Model Status:** {diagnostics.get('model_status', 'Unknown')}")
        
        if diagnostics.get('unmatched_sales_skus'):
            st.error(f"**Unmatched Sales SKUs:** {', '.join(diagnostics['unmatched_sales_skus'])}")
        else:
            st.success("All Sales SKUs successfully matched to Inventory.")
            
        if diagnostics.get('inv_skus_without_sales'):
            st.warning(f"**Inventory without Sales:** {', '.join(diagnostics['inv_skus_without_sales'])}")
            
        if diagnostics.get('fallback_skus'):
            st.info(f"**SKUs using Fallback (Moving Avg):** {', '.join(diagnostics['fallback_skus'])}")

st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)

if ml_recs:
    recs_df = pd.DataFrame(ml_recs)
    
    st.markdown("### ML Forecasts & Analytics")
    ch1, ch2 = st.columns(2)
    
    # Chart 1: Sales vs Current Stock
    with ch1:
        fig1 = px.scatter(recs_df, x='Current_Stock', y='Sales_30_Days', size='Predicted_Daily_Demand', color='Classification', hover_name='Product_Name', title='Sales vs Current Stock')
        fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937'), title_font=dict(color='#111827'), legend_title_font=dict(color='#1F2937'), paper_bgcolor='rgba(0,0,0,0)')
        fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E5E7EB', tickfont=dict(color='#374151'), title_font=dict(color='#1F2937'))
        fig1.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E5E7EB', tickfont=dict(color='#374151'), title_font=dict(color='#1F2937'))
        st.plotly_chart(fig1, use_container_width=True)

    # Chart 2: Top 10 Fast Moving Products
    with ch2:
        top_10 = recs_df.sort_values('Sales_30_Days', ascending=False).head(10)
        fig2 = px.bar(top_10, x='Sales_30_Days', y='Product_Name', orientation='h', title='Top 10 Fast Moving Products', color='Predicted_Daily_Demand', color_continuous_scale='Reds')
        fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937'), title_font=dict(color='#111827'), yaxis={'categoryorder':'total ascending'})
        fig2.update_xaxes(showgrid=True, gridcolor='#E5E7EB', tickfont=dict(color='#374151'))
        fig2.update_yaxes(tickfont=dict(color='#374151'))
        st.plotly_chart(fig2, use_container_width=True)

    ch3, ch4 = st.columns(2)
    # Chart 3: Predicted Demand by SKU
    with ch3:
        fig3 = px.bar(recs_df, x='Product_Name', y='Predicted_Daily_Demand', title='ML Predicted Daily Demand', color='Classification')
        fig3.update_layout(plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937'), title_font=dict(color='#111827'))
        fig3.update_yaxes(showgrid=True, gridcolor='#E5E7EB', tickfont=dict(color='#374151'))
        fig3.update_xaxes(tickfont=dict(color='#374151'), tickangle=45)
        st.plotly_chart(fig3, use_container_width=True)
        
    # Chart 4: Inventory Days Remaining
    with ch4:
        valid_days = recs_df[recs_df['Days_Remaining'] < 999].sort_values('Days_Remaining')
        fig4 = px.bar(valid_days, x='Product_Name', y='Days_Remaining', title='Estimated Days of Stock Remaining', color='Days_Remaining', color_continuous_scale='RdYlGn')
        fig4.update_layout(plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937'), title_font=dict(color='#111827'))
        fig4.update_yaxes(showgrid=True, gridcolor='#E5E7EB', tickfont=dict(color='#374151'))
        fig4.update_xaxes(tickfont=dict(color='#374151'), tickangle=45)
        st.plotly_chart(fig4, use_container_width=True)
        
    ch5, ch6 = st.columns(2)
    # Chart 5: Low Stock Risk
    with ch5:
        recs_df['Risk_Level'] = (recs_df['Reorder_Point'] - recs_df['Current_Stock']).clip(lower=0)
        risk_df = recs_df[recs_df['Risk_Level'] > 0].sort_values('Risk_Level', ascending=False)
        if not risk_df.empty:
            fig5 = px.bar(risk_df, x='Product_Name', y='Risk_Level', title='Low Stock Risk (Deficit from Reorder Point)', color_discrete_sequence=['#DC2626'])
            fig5.update_layout(plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937'), title_font=dict(color='#111827'))
            fig5.update_yaxes(showgrid=True, gridcolor='#E5E7EB', tickfont=dict(color='#374151'))
            fig5.update_xaxes(tickfont=dict(color='#374151'))
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No immediate stock risks.")
            
    # Chart 6: Historical vs ML Forecast
    with ch6:
        # Just plotting a summary comparison
        fig6 = go.Figure()
        fig6.add_trace(go.Bar(x=recs_df['Product_Name'], y=recs_df['Avg_Daily_Demand'], name='Historical (Last 30d)', marker_color='#94A3B8'))
        fig6.add_trace(go.Bar(x=recs_df['Product_Name'], y=recs_df['Predicted_Daily_Demand'], name='ML Forecast (Next 7d)', marker_color='#C65D47'))
        fig6.update_layout(title='Historical vs ML Forecast', barmode='group', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937'), title_font=dict(color='#111827'))
        fig6.update_yaxes(showgrid=True, gridcolor='#E5E7EB', tickfont=dict(color='#374151'))
        fig6.update_xaxes(tickfont=dict(color='#374151'), tickangle=45)
        st.plotly_chart(fig6, use_container_width=True)

st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)

# ==========================================
# AI INVENTORY GUIDE
# ==========================================
st.markdown("### AI Inventory Guide")

if ml_recs:
    for rec in ml_recs:
        status_color = "#10B981" if rec['Status'] == "HEALTHY" else "#F59E0B" if rec['Status'] == "LOW STOCK" else "#EF4444"
        bg_color = "#ECFDF5" if rec['Status'] == "HEALTHY" else "#FEF3C7" if rec['Status'] == "LOW STOCK" else "#FEF2F2"
        border_color = status_color
        
        st.markdown(f"""
        <div style='background-color: {bg_color}; padding: 1.5rem; border-radius: 8px; border-left: 5px solid {border_color}; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
            <h4 style='margin-top: 0; color: #111827; font-weight: 700; font-size: 1.1rem; text-transform: uppercase;'>{rec['Product_Name']}</h4>
            <div style='display: flex; flex-wrap: wrap; gap: 1.5rem; margin-bottom: 1rem; color: #374151; font-size: 0.95rem;'>
                <div><strong>Current Stock:</strong> {rec['Current_Stock']} pcs</div>
                <div><strong>30-Day Sales:</strong> {rec['Sales_30_Days']} pcs</div>
                <div><strong>Avg Daily Demand:</strong> {rec['Avg_Daily_Demand']} /day</div>
                <div><strong>Predicted Demand:</strong> <span style='color: #059669; font-weight: bold;'>{rec['Predicted_Daily_Demand']} /day</span></div>
                <div><strong>Days Remaining:</strong> {rec['Days_Remaining']} days</div>
                <div><strong>Reorder Point:</strong> {rec['Reorder_Point']} pcs</div>
                <div><strong>Recommended Order:</strong> <span style='color: #4F46E5; font-weight: bold;'>{rec['Recommended_Order']} pcs</span></div>
            </div>
            <div style='margin-bottom: 0.5rem;'>
                <span style='background-color: {status_color}; color: white; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.8rem; font-weight: bold; letter-spacing: 0.05em;'>
                    {rec['Status']}
                </span>
                <span style='margin-left: 0.5rem; background-color: #4B5563; color: white; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.8rem; font-weight: bold; letter-spacing: 0.05em;'>
                    {rec['Classification']}
                </span>
            </div>
            <div style='color: #1F2937; font-size: 1rem; margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid rgba(0,0,0,0.05);'>
                <strong>Recommendation:</strong> {rec['Recommendation']}
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("ML recommendations not available. Please ensure sales data is present.")
