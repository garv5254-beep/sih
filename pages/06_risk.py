import streamlit as st
from components.sidebar import render_sidebar
from components.header import render_header
from utils.theme import apply_theme, get_colors

st.set_page_config(page_title="BizMetrics - Risk Analysis", layout="wide")
apply_theme()
render_sidebar()
render_header("Risk Center", "Identify business risks before they become problems.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]
risks = result.get("risks", [])
colors = get_colors()

st.markdown("### Overall Risk Score")
score = 100 - (len(risks) * 10)
score = max(0, min(100, score))

health_color = colors['olive'] if score > 70 else colors['terracotta'] if score > 40 else colors['deep_rust']
st.markdown(
    f"""
    <div class="ep-card" style="text-align: center; max-width: 400px;">
        <h1 style="font-size: 5rem; color: {health_color}; margin: 0;">{score}</h1>
        <p style="color: #4B5563; font-size: 1.2rem; font-weight: 500;">Out of 100</p>
    </div>
    """, unsafe_allow_html=True
)

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)
st.markdown("### Detected Risks")

if not risks:
    st.success("No critical risks detected. Your business is operating smoothly.")
else:
    for risk in risks:
        severity = risk.get('severity', 'LOW').upper()
        
        color_map = {
            'CRITICAL': colors['deep_rust'],
            'HIGH': colors['deep_rust'],
            'MEDIUM': colors['terracotta'],
            'LOW': colors['olive']
        }
        bg_map = {
            'CRITICAL': '#FEE2E2',
            'HIGH': '#FEF3C7',
            'MEDIUM': '#FFEDD5',
            'LOW': '#ECFCCB'
        }
        
        sev_color = color_map.get(severity, colors['olive'])
        bg_color = bg_map.get(severity, '#ECFCCB')
        
        st.markdown(
            f"""
            <div class="ep-card" style="border-left: 4px solid {sev_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="margin: 0;">{risk.get('risk')}</h4>
                    <span style="background-color: {bg_color}; color: {sev_color}; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">{severity}</span>
                </div>
                <p style="color: #4B5563; font-size: 0.95rem; margin-bottom: 0.5rem;"><strong>Reason:</strong> {risk.get('risk')}</p>
                <p style="color: #4B5563; font-size: 0.95rem; margin: 0;"><strong>Recommended Action:</strong> {risk.get('action')}</p>
            </div>
            """, unsafe_allow_html=True
        )

