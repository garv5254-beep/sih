import pandas as pd
import numpy as np
from inventory_ml import InventoryML, generate_inventory_recommendations

def load_master_csv(csv_file):
    """
    1. Load Data
    Reads the single master CSV.
    """
    try:
        df = pd.read_csv(csv_file)
        print(f"Loaded {csv_file} successfully.")
        return df
    except Exception as e:
        print(f"Error loading master CSV: {e}")
        return pd.DataFrame()

def normalize_sku(value):
    if pd.isna(value):
        return "UNKNOWN_SKU"
    return str(value).strip().upper().replace(" ", "")

def validate_and_clean(data):
    """
    2. Validate
    Handles missing values, dates/amounts, and duplicate data.
    """
    if data is None or data.empty:
        return data
        
    print("Validating and cleaning data...")
    
    # Normalize SKU / Product_ID
    if 'Product_ID' in data.columns:
        data['Product_ID'] = data['Product_ID'].apply(normalize_sku)
    elif 'SKU' in data.columns:
        data['SKU'] = data['SKU'].apply(normalize_sku)
        data['Product_ID'] = data['SKU'] # Standardize to Product_ID
    
    product_col = "Product_Name"
    if product_col in data.columns:
        data[product_col] = (
            data[product_col]
            .fillna("")
            .astype(str)
            .str.strip()
        )
        data["Display_Product"] = data.apply(
            lambda row: row[product_col] if row[product_col] != "" else (row.get('Product_ID', 'Unnamed Product')),
            axis=1
        )
    else:
        data["Display_Product"] = data.get('Product_ID', 'Unnamed Product')
        
    # Clean string amounts (e.g. ₹100,000 -> 100000, 51.7% -> 51.7)
    for col in data.columns:
        if data[col].dtype == object:
            if any(x in col.lower() for x in ['amount', 'price', 'cost', 'emi', 'principal', 'margin', 'rate', 'discount']):
                # Remove ₹, ,, %, and handle Lakh/Crore if they appear
                cleaned = data[col].astype(str).str.replace('₹', '', regex=False)\
                                                .str.replace(',', '', regex=False)\
                                                .str.replace('%', '', regex=False)\
                                                .str.strip()
                                                
                # Basic conversion, ignoring Lakh/Crore text conversion since we didn't find any, but if we did, we would handle it here.
                # Just coercion to float is safe for what we have.
                data[col] = pd.to_numeric(cleaned, errors='coerce')
    
    return data

def analyze_business(data):
    """
    3. Business Profile Engine
    """
    biz_df = data[data['Record_Type'] == 'Business']
    if biz_df.empty:
        return {"Shop_Name": "Unknown", "Owner_Name": "Unknown"}
    
    # Just take the first row for the business profile
    row = biz_df.iloc[0]
    return {
        "Shop_Name": row.get("Shop_Name", "Unknown"),
        "Owner_Name": row.get("Owner_Name", "Unknown"),
        "Sector": row.get("Sector", "Unknown"),
        "Business_Size": row.get("Business_Size", "Unknown"),
        "Status": "Active"
    }

