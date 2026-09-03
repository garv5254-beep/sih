import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from components.charts import create_line_chart, get_base_layout
from utils.formatting import format_currency
from utils.theme import apply_theme, get_colors

st.set_page_config(page_title="BizMetrics - Inventory & Forecasting", layout="wide")
apply_theme()
render_sidebar()
render_header("Inventory & Forecasting", "ML-powered demand forecasting and stock recommendations.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]
raw_data = st.session_state.get("raw_data", pd.DataFrame())
inv = result.get("inventory", {})
fc = result.get("forecast", {})
colors = get_colors()

if not raw_data.empty:
    inv_df = raw_data[raw_data['record_type'].str.lower() == 'inventory'].copy()
    sales_df = raw_data[raw_data['record_type'].str.lower() == 'sale'].copy()
else:
    inv_df = pd.DataFrame()
    sales_df = pd.DataFrame()

if inv_df.empty:
    st.info("No inventory records found.")
    st.stop()

# Ensure numeric types
inv_df['current_stock'] = pd.to_numeric(inv_df.get('current_stock', 0), errors='coerce').fillna(0)
inv_df['purchase_price'] = pd.to_numeric(inv_df.get('purchase_price', 0).astype(str).str.replace('₹','').str.replace(',',''), errors='coerce').fillna(0)

total_skus = inv.get('total_skus', len(inv_df))
total_value = inv.get('total_value', (inv_df['current_stock'] * inv_df['purchase_price']).sum())
low_stock = inv.get('low_stock_items', 0)
fast_moving = inv.get('fast_moving', 0)
slow_moving = inv.get('slow_moving', 0)
dead_stock_value = inv.get('dead_stock_value', 0)
avg_turnover = inv.get('avg_turnover', 0)
avg_days = inv.get('avg_days_remaining', 0)
ml_recs = inv.get("ml_recommendations", [])

# ==========================================
# 1. Inventory Overview
# ==========================================
st.markdown("### Inventory Overview")
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
# 2. Demand Forecast
# ==========================================
st.markdown("### Demand Forecast")

fc1, fc2, fc3 = st.columns(3)
with fc1: kpi_card("Projected Sales (Next Month)", format_currency(fc.get('next_month_projected_sales', 0)))
with fc2: kpi_card("Upcoming Festivals", ", ".join(fc.get('upcoming_festivals', [])))
with fc3: kpi_card("Recommended Stock Increase", fc.get('recommended_stock_increase', 'N/A'))

if not sales_df.empty and 'date' in sales_df.columns and 'total_amount' in sales_df.columns:
    sales_df['date'] = pd.to_datetime(sales_df['date'], errors='coerce')
    sales_trend = sales_df.groupby('date')['total_amount'].sum().reset_index()
    if not sales_trend.empty:
        last_date = sales_trend['date'].max()
        forecast_dates = [last_date + pd.Timedelta(days=30), last_date + pd.Timedelta(days=60)]
        last_val = sales_trend['total_amount'].iloc[-1]
        forecast_vals = [last_val * 1.10, last_val * 1.21]
        
        hist_df = sales_trend.copy()
        hist_df['Type'] = 'Historical'
        fc_df = pd.DataFrame({'date': forecast_dates, 'total_amount': forecast_vals, 'Type': 'Forecast'})
        combined = pd.concat([hist_df, fc_df])
        
        fig_trend = px.line(combined, x='date', y='total_amount', color='Type', line_dash='Type', color_discrete_map={'Historical': colors['olive'], 'Forecast': colors['terracotta']}, title='Historical vs Forecast Revenue')
        fig_trend.update_layout(**get_base_layout())
        st.plotly_chart(fig_trend, width="stretch")
st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)

# ==========================================
# 3. Reorder Recommendations
# ==========================================
st.markdown("### Reorder Recommendations")
if ml_recs:
    recs_df = pd.DataFrame(ml_recs)
    
    # Display table of recommendations
    display_cols = ['product_name', 'current_stock', 'Avg_Daily_Demand', 'Predicted_Daily_Demand', 'Reorder_Point', 'Recommended_Order', 'status', 'Classification']
    st.dataframe(recs_df[display_cols].style.background_gradient(subset=['Recommended_Order'], cmap='Blues'))

