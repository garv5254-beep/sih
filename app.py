import streamlit as st
from utils.theme import apply_theme
from utils.data_loader import find_master_csv, get_cached_pipeline_result, load_master_data

st.set_page_config(page_title="BizMetrics", layout="wide", initial_sidebar_state="expanded")
apply_theme()

if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

if "owner_authenticated" not in st.session_state:
    st.session_state["owner_authenticated"] = False

OWNER_NAME = "Garv G"
OWNER_PASSWORD = "Garv@1212"


def render_owner_loading(placeholder, stage, progress, detail):
    """Render the actual loading stage without adding artificial wait time."""
    cards = "".join(
        f"<span class='loading-chip' style='animation-delay: {index * 0.12}s'>{label}</span>"
        for index, label in enumerate(("₹", "▥", "👥", "↗"))
    )
    placeholder.markdown(
        f"""
        <style>
            .biz-loading {{
                min-height: 82vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #F4EBDD;
                color: #263238;
                overflow: hidden;
                border-radius: 18px;
                padding: 3rem 1rem;
                box-sizing: border-box;
            }}
            .loading-shell {{ max-width: 760px; width: 100%; text-align: center; }}
            .loading-brand {{
                margin: 0;
                color: #A94B3C !important;
                font: 700 3rem/1.1 Georgia, serif !important;
                letter-spacing: .02em;
            }}
            .loading-subtitle {{ margin: .55rem 0 2rem; color: #68705A !important; font-size: 1rem; }}
            .loading-scene {{ height: 230px; position: relative; perspective: 900px; margin: 0 auto 1.5rem; }}
            .loading-store {{
                position: absolute; left: 50%; top: 58px; transform: translateX(-50%) rotateX(8deg);
                width: 230px; height: 120px; border-radius: 12px 12px 20px 20px;
                background: linear-gradient(145deg, #A94B3C, #7f382e); box-shadow: 0 22px 28px rgba(91, 56, 39, .25);
                animation: store-float 3.2s ease-in-out infinite;
            }}
            .loading-store:before {{ content: 'BizMetrics'; position: absolute; left: 25px; right: 25px; top: 30px; padding: 10px 4px; border-radius: 5px; background: #F4EBDD; color: #263238; font-weight: 700; }}
            .loading-store:after {{ content: ''; position: absolute; left: -12px; right: -12px; top: -14px; height: 24px; border-radius: 8px; background: repeating-linear-gradient(90deg, #68705A 0 24px, #F4EBDD 24px 48px); box-shadow: 0 6px 0 rgba(38, 50, 56, .12); }}
            .loading-base {{ position: absolute; left: 50%; top: 176px; width: 330px; height: 22px; transform: translateX(-50%) rotateX(62deg); border-radius: 50%; background: #68705A; box-shadow: 0 16px 22px rgba(91, 56, 39, .18); }}
            .loading-chip {{ position: relative; display: inline-flex; align-items: center; justify-content: center; width: 54px; height: 42px; margin: 0 13px; border: 1px solid rgba(169, 75, 60, .25); border-radius: 10px; background: #FFFFFF; color: #A94B3C; font-size: 1.35rem; font-weight: 700; box-shadow: 0 8px 16px rgba(91, 56, 39, .14); animation: chip-float 2.4s ease-in-out infinite; }}
            .loading-chips {{ position: absolute; left: 0; right: 0; top: 0; }}
            .loading-stage {{ color: #263238 !important; font-size: 1.25rem; font-weight: 700; margin: .5rem 0 .3rem; }}
            .loading-detail {{ color: #68705A !important; margin: 0 0 1rem; }}
            .loading-track {{ height: 10px; max-width: 500px; margin: 0 auto; background: rgba(104, 112, 90, .2); border-radius: 99px; overflow: hidden; }}
            .loading-progress {{ height: 100%; width: {progress}%; background: linear-gradient(90deg, #68705A, #A94B3C); border-radius: inherit; transition: width .25s ease; }}
            .loading-percent {{ color: #A94B3C !important; font-weight: 700; margin-top: .6rem; }}
            @keyframes store-float {{ 0%, 100% {{ transform: translateX(-50%) rotateX(8deg) translateY(0); }} 50% {{ transform: translateX(-50%) rotateX(8deg) translateY(-8px); }} }}
            @keyframes chip-float {{ 0%, 100% {{ transform: translateY(0) rotateY(0); opacity: .8; }} 50% {{ transform: translateY(-12px) rotateY(12deg); opacity: 1; }} }}
            @media (prefers-reduced-motion: reduce) {{ .loading-store, .loading-chip {{ animation: none; }} }}
            @media (max-width: 600px) {{ .loading-brand {{ font-size: 2.25rem !important; }} .loading-store {{ width: 190px; }} .loading-base {{ width: 270px; }} .loading-chip {{ margin: 0 4px; }} }}
        </style>
        <div class='biz-loading'>
            <div class='loading-shell'>
                <h1 class='loading-brand'>BizMetrics</h1>
                <p class='loading-subtitle'>Business Insights. Smarter Decisions.</p>
                <div class='loading-scene'>
                    <div class='loading-chips'>{cards}</div>
                    <div class='loading-store'></div>
                    <div class='loading-base'></div>
                </div>
                <div class='loading-stage'>{stage}</div>
                <p class='loading-detail'>{detail}</p>
                <div class='loading-track'><div class='loading-progress'></div></div>
                <div class='loading-percent'>{progress}%</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def prepare_owner_session(loading_placeholder):
    csv_path = find_master_csv()
    if csv_path is None:
        raise FileNotFoundError("rural_business_master_data.csv was not found.")

    file_stat = csv_path.stat()
    file_signature = (file_stat.st_mtime_ns, file_stat.st_size)
    render_owner_loading(loading_placeholder, "Welcome, Owner", 0, "Getting BizMetrics ready for your business.")
    render_owner_loading(loading_placeholder, "Loading your business data...", 25, "Reading the master dataset and validating its records.")
    load_master_data(str(csv_path), file_signature)
    render_owner_loading(loading_placeholder, "Analyzing business performance...", 50, "Preparing the lightweight dashboard metrics.")
    clean_df, result = get_cached_pipeline_result(str(csv_path), file_signature, include_inventory_ml=False)
    render_owner_loading(loading_placeholder, "Preparing your business tools...", 75, "Setting up shared data for fast page navigation.")
    st.session_state["raw_data"] = clean_df
    st.session_state["pipeline_result"] = result
    st.session_state["dataset_path"] = str(csv_path)
    render_owner_loading(loading_placeholder, "Almost ready...", 90, "Checking the dashboard data before opening your workspace.")
    if not isinstance(result, dict) or "financial" not in result:
        raise RuntimeError("Dashboard data was not prepared correctly.")
    render_owner_loading(loading_placeholder, "All set, Owner!", 100, "Your BizMetrics dashboard is ready.")

if st.session_state["user_role"] == "customer":
    st.markdown("<h2 style='color: #9D4330; font-family: \"Playfair Display\", serif;'>CUSTOMER PORTAL</h2>", unsafe_allow_html=True)
    st.markdown("### Welcome to BizMetrics Customer Portal")
    st.markdown("The customer experience is currently being prepared.")
    st.markdown("Customer features will include:\n\n• Customer Profile\n• Purchase History\n• Digital Bills\n• Payment History\n• Outstanding Amount\n• Customer QR\n• Account Information\n")
    if st.button("← Back to Access Selection"):
        st.session_state["user_role"] = None
        st.rerun()
    
    # Hide sidebar for customer portal
    st.markdown('<style>[data-testid="stSidebar"] { display: none; }</style>', unsafe_allow_html=True)
    st.stop()

elif st.session_state["user_role"] == "owner":
    if not st.session_state["owner_authenticated"]:
        st.markdown('<style>[data-testid="stSidebar"] { display: none; }</style>', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #9D4330; font-family: \"Playfair Display\", serif; margin-top: 3rem;'>OWNER LOGIN</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6B705C; margin-bottom: 2rem;'>Access your BizMetrics<br>Owner Dashboard</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            owner_name = st.text_input("Owner Name")
            owner_password = st.text_input("Password", type="password")
            
            if st.button("LOGIN", use_container_width=True, type="primary"):
                if not owner_name or not owner_password:
                    st.warning("⚠️ Please enter both owner name and password.")
                elif owner_name == OWNER_NAME and owner_password == OWNER_PASSWORD:
                    st.session_state["owner_authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ Invalid owner name or password.")
            
            if st.button("← Back", use_container_width=True):
                st.session_state["user_role"] = None
                st.session_state["owner_authenticated"] = False
                st.rerun()
        st.stop()
    else:
        if "pipeline_result" not in st.session_state or "raw_data" not in st.session_state:
            loading_placeholder = st.empty()
            try:
                prepare_owner_session(loading_placeholder)
            except FileNotFoundError:
                with loading_placeholder.container():
                    st.error("We couldn't load your business data.")
                    st.info("Place rural_business_master_data.csv in the project root or data/ directory.")
                    if st.button("Try Again", type="primary"):
                        st.rerun()
                st.stop()
            except Exception as exc:
                with loading_placeholder.container():
                    st.error("We couldn't prepare your BizMetrics dashboard.")
                    st.exception(exc)
                    if st.button("Try Again", type="primary"):
                        st.cache_data.clear()
                        st.rerun()
                st.stop()
        st.switch_page("pages/01_dashboard.py")

else:
    # Hide sidebar for access selection
    st.markdown('<style>[data-testid="stSidebar"] { display: none; }</style>', unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1rem; margin-top: 3rem;">
            <h1 style="color: #9D4330; font-size: 3.5rem; font-family: 'Playfair Display', serif; margin-bottom: 0;">BIZMETRICS</h1>
            <h3 style="color: #6B705C; font-weight: 300; margin-top: 0;">Business Intelligence</h3>
        </div>
        """, unsafe_allow_html=True
    )
    
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="display: inline-block; padding: 10px 40px; border: 1px solid #E5E7EB; border-radius: 20px; background-color: #FAF9F6;">
                <h3 style="margin: 0; color: #4B5563; font-size: 1.2rem;">SELECT ACCESS</h3>
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                """
                <div style="background-color: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border: 1px solid #E5E7EB; margin-bottom: 15px;">
                    <h1 style="font-size: 3rem; margin: 0;">👨‍💼</h1>
                    <h3 style="color: #4B5563; margin-top: 10px;">OWNER</h3>
                    <p style="color: #6B705C; font-size: 0.9rem; margin-bottom: 0;">Full Business Management</p>
                </div>
                """, unsafe_allow_html=True
            )
            if st.button("Continue as Owner", use_container_width=True, type="primary"):
                st.session_state["user_role"] = "owner"
                st.rerun()
                
        with c2:
            st.markdown(
                """
                <div style="background-color: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border: 1px solid #E5E7EB; margin-bottom: 15px;">
                    <h1 style="font-size: 3rem; margin: 0;">👤</h1>
                    <h3 style="color: #4B5563; margin-top: 10px;">CUSTOMER</h3>
                    <p style="color: #6B705C; font-size: 0.9rem; margin-bottom: 0;">View Your Business Relationship</p>
                </div>
                """, unsafe_allow_html=True
            )
            if st.button("Continue as Customer", use_container_width=True):
                st.session_state["user_role"] = "customer"
                st.rerun()
