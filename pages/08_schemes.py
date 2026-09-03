import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from utils.theme import apply_theme, get_colors

st.set_page_config(page_title="BizMetrics - Schemes", layout="wide")
apply_theme()
render_sidebar()
render_header("Schemes & Promotions", "Data-driven and market-based promotion recommendations")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.stop()

result = st.session_state["pipeline_result"]
schemes_data = result.get("schemes", {})
promotions = schemes_data.get("promotions", [])
govt_schemes = schemes_data.get("govt_schemes", [])
colors = get_colors()

st.markdown("### Promotional Schemes")

if not promotions:
    st.info("No promotional schemes recommended at this time.")
else:
    data_driven = [p for p in promotions if p.get('Type') == 'DATA-DRIVEN']
    market_based = [p for p in promotions if p.get('Type') == 'MARKET-BASED']
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<h4 style='color: {colors.get('olive', '#6B705C')};'>Data-Driven Recommendations</h4>", unsafe_allow_html=True)
        if not data_driven:
            st.info("No data-driven recommendations available.")
        for p in data_driven:
            st.markdown(f"""
            <div style="background: {colors.get('background', '#FAF9F6')}; padding: 15px; border-radius: 8px; border-left: 5px solid {colors.get('olive', '#6B705C')}; margin-bottom: 15px; border-top: 1px solid #E5E7EB; border-right: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB;">
                <h5 style="margin-top: 0; color: #1F2937;">{p.get('Scheme Name')}</h5>
                <p style="margin: 4px 0;"><strong>Target Customers:</strong> {p.get('Target Customers')}</p>
                <p style="margin: 4px 0;"><strong>Target Products:</strong> {p.get('Target Products')}</p>
                <p style="margin: 4px 0;"><strong>Reason:</strong> {p.get('Reason')}</p>
                <p style="margin: 4px 0;"><strong>Period:</strong> {p.get('Recommended Period')}</p>
                <p style="margin: 4px 0;"><strong>Objective:</strong> {p.get('Expected Objective')}</p>
                <span style="background: #E5E7EB; color: #4B5563; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">Priority: {p.get('Priority')}</span>
            </div>
            """, unsafe_allow_html=True)
            
    with c2:
        st.markdown(f"<h4 style='color: {colors.get('terracotta', '#C65D47')};'>Market-Based Recommendations</h4>", unsafe_allow_html=True)
        if not market_based:
            st.info("No market-based recommendations available.")
        for p in market_based:
            st.markdown(f"""
            <div style="background: {colors.get('background', '#FAF9F6')}; padding: 15px; border-radius: 8px; border-left: 5px solid {colors.get('terracotta', '#C65D47')}; margin-bottom: 15px; border-top: 1px solid #E5E7EB; border-right: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB;">
                <h5 style="margin-top: 0; color: #1F2937;">{p.get('Scheme Name')}</h5>
                <p style="margin: 4px 0;"><strong>Target Customers:</strong> {p.get('Target Customers')}</p>
                <p style="margin: 4px 0;"><strong>Target Products:</strong> {p.get('Target Products')}</p>
                <p style="margin: 4px 0;"><strong>Reason:</strong> {p.get('Reason')}</p>
                <p style="margin: 4px 0;"><strong>Period:</strong> {p.get('Recommended Period')}</p>
                <p style="margin: 4px 0;"><strong>Objective:</strong> {p.get('Expected Objective')}</p>
                <span style="background: #E5E7EB; color: #4B5563; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">Priority: {p.get('Priority')}</span>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br><hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)
st.markdown("### Government Schemes Eligibility")
if not govt_schemes:
    st.info("No eligible government schemes found.")
else:
    for g in govt_schemes:
        if g.get('eligible'):
            st.success(f"**{g.get('scheme_name')}**: Eligible. Missing Docs: {', '.join(g.get('missing_docs', ['None']))}")
        else:
            st.error(f"**{g.get('scheme_name')}**: Not Eligible. Reason: {g.get('reason')}")
