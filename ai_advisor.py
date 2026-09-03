import os
import json
import re
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Try importing google.generativeai
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
import streamlit as st

# Load environment variables from .env file
load_dotenv()

class IndiaMarketCalendar:
    """India-aware calendar intelligence layer for business seasons and festivals."""
    
    # Static festival dates using 'YYYY' as placeholder
    FESTIVALS = {
        "Republic Day": {"date": "{}-01-26", "season": "Winter"},
        "Maha Shivaratri": {"date": "{}-02-14", "season": "Spring"},
        "Holi": {"date": "{}-03-04", "season": "Spring"},
        "Eid ul-Fitr": {"date": "{}-03-20", "season": "Spring"},
        "Baisakhi": {"date": "{}-04-14", "season": "Summer"},
        "Akshaya Tritiya": {"date": "{}-04-20", "season": "Summer"},
        "Independence Day": {"date": "{}-08-15", "season": "Monsoon"},
        "Raksha Bandhan": {"date": "{}-08-28", "season": "Monsoon"},
        "Janmashtami": {"date": "{}-09-04", "season": "Monsoon"},
        "Ganesh Chaturthi": {"date": "{}-09-14", "season": "Monsoon"},
        "Onam": {"date": "{}-09-24", "season": "Monsoon"},
        "Navratri": {"date": "{}-10-10", "season": "Autumn"},
        "Durga Puja": {"date": "{}-10-17", "season": "Autumn"},
        "Dussehra": {"date": "{}-10-20", "season": "Autumn"},
        "Karwa Chauth": {"date": "{}-10-31", "season": "Autumn"},
        "Dhanteras": {"date": "{}-11-08", "season": "Autumn"},
        "Diwali": {"date": "{}-11-10", "season": "Autumn"},
        "Bhai Dooj": {"date": "{}-11-12", "season": "Autumn"},
        "Christmas": {"date": "{}-12-25", "season": "Winter"},
    }
    
    SEASONS = [
        {"name": "Summer", "start": "03-01", "end": "05-31"},
        {"name": "Monsoon", "start": "06-01", "end": "09-15"},
        {"name": "Autumn (Festive)", "start": "09-16", "end": "11-30"},
        {"name": "Winter", "start": "12-01", "end": "02-28"},
    ]

    @classmethod
    def get_upcoming_festivals(cls, current_date, horizon_days=45):
        """Finds festivals within the horizon_days from current_date."""
        upcoming = []
        current_year = current_date.year
        for name, details in cls.FESTIVALS.items():
            fest_date_str = details["date"].format(current_year)
            fest_date = pd.to_datetime(fest_date_str)
            days_until = (fest_date - current_date).days
            if days_until < 0:
                # If passed this year, check next year
                fest_date_str = details["date"].format(current_year + 1)
                fest_date = pd.to_datetime(fest_date_str)
                days_until = (fest_date - current_date).days
                
            if 0 <= days_until <= horizon_days:
                upcoming.append({"name": name, "days_until": days_until, "season": details["season"]})
        # Sort by proximity
        upcoming.sort(key=lambda x: x["days_until"])
        return upcoming

class IntentDetector:
    """Classifies user query intent."""
    CATEGORIES = {
        "FINANCIAL": ["profit", "margin", "revenue", "cogs", "expense", "tax", "cash", "loss", "performing"],
        "SALES": ["sell", "sales", "sold", "discount", "product performance", "growth", "improve sales"],
        "INVENTORY": ["stock", "reorder", "inventory", "sku", "shortage", "overstock", "dead stock", "lead time"],
        "CUSTOMER": ["customer", "target", "retention", "aov", "segment", "buyer", "churn"],
        "RECEIVABLES": ["receivable", "outstanding", "overdue", "collection", "payment", "due", "payments", "owe", "owes", "money"],
        "FORECAST": ["forecast", "predict", "next month", "future demand"],
        "FESTIVAL": ["festival", "diwali", "dussehra", "holi", "season", "prepare for", "holiday"],
        "MARKETING": ["marketing", "campaign", "promote", "increase sales"],
        "RISK": ["risk", "danger", "threat", "weakness"],
        "LOAN": ["loan", "emi", "interest", "principal", "borrow", "debt"],
        "SCHEME": ["scheme", "promotion", "loyalty", "offer", "campaign", "discount"],
        "DATA_QUALITY": ["data quality", "invalid", "missing", "duplicate", "score", "bad data", "dataset"]
    }

    @classmethod
    def detect(cls, query: str):
        query = query.lower()
        matched = []
        for intent, keywords in cls.CATEGORIES.items():
            for kw in keywords:
                if kw in query:
                    matched.append(intent)
                    break
        if not matched:
            return ["GENERAL"]
        return matched

