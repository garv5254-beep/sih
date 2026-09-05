import streamlit as st
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from utils.theme import apply_theme, get_colors
import pandas as pd

st.set_page_config(page_title="BizMetrics - Risk", layout="wide")
apply_theme()
render_sidebar()
render_header("Risk Dashboard", "Analyze business risks and vulnerabilities")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.stop()

result = st.session_state["pipeline_result"]
risks_data = result.get("risks", {"score": 100, "risk_list": []})
score = risks_data.get("score", 100)
risk_list = risks_data.get("risk_list", [])

colors = get_colors()

# KPI Cards
c1, c2, c3, c4 = st.columns(4)
with c1: 
    # Determine severity color for the overall score
    score_color = colors.get("olive", "#78805B") # High score (low risk)
    if score <= 30:
        score_color = colors.get("deep_rust", "#9D4330") # Critical
    elif score <= 60:
        score_color = colors.get("terracotta", "#9B493C") # High
    elif score <= 80:
        score_color = "#EAB308" # Medium (Yellow)
        
    st.markdown(f"""
    <div style="background: {colors.get('background', '#EDE5D0')}; padding: 20px; border-radius: 12px; border: 1px solid rgba(41,38,34,.12); text-align: center;">
        <h3 style="margin: 0; color: #4B5563; font-size: 1rem;">Overall Risk Score</h3>
        <h1 style="margin: 0; color: {score_color}; font-size: 2.5rem;">{score}/100</h1>
    </div>
    """, unsafe_allow_html=True)

# Count risks by severity
high_risks = len([r for r in risk_list if r.get("severity") == "HIGH"])
med_risks = len([r for r in risk_list if r.get("severity") == "MEDIUM"])

with c2: kpi_card("Total Active Risks", len(risk_list))
with c3: kpi_card("High Severity Risks", high_risks)
with c4: kpi_card("Medium Severity Risks", med_risks)

st.markdown("<br>", unsafe_allow_html=True)

if not risk_list:
    st.success("No significant business risks detected based on current data.")
else:
    st.markdown("### Risk Insights")
    
    # Categorize risks
    financial_risks = [r for r in risk_list if r.get("category") == "Financial"]
    inventory_risks = [r for r in risk_list if r.get("category") == "Inventory"]
    customer_risks = [r for r in risk_list if r.get("category") == "Customer"]
    receivables_risks = [r for r in risk_list if r.get("category") == "Receivables/Credit"]
    operational_risks = [r for r in risk_list if r.get("category") == "Operational"]
    
    tabs = st.tabs(["All Risks", "Financial", "Inventory", "Customer", "Receivables", "Operational"])
    
    def render_risk_cards(risk_group):
        if not risk_group:
            st.info("No risks detected in this category.")
            return
            
        for r in risk_group:
            sev_color = colors.get('deep_rust', '#78372F') if r.get("severity") == "HIGH" else colors.get('terracotta', '#9B493C')
            st.markdown(f"""
            <div style="background: {colors.get('background', '#EDE5D0')}; padding: 15px; border-radius: 12px; border-left: 5px solid {sev_color}; margin-bottom: 10px; border-top: 1px solid rgba(41,38,34,.12); border-right: 1px solid rgba(41,38,34,.12); border-bottom: 1px solid rgba(41,38,34,.12);">
                <div style="display: flex; justify-content: space-between;">
                    <h4 style="margin: 0; color: #1F2937;">{r.get('risk', 'Unknown Risk')}</h4>
                    <span style="background: {sev_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">{r.get('severity', 'UNKNOWN')}</span>
                </div>
                <p style="margin: 8px 0 4px 0; color: #4B5563;"><strong>Reason:</strong> {r.get('reason', 'N/A')}</p>
                <p style="margin: 0; color: #4B5563;"><strong>Action:</strong> {r.get('action', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
    with tabs[0]: render_risk_cards(risk_list)
    with tabs[1]: render_risk_cards(financial_risks)
    with tabs[2]: render_risk_cards(inventory_risks)
    with tabs[3]: render_risk_cards(customer_risks)
    with tabs[4]: render_risk_cards(receivables_risks)
    with tabs[5]: render_risk_cards(operational_risks)
