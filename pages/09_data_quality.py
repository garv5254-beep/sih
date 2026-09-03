import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from utils.theme import apply_theme, get_colors

st.set_page_config(page_title="BizMetrics - Data Quality", layout="wide")
apply_theme()
render_sidebar()
render_header("Data Quality Monitor", "Analyze and improve dataset health")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.stop()

result = st.session_state["pipeline_result"]
dq_data = result.get("data_quality", {})
colors = get_colors()

# KPI Cards
c1, c2, c3, c4, c5, c6 = st.columns(6)

score = dq_data.get('score', 0)
score_color = colors.get('olive', '#6B705C')
if score < 80:
    score_color = colors.get('terracotta', '#C65D47')
if score < 50:
    score_color = colors.get('deep_rust', '#9D4330')

with c1: 
    st.markdown(f"""
    <div style="background: {colors.get('background', '#FAF9F6')}; padding: 15px; border-radius: 8px; border: 1px solid #E5E7EB; text-align: center;">
        <h4 style="margin: 0; color: #4B5563; font-size: 0.9rem;">Quality Score</h4>
        <h2 style="margin: 0; color: {score_color}; font-size: 2rem;">{score:.0f}/100</h2>
    </div>
    """, unsafe_allow_html=True)
    
with c2: kpi_card("Total Records", f"{dq_data.get('total_records', 0):,}")
with c3: kpi_card("Missing Values", f"{dq_data.get('missing_values', 0):,}")
with c4: kpi_card("Duplicate Rows", f"{dq_data.get('duplicate_records', 0):,}")
with c5: kpi_card("Invalid Values", f"{dq_data.get('invalid_values', 0):,}")
with c6: kpi_card("Columns", f"{dq_data.get('columns_analyzed', 0):,}")

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Column Analysis")
    cols_data = dq_data.get("columns", [])
    if cols_data:
        df = pd.DataFrame(cols_data)
        
        def highlight_quality(val):
            color = ''
            if val == 'Good': color = f"background-color: {colors.get('olive', '#6B705C')}; color: white;"
            elif val == 'Warning': color = f"background-color: {colors.get('terracotta', '#C65D47')}; color: white;"
            elif val == 'Critical': color = f"background-color: {colors.get('deep_rust', '#9D4330')}; color: white;"
            return color

        # Sort to put critical/warning at the top
        df['sort_key'] = df['Quality'].map({'Critical': 0, 'Warning': 1, 'Good': 2})
        df = df.sort_values('sort_key').drop('sort_key', axis=1)
        
        st.dataframe(df.style.map(highlight_quality, subset=['Quality']).format({'Missing_Pct': '{:.1f}%'}), use_container_width=True)
    else:
        st.info("No column data available.")

with col2:
    st.markdown("### Actionable Recommendations")
    recommendations = dq_data.get("recommendations", [])
    if recommendations:
        for rec in recommendations:
            st.markdown(f"""
            <div style="background: {colors.get('background', '#FAF9F6')}; padding: 10px; border-radius: 8px; border-left: 4px solid {colors.get('terracotta', '#C65D47')}; margin-bottom: 10px; border-top: 1px solid #E5E7EB; border-right: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB;">
                <p style="margin: 0; color: #1F2937;">{rec}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No critical data quality issues found! Dataset is healthy.")