st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)

# ==========================================
# 4. ML Forecasting
# ==========================================
st.markdown("### ML Forecasting")
if ml_recs:
    ch1, ch2 = st.columns(2)
    with ch1:
        fig1 = px.scatter(recs_df, x='current_stock', y='Sales_30_Days', size='Predicted_Daily_Demand', color='Classification', hover_name='product_name', title='Sales vs Current Stock')
        fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937'), title_font=dict(color='#111827'))
        st.plotly_chart(fig1, width="stretch")
    with ch2:
        top_10 = recs_df.sort_values('Sales_30_Days', ascending=False).head(10)
        fig2 = px.bar(top_10, x='Sales_30_Days', y='product_name', orientation='h', title='Top 10 Fast Moving Products', color='Predicted_Daily_Demand', color_continuous_scale='Reds')
        fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937'), title_font=dict(color='#111827'), yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig2, width="stretch")

    ch3, ch4 = st.columns(2)
    with ch3:
        fig3 = px.bar(recs_df, x='product_name', y='Predicted_Daily_Demand', title='ML Predicted Daily Demand', color='Classification')
        fig3.update_layout(plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937'), title_font=dict(color='#111827'))
        st.plotly_chart(fig3, width="stretch")
    with ch4:
        fig6 = go.Figure()
        fig6.add_trace(go.Bar(x=recs_df['product_name'], y=recs_df['Avg_Daily_Demand'], name='Historical (Last 30d)', marker_color='#94A3B8'))
        fig6.add_trace(go.Bar(x=recs_df['product_name'], y=recs_df['Predicted_Daily_Demand'], name='ML Forecast (Next 7d)', marker_color='#C65D47'))
        fig6.update_layout(title='Historical vs ML Forecast', barmode='group', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937'), title_font=dict(color='#111827'))
        st.plotly_chart(fig6, width="stretch")

st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)

# ==========================================
# 5. AI Inventory Guide
# ==========================================
st.markdown("### AI Inventory Guide")
if ml_recs:
    for rec in ml_recs:
        status_color = "#10B981" if rec['status'] == "HEALTHY" else "#F59E0B" if rec['status'] == "LOW STOCK" else "#EF4444"
        bg_color = "#ECFDF5" if rec['status'] == "HEALTHY" else "#FEF3C7" if rec['status'] == "LOW STOCK" else "#FEF2F2"
        border_color = status_color
        
        st.markdown(f"""
        <div style='background-color: {bg_color}; padding: 1.5rem; border-radius: 8px; border-left: 5px solid {border_color}; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
            <h4 style='margin-top: 0; color: #111827; font-weight: 700; font-size: 1.1rem; text-transform: uppercase;'>{rec['product_name']}</h4>
            <div style='display: flex; flex-wrap: wrap; gap: 1.5rem; margin-bottom: 1rem; color: #374151; font-size: 0.95rem;'>
                <div><strong>Current Stock:</strong> {rec['current_stock']} pcs</div>
                <div><strong>Predicted Demand:</strong> <span style='color: #059669; font-weight: bold;'>{rec['Predicted_Daily_Demand']} /day</span></div>
                <div><strong>Days Remaining:</strong> {rec['Days_Remaining']} days</div>
                <div><strong>Recommended Order:</strong> <span style='color: #4F46E5; font-weight: bold;'>{rec['Recommended_Order']} pcs</span></div>
            </div>
            <div style='margin-bottom: 0.5rem;'>
                <span style='background-color: {status_color}; color: white; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.8rem; font-weight: bold; letter-spacing: 0.05em;'>
                    {rec['status']}
                </span>
            </div>
            <div style='color: #1F2937; font-size: 1rem; margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid rgba(0,0,0,0.05);'>
                <strong>Recommendation:</strong> {rec['Recommendation']}
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("ML recommendations not available. Please ensure sales data is present.")
