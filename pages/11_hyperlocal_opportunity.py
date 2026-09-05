import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ai_advisor import DeterministicFallback, IntentDetector, SUPPORTED_LANGUAGES, call_llm, detect_language
from components.header import render_header
from components.sidebar import render_sidebar
from pipeline import calculate_financials
from utils.formatting import format_currency
from utils.pdf_report import generate_feasibility_pdf
from utils.hyperlocal_intelligence import (
    buyer_concentration,
    competitor_density,
    demand_competition_matrix,
    distribution_channels,
    localized_swot,
    market_reach,
    monthly_business_seasonality,
    pricing_intelligence,
    rank_alternative_businesses,
    supply_chain_risk,
    supplier_intelligence,
)
from utils.sih_finance import build_quarterly_schedule, calculate_emi, financing_capacity, select_scheme
from utils.theme import apply_theme

st.set_page_config(page_title="BizMetrics - Business Advisor", layout="wide")
apply_theme()
render_sidebar()
render_header("Your Business Advisor", "Choose a place and business. BizMetrics will explain the result simply.")

if "pipeline_result" not in st.session_state or "raw_data" not in st.session_state:
    st.error("BizMetrics data could not be loaded.")
    st.stop()
raw_data = st.session_state["raw_data"]

if "advisor_language" not in st.session_state:
    st.session_state["advisor_language"] = "English"
if "hyperlocal_check_complete" not in st.session_state:
    st.session_state["hyperlocal_check_complete"] = False

st.markdown("# 🌱 Start Your Business")
st.caption("Tell us what you want to start, how much money you have, and where you want to open it.")

st.markdown("## 🏪 What business are you interested in?")
business_choices = ["Grocery / Kirana", "Electronics", "Hardware", "Clothing", "Food Stall", "Dairy", "Poultry", "Agriculture Supplies", "Mobile Repair", "Tailoring", "Beauty Salon", "Small Restaurant", "General Store", "Other"]
business_choice = st.selectbox("Select Business", business_choices)
custom_business = st.text_input("Your business idea", placeholder="Type your business idea", disabled=business_choice != "Other")
business_name = custom_business.strip() or business_choice

st.markdown("## 💡 What type of business are you interested in?")
business_interest_options = [
    "Retail & Grocery", "Electronics & Mobile", "Electrical & Hardware", "Food & Beverage",
    "Dairy & Agriculture", "Poultry & Livestock", "Clothing & Tailoring", "Beauty & Personal Care",
    "Repair & Services", "Education & Stationery", "Transport & Delivery", "Manufacturing & Food Processing",
    "Digital & Online Services", "Home-Based Business", "Local Trading", "Other",
]
business_interests = st.multiselect("Business Interests", business_interest_options, default=[])
open_to_any = st.checkbox("I am open to any profitable business")

st.markdown("## 💰 How much money do you have to start the business?")
own_money = st.number_input("Available money", min_value=0.0, value=50000.0, step=5000.0, format="%.0f", help="Enter the money you can use to start this business.")

st.markdown("## 📍 Where do you want to open the business?")
location_columns = st.columns(4)
with location_columns[0]:
    state = st.selectbox("State", ["Chhattisgarh", "Madhya Pradesh", "Maharashtra"])
with location_columns[1]:
    district = st.selectbox("District", ["Durg", "Raipur", "Bhilai"])
