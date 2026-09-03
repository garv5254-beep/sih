import streamlit as st
from utils.formatting import t

def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="margin-bottom: 2rem;">
                <h2 style="color: #9D4330; margin: 0; font-size: 1.8rem; font-family: 'Playfair Display', serif;">BizMetrics</h2>
                <p style="color: #6B705C; margin: 0; font-size: 0.9rem;">Smart Business Intelligence</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # In a real multi-page app, pages are listed automatically. 
        # But we want to ensure custom styling can be applied if possible.
        # Standard streamlit sidebar uses system fonts, but we overrode it in theme.py.
        
        st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
        st.divider()
        
        # Language Selector
        lang = st.selectbox(
            "Language",
            options=["English", "हिन्दी"],
            index=0 if st.session_state.get('language', 'English') == 'English' else 1,
            key="lang_selector",
            label_visibility="collapsed"
        )
        
        if lang != st.session_state.get('language'):
            st.session_state['language'] = lang
            st.rerun()
            
        st.markdown(
            """
            <div style="display: flex; align-items: center; margin-top: 1rem;">
                <div style="width: 10px; height: 10px; background-color: #6B705C; border-radius: 50%; margin-right: 8px;"></div>
                <span style="font-size: 0.85rem; color: #4B5563;">Data Connected</span>
            </div>
            <div style="font-size: 0.8rem; color: #4B5563; margin-left: 18px;">Master Dataset</div>
            """,
            unsafe_allow_html=True
        )

