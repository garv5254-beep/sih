import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from utils.theme import apply_theme, get_colors

# 🔧 MINIMAL SIDEBAR VISIBILITY FIX - Only override what's absolutely necessary
st.markdown("""
<style>
    /* Make sidebar visible if theme accidentally hid it */
    [data-testid="stSidebar"] {
        visibility: visible !important;
        display: block !important;
    }

    /* Ensure sidebar has reasonable width if set to 0px */
    [data-testid="stSidebar"] {
        min-width: 200px !important;
    }
</style>
""", unsafe_allow_html=True)

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

# Filter for new retailer schemes if you have a field for this
# new_retailer_schemes = [g for g in govt_schemes if g.get('target_audience') == 'New Retailers']
# For now, we'll show all schemes but you can uncomment above and use new_retailer_schemes below
new_retailer_schemes = govt_schemes  # Remove this line and uncomment the filter above if you have target_audience field

if not new_retailer_schemes:
    st.info("No government schemes found.")
else:
    # Separate eligible and ineligible schemes for better organization
    eligible_schemes = [g for g in new_retailer_schemes if g.get('eligible')]
    ineligible_schemes = [g for g in new_retailer_schemes if not g.get('eligible')]

    # Display eligible schemes
    if eligible_schemes:
        st.markdown("#### ✅ Eligible Schemes")
        for g in eligible_schemes:
            with st.container():
                # Create a card-like display
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**{g.get('scheme_name', 'Unnamed Scheme')}**")
                    if g.get('description'):
                        st.caption(g.get('description'))

                    # Details in expandable section
                    with st.expander("View Details"):
                        if g.get('missing_docs'):
                            st.info(f"**Missing Documents:** {', '.join(g.get('missing_docs', []))}")
                        if g.get('benefits'):
                            st.write(f"**Benefits:** {g.get('benefits')}")
                        if g.get('application_process'):
                            st.write(f"**Application Process:** {g.get('application_process')}")
                        if g.get('validity'):
                            st.write(f"**Validity:** {g.get('validity')}")

                with col2:
                    # Link buttons
                    link_col1, link_col2 = st.columns(2)
                    with link_col1:
                        if g.get('apply_link'):
                            st.link_button("Apply Now", g.get('apply_link'), use_container_width=True)
                        elif g.get('details_link'):
                            st.link_button("Details", g.get('details_link'), use_container_width=True)
                    with link_col2:
                        if g.get('details_link') and not g.get('apply_link'):
                            st.link_button("Apply", g.get('details_link'), use_container_width=True)
                        elif g.get('faq_link'):
                            st.link_button("FAQ", g.get('faq_link'), use_container_width=True)

                st.divider()

    # Display ineligible schemes
    if ineligible_schemes:
        st.markdown("#### ❌ Not Eligible Schemes")
        for g in ineligible_schemes:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**{g.get('scheme_name', 'Unnamed Scheme')}**")
                    if g.get('reason'):
                        st.caption(f"Reason: {g.get('reason')}")

                    with st.expander("View Details"):
                        if g.get('eligibility_criteria'):
                            st.write(f"**Eligibility Criteria:** {g.get('eligibility_criteria')}")
                        if g.get('benefits'):
                            st.write(f"**Benefits (if eligible):** {g.get('benefits')}")
                        if g.get('alternative_schemes'):
                            st.write(f"**Alternative Schemes:** {', '.join(g.get('alternative_schemes', []))}")

                with col2:
                    if g.get('details_link'):
                        st.link_button("Learn More", g.get('details_link'), use_container_width=True)

                st.divider()

# ADD MORE SCHEMES SECTION - Display any other scheme types found in the data
st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB;'><br>", unsafe_allow_html=True)
st.markdown("### Other Scheme Types")

# Get all scheme types except promotions and govt_schemes which we already displayed
other_scheme_types = {k: v for k, v in schemes_data.items()
                     if k not in ['promotions', 'govt_schemes'] and isinstance(v, list)}

if not other_scheme_types:
    st.info("No other scheme types found in the data.")
else:
    for scheme_type, scheme_list in other_scheme_types.items():
        if not scheme_list:
            continue

        # Format the scheme type name for display (convert snake_case to Title Case)
        display_name = scheme_type.replace('_', ' ').title()
        st.markdown(f"#### {display_name}")

        if not scheme_list:
            st.info(f"No {display_name.lower()} available.")
        else:
            # Display as a simple table for quick overview
            try:
                df = pd.DataFrame(scheme_list)
                if not df.empty:
                    # Show first few columns or all if less than 5 columns
                    cols_to_show = df.columns.tolist()[:5] if len(df.columns) > 5 else df.columns.tolist()
                    st.dataframe(df[cols_to_show], use_container_width=True, hide_index=True)

                    # Show expandable details for each item if there are more columns
                    if len(df.columns) > 5:
                        with st.expander(f"See all columns for {display_name}"):
                            st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info(f"No {display_name.lower()} available.")
            except Exception as e:
                # Fallback to simple display if DataFrame creation fails
                st.write(f"Found {len(scheme_list)} {display_name.lower()}:")
                for i, item in enumerate(scheme_list[:5]):  # Show first 5 items
                    if isinstance(item, dict):
                        # Show key-value pairs
                        details = ", ".join([f"{k}: {v}" for k, v in list(item.items())[:3]])
                        st.write(f"{i+1}. {details}")
                    else:
                        st.write(f"{i+1}. {item}")
                if len(scheme_list) > 5:
                    st.caption(f"... and {len(scheme_list) - 5} more")

        st.markdown("---")  # Separator between scheme types