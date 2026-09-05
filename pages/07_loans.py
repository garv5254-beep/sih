import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from components.sidebar import render_sidebar
from components.header import render_header
from components.cards import kpi_card
from utils.formatting import format_currency
from utils.theme import apply_theme
from utils.sih_finance import build_quarterly_schedule, calculate_emi, financing_capacity, select_scheme

st.set_page_config(page_title="BizMetrics - Loan Simulator", layout="wide")
apply_theme()
render_sidebar()
render_header("Loan Eligibility & EMI Simulator", "Enter your required loan amount and compare available loan policies under the SIH Framework.")

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
# 2. MARGIN & PROJECT COST (SIH 10/90 STRUCTURE)
# -------------------------------------------------------------
st.markdown("### ⚙️ SIH Project Cost & Margin Setup")
col_m1, col_m2 = st.columns(2)
with col_m1:
    available_margin = st.number_input("Available Margin Capital (₹)", min_value=0.0, value=50000.0, step=5000.0)

capacity = financing_capacity(available_margin)
max_project_cost = capacity["maximum_project_cost"]
max_loan_amount = capacity["maximum_loan"]

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
col_k1.metric("Available Margin Capital", format_currency(available_margin))
col_k2.metric("Maximum Project Cost", format_currency(max_project_cost))
col_k3.metric("Required Margin Contribution", format_currency(capacity["required_margin"]))
col_k4.metric("Maximum Loan Amount (90%)", format_currency(max_loan_amount))

# -------------------------------------------------------------
# 3. INTERACTIVE LOAN CONTROLS
# -------------------------------------------------------------
st.markdown("---")
st.markdown("### 💵 Interactive Loan Simulator")
col_in1, col_in2, col_in3, col_in4 = st.columns(4)

with col_in1:
    proposed_project_cost = st.number_input("Proposed Project Cost (₹)", min_value=0.0, value=max_project_cost, step=10000.0)
    desired_loan = st.number_input("Loan Amount (₹)", min_value=0.0, value=float(proposed_project_cost * 0.90), step=5000.0)

if proposed_project_cost > max_project_cost:
    st.error(f"⚠ Proposed Project Cost ({format_currency(proposed_project_cost)}) exceeds your Maximum Project Cost capacity ({format_currency(max_project_cost)}).")
    st.stop()
elif proposed_project_cost > 5000000:
    st.error("⚠ Proposed Project Cost exceeds ₹50 Lakh. This is unsupported under the current SIH financial structure.")
    st.stop()

# Automatic Scheme Selection
scheme = select_scheme(proposed_project_cost)
sih_scheme = scheme["name"]
if not scheme["supported"]:
    st.error(scheme["reason"])
    st.stop()
def_interest = scheme["interest_rate"]
def_tenure = scheme["tenure_years"]
def_moratorium = scheme["moratorium_months"]
if desired_loan > max_loan_amount:
    st.error("Loan amount cannot exceed the available 90% financing capacity.")
    st.stop()
    
st.session_state["selected_sih_scheme"] = sih_scheme

with col_in2:
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=float(def_interest), step=0.5)
with col_in3:
    tenure_years = st.number_input("Tenure (Years)", min_value=1.0, value=float(def_tenure), step=1.0)
with col_in4:
    moratorium_months = st.number_input("Moratorium (Months)", min_value=0, max_value=int(tenure_years*12), value=int(def_moratorium), step=1)

tenure_months = int(tenure_years * 12)

# -------------------------------------------------------------
# 4. EMI & QUARTERLY REPAYMENT ENGINE
# -------------------------------------------------------------
emi_equivalent = calculate_emi(desired_loan, interest_rate, tenure_months)
repayment = build_quarterly_schedule(desired_loan, interest_rate, tenure_months, moratorium_months)
sched_df = repayment["schedule"]
q_payment = repayment["quarterly_payment"]
total_q_interest = repayment.get("total_interest", 0.0)
total_q_principal = repayment.get("total_principal", 0.0)
total_repayment = repayment.get("total_repayment", 0.0)
balance = repayment.get("final_balance", 0.0)
is_valid = repayment.get("valid", False)