class BizMetricsContextBuilder:
    """Extracts only relevant context for the LLM to optimize performance and token usage."""
    
    @staticmethod
    def build(pipeline_result, intents, current_date):
        context = {"current_date": current_date.strftime("%Y-%m-%d")}
        
        # Festival Context
        upcoming_fests = IndiaMarketCalendar.get_upcoming_festivals(current_date)
        if upcoming_fests:
            context["upcoming_festivals"] = upcoming_fests
            
        business = pipeline_result.get("business", {})
        context["business_profile"] = {
            "name": business.get("Shop_Name"),
            "sector": business.get("sector"),
            "size": business.get("Business_Size")
        }

        if "FINANCIAL" in intents or "GENERAL" in intents or "RISK" in intents:
            fin = pipeline_result.get("financial", {})
            context["financials"] = {
                "revenue": fin.get("total_revenue", 0),
                "gross_profit": fin.get("gross_profit", 0),
                "operating_profit": fin.get("operating_profit", 0),
                "net_profit": fin.get("net_profit", 0),
                "profit_margin": fin.get("profit_margin", 0),
                "total_expenses": fin.get("total_expenses", 0)
            }
            
        if "INVENTORY" in intents or "FESTIVAL" in intents or "GENERAL" in intents or "RISK" in intents:
            inv = pipeline_result.get("inventory", {})
            context["inventory"] = {
                "total_skus": inv.get("total_skus", 0),
                "low_stock_items": inv.get("low_stock_items", 0),
                "dead_stock_value": inv.get("dead_stock_value", 0),
                "fast_moving_skus": inv.get("fast_moving", 0),
                "slow_moving_skus": inv.get("slow_moving", 0),
                "ml_recommendations": inv.get("ml_recommendations", [])[:10] # Top 10 recs to save tokens
            }

        if "CUSTOMER" in intents or "MARKETING" in intents or "FESTIVAL" in intents or "GENERAL" in intents:
            cust = pipeline_result.get("customers", {})
            context["customers"] = {
                "total": cust.get("total_customers", 0),
                "active": cust.get("active_customers", 0),
                "high_value": cust.get("high_value_customers", 0),
                "at_risk": sum(1 for c in cust.get("customers", []) if c.get("status") == "At Risk"),
                "aov": cust.get("aov", 0)
            }

        if "RECEIVABLES" in intents or "RISK" in intents or "GENERAL" in intents:
            rec = pipeline_result.get("receivables", {})
            context["receivables"] = {
                "total_outstanding": rec.get("total_outstanding", 0),
                "overdue": rec.get("overdue", 0)
            }

        if "SALES" in intents or "FORECAST" in intents:
            forecast = pipeline_result.get("forecast", {})
            context["forecast"] = forecast

        if "RISK" in intents or "GENERAL" in intents:
            risk = pipeline_result.get("risks", {})
            context["risks"] = {
                "score": risk.get("score", 100),
                "total_risks": len(risk.get("risk_list", []))
            }
            if risk.get("risk_list"):
                context["risks"]["top_risks"] = risk["risk_list"][:3]
                
        if "LOAN" in intents or "GENERAL" in intents:
            loans = pipeline_result.get("loans", {})
            context["loans"] = {
                "total_principal": loans.get("total_principal", 0),
                "outstanding_principal": loans.get("outstanding_principal", 0),
                "monthly_emi": loans.get("monthly_emi", 0),
                "monthly_interest": loans.get("monthly_interest", 0)
            }
            
        if "SCHEME" in intents or "GENERAL" in intents or "FESTIVAL" in intents:
            schemes = pipeline_result.get("schemes", {})
            context["schemes"] = {
                "govt_eligible": len([s for s in schemes.get("govt_schemes", []) if s.get("eligible")]),
                "promotions": schemes.get("promotions", [])[:3]
            }
            
        if "DATA_QUALITY" in intents or "GENERAL" in intents:
            dq = pipeline_result.get("data_quality", {})
            context["data_quality"] = {
                "score": dq.get("score", 100),
                "missing": dq.get("missing_values", 0),
                "duplicates": dq.get("duplicate_records", 0),
                "invalid": dq.get("invalid_values", 0),
                "recommendations": dq.get("recommendations", [])
            }

        return context

