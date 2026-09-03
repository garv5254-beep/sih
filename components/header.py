import streamlit as st
from utils.formatting import t

def render_header(title_key, description_key):
    lang = st.session_state.get('language', 'English')
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(f"<h1 style='margin-bottom: 0.2rem;'>{t(title_key, lang)}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #4B5563; font-size: 1.1rem; margin-top: 0;'>{t(description_key, lang)}</p>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(t("Refresh Data", lang) if lang == "English" else "डेटा रिफ्रेश करें", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            # Clear pipeline results from session state to force a reload, but don't delete everything
            if "pipeline_result" in st.session_state:
                del st.session_state["pipeline_result"]
            if "raw_data" in st.session_state:
                del st.session_state["raw_data"]
            # Switch back to app.py to reload the dataset centrally
            st.switch_page("app.py")
            
    st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 1rem 0 2rem 0;'>", unsafe_allow_html=True)

