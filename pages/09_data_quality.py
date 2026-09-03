import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from utils.theme import apply_theme

st.set_page_config(page_title="BizMetrics - Data Quality", layout="wide")
apply_theme()
render_sidebar()
render_header("Data Quality", "Review the quality of your connected dataset.")

if "raw_data" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

df = st.session_state["raw_data"]
dataset_path = st.session_state.get("dataset_path", "rural_business_master_data.csv")

st.markdown("### Dataset Status")
st.markdown("""
<div style='background-color: #F4F1DE; color: #9D4330; padding: 0.5rem; border-radius: 4px; font-weight: 600; margin-bottom: 1rem; border-left: 4px solid #C65D47;'>
    Demo Business Dataset / Prototype Data
</div>
""", unsafe_allow_html=True)
st.success("✓ Connected")
st.markdown(f"**Dataset:** `{dataset_path}`")

rows = len(df)
cols = len(df.columns)
missing = df.isnull().sum().sum()
dupes = df.duplicated().sum()

c1, c2, c3, c4 = st.columns(4)
with c1: kpi_card("Rows Loaded", str(rows))
with c2: kpi_card("Columns Detected", str(cols))
with c3: kpi_card("Missing Values", str(missing))
with c4: kpi_card("Duplicate Records", str(dupes))

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)
st.markdown("### Record Type Distribution")
record_counts = df['Record_Type'].value_counts() if 'Record_Type' in df.columns else pd.Series()
rc_cols = st.columns(len(record_counts)) if len(record_counts) > 0 else st.columns(1)
for i, (rt, count) in enumerate(record_counts.items()):
    with rc_cols[i]:
        st.markdown(f"""
        <div class="ep-card" style="text-align: center; padding: 1rem;">
            <h2 style="margin: 0; color: #C65D47;">{count}</h2>
            <p style="margin: 0; font-size: 0.8rem; color: #4B5563; text-transform: uppercase;">{rt}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)

if missing > 0 or dupes > 0:
    st.warning("⚠ Your data contains missing or duplicate records. Consider cleaning your data for better insights.")
else:
    st.success("✓ Data is clean and ready for analysis.")
    
st.markdown("### Preview")
st.dataframe(df.head(100), width="stretch")