# -------------------------------------------------------------
# 6. KPI SUMMARY
# -------------------------------------------------------------
st.markdown("### 📊 Loan Summary")
c1, c2, c3, c4 = st.columns(4)
with c1: kpi_card("Requested Loan Amount", format_currency(desired_loan))
with c2: kpi_card("Monthly EMI Equivalent", format_currency(emi_equivalent))
with c3: kpi_card("Quarterly Repayment", format_currency(q_payment) if q_payment > 0 else "N/A")
with c4: kpi_card("Total Repayment", format_currency(total_repayment))

c5, c6, c7, c8 = st.columns(4)
with c5: kpi_card("Interest Rate", f"{interest_rate}%")
with c6: kpi_card("Tenure", f"{tenure_months} months")
with c7: kpi_card("Moratorium", f"{moratorium_months} months")
with c8: kpi_card("Total Interest", format_currency(total_q_interest))

if is_valid:
    st.success("✓ Repayment Schedule Valid")
else:
    st.error("⚠ Calculation Validation Required")

# -------------------------------------------------------------
# 7. VISUALIZATIONS
# -------------------------------------------------------------
st.markdown("---")
st.markdown("### 📈 Visual Repayment Timeline & Analysis")
v_col1, v_col2 = st.columns(2)

with v_col1:
    fig_line = go.Figure()
    if not sched_df.empty:
        fig_line.add_trace(go.Scatter(x=sched_df['Quarter'], y=sched_df['Closing Principal'], mode='lines+markers', name='Outstanding Principal', line=dict(color='#9B493C', width=3)))
    fig_line.update_layout(title="Outstanding Principal Over Time", xaxis_title="Quarter", yaxis_title="Balance (₹)", plot_bgcolor="#EDE5D0", paper_bgcolor="#FFFFFF", font=dict(color="#292622"))
    st.plotly_chart(fig_line, use_container_width=True)

with v_col2:
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=['Total Breakup'], y=[desired_loan], name='Principal', marker_color='#9B493C'))
    fig_bar.add_trace(go.Bar(x=['Total Breakup'], y=[total_q_interest], name='Total Interest', marker_color='#78805B'))
    fig_bar.update_layout(title="Interest vs Principal Analysis", barmode='stack', plot_bgcolor="#EDE5D0", paper_bgcolor="#FFFFFF", font=dict(color="#292622"))
    st.plotly_chart(fig_bar, use_container_width=True)

# -------------------------------------------------------------
# 8. SCHEME COMPARISON
# -------------------------------------------------------------
st.markdown("---")
st.markdown("### 🏛️ Scheme Comparison")
col_pol1, col_pol2 = st.columns(2)

with col_pol1:
    st.markdown("#### Micro Finance")
    if sih_scheme == "Micro Finance":
        st.success("**Selected Scheme (Project Cost ≤ ₹1.40 Lakh)**")
    else:
        st.markdown("**Not Selected**")
    st.markdown(f"- **Interest Rate:** 6.5%\n- **Tenure:** 3 years\n- **Moratorium:** 3 months")

with col_pol2:
    st.markdown("#### Term Loan")
    if sih_scheme == "Term Loan":
        st.success("**Selected Scheme (Project Cost > ₹1.40 Lakh)**")
    else:
        st.markdown("**Not Selected**")
    st.markdown(f"- **Interest Rate:** 8%\n- **Tenure:** 7 years\n- **Moratorium:** 6 months")