def calculate_financials(data):
    """
    4. Financial Engine
    """
    if data.empty or 'Record_Type' not in data.columns:
        sales_df = pd.DataFrame()
        expenses_df = pd.DataFrame()
        inv_df = pd.DataFrame()
        loan_df = pd.DataFrame()
    else:
        sales_df = data[data['Record_Type'] == 'Sale'].copy()
        expenses_df = data[data['Record_Type'] == 'Expense'].copy()
        inv_df = data[data['Record_Type'] == 'Inventory'].copy()
        loan_df = data[data['Record_Type'] == 'Loan'].copy()
    
    # Pre-compute product costs and selling prices
    product_costs = {}
    product_selling_prices = {}
    for _, row in inv_df.iterrows():
        pid = row.get('Product_ID') or row.get('SKU')
        if pd.isna(pid): continue
        pid = normalize_sku(pid)
        cost_str = str(row.get('Purchase_Price', '0')).replace('₹', '').replace(',', '').strip()
        product_costs[pid] = pd.to_numeric(cost_str, errors='coerce')
        sell_str = str(row.get('Selling_Price', '0')).replace('₹', '').replace(',', '').strip()
        product_selling_prices[pid] = pd.to_numeric(sell_str, errors='coerce')
        
    revenue = 0
    cogs = 0
    
    # Calculate Revenue and exact COGS
    if not sales_df.empty:
        sales_df['Quantity_Num'] = pd.to_numeric(sales_df['Quantity'], errors='coerce').fillna(0)
        
        # Calculate revenue strictly from Qty * Selling_Price * (1 - discount/100)
        if 'Discount_Percent' in sales_df.columns:
            sales_df['Discount_Num'] = pd.to_numeric(sales_df['Discount_Percent'], errors='coerce').fillna(0)
        else:
            sales_df['Discount_Num'] = 0
            
        for _, row in sales_df.iterrows():
            pid = normalize_sku(row.get('Product_ID', ''))
            qty = row['Quantity_Num']
            discount = row['Discount_Num']
            
            sell_price = product_selling_prices.get(pid, 0)
            cost_price = product_costs.get(pid, 0)
            
            calculated_amount = qty * sell_price * (1 - (discount / 100.0))
            
            revenue += calculated_amount
            cogs += qty * cost_price
            
    # Operating Expenses (Rent, Wages, etc.)
    # Exclude loan principal/interest if mistakenly added as expense
    if 'Amount' in expenses_df.columns:
        categories_to_exclude = ['loan', 'interest', 'inventory', 'repayment', 'principal']
        valid_expenses = expenses_df[
            ~expenses_df.get('Category', pd.Series(dtype=str)).astype(str).str.lower().str.contains('|'.join(categories_to_exclude), na=False)
        ]
        expenses = pd.to_numeric(
            valid_expenses['Amount'].astype(str).str.replace('₹', '').str.replace(',', '').str.strip(), errors='coerce'
        ).sum()
    else:
        expenses = 0
        
    gross_profit = revenue - cogs
    operating_profit = gross_profit - expenses
    
    # Interest Expense
    interest_expense = 0
    if not loan_df.empty:
        if 'Outstanding_Principal' in loan_df.columns and 'Interest_Rate' in loan_df.columns:
            for _, row in loan_df.iterrows():
                principal = pd.to_numeric(str(row['Outstanding_Principal']).replace('₹', '').replace(',', '').strip(), errors='coerce')
                rate = pd.to_numeric(str(row['Interest_Rate']).replace('%', '').strip(), errors='coerce')
                if pd.notna(principal) and pd.notna(rate):
                    # Monthly interest assumption for the demo
                    interest_expense += principal * (rate / 100.0) / 12.0
                    
    profit_before_tax = operating_profit - interest_expense
    
    # Taxes (Demo assumption: 5% flat on positive profit)
    taxes = max(profit_before_tax, 0) * 0.05
    
    net_profit = profit_before_tax - taxes
    
    # If revenue is exactly zero, we handle None or 0 gracefully
    gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
    net_margin = (net_profit / revenue * 100) if revenue > 0 else 0
    
    return {
        "total_revenue": revenue,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "total_expenses": expenses,
        "operating_profit": operating_profit,
        "interest_expense": interest_expense,
        "profit_before_tax": profit_before_tax,
        "taxes": taxes,
        "net_profit": net_profit,
        "gross_margin": gross_margin,
        "profit_margin": net_margin,
        "cash_flow": net_profit
    }

def analyze_receivables(data):
    """
    5. Customer Engine / Receivables
    """
    rec_df = data[data['Record_Type'] == 'Receivable']
    
    if 'Outstanding_Amount' in rec_df.columns:
        outstanding = pd.to_numeric(rec_df['Outstanding_Amount'], errors='coerce')
        total_outstanding = outstanding.sum()
        
        # Assume overdue if status is Attention or Overdue, or days overdue > 0
        overdue = 0
        if 'Payment_Status' in rec_df.columns:
            overdue = outstanding[rec_df['Payment_Status'].isin(['Attention', 'Overdue'])].sum()
        elif 'Days_Overdue' in rec_df.columns:
            overdue = outstanding[pd.to_numeric(rec_df['Days_Overdue'], errors='coerce') > 0].sum()
    else:
        total_outstanding = 0
        overdue = 0
        
    return {
        "total_outstanding": total_outstanding,
        "overdue": overdue,
        "days_sales_outstanding": 0 # Needs total credit sales to calculate
    }

