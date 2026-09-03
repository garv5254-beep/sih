import streamlit as st
from components.sidebar import render_sidebar
from components.header import render_header
from utils.formatting import format_currency
from utils.theme import apply_theme

st.set_page_config(page_title="BizMetrics - AI Advisor", layout="wide")
apply_theme()
render_sidebar()
render_header("BizMetrics AI Advisor", "Ask questions about your business.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(
        """
        <div style="background-color: #F4F1DE; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #C65D47;">
            <strong style="color: #9D4330;">AI BUSINESS ADVISOR:</strong> Ask me about your business.
        </div>
        """, unsafe_allow_html=True
    )
    
    st.markdown("""
    **Suggested Prompts:**
    - "Why is my profit decreasing?"
    - "What are my biggest risks?"
    - "Which inventory should I reorder?"
    """)
    
    user_input = st.text_input("Ask a question...", placeholder="How is my business performing?")
    if user_input:
        st.markdown(f"""
        <div class="ep-card">
            <h4 style="color: #6B705C;">AI Response</h4>
            <p style="color: #4B5563;">Based on your verified data, here is the automated advice:</p>
            <p style="color: #111827;">{result.get('advice', 'No advice available.')}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Default advice
        st.markdown(f"""
        <div class="ep-card">
            <h4 style="color: #6B705C;">Automated Summary</h4>
            <p style="color: #111827;">{result.get('advice', 'No advice available.')}</p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("### Business Context")
    f = result.get('financial', {})
    r = result.get('receivables', {})
    
    st.markdown(
        f"""
        <div class="ep-card">
            <p><strong>Revenue:</strong> {format_currency(f.get('total_revenue', 0))}</p>
            <p><strong>Profit Margin:</strong> {f.get('profit_margin', 0):.2f}%</p>
            <p><strong>Receivables:</strong> {format_currency(r.get('total_outstanding', 0))}</p>
            <p><strong>Risks Detected:</strong> {len(result.get('risks', []))}</p>
        </div>
        """, unsafe_allow_html=True
    )

