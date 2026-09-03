import streamlit as st
from components.sidebar import render_sidebar
from components.header import render_header
from utils.theme import apply_theme, get_colors

st.set_page_config(page_title="BizMetrics - Government Schemes", layout="wide")
apply_theme()
render_sidebar()
render_header("Government Schemes", "Discover schemes your business is eligible for.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]
schemes = result.get("schemes", [])
colors = get_colors()

st.markdown("### Potential Schemes")

if not schemes:
    st.info("No scheme eligibility data available. Coming from verified scheme data.")
else:
    for scheme in schemes:
        is_eligible = scheme.get("eligible", False)
        
        status_color = colors['olive'] if is_eligible else colors['terracotta']
        status_bg = '#ECFCCB' if is_eligible else '#FFEDD5'
        status_text = "ELIGIBLE" if is_eligible else "NOT ELIGIBLE"
        
        st.markdown(
            f"""
            <div class="ep-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: #111827;">{scheme.get('scheme_name', 'Unknown Scheme')}</h4>
                    <span style="background-color: {status_bg}; color: {status_color}; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">{status_text}</span>
                </div>
            """, unsafe_allow_html=True
        )
        
        if is_eligible:
            missing = scheme.get("missing_docs", [])
            if missing:
                st.markdown(f"<p style='color: #9D4330; font-size: 0.95rem; margin: 0;'><strong>Missing Information:</strong> {', '.join(missing)}</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #6B705C; font-size: 0.95rem; margin: 0;'>✓ All eligibility criteria satisfied.</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color: #4B5563; font-size: 0.95rem; margin: 0;'><strong>Reason:</strong> {scheme.get('reason', 'N/A')}</p>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