class DeterministicFallback:
    """Rule-based engine when LLM fails or is unavailable."""
    
    @staticmethod
    def generate(query, context, intents):
        insights_list = []
        
        # Financial
        if "FINANCIAL" in intents or "GENERAL" in intents:
            margin = context.get("financials", {}).get("profit_margin", 0)
            if margin < 10:
                insights_list.append({
                    "category": "FINANCIAL",
                    "title": "Low Margin Warning",
                    "finding": f"Net profit margin is currently below 10% ({margin:.1f}%).",
                    "action": "Review operating expenses and discounting strategies.",
                    "priority": "HIGH"
                })

        # Inventory
        if "INVENTORY" in intents or "GENERAL" in intents or "FESTIVAL" in intents:
            low_stock = context.get("inventory", {}).get("low_stock_items", 0)
            if low_stock > 0:
                insights_list.append({
                    "category": "INVENTORY",
                    "title": "Inventory Risk",
                    "finding": f"{low_stock} SKUs are currently below their minimum safety stock.",
                    "action": "Prioritize reordering fast-moving items.",
                    "priority": "HIGH"
                })
                
            fests = context.get("upcoming_festivals", [])
            if fests and ("FESTIVAL" in intents or "GENERAL" in intents):
                fest = fests[0]
                insights_list.append({
                    "category": "MARKET",
                    "title": "Festive Preparation",
                    "finding": f"{fest['name']} is approaching in {fest['days_until']} days.",
                    "action": "Ensure fast-moving product inventory covers the supplier lead time.",
                    "priority": "MEDIUM"
                })

        # Receivables
        if "RECEIVABLES" in intents or "GENERAL" in intents:
            overdue = context.get("receivables", {}).get("overdue", 0)
            total_out = context.get("receivables", {}).get("total_outstanding", 0)
            if overdue > 0:
                insights_list.append({
                    "category": "RECEIVABLES",
                    "title": "Cashflow Risk",
                    "finding": f"You have ₹{overdue:,.0f} in overdue receivables out of ₹{total_out:,.0f} total outstanding.",
                    "action": "Prioritize following up with overdue accounts.",
                    "priority": "HIGH"
                })
            elif total_out > 0:
                insights_list.append({
                    "category": "RECEIVABLES",
                    "title": "Receivables Status",
                    "finding": f"You have ₹{total_out:,.0f} in outstanding receivables, but none are currently marked overdue.",
                    "action": "Monitor outstanding payments.",
                    "priority": "LOW"
                })

        # Customers
        if "CUSTOMER" in intents or "GENERAL" in intents:
            at_risk = context.get("customers", {}).get("at_risk", 0)
            high_value = context.get("customers", {}).get("high_value", 0)
            if at_risk > 0:
                insights_list.append({
                    "category": "CUSTOMER",
                    "title": "Customer Retention",
                    "finding": f"You have {at_risk} customers at risk of churning.",
                    "action": "Consider a targeted re-engagement campaign.",
                    "priority": "MEDIUM"
                })
            if high_value > 0:
                insights_list.append({
                    "category": "CUSTOMER",
                    "title": "Customer Target",
                    "finding": "High-value customers represent a significant portion of revenue.",
                    "action": "Target them with exclusive loyalty offers.",
                    "priority": "LOW"
                })

        # Risk
        if "RISK" in intents:
            risk_score = context.get("risks", {}).get("score", 100)
            if risk_score < 50:
                insights_list.append({
                    "category": "RISK",
                    "title": "High Business Risk",
                    "finding": f"Your risk score is {risk_score}/100.",
                    "action": "Immediate attention required on high-severity items.",
                    "priority": "HIGH"
                })
                
        # Loans
        if "LOAN" in intents:
            out_prin = context.get("loans", {}).get("outstanding_principal", 0)
            emi = context.get("loans", {}).get("monthly_emi", 0)
            if out_prin > 0:
                insights_list.append({
                    "category": "FINANCIAL",
                    "title": "Loan Status",
                    "finding": f"You have ₹{out_prin:,.0f} outstanding with a monthly EMI burden of ₹{emi:,.0f}.",
                    "action": "Ensure cash flow covers upcoming EMIs.",
                    "priority": "MEDIUM"
                })
                
        # Schemes
        if "SCHEME" in intents:
            promos = context.get("schemes", {}).get("promotions", [])
            if promos:
                insights_list.append({
                    "category": "MARKET",
                    "title": "Promotions Available",
                    "finding": f"Recommended scheme: '{promos[0].get('Scheme Name')}'.",
                    "action": f"Run this scheme targeting {promos[0].get('Target Customers')}.",
                    "priority": "MEDIUM"
                })
                
        # Data Quality
        if "DATA_QUALITY" in intents:
            dq_score = context.get("data_quality", {}).get("score", 100)
            if dq_score < 70:
                insights_list.append({
                    "category": "DATA QUALITY",
                    "title": "Data Quality Warning",
                    "finding": f"Your data quality score is {dq_score}/100.",
                    "action": "Fix missing or invalid values to ensure accurate insights.",
                    "priority": "HIGH"
                })

        # Formatting as JSON for consistent UI consumption
        return {
            "impact": "Operational stability",
            "source": "FALLBACK",
            "recommendations": insights_list
        }

