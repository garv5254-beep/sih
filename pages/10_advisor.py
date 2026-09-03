import streamlit as st
from components.sidebar import render_sidebar
from components.header import render_header
from utils.formatting import format_currency
from utils.theme import apply_theme
from ai_advisor import generate_business_advice

st.set_page_config(page_title="BizMetrics - AI Advisor", layout="wide")
apply_theme()
render_sidebar()
render_header("BizMetrics AI Advisor", "Ask questions about your business.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.info("Developer Note:\nPlace rural_business_master_data.csv in the project root or data/ directory.")
    st.stop()

result = st.session_state["pipeline_result"]

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(
        """
        <div style="background-color: #F4F1DE; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #C65D47;">
            <strong style="color: #9D4330;">AI BUSINESS ADVISOR:</strong> Powered by Contextual Business Intelligence.
        </div>
        """, unsafe_allow_html=True
    )
    
    st.markdown("""
    **Suggested Prompts:**
    - "How is my business performing?"
    - "Why did my profit change?"
    - "Which customers should I target?"
    - "Prepare my business for the next major Indian festival."
    - "Who has outstanding payments?"
    """)
    
    with st.form(key="advisor_form"):
        user_input = st.text_input("Ask a question...", placeholder="What products should I reorder?")
        submit_button = st.form_submit_button(label="Ask Advisor")
        
    if submit_button and user_input:
        with st.spinner("Analyzing business data and market context..."):
            response = generate_business_advice(
                user_query=user_input, 
                pipeline_result=result, 
                chat_history=st.session_state["chat_history"]
            )
            if response:
                st.session_state["chat_history"].append({
                    "user": user_input,
                    "ai": response
                })

    # Display Chat History
    for chat in reversed(st.session_state["chat_history"]):
        user_msg = chat["user"]
        ai_resp = chat["ai"]
        
        st.markdown(f"**You:** {user_msg}")
        
        if isinstance(ai_resp, dict):
            st.markdown("### 💡 AI Business Recommendations")
            
            recs = ai_resp.get("recommendations", [])
            if not recs:
                st.info("No major issues detected based on available data.")
            else:
                for idx, rec in enumerate(recs):
                    priority = rec.get("priority", "LOW").upper()
                    if priority in ["HIGH", "CRITICAL"]:
                        pri_color = "#9D4330" # Deep Rust
                    elif priority == "MEDIUM":
                        pri_color = "#C65D47" # Terracotta
                    else:
                        pri_color = "#6B705C" # Olive / Low / Opportunity

                    st.markdown(f"""
                    <div style="background-color: #FAF9F6; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 5px solid {pri_color}; border-top: 1px solid #E5E7EB; border-right: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.2rem; font-weight: bold; color: {pri_color};">{idx+1:02d}</span>
                            <span style="font-size: 0.9rem; font-weight: bold; color: {pri_color};">● {rec.get('category', 'GENERAL').upper()}</span>
                        </div>
                        <h4 style="color: #1F2937; margin-top: 0; margin-bottom: 1rem;">{rec.get('title', '')}</h4>
                        <p style="color: #4B5563; margin-bottom: 0.5rem;"><strong>Finding</strong><br>{rec.get('finding', '')}</p>
                        <p style="color: #1F2937; margin-bottom: 1rem;"><strong>Recommended Action</strong><br>{rec.get('action', '')}</p>
                        <div style="font-size: 0.8rem; font-weight: bold; color: {pri_color}; letter-spacing: 0.05em;">PRIORITY: {priority}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            impact = ai_resp.get("impact", "")
            if impact:
                st.markdown(f"""
                <hr style="margin-top: 2rem; border-color: #E2E8F0;" />
                <h5 style="color: #6B705C;">BUSINESS IMPACT</h5>
                <p style="color: #374151;">{impact}</p>
                <br/>
                """, unsafe_allow_html=True)
        else:
            # Fallback for plain string
            st.info(ai_resp)

with col2:
    st.markdown("### Business Context Engine")
    f = result.get('financial', {})
    r = result.get('receivables', {})
    i = result.get('inventory', {})
    
    st.markdown(
        f"""
        <div class="ep-card">
            <h5 style="color: #6B705C;">Live Data Status</h5>
            <p><strong>Revenue:</strong> {format_currency(f.get('total_revenue', 0))}</p>
            <p><strong>Profit Margin:</strong> {f.get('profit_margin', 0):.2f}%</p>
            <p><strong>Receivables:</strong> {format_currency(r.get('total_outstanding', 0))}</p>
            <p><strong>Low Stock SKUs:</strong> {i.get('low_stock_items', 0)}</p>
            <p><strong>Risks Detected:</strong> {len(result.get('risks', []))}</p>
        </div>
        """, unsafe_allow_html=True
    )
