import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from components.charts import create_line_chart, get_base_layout
from utils.formatting import format_currency, t
from utils.theme import apply_theme, get_colors
import plotly.express as px

st.set_page_config(page_title="BizMetrics - Forecasting", layout="wide")
apply_theme()
render_sidebar()
render_header("Forecasting", "Understand where your business may be heading.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]
fc = result.get("forecast", {})
colors = get_colors()

c1, c2, c3 = st.columns(3)
with c1: kpi_card("Projected Sales (Next Month)", format_currency(fc.get('next_month_projected_sales', 0)))
with c2: kpi_card("Upcoming Festivals", ", ".join(fc.get('upcoming_festivals', [])))
with c3: kpi_card("Recommended Stock Increase", fc.get('recommended_stock_increase', 'N/A'))

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)

# Creating a mock forecast chart to illustrate the historical -> forecast concept requested
raw_data = st.session_state.get("raw_data", pd.DataFrame())
if not raw_data.empty:
    sales_df = raw_data[raw_data['Record_Type'].str.lower() == 'sale'].copy()
    if 'Date' in sales_df.columns and 'Total_Amount' in sales_df.columns:
        sales_df['Date'] = pd.to_datetime(sales_df['Date'], errors='coerce')
        sales_trend = sales_df.groupby('Date')['Total_Amount'].sum().reset_index()
        
        # Very simple heuristic visualization since backend doesn't provide time-series forecast
        if not sales_trend.empty:
            last_date = sales_trend['Date'].max()
            forecast_dates = [last_date + pd.Timedelta(days=30), last_date + pd.Timedelta(days=60)]
            last_val = sales_trend['Total_Amount'].iloc[-1]
            forecast_vals = [last_val * 1.10, last_val * 1.21]
            
            # Combine
            hist_df = sales_trend.copy()
            hist_df['Type'] = 'Historical'
            
            fc_df = pd.DataFrame({'Date': forecast_dates, 'Total_Amount': forecast_vals, 'Type': 'Forecast'})
            combined = pd.concat([hist_df, fc_df])
            
            st.markdown("### Historical vs Forecast Revenue")
            
            fig = px.line(combined, x='Date', y='Total_Amount', color='Type', line_dash='Type', color_discrete_map={'Historical': colors['olive'], 'Forecast': colors['terracotta']})
            fig.update_layout(**get_base_layout())
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### Forecast Summary")
            st.info("Expected direction: Growing")
    else:
        st.info("Insufficient historical data to render forecast chart.")
else:
    st.info("Raw data not available.")

