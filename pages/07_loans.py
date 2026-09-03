import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from utils.formatting import format_currency
from utils.theme import apply_theme

st.set_page_config(page_title="BizMetrics - Loan Simulator", layout="wide")
apply_theme()
render_sidebar()
render_header("Loan Eligibility & EMI Simulator", "Enter your required loan amount and compare available loan policies.")

if "pipeline_result" not in st.session_state:
    st.error("BizMetrics dataset could not be found.")
    st.stop()

result = st.session_state["pipeline_result"]
loans_data = result.get("loans", {})
financials = result.get("financials", {})

# -------------------------------------------------------------
# 1. EXTRACT EXISTING BUSINESS DATA
# -------------------------------------------------------------
total_revenue = financials.get('total_revenue', 0)
net_profit = financials.get('net_profit', 0)
total_expenses = financials.get('total_expenses', 0)

monthly_business_income = total_revenue / 12 if total_revenue else 0
monthly_operating_expenses = total_expenses / 12 if total_expenses else 0
monthly_net_profit = net_profit / 12 if net_profit else 0

existing_principal = loans_data.get('outstanding_principal', 0)
existing_emi = loans_data.get('monthly_emi', 0)


# -------------------------------------------------------------
# 2. POLICY DEFINITIONS (DEMO RULES)
# -------------------------------------------------------------
# Micro Loan: Max 20% of annual revenue, max 36 months
micro_limit = total_revenue * 0.20
micro_max_tenure = 36

# Term Loan: Max 50% of annual revenue or 3x net profit (whichever higher), up to 60 months
term_limit = max(total_revenue * 0.50, net_profit * 3)
term_max_tenure = 60

# -------------------------------------------------------------
# 3. INTERACTIVE CONTROLS
# -------------------------------------------------------------
st.markdown("### ⚙️ Simulator Controls")
col_in1, col_in2, col_in3 = st.columns(3)
with col_in1:
    desired_loan = st.number_input("Desired Loan Amount (₹)", min_value=0.0, value=100000.0, step=10000.0)
with col_in2:
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=10.0, step=0.5)
with col_in3:
    tenure_months = st.selectbox("Tenure", options=[6, 12, 18, 24, 36, 48, 60], index=4)  # Default 36 months

# -------------------------------------------------------------
# 4. EMI & REPAYMENT CALCULATION
# -------------------------------------------------------------
def calculate_emi(p, r_annual, n):
    if p <= 0 or n <= 0:
        return 0, 0, 0
    if r_annual == 0:
        return p / n, 0, p
    r = (r_annual / 100) / 12
    emi = p * r * ((1 + r)**n) / (((1 + r)**n) - 1)
    total_repayment = emi * n
    total_interest = total_repayment - p
    return emi, total_interest, total_repayment

emi, total_interest, total_repayment = calculate_emi(desired_loan, interest_rate, tenure_months)

# -------------------------------------------------------------
# 5. ELIGIBILITY EVALUATION
# -------------------------------------------------------------
is_micro_eligible = desired_loan <= micro_limit and tenure_months <= micro_max_tenure
is_term_eligible = desired_loan <= term_limit and tenure_months <= term_max_tenure

def get_eligibility_status(is_eligible, limit, max_tenure):
    if is_eligible:
        return "ELIGIBLE"
    elif desired_loan > limit:
        return f"Requested amount exceeds the calculated eligible limit by {format_currency(desired_loan - limit)}."
    elif tenure_months > max_tenure:
        return f"Requested tenure exceeds the maximum allowed ({max_tenure} months) for this policy."
    return "NOT ELIGIBLE"

micro_status = get_eligibility_status(is_micro_eligible, micro_limit, micro_max_tenure)
term_status = get_eligibility_status(is_term_eligible, term_limit, term_max_tenure)

# -------------------------------------------------------------
# 6. KPI SUMMARY
# -------------------------------------------------------------
st.markdown("### 📊 Loan Summary")
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: kpi_card("Requested Amount", format_currency(desired_loan))
with c2: kpi_card("Monthly EMI", format_currency(emi))
with c3: kpi_card("Total Interest", format_currency(total_interest))
with c4: kpi_card("Total Repayment", format_currency(total_repayment))
with c5: kpi_card("Interest Rate", f"{interest_rate}%")
with c6: kpi_card("Tenure", f"{tenure_months} months")


# -------------------------------------------------------------
# 7. POLICY COMPARISON & RECOMMENDATION
# -------------------------------------------------------------
st.markdown("---")
col_pol1, col_pol2, col_pol3 = st.columns([2, 2, 1.5])

