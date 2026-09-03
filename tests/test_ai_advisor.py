import pytest
import pandas as pd
from ai_advisor import IntentDetector, IndiaMarketCalendar, DeterministicFallback

def test_intent_detection():
    # Financial
    assert "FINANCIAL" in IntentDetector.detect("Why did my profit fall?")
    # Inventory
    assert "INVENTORY" in IntentDetector.detect("What should I reorder?")
    # Receivables
    assert "RECEIVABLES" in IntentDetector.detect("Who has outstanding payments?")
    # Festival
    assert "FESTIVAL" in IntentDetector.detect("Prepare for the next festival.")
    # Sales
    assert "SALES" in IntentDetector.detect("How to improve sales?")
    # Customers
    assert "CUSTOMER" in IntentDetector.detect("Which customers should I target?")
    # General Fallback
    assert "GENERAL" in IntentDetector.detect("Hello!")

def test_festival_proximity():
    # Anchor date: August 30, 2026
    current_date = pd.to_datetime("2026-08-30")
    upcoming = IndiaMarketCalendar.get_upcoming_festivals(current_date, horizon_days=45)
    
    # Should find Janmashtami (Sept 4), Ganesh Chaturthi (Sept 14), Onam (Sept 24), Navratri (Oct 10)
    names = [f["name"] for f in upcoming]
    assert "Janmashtami" in names
    assert "Ganesh Chaturthi" in names
    assert "Onam" in names
    assert "Navratri" in names
    
    # Check days logic
    janmashtami = next(f for f in upcoming if f["name"] == "Janmashtami")
    assert janmashtami["days_until"] == 5

def test_deterministic_fallback():
    context = {
        "financials": {"profit_margin": 8.0},
        "inventory": {"low_stock_items": 3},
        "upcoming_festivals": [{"name": "Diwali", "days_until": 15, "season": "Autumn"}],
        "receivables": {"overdue": 10000},
        "customers": {"at_risk": 5}
    }
    
    # Financial Intent
    res = DeterministicFallback.generate("margin", context, ["FINANCIAL"])
    assert "Low Margin Warning" in res["recommendation"]
    
    # Inventory & Festival Intent
    res = DeterministicFallback.generate("stock", context, ["INVENTORY", "FESTIVAL"])
    assert "Inventory Risk" in res["recommendation"]
    assert "Festive Preparation" in res["recommendation"]
    assert "Diwali" in res["recommendation"]
    
    # Receivables Intent
    res = DeterministicFallback.generate("payments", context, ["RECEIVABLES"])
    assert "Cashflow Risk" in res["recommendation"]
    
    # Customer Intent
    res = DeterministicFallback.generate("customers", context, ["CUSTOMER"])
    assert "Customer Retention" in res["recommendation"]