def get_gemini_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None

def call_llm(query, context, chat_history):
    """Wrapper to call Gemini API if available, else fallback."""
    api_key = get_gemini_api_key()
    if not GENAI_AVAILABLE or not api_key:
        return None
        
    genai.configure(api_key=api_key)
    
    # Use flash for faster responses, but allow fallback
    model_name = "gemini-1.5-flash"
    
    system_prompt = f"""You are the BizMetrics AI Advisor, an expert India-aware business intelligence engine.
You must analyze the provided data context to answer the user's query.
Never make up numerical benefits, fake historical sales, or generic chatbot answers.
You must return your response STRICTLY as a valid JSON object matching exactly this schema:
{{
  "impact": "Expected business impact summary for all recommendations",
  "recommendations": [
    {{
      "category": "FINANCIAL | INVENTORY | SALES | CUSTOMER | RECEIVABLES | MARKET | RISK | DATA QUALITY",
      "title": "Short title of the recommendation",
      "finding": "What you found based strictly on data.",
      "action": "Specific recommended action.",
      "priority": "HIGH | MEDIUM | LOW"
    }}
  ]
}}

BUSINESS CONTEXT:
{json.dumps(context, indent=2, default=str)}

CHAT HISTORY:
{json.dumps(chat_history[-4:], indent=2, default=str)}
"""

    try:
        model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
        response = model.generate_content(query)
        
        # Parse JSON
        resp_text = response.text.strip()
        if resp_text.startswith("```json"):
            resp_text = resp_text[7:-3].strip()
        elif resp_text.startswith("```"):
            resp_text = resp_text[3:-3].strip()
            
        return json.loads(resp_text)
    except Exception as e:
        print(f"LLM Error: {e}")
        return None

def generate_business_advice(user_query, pipeline_result, current_date=None, chat_history=None):
    """
    Main entry point for the AI Intelligence layer.
    """
    if current_date is None:
        current_date = pd.to_datetime('today')
        
    if chat_history is None:
        chat_history = []

    intents = IntentDetector.detect(user_query)
    context = BizMetricsContextBuilder.build(pipeline_result, intents, current_date)
    
    response = call_llm(user_query, context, chat_history)
    
    if response:
        response['source'] = 'LLM'
    else:
        # Deterministic Fallback
        response = DeterministicFallback.generate(user_query, context, intents)
        response['source'] = 'FALLBACK'
        
    return response

if __name__ == "__main__":
    # Simple test
    print(IntentDetector.detect("Why did my profit fall?"))
    print(IndiaMarketCalendar.get_upcoming_festivals(pd.to_datetime("2026-08-30")))