with col_pol1:
    st.markdown("#### Micro Loan Policy")
    if is_micro_eligible:
        st.success(f"**Status:** {micro_status}")
    else:
        st.error(f"**Status:** {micro_status}")
    
    st.markdown(f"""
    - **Eligible Limit:** {format_currency(micro_limit)}
    - **Maximum Tenure:** {micro_max_tenure} months
    - **Estimated EMI:** {format_currency(emi) if tenure_months <= micro_max_tenure else "N/A (Tenure Exceeded)"}
    """)

with col_pol2:
    st.markdown("#### Term Loan Policy")
    if is_term_eligible:
        st.success(f"**Status:** {term_status}")
    else:
        st.error(f"**Status:** {term_status}")
        
    st.markdown(f"""
    - **Eligible Limit:** {format_currency(term_limit)}
    - **Available Tenure:** Up to {term_max_tenure} months
    - **Estimated EMI:** {format_currency(emi) if tenure_months <= term_max_tenure else "N/A (Tenure Exceeded)"}
    """)

with col_pol3:
    st.markdown("#### 💡 Recommendation")
    
    if desired_loan == 0:
        st.info("Enter a loan amount to get a recommendation.")
    elif is_micro_eligible:
        st.info("**Micro Loan**\n\nRequested amount is within the Micro Loan eligibility limit and offers favorable terms for smaller requirements.")
    elif is_term_eligible:
        st.info("**Term Loan**\n\nRequested amount exceeds the Micro Loan limit but falls within the Term Loan eligibility limit.")
    else:
        st.warning("**No Eligible Option**\n\nRequested amount exceeds all calculated eligibility limits.")


# -------------------------------------------------------------
# 8. AFFORDABILITY CHECK & EXISTING DEBT
# -------------------------------------------------------------
st.markdown("---")
st.markdown("### 💰 EMI Affordability & Debt Impact")

col_aff1, col_aff2 = st.columns(2)

combined_emi = existing_emi + emi
monthly_cash = monthly_net_profit

if monthly_cash > 0:
    foir = (combined_emi / monthly_cash) * 100
else:
    foir = 100.0 if combined_emi > 0 else 0.0

available_cash_after_emi = monthly_cash - combined_emi

with col_aff1:
    st.markdown("**Business Income Profile (Monthly Average)**")
    st.markdown(f"- **Revenue:** {format_currency(monthly_business_income)}")
    st.markdown(f"- **Operating Expenses & COGS:** {format_currency(monthly_operating_expenses)}")
    st.markdown(f"- **Net Profit (Cash Available):** {format_currency(monthly_cash)}")
    
    if foir < 40:
        st.success("✅ **Comfortable Affordability**")
    elif foir < 65:
        st.warning("⚠️ **Moderate Burden**")
    else:
        st.error("🚨 **High Burden**")

with col_aff2:
    st.markdown("**Debt Impact**")
    if existing_principal > 0:
        st.markdown(f"- **Existing Outstanding Principal:** {format_currency(existing_principal)}")
        st.markdown(f"- **Existing Monthly EMI:** {format_currency(existing_emi)}")
    else:
        st.markdown("- No existing loan records found in the dataset.")
        
    st.markdown(f"- **Proposed EMI:** {format_currency(emi)}")
    st.markdown(f"- **Combined Monthly EMI:** {format_currency(combined_emi)}")
    st.markdown(f"- **Estimated Available Cash (After EMI):** {format_currency(available_cash_after_emi)}")
    st.markdown(f"- **EMI-to-Profit Ratio:** {foir:.1f}%")


# -------------------------------------------------------------
# 9. AMORTIZATION SCHEDULE
# -------------------------------------------------------------
st.markdown("---")
st.markdown("### 📅 Full Repayment Schedule")

if desired_loan > 0 and tenure_months > 0:
    schedule = []
    balance = desired_loan
    r_monthly = (interest_rate / 100) / 12
    
    for month in range(1, tenure_months + 1):
        interest_payment = balance * r_monthly
        principal_payment = emi - interest_payment
        
        # Handle final rounding
        if month == tenure_months:
            principal_payment = balance
            emi_adjusted = principal_payment + interest_payment
            balance = 0.0
        else:
            emi_adjusted = emi
            balance -= principal_payment
            
        schedule.append({
            "Month": month,
            "Opening Balance": balance + principal_payment if month < tenure_months else balance + principal_payment,
            "EMI": emi_adjusted,
            "Interest": interest_payment,
            "Principal": principal_payment,
            "Closing Balance": max(0, balance)
        })
        
    sched_df = pd.DataFrame(schedule)
    
    for col in ["Opening Balance", "EMI", "Interest", "Principal", "Closing Balance"]:
        sched_df[col] = sched_df[col].apply(lambda x: format_currency(x))
        
    st.dataframe(sched_df, hide_index=True, width="stretch")
else:
    st.info("Enter a loan amount to generate the repayment schedule.")