def analyze_payables(data):
    """
    6. Vendor Engine / Payables
    """
    pay_df = data[data['Record_Type'] == 'Payable']
    if 'Outstanding_Amount' in pay_df.columns:
        total_payables = pd.to_numeric(pay_df['Outstanding_Amount'], errors='coerce').sum()
    else:
        total_payables = 0
        
    return {
        "total_payables": total_payables,
        "overdue_payables": 0 # Simplified
    }

def analyze_inventory(data):
    """
    7. Inventory Engine
    """
    inv_df = data[data['Record_Type'] == 'Inventory']
    
    total_items = len(inv_df)
    low_stock = 0
    dead_stock_val = 0
    
def analyze_inventory(df):
    inv = df[df['Record_Type'] == 'Inventory'].copy()
    sales_df = df[df['Record_Type'] == 'Sale'].copy()
    
    if inv.empty:
        return {"total_skus": 0, "low_stock_items": 0, "dead_stock_value": 0, "items": [], "ml_recommendations": []}
        
    cur_stock = pd.to_numeric(inv['Current_Stock'], errors='coerce').fillna(0)
    min_stock = pd.to_numeric(inv['Minimum_Stock'], errors='coerce').fillna(0)
    max_stock = pd.to_numeric(inv['Maximum_Stock'], errors='coerce').fillna(100)
    price = pd.to_numeric(inv['Purchase_Price'].astype(str).str.replace('₹', '').str.replace(',', ''), errors='coerce').fillna(0)
    
    total_val = (cur_stock * price).sum()
    low_stock = cur_stock <= min_stock
    
    dead_stock_mask = cur_stock > max_stock
    dead_stock_val = (cur_stock[dead_stock_mask] * price[dead_stock_mask]).sum()
    
    # Run ML Engine
    try:
        # Pre-process sales df quantities
        if not sales_df.empty:
            sales_df['Quantity'] = pd.to_numeric(sales_df['Quantity'], errors='coerce').fillna(0)
        
        ml_engine = InventoryML()
        predictions, diagnostics = ml_engine.predict_demand(sales_df, inv)
        recs_df = generate_inventory_recommendations(inv, sales_df, predictions, diagnostics)
        ml_recs = recs_df.to_dict('records')
        
        # Calculate new KPIs based on ML classifications
        fast_moving = len(recs_df[recs_df['Classification'] == 'FAST MOVING'])
        slow_moving = len(recs_df[recs_df['Classification'] == 'SLOW MOVING'])
        dead_stock = len(recs_df[recs_df['Classification'] == 'DEAD STOCK'])
        avg_turnover = recs_df['Sales_30_Days'].sum() / len(recs_df) if len(recs_df) > 0 else 0
        avg_days = recs_df['Days_Remaining'].replace(999, np.nan).mean()
        
    except Exception as e:
        print(f"ML Engine error: {e}")
        ml_recs = []
        diagnostics = {}
        fast_moving, slow_moving, dead_stock, avg_turnover, avg_days = 0, 0, 0, 0, 0
    
    # Enhance the original items payload
    items = inv.to_dict('records')
    for item in items:
        item['stock_status'] = 'Low Stock' if pd.to_numeric(item.get('Current_Stock', 0), errors='coerce') <= pd.to_numeric(item.get('Minimum_Stock', 0), errors='coerce') else 'Healthy'
    
    return {
        "total_skus": len(inv),
        "total_value": total_val,
        "low_stock_items": low_stock.sum(),
        "dead_stock_value": dead_stock_val,
        "fast_moving": fast_moving,
        "slow_moving": slow_moving,
        "dead_stock_count": dead_stock,
        "avg_turnover": avg_turnover,
        "avg_days_remaining": avg_days,
        "items": items,
        "ml_recommendations": ml_recs,
        "ml_diagnostics": diagnostics
    }