with location_columns[2]:
    location_options = sorted(raw_data.get("city", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()) or ["Your village"]
    block = st.selectbox("Block", location_options)
with location_columns[3]:
    village = st.selectbox("Village / Town", location_options + ["Other village"])

selected_language = st.session_state["advisor_language"]

is_hindi = selected_language == "Hindi (हिंदी)"
is_hinglish = selected_language == "Hinglish"
def ui_text(english, hindi, hinglish=None):
    return hindi if is_hindi else hinglish if is_hinglish and hinglish else english

if st.button("🔍 CHECK MY BUSINESS", type="primary", use_container_width=True):
    st.session_state["hyperlocal_check_complete"] = True
if not st.session_state["hyperlocal_check_complete"]:
    st.info("Choose your place and business, then press CHECK MY BUSINESS.")
    st.stop()

with st.expander("⚙️ Advanced Options", expanded=False):
    st.caption("Optional technical assumptions. Most new entrepreneurs can leave these unchanged.")
    language_options = list(SUPPORTED_LANGUAGES)
    selected_language = st.selectbox("भाषा / Language", language_options, index=language_options.index(st.session_state["advisor_language"]) if st.session_state["advisor_language"] in language_options else 0)
    st.session_state["advisor_language"] = selected_language
    use_capacity_estimate = st.checkbox("Use financing-capacity estimate", value=False)
    assumption_columns = st.columns(3)
    with assumption_columns[0]:
        customers_per_day = st.number_input("Expected daily customers", min_value=0, value=20, step=1)
        working_days = st.number_input("Working days per month", min_value=1, max_value=31, value=26, step=1)
    with assumption_columns[1]:
        rent = st.number_input("Monthly rent", min_value=0.0, value=5000.0, step=500.0)
        salary = st.number_input("Monthly staff cost", min_value=0.0, value=10000.0, step=1000.0)
    with assumption_columns[2]:
        other_expenses = st.number_input("Other monthly costs", min_value=0.0, value=3000.0, step=500.0)
    equipment = st.number_input("Equipment cost", min_value=0.0, value=100000.0, step=5000.0)
    opening_stock = st.number_input("Opening stock", min_value=0.0, value=50000.0, step=5000.0)
    shop_setup = st.number_input("Shop setup", min_value=0.0, value=30000.0, step=5000.0)
    licence = st.number_input("Licence and registration", min_value=0.0, value=5000.0, step=1000.0)
    working_capital = st.number_input("Working capital", min_value=0.0, value=10000.0, step=5000.0)
    other_startup = st.number_input("Other startup costs", min_value=0.0, value=5000.0, step=1000.0)

capacity = financing_capacity(own_money)
project_cost = capacity["maximum_project_cost"] if use_capacity_estimate and own_money > 0 else equipment + opening_stock + shop_setup + licence + working_capital + other_startup
scheme = select_scheme(project_cost)
if not scheme["supported"] or project_cost > capacity["maximum_project_cost"]:
    st.error(scheme.get("reason", "The business cost is higher than your available financing capacity."))
    st.stop()
loan_amount = project_cost * 0.90
interest_rate = scheme["interest_rate"]
tenure_years = scheme["tenure_years"]
moratorium_months = scheme["moratorium_months"]
monthly_payment = calculate_emi(loan_amount, interest_rate, tenure_years * 12)
repayment = build_quarterly_schedule(loan_amount, interest_rate, tenure_years * 12, moratorium_months)

record_type = raw_data.get("record_type", pd.Series(dtype=str)).astype(str).str.lower()
inventory = raw_data[record_type == "inventory"].copy()
sales = raw_data[record_type == "sale"].copy()
category_column = "sector" if "sector" in inventory.columns else "category"
category_matches = inventory[category_column].astype(str).str.contains(business_name, case=False, na=False) if category_column in inventory.columns else pd.Series(False, index=inventory.index)
products = inventory.loc[category_matches, "product_id"] if "product_id" in inventory.columns else pd.Series(dtype=str)
category_sales = sales[sales.get("product_id", pd.Series(dtype=str)).isin(products)] if not products.empty else pd.DataFrame()
if not category_sales.empty:
    quantity = pd.to_numeric(category_sales.get("quantity", 0), errors="coerce").sum()
    demand_score = 85 if quantity > 1000 else 65 if quantity > 100 else 40
    demand_source = "Historical category sales"
else:
    demand_score = 55
    demand_source = "Estimate based on available information"
customer_ids = category_sales.get("customer_id", pd.Series(dtype=str)).dropna().nunique() if not category_sales.empty else 0
competition_score = 80 if customer_ids > 50 else 45 if not category_sales.empty else 60
matrix = demand_competition_matrix(demand_score, competition_score)
pricing = pricing_intelligence(raw_data, business_name)
reach = market_reach(raw_data, village, district)
density = competitor_density(raw_data, business_name)
channels = distribution_channels(business_name)
buyer_risk = buyer_concentration(raw_data)
supply_risk = supply_chain_risk(raw_data, business_name)
supplier_data = supplier_intelligence(raw_data)

selling_price = pricing.get("reference_price") or 100.0
purchase_price = selling_price * (1 - (pricing.get("expected_margin") or 0) / 100) if pricing.get("reference_price") else 0.0
synthetic_rows = [
    {"record_type": "Inventory", "product_id": "SIMPLE_PLAN", "purchase_price": purchase_price, "selling_price": selling_price},
    {"record_type": "Sale", "product_id": "SIMPLE_PLAN", "quantity": customers_per_day * working_days, "discount_percent": 0},
    {"record_type": "Expense", "category": "Rent", "amount": rent},
    {"record_type": "Expense", "category": "Salary", "amount": salary},
    {"record_type": "Expense", "category": "Other", "amount": other_expenses},
    {"record_type": "Loan", "outstanding_principal": loan_amount, "principal_amount": loan_amount, "interest_rate": interest_rate, "monthly_emi": monthly_payment},
]
financials = calculate_financials(pd.DataFrame(synthetic_rows))
net_profit = financials.get("net_profit", 0)
financial_score = 80 if net_profit > monthly_payment else 35 if net_profit > 0 else 10
opportunity_score = demand_score * 0.5 + competition_score * 0.2 + financial_score * 0.3
profit_potential = max(0, min(100, financial_score))
financial_feasibility = 80 if project_cost <= capacity["maximum_project_cost"] else 20
loan_affordability = 80 if monthly_payment <= net_profit else 40 if net_profit > 0 else 15
seasonality_score = 65 if not category_sales.empty and "date" in category_sales.columns else 50
risk_component = 75
if supply_risk["level"] in ("Medium", "High", "Needs Verification"):
    risk_component -= 15
if buyer_risk["risk_level"] in ("Medium", "High", "Needs Verification"):
    risk_component -= 10
success_probability = round(max(0, min(100, (
    demand_score * 0.25
    + (100 - competition_score) * 0.15
    + profit_potential * 0.20
    + financial_feasibility * 0.15
    + seasonality_score * 0.10
    + loan_affordability * 0.10
    + risk_component * 0.05
))))
outlook = "GOOD OPPORTUNITY" if opportunity_score >= 65 else "MODERATE OPPORTUNITY" if opportunity_score >= 50 else "HIGH RISK"
market_label = "GOOD" if demand_score >= 70 else "AVERAGE" if demand_score >= 40 else "LOW"
competition_label = "HIGH" if competition_score >= 70 else "MEDIUM" if competition_score >= 40 else "LOW"
gap_label = "GOOD MARKET GAP" if matrix["opportunity_gap"] in ("Potentially Underserved", "Moderately Underserved") else "CROWDED MARKET" if "Saturated" in matrix["opportunity_gap"] else "SOME OPPORTUNITY"
st.session_state["selected_sih_scheme"] = scheme["name"]
st.session_state["sih_financing_context"] = {"project_cost": project_cost, "available_margin": own_money, "loan_amount": loan_amount, "interest_rate": interest_rate, "tenure_years": tenure_years, "moratorium_months": moratorium_months}

st.markdown(f"# 🌱 {ui_text('YOUR BUSINESS RESULT', 'आपके व्यवसाय का परिणाम', 'YOUR BUSINESS RESULT')}")
st.caption(f"{ui_text('Business', 'व्यवसाय', 'Business')}: {business_name} | {ui_text('Location', 'स्थान', 'Location')}: {village}, {block}, {district}")
if outlook == "GOOD OPPORTUNITY":
    st.success(f"## 🟢 {outlook}")
elif outlook == "MODERATE OPPORTUNITY":
    st.warning(f"## 🟡 {outlook}")
else:
    st.error(f"## 🔴 {outlook}")

st.markdown(f"## 📊 {ui_text('Estimated Business Success Probability', 'अनुमानित व्यवसाय सफलता संभावना', 'Estimated Business Success Probability')}")
chart = go.Figure(data=[go.Pie(
    labels=["Success probability", "Risk / uncertainty"],
    values=[success_probability, 100 - success_probability],
    hole=0.64,
    marker_colors=["#78805B", "#EDE5D0"],
    textinfo="none",
)])
chart.update_layout(showlegend=False, height=280, margin=dict(l=10, r=10, t=10, b=10), annotations=[{
    "text": f"{success_probability}%<br><sup>estimated</sup>", "showarrow": False, "font": {"size": 24, "color": "#292622"}
}])
chart_columns = st.columns([1, 1])
with chart_columns[0]:
    st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
with chart_columns[1]:
    st.metric("Success Probability", f"{success_probability}%")
    st.metric("Risk / Uncertainty", f"{100 - success_probability}%")
    st.caption("This is an estimate based on available business and market information. It is not a guarantee.")

loan_column, market_column = st.columns(2)
with loan_column:
    st.markdown(f"## 💰 {ui_text('Your Loan', 'आपका लोन', 'Aapka Loan')}")
    st.metric(ui_text("Business Cost", "व्यवसाय की लागत", "Business Cost"), format_currency(project_cost))
    st.metric(ui_text("Your Money", "आपका पैसा", "Aapka Paisa"), format_currency(own_money))
    st.metric(ui_text("Possible Loan", "संभावित लोन", "Possible Loan"), format_currency(loan_amount))
    st.write(f"{ui_text('Loan type', 'लोन का प्रकार', 'Loan type')}: **{scheme['name']}**")
    st.write(f"{ui_text('Monthly payment', 'हर महीने की किस्त', 'Monthly payment')}: **{format_currency(monthly_payment)}**")
    st.write(f"{ui_text('Loan period', 'लोन की अवधि', 'Loan period')}: **{tenure_years} years** | {ui_text('Payment starts after', 'किस्त शुरू होगी', 'Payment starts after')}: **{moratorium_months} months**")
with market_column:
    st.markdown(f"## 🏪 {ui_text('Will People Buy This?', 'क्या लोग इसे खरीदेंगे?', 'Log kharidenge?')}")
    st.metric(ui_text("Local Demand", "स्थानीय मांग", "Local Demand"), market_label)
    st.write("Many people may need this business." if market_label == "GOOD" else "Local information is limited, so this is an estimate." if market_label == "AVERAGE" else "Demand looks weak in the available information.")
    st.markdown(f"## 👥 {ui_text('Competition', 'प्रतियोगिता', 'Competition')}")
    st.metric(ui_text("Competition", "प्रतियोगिता", "Competition"), competition_label)
    st.write("Few similar businesses appear in the available data." if competition_label == "LOW" else "Several similar businesses may already be active. Improve service or pricing." if competition_label == "HIGH" else "Some similar businesses appear in the available data.")

st.markdown(f"## 📍 {ui_text('Your Local Market', 'आपका स्थानीय बाजार', 'Aapka Local Market')}")
reach_columns = st.columns(2)
for column, radius in zip(reach_columns, ("5_km", "10_km")):
    with column:
        data = reach[radius]
        known = data.get("known_customers", data.get("estimated_consumers"))
        st.metric(radius.replace("_", " ").upper(), f"{known:,} known customers" if known is not None else "Not enough local data")
st.caption("Exact population is not available; nearby customer information is used where possible.")

st.markdown(f"## 📈 {ui_text('Is This a Good Opportunity?', 'क्या यह अच्छा अवसर है?', 'Kya yeh achha mauka hai?')}")
st.success(f"🟢 {gap_label}" if gap_label == "GOOD MARKET GAP" else f"🟡 {gap_label}" if gap_label == "SOME OPPORTUNITY" else f"🔴 {gap_label}")
st.write("Demand looks good and competition is manageable." if gap_label == "GOOD MARKET GAP" else "There may be room, but check local customers before investing." if gap_label == "SOME OPPORTUNITY" else "Demand and competition suggest you should be careful.")

st.markdown(f"## 📅 {ui_text('Monthly Market Conditions', 'मासिक बाजार स्थिति', 'Monthly Market Conditions')}")
monthly_profile = monthly_business_seasonality(raw_data, business_name, village, block, district, state)
monthly_rows = monthly_profile["rows"]
if monthly_rows:
    monthly_data = pd.Series({month + 1: row["Demand Score"] for month, row in enumerate(monthly_rows)})
else:
    monthly_data = pd.Series({month: 0 for month in range(1, 13)})

best_months = ", ".join(monthly_profile["best_months"])
difficult_months = ", ".join(monthly_profile["difficult_months"])
st.markdown("### 📅 Best & Difficult Months")
month_cards = st.columns(2)
with month_cards[0]:
    st.success(f"🟢 BEST MONTH\n\n{best_months}\n\nDemand Score: {int(monthly_data.max()) if monthly_rows else 'Estimated'}/100\n\nWhy: Strongest available demand signal for this business.")
with month_cards[1]:
    st.error(f"🔴 DIFFICULT MONTH\n\n{difficult_months}\n\nDemand Score: {int(monthly_data.min()) if monthly_rows else 'Estimated'}/100\n\nWhy: Lowest available demand signal; protect cash flow while fixed costs continue.")
st.caption(f"Confidence: {monthly_profile['confidence']} | Data basis: {monthly_profile['basis']}")
if not monthly_profile["reliable"]:
    st.warning("⚠️ Limited historical data. Reliable monthly business data is insufficient, so BizMetrics is using a broader seasonal estimate.")

if monthly_rows:
    high, low = monthly_data.quantile(0.66), monthly_data.quantile(0.33)
    trend = go.Figure(go.Scatter(x=[row["Month"] for row in monthly_rows], y=[row["Demand Score"] for row in monthly_rows], mode="lines+markers", line={"color": "#9B493C", "width": 3}, marker={"color": "#78805B", "size": 8}))
    trend.update_layout(title="Monthly Demand Trend", yaxis={"range": [0, 100], "title": "Demand score"}, xaxis_title="Month", height=320, margin={"l": 20, "r": 20, "t": 50, "b": 20})
    st.plotly_chart(trend, width="stretch", config={"displayModeBar": False})
    st.dataframe(pd.DataFrame(monthly_rows), hide_index=True, width="stretch")
else:
    high, low = 0, 0
    st.info("Monthly seasonality cannot be calculated because transaction dates are unavailable.")

st.markdown("### 💡 Seasonal Business Advice")
st.write(f"Prepare inventory and confirm suppliers before {best_months}. Protect working capital and reduce unnecessary stock before {difficult_months}.")
if monthly_rows and monthly_data.min() < monthly_data.max() and monthly_payment > 0:
    st.warning("⚠️ Repayment Comfort Warning: weaker demand months may generate lower cash flow while the loan repayment remains fixed. Maintain a working-capital reserve.")

st.markdown(f"## 🛒 {ui_text('How Can You Sell?', 'आप कैसे बेच सकते हैं?', 'Kaise bechen?')}")
st.write(" | ".join(channel["channel"] for channel in channels))
st.markdown(f"## ⚠️ {ui_text('What Could Go Wrong?', 'क्या गलत हो सकता है?', 'Kya galat ho sakta hai?')}")
watch_items = []
if competition_label in ("HIGH", "MEDIUM"):
    watch_items.append("Many similar businesses may reduce your sales.")
if supply_risk["level"] in ("Medium", "High", "Needs Verification"):
    watch_items.append("Product availability or transport may affect your business.")
if buyer_risk["risk_level"] in ("High", "Medium", "Needs Verification"):
    watch_items.append("Customers paying late can reduce the cash available to you.")
if loan_amount > 0:
    watch_items.append("Your monthly loan payment must be affordable.")
if monthly_data.max() == 0:
    watch_items.append("Sales may be lower in some months; local seasonal data is limited.")
for item in watch_items[:5] or ["Some risks need local checking."]:
    st.warning(item)

st.markdown(f"## 🤖 {ui_text('IF NOT THIS, TRY THIS', 'अगर यह नहीं, तो यह आजमाएं', 'Agar yeh nahi, to yeh aazmaen')}")
alternatives = rank_alternative_businesses(
    raw_data,
    business_name,
    own_money,
    village=village,
    block=block,
    district=district,
    state=state,
    seasonality_score=seasonality_score,
    risk_score=risk_component,
    business_interests=business_interests,
    open_to_any=open_to_any,
)
for alternative in alternatives:
    candidate_profile = monthly_business_seasonality(raw_data, alternative["business"], village, block, district, state)
    alternative["best_month"] = ", ".join(candidate_profile["best_months"])
    alternative["difficult_month"] = ", ".join(candidate_profile["difficult_months"])
    alternative["seasonality_confidence"] = candidate_profile["confidence"]
if alternatives:
    st.markdown("### 💡 Recommended Secondary Businesses")
    st.caption("These alternatives are ranked using your interests, capital, local indicators, seasonality, and risk.")
    for index, alternative in enumerate(alternatives[:3], 1):
        medal = ("🥇 Best Alternative" if index == 1 else "🥈 Second Alternative" if index == 2 else "🥉 Third Alternative")
        with st.container(border=True):
            st.markdown(f"#### {medal}: {alternative['business']}")
            score_columns = st.columns(5)
            score_columns[0].metric("Opportunity", f"{alternative['score']}/100")
            score_columns[1].metric("Interest Match", f"{alternative['interest_match']}/100")
            score_columns[2].metric("Demand", f"{alternative['demand']}/100")
            score_columns[3].metric("Competition Advantage", f"{100 - alternative['competition']}/100")
            score_columns[4].metric("Capital Fit", f"{alternative['capital_fit']}%")
            st.write(f"Why recommended: {alternative['reason']}.")
            st.write(f"Best month: {alternative['best_month']} | Difficult month: {alternative['difficult_month']}")
            st.caption(f"Data basis: {alternative['data_basis']} | Confidence: {alternative['confidence']}")
else:
    st.info("Not enough local data to confidently recommend an alternative business.")

st.markdown(f"## 💡 {ui_text('Our Advice', 'हमारी सलाह', 'Hamari salah')}")
advice = ["Start with customers in your nearby villages.", "Keep initial stock focused on products people buy often."]
if loan_amount > 0:
    advice.append("Keep enough cash ready for monthly loan payments.")
advice.append("Keep some money aside for slower months.")
for number, item in enumerate(advice[:5], 1):
    st.write(f"{number}. {item}")

st.markdown(f"## ✅ {ui_text('Should You Start This Business?', 'क्या आपको यह व्यवसाय शुरू करना चाहिए?', 'Kya aap yeh business shuru karein?')}")
decision = "🟢 YES — LOOKS PROMISING" if success_probability >= 65 else "🟡 MAYBE — CHECK BEFORE STARTING" if success_probability >= 45 else "🔴 HIGH RISK — CONSIDER ANOTHER BUSINESS"
if decision.startswith("🟢"):
    st.success(decision)
elif decision.startswith("🟡"):
    st.warning(decision)
else:
    st.error(decision)
st.write("Demand, competition, and the estimated loan plan look manageable." if success_probability >= 65 else "Check local customers, costs, and repayment comfort before investing.")

with st.expander("🔎 See Detailed Information", expanded=False):
    detail_columns = st.columns(5)
    detail_columns[0].metric("Demand", f"{demand_score}/100")
    detail_columns[1].metric("Competition", f"{competition_score}/100")
    detail_columns[2].metric("Business Opportunity", f"{opportunity_score:.1f}/100")
    detail_columns[3].metric("Financial Feasibility", f"{financial_score}/100")
    detail_columns[4].metric("Data Source", demand_source)
    st.markdown("#### Market Reach")
    reach_columns = st.columns(2)
    for column, radius in zip(reach_columns, ("5_km", "10_km")):
        with column:
            reach_data = reach[radius]
            st.metric(radius.replace("_", " ").upper(), reach_data.get("interpretation", "Data not available"))
    st.markdown("#### Pricing Intelligence")
    pricing_columns = st.columns(3)
    pricing_columns[0].metric("Reference Price", format_currency(pricing.get("reference_price")))
    pricing_columns[1].metric("Expected Margin", f"{pricing.get('expected_margin', 'Not available')}%")
    pricing_columns[2].metric("Confidence", pricing.get("confidence", "Not available"))
    st.markdown("#### Supplier and Risk")
    risk_columns = st.columns(3)
    risk_columns[0].metric("Supplier Count", supplier_data.get("supplier_count", "Not available"))
    risk_columns[1].metric("Supply Risk", supply_risk.get("level", "Not available"))
    risk_columns[2].metric("Customer Dependency", buyer_risk.get("risk_level", "Not available"))
    st.markdown("#### SWOT")
    swot = localized_swot(demand_score, competition_score, pricing.get("expected_margin") or 0, project_cost, 90, matrix["opportunity_gap"], supply_risk["level"], buyer_risk["risk_level"])
    for label, items in swot.items():
        st.write(f"{label}: {', '.join(items) if items else 'None identified'}")
    st.markdown("#### Estimated Monthly Financials")
    financial_columns = st.columns(4)
    financial_columns[0].metric("Sales", format_currency(financials.get("sales", 0)))
    financial_columns[1].metric("Expenses", format_currency(financials.get("total_expenses", 0)))
    financial_columns[2].metric("Net Profit", format_currency(financials.get("net_profit", 0)))
    financial_columns[3].metric("Break-Even", str(financials.get("break_even", "Not available")))
    st.markdown("#### Loan Details")
    loan_columns = st.columns(5)
    loan_columns[0].metric("Interest", f"{interest_rate}%")
    loan_columns[1].metric("Tenure", f"{tenure_years} years")
    loan_columns[2].metric("Moratorium", f"{moratorium_months} months")
    loan_columns[3].metric("Monthly Payment", format_currency(monthly_payment))
    loan_columns[4].metric("Quarterly Payment", format_currency(repayment["quarterly_payment"]))
    st.info("Interest treatment during the moratorium is a repayment-simulation assumption, not an explicit lender rule.")
    st.dataframe(repayment["schedule"].style.format({column: format_currency for column in ["Opening Principal", "Interest", "Principal Repaid", "Total Payment", "Closing Principal", "Cumulative Interest", "Cumulative Repayment"]}), hide_index=True, width="stretch")
    st.markdown("### ⚙️ What-If")
    what_if_loan = st.number_input("Try another loan amount", min_value=0.0, max_value=float(capacity["maximum_loan"]), value=float(loan_amount), step=5000.0)
    what_if_repayment = build_quarterly_schedule(what_if_loan, interest_rate, tenure_years * 12, moratorium_months)
    st.write(f"Monthly payment: {format_currency(calculate_emi(what_if_loan, interest_rate, tenure_years * 12))}")
    st.write(f"Total repayment: {format_currency(what_if_repayment.get('total_repayment', 0))}")

st.markdown("## 🤖 Ask About Your Business")
if "hyperlocal_chat" not in st.session_state:
    st.session_state["hyperlocal_chat"] = []
question = st.text_input("Ask a question", placeholder="Will this business work in my village?")
if st.button("Ask Advisor") and question:
    advisor_context = {
        "business": business_name,
        "business_interests": business_interests,
        "open_to_any_business": open_to_any,
        "location": f"{village}, {block}, {district}, {state}",
        "market": {"demand": demand_score, "competition": competition_score, "gap": matrix["opportunity_gap"], "reach": reach},
        "loan": {"amount": loan_amount, "interest": interest_rate, "tenure": tenure_years, "moratorium": moratorium_months, "monthly_payment": monthly_payment, "quarterly_payment": repayment["quarterly_payment"]},
        "financials": financials,
        "risks": {"supply": supply_risk, "buyer": buyer_risk},
        "secondary_businesses": alternatives,
        "best_month": best_months,
        "difficult_month": difficult_months,
        "monthly_demand": monthly_rows,
        "seasonality_confidence": monthly_profile["confidence"],
        "feasibility": {"outlook": outlook, "decision": decision},
    }
    language = detect_language(question, selected_language)
    response = call_llm(question, advisor_context, st.session_state["hyperlocal_chat"], language, "Simple")
    if response is None:
        response = DeterministicFallback.generate(question, advisor_context, IntentDetector.detect(question), language, "Simple")
    st.session_state["hyperlocal_chat"].append({"user": question, "ai": response})
for message in reversed(st.session_state["hyperlocal_chat"]):
    st.markdown(f"**You:** {message['user']}")
    response = message["ai"]
    if isinstance(response, dict):
        for recommendation in response.get("recommendations", []):
            st.info(f"**{recommendation.get('title', 'Advice')}**\n\n{recommendation.get('finding', '')}\n\n{recommendation.get('action', '')}")
    else:
        st.info(str(response))

st.markdown("### 📄 Your Feasibility Report is Ready")
st.caption("Download this report to view your business market, loan, risk, repayment and monthly market outlook.")

feasibility_report_data = {
    "business_name": business_name,
    "business_category": business_choice if custom_business.strip() == "" else custom_business.strip(),
    "state": state,
    "district": district,
    "block": block,
    "village": village,
    "report_date": pd.Timestamp.today().strftime("%Y-%m-%d"),
    "business_outlook": outlook,
    "possible_business_cost": project_cost,
    "your_money": own_money,
    "possible_loan": loan_amount,
    "loan_type": scheme["name"],
    "monthly_payment": monthly_payment,
    "business_risk": competition_label,
    "summary": "Demand appears good, competition is manageable and the estimated loan payment appears affordable." if opportunity_score >= 65 else "Market data is mixed, so additional local validation is recommended before investing.",
    "market_outlook": {
        "customer_demand": market_label,
        "market_condition": matrix["demand_level"],
        "local_market_opportunity": gap_label,
        "km_5": str(reach["5_km"].get("known_customers", "Not available")),
        "km_10": str(reach["10_km"].get("known_customers", "Not available")),
        "distribution_channels": " | ".join(channel["channel"] for channel in channels),
        "demand_vs_competition": f"Demand: {market_label} | Competition: {competition_label}",
        "underserved_opportunity": gap_label,
    },
    "competition": {
        "level": competition_label,
        "density": density.get("level", "Not available"),
        "explanation": "Several similar businesses may already be active in the area; use service and convenience to differentiate." if competition_label == "HIGH" else "Competition exists but remains manageable in the current market view.",
        "pricing_position": "Competitive" if pricing.get("reference_price") else "Not available",
        "advice": "Focus on service quality, product availability and local customer trust." if competition_label in ("HIGH", "MEDIUM") else "Maintain a simple, customer-friendly offer and consistent quality.",
    },
    "monthly_market_conditions": [
        {"Month": pd.Timestamp(2026, month, 1).strftime("%B"), "Market Condition": "Good" if value >= high and value > 0 else "Difficult" if value <= low else "Average", "Advice": "Keep normal stock" if value >= high else "Reduce stock" if value <= low else "Control inventory"}
        for month, value in sorted(monthly_data.items())
    ],
    "risk_summary": [
        {"risk": "Demand Risk", "status": demand_score >= 70 and "LOW" or "MEDIUM", "explanation": "The demand signal is based on available local and category indicators."},
        {"risk": "Competition Risk", "status": competition_label in ("HIGH", "VERY HIGH") and "HIGH" or "MEDIUM", "explanation": "Competitor activity is tracked through observed market signals."},
        {"risk": "Financial Risk", "status": net_profit > 0 and "LOW" or "HIGH", "explanation": "Cash flow and operating costs are compared with the estimated business margin."},
        {"risk": "Loan Risk", "status": monthly_payment <= financials.get("net_profit", 0) and "LOW" or "MEDIUM", "explanation": "Repayment requirements are compared to operating cash flow and affordability."},
        {"risk": "Operational Risk", "status": "MEDIUM", "explanation": "Business operations depend on local supply and service consistency."},
        {"risk": "Supply Chain Risk", "status": supply_risk.get("level", "Needs Verification"), "explanation": supply_risk.get("reason", "Supplier lead-time information is limited.")},
        {"risk": "Seasonal Risk", "status": "MEDIUM", "explanation": "Demand changes with seasonal usage and festive cycles."},
        {"risk": "Buyer Concentration Risk", "status": buyer_risk.get("risk_level", "Needs Verification"), "explanation": buyer_risk.get("reason", "Buyer concentration risk is based on customer revenue concentration.")},
    ],
    "swot": localized_swot(demand_score, competition_score, pricing.get("expected_margin") or 0, project_cost, 90, matrix["opportunity_gap"], supply_risk["level"], buyer_risk["risk_level"]),
    "pricing": {
        "recommended_price": pricing.get("recommended_price") or pricing.get("reference_price"),
        "expected_margin": pricing.get("expected_margin"),
        "pricing_explanation": "Use an observed local reference price and benchmark it against service, convenience and local customer expectations.",
        "sales_channels": [channel["channel"] for channel in channels],
    },
    "business_cost": {
        "Equipment": equipment,
        "Inventory": opening_stock,
        "Shop Setup": shop_setup,
        "Licensing": licence,
        "Working Capital": working_capital,
        "Total Business Cost": project_cost,
    },
    "sih_structure": {
        "your_money": own_money,
        "maximum_project_cost": capacity["maximum_project_cost"],
        "possible_loan": loan_amount,
        "explanation": "Under the 10% / 90% structure, the entrepreneur contributes approximately 10% and the financing agency can provide up to 90%, subject to applicable limits and eligibility.",
    },
    "loan_scheme": {
        "loan_type": scheme["name"],
        "interest_rate": interest_rate,
        "loan_period": tenure_years,
        "moratorium": moratorium_months,
        "possible_loan": loan_amount,
    },
    "repayment": {
        "monthly_payment": monthly_payment,
        "total_interest": repayment.get("total_interest", 0),
        "total_repayment": repayment.get("total_repayment", 0),
        "schedule": [
            {
                "Quarter": row.get("Quarter"),
                "Opening Balance": row.get("Opening Principal"),
                "Interest": row.get("Interest"),
                "Principal Repaid": row.get("Principal Repaid"),
                "Payment": row.get("Total Payment"),
                "Closing Balance": row.get("Closing Principal"),
            }
            for _, row in repayment.get("schedule", pd.DataFrame()).iterrows()
        ],
    },
    "profitability": {
        "expected_sales": financials.get("sales", 0),
        "product_cost": financials.get("product_cost", 0),
        "business_expenses": financials.get("total_expenses", 0),
        "expected_profit": net_profit,
        "profit_margin": financials.get("profit_margin", 0),
        "break_even": financials.get("break_even", "Not available"),
        "loan_affordability": "Affordable" if monthly_payment <= financials.get("net_profit", 0) else "Needs review",
    },
    "what_if": [
        {"Scenario": "Customer volume changes", "Result": "Available in the detailed feasibility analysis."},
        {"Scenario": "Selling price changes", "Result": "Available in the detailed feasibility analysis."},
        {"Scenario": "Expense changes", "Result": "Available in the detailed feasibility analysis."},
    ],
    "decision": decision,
    "ai_advice": advice,
}

try:
    report_bytes = generate_feasibility_pdf(feasibility_report_data)
    st.download_button(
        label="📄 Download Feasibility Report",
        data=report_bytes,
        file_name="BizMetrics_Feasibility_Report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
except Exception as exc:
    st.error("Unable to create the PDF. Please try again.")
    import logging
    logging.exception("Feasibility PDF generation failed: %s", exc)
