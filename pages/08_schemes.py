import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from utils.formatting import format_currency
from utils.theme import apply_theme

st.set_page_config(page_title="BizMetrics - Schemes", layout="wide")
apply_theme()
render_sidebar()
render_header("Business Schemes & Eligibility", "Find schemes relevant to your business and check eligibility using your BizMetrics profile.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.stop()

result = st.session_state["pipeline_result"]

# -----------------------------------------------------------------
# 1. EXTRACT BUSINESS PROFILE DATA safely
# -----------------------------------------------------------------
business_data = result.get("business", {})
financials_data = result.get("financials", {})

def safe_numeric(val, default=None):
    if pd.isna(val) or val is None or val == "":
        return default
    try:
        return float(val)
    except:
        return default

# Safely extract attributes
b_name = business_data.get('business_name', 'Unknown Business')
b_sector = business_data.get('sector', 'Retail')
b_state = business_data.get('state', 'Unknown')
b_employees = safe_numeric(business_data.get('employees'), None)
b_age = safe_numeric(business_data.get('business_age_years'), None)

# Missing values for critical registrations will trigger warning instead of failure
b_udyam = business_data.get('udyam_registered') 
if pd.isna(b_udyam): b_udyam = None

b_gst = business_data.get('gst_registered')
if pd.isna(b_gst): b_gst = None

b_revenue = safe_numeric(financials_data.get('total_revenue'), None)

# -----------------------------------------------------------------
# 2. DEFINE LOCAL SCHEME DATABASE (HARDCODED FOR ACCURACY)
# -----------------------------------------------------------------
# Note: "Market-Based Recommendation" denotes unofficial/partner schemes.
ALL_SCHEMES = [
    {
        "id": "s1",
        "name": "PM MUDRA Yojana - Tarun",
        "category": "Business Finance",
        "department": "Ministry of Micro, Small and Medium Enterprises",
        "benefit": "Loans up to ₹10 Lakhs without collateral.",
        "type": "Official Govt Scheme",
        "state_restriction": None,
        "criteria": [
            {"key": "Business Type", "req_text": "Non-Corporate Small Business", "eval": lambda: ("✓", "Satisfied")},
            {"key": "Business Age", "req_text": "Minimum 2 years", "eval": lambda: ("✓", "Satisfied") if b_age and b_age >= 2 else (("✗", "Less than 2 years") if b_age else ("⚠", "Information Required"))},
            {"key": "Udyam Registration", "req_text": "Required", "eval": lambda: ("✓", "Registered") if str(b_udyam).lower() in ['true', 'yes', '1'] else (("✗", "Not Registered") if b_udyam is not None else ("⚠", "Information Required"))}
        ],
        "documents": ["Aadhaar", "PAN", "Business proof", "6-months Bank Statement"],
        "url": "https://www.mudra.org.in/"
    },
    {
        "id": "s2",
        "name": "CGTMSE Credit Guarantee",
        "category": "Business Finance",
        "department": "Ministry of MSME",
        "benefit": "Collateral-free credit up to ₹200 Lakhs.",
        "type": "Official Govt Scheme",
        "state_restriction": None,
        "criteria": [
            {"key": "Sector", "req_text": "Retail / Manufacturing / Service", "eval": lambda: ("✓", f"Satisfied ({b_sector})")},
            {"key": "Udyam Registration", "req_text": "Required", "eval": lambda: ("✓", "Registered") if str(b_udyam).lower() in ['true', 'yes', '1'] else (("✗", "Not Registered") if b_udyam is not None else ("⚠", "Information Required"))},
            {"key": "Business Size", "req_text": "Micro or Small", "eval": lambda: ("✓", "Satisfied") if b_revenue and b_revenue <= 500000000 else (("✗", "Exceeds limit") if b_revenue else ("⚠", "Information Required"))}
        ],
        "documents": ["Udyam certificate", "Project Report", "CGTMSE application"],
        "url": "https://www.cgtmse.in/"
    },
    {
        "id": "s3",
        "name": "Chhattisgarh State Industrial Policy Subsidy",
        "category": "State/Regional",
        "department": "Govt of Chhattisgarh",
        "benefit": "Interest subsidy and capital investment support.",
        "type": "Official Govt Scheme",
        "state_restriction": "Chhattisgarh",
        "criteria": [
            {"key": "State", "req_text": "Chhattisgarh", "eval": lambda: ("✓", "Chhattisgarh") if b_state == "Chhattisgarh" else ("✗", b_state)},
            {"key": "GST Registration", "req_text": "Required", "eval": lambda: ("✓", "Registered") if str(b_gst).lower() in ['true', 'yes', '1'] else (("✗", "Not Registered") if b_gst is not None else ("⚠", "Information Required"))}
        ],
        "documents": ["State Domicile", "GST documents", "Investment Proof"],
        "url": "https://industries.cg.gov.in/"
    },
    {
        "id": "s4",
        "name": "ONDC Digital Commerce Onboarding",
        "category": "Digital Business",
        "department": "DPIIT",
        "benefit": "Access to pan-India e-commerce buyers with zero setup fees.",
        "type": "Market-Based Recommendation",
        "state_restriction": None,
        "criteria": [
            {"key": "GST Registration", "req_text": "Required", "eval": lambda: ("✓", "Registered") if str(b_gst).lower() in ['true', 'yes', '1'] else (("✗", "Not Registered") if b_gst is not None else ("⚠", "Information Required"))},
            {"key": "Bank Account", "req_text": "Active Current Account", "eval": lambda: ("⚠", "Needs Verification")}
        ],
        "documents": ["GST details", "Bank Account info", "Product Catalog"],
        "url": "https://ondc.org/"
    },
    {
        "id": "s5",
        "name": "Pradhan Mantri Kaushal Vikas Yojana (PMKVY)",
        "category": "Skill & Employment",
        "department": "Ministry of Skill Development",
        "benefit": "Free skill training for employees/apprentices.",
        "type": "Official Govt Scheme",
        "state_restriction": None,
        "criteria": [
            {"key": "Employees", "req_text": "Has staff to train", "eval": lambda: ("✓", f"{int(b_employees)} employees") if b_employees and b_employees > 0 else (("✗", "No employees listed") if b_employees is not None else ("⚠", "Information Required"))}
        ],
        "documents": ["Aadhaar of candidates", "Business registration"],
        "url": "https://www.pmkvyofficial.org/"
    }
]

# -----------------------------------------------------------------
# 3. EVALUATION ENGINE
# -----------------------------------------------------------------
evaluated_schemes = []
for scheme in ALL_SCHEMES:
    c_results = []
    satisfied_count = 0
    total_applicable = 0
    has_failed_criteria = False
    has_warning_criteria = False
    
    for c in scheme["criteria"]:
        icon, status_text = c["eval"]()
        c_results.append({
            "Criterion": c["key"],
            "Requirement": c["req_text"],
            "Business Value": status_text,
            "Icon": icon
        })
        
        if icon == "✓":
            satisfied_count += 1
            total_applicable += 1
        elif icon == "✗":
            has_failed_criteria = True
            total_applicable += 1
        elif icon == "⚠":
            has_warning_criteria = True
            # Does not count towards total_applicable to prevent artificial failure score
            
    score = (satisfied_count / total_applicable * 100) if total_applicable > 0 else 0
    
    if has_failed_criteria:
        eligibility = "Likely Not Eligible"
    elif has_warning_criteria:
        eligibility = "Needs Verification"
    else:
        eligibility = "Likely Eligible"
        
    priority = "Low"
    if eligibility == "Likely Eligible" and score >= 90:
        priority = "High"
    elif eligibility in ["Likely Eligible", "Needs Verification"] and score >= 50:
        priority = "Medium"
        
    evaluated_schemes.append({
        "id": scheme["id"],
        "name": scheme["name"],
        "category": scheme["category"],
        "department": scheme["department"],
        "benefit": scheme["benefit"],
        "type": scheme["type"],
        "state_restriction": scheme["state_restriction"],
        "documents": scheme["documents"],
        "url": scheme["url"],
        "criteria_results": c_results,
        "score": score,
        "eligibility": eligibility,
        "priority": priority
    })

# -----------------------------------------------------------------
# 4. KPI CARDS
# -----------------------------------------------------------------
total_schemes = len(evaluated_schemes)
likely_eligible = sum(1 for s in evaluated_schemes if s["eligibility"] == "Likely Eligible")
not_eligible = sum(1 for s in evaluated_schemes if s["eligibility"] == "Likely Not Eligible")
needs_verification = sum(1 for s in evaluated_schemes if s["eligibility"] == "Needs Verification")
high_priority = sum(1 for s in evaluated_schemes if s["priority"] == "High")

c1, c2, c3, c4, c5 = st.columns(5)
with c1: kpi_card("Total Schemes", total_schemes)
with c2: kpi_card("Likely Eligible", likely_eligible)
with c3: kpi_card("Needs Verification", needs_verification)
with c4: kpi_card("Not Eligible", not_eligible)
with c5: kpi_card("High Priority", high_priority)

st.markdown("---")

# -----------------------------------------------------------------
# 5. SEARCH AND FILTERS
# -----------------------------------------------------------------
st.markdown("### 🔍 Search & Filters")
f1, f2, f3, f4 = st.columns(4)
with f1:
    search_query = st.text_input("Search Scheme", "").lower()
with f2:
    filter_category = st.selectbox("Business Category", ["All", "Business Finance", "Digital Business", "Skill & Employment", "State/Regional"])
with f3:
    filter_eligibility = st.selectbox("Eligibility Status", ["All", "Likely Eligible", "Needs Verification", "Likely Not Eligible"])
with f4:
    filter_priority = st.selectbox("Priority", ["All", "High", "Medium", "Low"])

filtered_schemes = []
for s in evaluated_schemes:
    # Text search
    text_match = search_query in s["name"].lower() or search_query in s["department"].lower() or search_query in s["benefit"].lower()
    cat_match = filter_category == "All" or filter_category == s["category"]
    elig_match = filter_eligibility == "All" or filter_eligibility == s["eligibility"]
    prio_match = filter_priority == "All" or filter_priority == s["priority"]
    
    if text_match and cat_match and elig_match and prio_match:
        filtered_schemes.append(s)

st.markdown("---")

# -----------------------------------------------------------------
# 6. SCHEME DASHBOARD (CARDS)
# -----------------------------------------------------------------
st.markdown("### 📋 Recommended Schemes")

if not filtered_schemes:
    st.info("No schemes match your filter criteria.")
else:
    # Using columns to layout scheme names for user to select
    selected_scheme_name = st.selectbox(
        "Select a scheme to view detailed eligibility and next steps:",
        options=[s["name"] for s in filtered_schemes]
    )
    
    selected_scheme = next((s for s in filtered_schemes if s["name"] == selected_scheme_name), None)
    
    if selected_scheme:
        # Theme colors map
        color_map = {
            "Likely Eligible": "success",
            "Needs Verification": "warning",
            "Likely Not Eligible": "error"
        }
        
        # Details view
        st.markdown(f"## {selected_scheme['name']}")
        st.markdown(f"**Category:** {selected_scheme['category']} | **Department:** {selected_scheme['department']}")
        st.markdown(f"**Source Type:** {selected_scheme['type']}")
        st.markdown(f"**Potential Benefit:** {selected_scheme['benefit']}")
        
        c_status, c_score = st.columns(2)
        
        with c_status:
            status = selected_scheme['eligibility']
            if status == "Likely Eligible":
                st.success(f"**Status:** {status}")
            elif status == "Needs Verification":
                st.warning(f"**Status:** {status}")
            else:
                st.error(f"**Status:** {status}")
                
        with c_score:
            score = selected_scheme['score']
            if selected_scheme['eligibility'] == "Needs Verification" and score == 0:
                st.warning("**Eligibility Score:** Cannot be fully determined (Information missing)")
            else:
                st.info(f"**Eligibility Score:** {score:.1f}%")
        
        st.markdown("### ✅ Eligibility Criteria")
        # Build dataframe for clear presentation
        df_criteria = pd.DataFrame(selected_scheme["criteria_results"])
        
        # Display cleanly
        st.dataframe(df_criteria, hide_index=True, width="stretch")
        
        st.markdown("### 📋 Action Plan & Next Steps")
        if selected_scheme["eligibility"] == "Likely Eligible":
            st.success("Recommended Next Steps:\n1. Verify eligibility on the official scheme portal.\n2. Prepare required documents.\n3. Complete registration/application.\n4. Track application status.")
        elif selected_scheme["eligibility"] == "Needs Verification":
            st.warning("Update your business profile with missing information (e.g., GST/Udyam/Employee details) to improve eligibility accuracy.")
        else:
            st.error("Your business profile currently does not meet one or more required criteria.")
            
        st.markdown("### 📄 Required Documents")
        st.markdown("\n".join([f"- {doc}" for doc in selected_scheme["documents"]]))
        
        st.markdown("### 🔗 Official Source")
        if selected_scheme["url"]:
            st.info(f"[Apply / Learn More]({selected_scheme['url']})")
        else:
            st.info("Official source not available in current dataset.")

        st.markdown("---")
        st.markdown("### 💡 Business-Specific Insights")
        if selected_scheme["category"] == "Business Finance" and b_sector == "Retail":
            st.markdown("Credit/working-capital schemes may be relevant because BizMetrics identifies receivables and inventory financing needs.")
        if selected_scheme["category"] == "State/Regional" and selected_scheme["state_restriction"] == b_state:
            st.markdown(f"Local initiatives in {b_state} strongly favor registered small businesses. Ensure state domicile documentation is ready.")
