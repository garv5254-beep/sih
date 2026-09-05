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

# Extract Data
score = dq_data.get('score', 0)
total_records = dq_data.get('total_records', 0)
missing_values = dq_data.get('missing_values', 0)
duplicate_records = dq_data.get('duplicate_records', 0)
invalid_values = dq_data.get('invalid_values', 0)
cols_analyzed = dq_data.get('columns_analyzed', 0)

# Determine Score Status
score_status = "Critical"
if score >= 90:
    score_status = "Excellent"
elif score >= 75:
    score_status = "Good"
elif score >= 60:
    score_status = "Needs Attention"
elif score >= 40:
    score_status = "Poor"

# KPI Cards
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: kpi_card("Quality Score", f"{score:.0f}/100", score_status)
with c2: kpi_card("Total Records", f"{total_records:,}")
with c3: kpi_card("Missing Values", f"{missing_values:,}")
with c4: kpi_card("Duplicate Rows", f"{duplicate_records:,}")
with c5: kpi_card("Invalid Values", f"{invalid_values:,}")
with c6: kpi_card("Columns", f"{cols_analyzed:,}")

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Column Analysis")
    cols_data = dq_data.get("columns", [])
    if cols_data:
        df = pd.DataFrame(cols_data)
        
        def highlight_quality(val):
            color = ''
            if val == 'Good': color = f"background-color: {colors.get('olive', '#78805B')}; color: white;"
            elif val == 'Warning': color = f"background-color: {colors.get('terracotta', '#9B493C')}; color: white;"
            elif val == 'Critical': color = f"background-color: {colors.get('deep_rust', '#78372F')}; color: white;"
            return color

        # Sort to put critical/warning at the top
        df['sort_key'] = df['Quality'].map({'Critical': 0, 'Warning': 1, 'Good': 2})
        df = df.sort_values('sort_key').drop('sort_key', axis=1)
        
        st.dataframe(
            df.style.map(highlight_quality, subset=['Quality']).format({'Missing_Pct': '{:.1f}%'}),
            width="stretch",
            hide_index=True
        )
    else:
        st.info("No column data available.")

with col2:
    st.markdown("### Actionable Recommendations")
    recommendations = dq_data.get("recommendations", [])
    if recommendations:
        for rec in recommendations:
            if "strong" in rec.lower():
                st.success(rec)
            elif "missing" in rec.lower() or "duplicate" in rec.lower() or "invalid" in rec.lower():
                st.warning(rec)
            else:
                st.info(rec)
    else:
        st.success("No critical data quality issues found! Dataset is healthy.")
