import pytest
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pipeline import calculate_financials

def test_financial_reconciliation():
    data = pd.DataFrame([
        {"Record_Type": "Sale", "Quantity": 2, "Product_ID": "PROD1", "Discount_Percent": 0},
        {"Record_Type": "Inventory", "Product_ID": "PROD1", "Purchase_Price": 30000, "Selling_Price": 50000},
        {"Record_Type": "Expense", "Amount": 20000, "Category": "Rent"},
        {"Record_Type": "Loan", "Outstanding_Principal": 500000, "Interest_Rate": "12%"}
    ])
    res = calculate_financials(data)
    assert res['total_revenue'] == 100000
    assert res['cogs'] == 60000
    assert res['gross_profit'] == 40000
    assert res['total_expenses'] == 20000
    assert res['operating_profit'] == 20000
    assert res['interest_expense'] == 5000
    assert res['profit_before_tax'] == 15000
    assert res['taxes'] == 15000 * 0.05
    assert res['net_profit'] == 15000 - (15000 * 0.05)

def test_zero_revenue():
    data = pd.DataFrame([
        {"Record_Type": "Sale", "Quantity": 0, "Product_ID": "PROD1", "Discount_Percent": 0},
        {"Record_Type": "Inventory", "Product_ID": "PROD1", "Purchase_Price": 30000, "Selling_Price": 50000}
    ])
    res = calculate_financials(data)
    assert res['total_revenue'] == 0
    assert res['profit_margin'] == 0
    assert res['gross_margin'] == 0

def test_loan_principal_exclusion():
    data = pd.DataFrame([
        {"Record_Type": "Sale", "Quantity": 1, "Product_ID": "PROD1", "Discount_Percent": 0},
        {"Record_Type": "Inventory", "Product_ID": "PROD1", "Purchase_Price": 0, "Selling_Price": 100000},
        {"Record_Type": "Expense", "Amount": 10000, "Category": "Loan Repayment"},
        {"Record_Type": "Expense", "Amount": 5000, "Category": "Principal"},
        {"Record_Type": "Expense", "Amount": 2000, "Category": "Inventory purchase"},
        {"Record_Type": "Loan", "Outstanding_Principal": 100000, "Interest_Rate": "12%"}
    ])
    res = calculate_financials(data)
    assert res['total_revenue'] == 100000
    assert res['total_expenses'] == 0 
    assert res['interest_expense'] == 1000

def test_edge_cases():
    # Empty dataset
    assert calculate_financials(pd.DataFrame())['total_revenue'] == 0

    # Missing discount, missing price, duplicate transaction
    data = pd.DataFrame([
        {"Record_Type": "Sale", "Quantity": 2, "Product_ID": "PROD1"},
        {"Record_Type": "Sale", "Quantity": 2, "Product_ID": "PROD1"}, # Duplicate
        {"Record_Type": "Inventory", "Product_ID": "PROD1", "Selling_Price": 100},
        {"Record_Type": "Sale", "Quantity": 1, "Product_ID": "PROD2"}, # Missing price in inventory
        {"Record_Type": "Inventory", "Product_ID": "PROD3", "Selling_Price": 100}, # Missing SKU in sales
        # Negative profit
        {"Record_Type": "Expense", "Amount": 1000, "Category": "Misc"}
    ])
    res = calculate_financials(data)
    # Revenue = 4 * 100 = 400
    assert res['total_revenue'] == 400
    assert res['cogs'] == 0
    assert res['total_expenses'] == 1000
    assert res['operating_profit'] == -600
    assert res['taxes'] == 0 # No negative tax
    assert res['net_profit'] == -600
