import streamlit as st
from utils.formatting import t

def render_sidebar():
    # Initialize sidebar state if not exists
    if "sidebar_collapsed" not in st.session_state:
        st.session_state.sidebar_collapsed = False

    with st.sidebar:
        # Add custom toggle button at the very top
        col1, col2 = st.columns([1, 4])
        with col1:
            # Toggle button with arrow indicator
            if st.button(
                "☰" if st.session_state.sidebar_collapsed else "▶",
                key="sidebar_toggle",
                help="Toggle sidebar",
                use_container_width=True
            ):
                st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
                st.rerun()
        with col2:
            # Add some vertical spacing to align with button
            st.markdown('<div style="padding-top: 8px;"></div>', unsafe_allow_html=True)

        # Add slight top padding to prevent content from being too close to top
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        # Your original sidebar content starts here
        st.markdown(
            """
            <div style="margin-bottom: 2rem;">
                <h2 style="color: #9B493C; margin: 0; font-size: 1.8rem; font-family: 'Playfair Display', serif;">BizMetrics</h2>
                    <p style="color: #78805B; margin: 0; font-size: 0.9rem;">Smart Business Intelligence</p>
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
                <div style="width: 10px; height: 10px; background-color: #78805B; border-radius: 50%; margin-right: 8px;"></div>
                <span style="font-size: 0.85rem; color: #292622;">Data Connected</span>
            </div>
            <div style="font-size: 0.8rem; color: #292622; margin-left: 18px;">Master Dataset</div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<br><br>", unsafe_allow_html=True)

        if st.button("← Back / Logout", use_container_width=True):
            st.session_state["user_role"] = None
            st.session_state["owner_authenticated"] = False
            st.switch_page("app.py")