comparison_rows = []
for comparison_name, comparison_rate, comparison_years, comparison_moratorium in [
    ("Micro Finance", 6.5, 3, 3),
    ("Term Loan", 8.0, 7, 6),
]:
    comparison_schedule = build_quarterly_schedule(
        desired_loan, comparison_rate, comparison_years * 12, comparison_moratorium
    )
    comparison_rows.append({
        "Scheme": comparison_name,
        "Status": "Selected" if comparison_name == sih_scheme else "Reference",
        "Interest": f"{comparison_rate}%",
        "Tenure": f"{comparison_years} years",
        "Moratorium": f"{comparison_moratorium} months",
        "Monthly EMI Equivalent": format_currency(calculate_emi(desired_loan, comparison_rate, comparison_years * 12)),
        "Total Interest": format_currency(comparison_schedule.get("total_interest", 0)),
        "Total Repayment": format_currency(comparison_schedule.get("total_repayment", 0)),
    })
st.dataframe(pd.DataFrame(comparison_rows), hide_index=True, width="stretch")

# -------------------------------------------------------------
# 9. AFFORDABILITY CHECK & EXISTING DEBT
# -------------------------------------------------------------
st.markdown("---")
st.markdown("### 💰 Affordability Analysis")

col_aff1, col_aff2 = st.columns(2)

combined_emi = existing_emi + emi_equivalent
monthly_cash = monthly_net_profit

if monthly_cash > 0:
    foir = (combined_emi / monthly_cash) * 100
else:
    foir = 100.0 if combined_emi > 0 else 0.0

available_cash_after_emi = monthly_cash - combined_emi

with col_aff1:
    st.markdown("**Business Income Profile (Monthly Average)**")
    st.markdown(f"- **Revenue:** {format_currency(monthly_business_income)}")
    st.markdown(f"- **Operating Expenses & COGS (Excl. Principal):** {format_currency(monthly_operating_expenses)}")
    st.markdown(f"- **Net Profit (Cash Available):** {format_currency(monthly_cash)}")
    
    if foir < 40:
        st.success("✅ **LOW BURDEN**: Affordable repayment relative to projected profit.")
    elif foir < 65:
        st.warning("⚠️ **MEDIUM BURDEN**: Repayment is manageable but requires monitoring.")
    else:
        st.error("🚨 **HIGH BURDEN**: Repayment may place significant pressure on business cash flow.")

with col_aff2:
    st.markdown("**Debt Impact**")
    if existing_principal > 0:
        st.markdown(f"- **Existing Outstanding Principal:** {format_currency(existing_principal)}")
        st.markdown(f"- **Existing Monthly EMI:** {format_currency(existing_emi)}")
    else:
        st.markdown("- No existing loan records found in the dataset.")
        
    st.markdown(f"- **Proposed EMI Equivalent:** {format_currency(emi_equivalent)}")
    st.markdown(f"- **Combined Monthly EMI:** {format_currency(combined_emi)}")
    st.markdown(f"- **Estimated Available Cash (After EMI):** {format_currency(available_cash_after_emi)}")
    st.markdown(f"- **Repayment Burden (EMI/Profit):** {foir:.1f}%")

# -------------------------------------------------------------
# 10. QUARTERLY REPAYMENT SCHEDULE
# -------------------------------------------------------------
st.markdown("---")
st.markdown("### 📅 Full Quarterly Repayment Schedule")
st.info("**MODELING ASSUMPTION:** Interest accrual during the moratorium is a modeling assumption used for repayment simulation; it is not presented as an explicit SIH rule.")

if desired_loan > 0 and tenure_months > 0:
    display_df = sched_df.copy()
    if not display_df.empty:
        for col in ["Opening Principal", "Interest", "Principal Repaid", "Total Payment", "Closing Principal", "Cumulative Interest", "Cumulative Repayment"]:
            display_df[col] = display_df[col].apply(lambda x: format_currency(x))
            
        st.dataframe(display_df, hide_index=True, width="stretch")
else:
    st.info("Enter a valid loan amount and tenure to generate the repayment schedule.")
