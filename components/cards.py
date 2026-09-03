import streamlit as st

def kpi_card(title, value, context=None):
    """
    Renders a premium EstatePro looking KPI card.
    """
    context_html = f"<div style='margin-top: 0.5rem; font-size: 0.8rem; color: #4B5563;'>{context}</div>" if context else ""
    
    st.markdown(
        f"""
        <div class="ep-card">
            <div class="ep-card-title">{title}</div>
            <div class="ep-card-value">{value}</div>
            {context_html}
        </div>
        """,
        unsafe_allow_html=True
    )

def insight_card(title, text):
    """
    Renders an intelligent insight card.
    """
    st.markdown(
        f"""
        <div class="ep-insight">
            <div class="ep-insight-title">{title}</div>
            <div class="ep-insight-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