def forecast_demand(data):
    """
    8. Forecasting Engine
    """
    # Simple heuristic forecasting based on historical sales
    sales_df = data[data['Record_Type'] == 'Sale']
    if 'Total_Amount' in sales_df.columns:
        hist_revenue = pd.to_numeric(sales_df['Total_Amount'], errors='coerce').sum()
    else:
        hist_revenue = 0
        
    # Assume a 10% month-over-month growth for the forecast
    return {
        "next_month_projected_sales": hist_revenue * 1.10,
        "upcoming_festivals": ["Diwali", "Dussehra"],
        "recommended_stock_increase": "15%"
    }

def detect_risks(financial, receivables, payables, inventory, forecast):
    """
    9. Risk Engine
    """
    risks = []
    
    if financial.get("profit_margin", 0) < 10:
        risks.append({"risk": "Low Margin", "severity": "MEDIUM", "action": "Review pricing strategy"})
        
    if receivables.get("overdue", 0) > 5000:
        risks.append({"risk": "High Overdue Receivables", "severity": "HIGH", "action": "Follow up on payments immediately"})
        
    if inventory.get("low_stock_items", 0) > 5:
        risks.append({"risk": "Inventory Shortage", "severity": "MEDIUM", "action": "Reorder top moving items"})
        
    return risks

def check_scheme_eligibility(business, financial):
    """
    10. Scheme Engine
    """
    schemes = [
        {"scheme_name": "MUDRA Yojana", "eligible": True, "missing_docs": ["Updated GST Return", "Business Pan Card"]},
        {"scheme_name": "PMEGP", "eligible": business.get("Sector", "") == "Manufacturing", "reason": "Manufacturing sector only"}
    ]
    return schemes

def generate_ai_advice(context):
    """
    11. AI Advisor
    """
    advice = (
        f"Based on the analysis, {context['business'].get('Shop_Name')} has a revenue of Rs. {context['financial'].get('total_revenue'):,.0f} "
        f"and a profit margin of {context['financial'].get('profit_margin'):.2f}%. "
    )
    
    overdue = context['receivables'].get('overdue', 0)
    if overdue > 0:
        advice += f"However, there are Rs. {overdue:,.0f} in overdue receivables requiring immediate attention. "
        
    advice += "With Diwali approaching, it is recommended to increase inventory for high-demand items by 15%. "
    return advice

def calculate_health_score(financial, receivables, payables, inventory, forecast):
    """
    12. Health Score Engine
    """
    score = 100
    
    if financial.get("profit_margin", 0) < 20:
        score -= 10
    if receivables.get("overdue", 0) > 5000:
        score -= 10
    if inventory.get("low_stock_items", 0) > 0:
        score -= 10
    if inventory.get("dead_stock_value", 0) > 5000:
        score -= 10
    if payables.get("total_payables", 0) > 30000:
        score -= 10
        
    return max(0, min(100, score))

def run_pipeline(data):
    """
    Main orchestration pipeline that runs all engines in sequence.
    """
    print("Starting Unified Rural Business Pipeline...")
    
    data = validate_and_clean(data)
    
    business = analyze_business(data)
    financial = calculate_financials(data)
    receivables = analyze_receivables(data)
    payables = analyze_payables(data)
    inventory = analyze_inventory(data)
    forecast = forecast_demand(data)
    
    risks = detect_risks(financial, receivables, payables, inventory, forecast)
    schemes = check_scheme_eligibility(business, financial)
    health_score = calculate_health_score(financial, receivables, payables, inventory, forecast)
    
    context = {
        "business": business,
        "financial": financial,
        "receivables": receivables,
        "payables": payables,
        "inventory": inventory,
        "forecast": forecast,
        "risks": risks,
        "schemes": schemes,
        "health_score": health_score
    }
    
    advice = generate_ai_advice(context)
    
    result = {
        "business": business,
        "financial": financial,
        "receivables": receivables,
        "payables": payables,
        "inventory": inventory,
        "forecast": forecast,
        "risks": risks,
        "schemes": schemes,
        "health_score": health_score,
        "advice": advice
    }
    
    print("Pipeline execution complete.")
    return result

if __name__ == "__main__":
    df = load_master_csv("rural_business_master_data.csv")
    res = run_pipeline(df)
    print(res)
