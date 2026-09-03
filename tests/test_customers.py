import pytest
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pipeline import analyze_customers

def test_customer_metrics():
    # Setup mock dataframe matching the required columns
    data = pd.DataFrame([
        # Customers
        {"Record_Type": "Receivable", "Customer_ID": "C1", "Customer_Name": "Customer 1", "Registration_Date": "2026-08-01"},
        {"Record_Type": "Receivable", "Customer_ID": "C2", "Customer_Name": "Customer 2", "Registration_Date": "2024-01-01"}, # Old reg -> not new
        {"Record_Type": "Receivable", "Customer_ID": "C3", "Customer_Name": "Customer 3", "Registration_Date": "2024-01-01"}, # Inactive
        
        # Sales for C1 (3 orders, total spent 60k)
        {"Record_Type": "Sale", "Customer_ID": "C1", "Quantity": 1, "Selling_Price": "20000", "Discount_Percent": 0, "Date": "2026-08-15", "Product_ID": "P1"},
        {"Record_Type": "Sale", "Customer_ID": "C1", "Quantity": 2, "Selling_Price": "10000", "Discount_Percent": 0, "Date": "2026-08-20", "Product_ID": "P2"},
        {"Record_Type": "Sale", "Customer_ID": "C1", "Quantity": 1, "Selling_Price": "25000", "Discount_Percent": 20, "Date": "2026-08-28", "Product_ID": "P1"}, # 20k
        
        # Sales for C2 (1 order, total spent 1000)
        {"Record_Type": "Sale", "Customer_ID": "C2", "Quantity": 1, "Selling_Price": "1000", "Discount_Percent": 0, "Date": "2026-08-29", "Product_ID": "P1"},
        
        # Sales for C3 (1 order, long ago)
        {"Record_Type": "Sale", "Customer_ID": "C3", "Quantity": 1, "Selling_Price": "1000", "Discount_Percent": 0, "Date": "2025-01-01", "Product_ID": "P1"},
    ])
    
    res = analyze_customers(data)
    
    assert res['total_customers'] == 3
    
    # C1: 60k spent -> High-Value
    # C2: 1k spent, 1 order -> One-Time
    # C3: Old order -> Inactive
    
    c1 = next(c for c in res['customers'] if c['Customer_ID'] == 'C1')
    c2 = next(c for c in res['customers'] if c['Customer_ID'] == 'C2')
    c3 = next(c for c in res['customers'] if c['Customer_ID'] == 'C3')
    
    assert c1['Total_Spent'] == 60000
    assert c1['Total_Orders'] == 3
    assert c1['AOV'] == 20000
    assert c1['Segment'] == "High-Value Customer" # Priority check for high value even if New
    assert c1['Status'] == "New"
    assert c1['Most_Purchased_Product'] == "P1" # qty 2 (1+1) vs P2 qty 2 (2). Actually P1 and P2 both 2. P1 is first or whatever index max gives.
    
    assert c2['Total_Spent'] == 1000
    assert c2['Total_Orders'] == 1
    assert c2['Segment'] == "One-Time Customer"
    assert c2['Status'] == "Active"
    
    assert c3['Segment'] == "Inactive Customer"
    assert c3['Status'] == "Inactive"
    
def test_empty_customers():
    data = pd.DataFrame()
    res = analyze_customers(data)
    assert res['total_customers'] == 0
    assert res['total_revenue'] == 0
    
def test_unmatched_sales():
    data = pd.DataFrame([
        {"Record_Type": "Receivable", "Customer_ID": "C1"},
        {"Record_Type": "Sale", "Customer_ID": "C2", "Quantity": 1, "Selling_Price": "100"}
    ])
    res = analyze_customers(data)
    # C1 has 0 sales
    assert res['total_customers'] == 1
    assert res['customers'][0]['Total_Orders'] == 0
    assert res['customers'][0]['Total_Spent'] == 0
    assert res['total_revenue'] == 0
