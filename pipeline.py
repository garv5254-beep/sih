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
    keywords = ['amount', 'price', 'cost', 'emi', 'principal', 'margin', 'rate', 'discount']
    amount_cols = [c for c in data.columns if data[c].dtype == object and any(k in c.lower() for k in keywords)]
    
    for col in amount_cols:
        # Regex replace is faster than chained string replaces
        cleaned = data[col].astype(str).str.replace(r'[₹,%]', '', regex=True).str.strip()
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
            
        # Vectorized revenue and COGS calculation
        sales_df['Normalized_PID'] = sales_df.get('Product_ID', '').apply(normalize_sku)
        
        sales_df['Sell_Price'] = sales_df['Normalized_PID'].map(product_selling_prices).fillna(0)
        sales_df['Cost_Price'] = sales_df['Normalized_PID'].map(product_costs).fillna(0)
        
        revenue_series = sales_df['Quantity_Num'] * sales_df['Sell_Price'] * (1 - (sales_df['Discount_Num'] / 100.0))
        cogs_series = sales_df['Quantity_Num'] * sales_df['Cost_Price']
        
        revenue += revenue_series.sum()
        cogs += cogs_series.sum()
            
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

def detect_risks(financial, receivables, payables, inventory, forecast, customers=None):
    """
    9. Risk Engine
    """
    risks = []
    score = 100
    
    # Financial Risk
    margin = financial.get("profit_margin", 0)
    if margin < 10:
        score -= 20
        risks.append({"category": "Financial", "risk": "Low Margin", "severity": "HIGH", "action": "Review pricing strategy", "reason": f"declining profit margin ({margin:.1f}%)"})
    elif margin < 20:
        score -= 10
        risks.append({"category": "Financial", "risk": "Suboptimal Margin", "severity": "MEDIUM", "action": "Optimize costs", "reason": f"margin is at {margin:.1f}%"})
        
    # Receivables Risk
    overdue = receivables.get("overdue", 0)
    if overdue > 50000:
        score -= 25
        risks.append({"category": "Receivables/Credit", "risk": "High Overdue Receivables", "severity": "HIGH", "action": "Follow up on payments immediately", "reason": f"high outstanding receivables (₹{overdue:,.2f})"})
    elif overdue > 5000:
        score -= 10
        risks.append({"category": "Receivables/Credit", "risk": "Moderate Overdue Receivables", "severity": "MEDIUM", "action": "Send payment reminders", "reason": f"overdue payments (₹{overdue:,.2f})"})
        
    # Inventory Risk
    low_stock = inventory.get("low_stock_items", 0)
    if low_stock > 10:
        score -= 15
        risks.append({"category": "Inventory", "risk": "Severe Inventory Shortage", "severity": "HIGH", "action": "Urgent restock needed", "reason": f"{low_stock} low-stock SKUs"})
    elif low_stock > 5:
        score -= 5
        risks.append({"category": "Inventory", "risk": "Inventory Shortage", "severity": "MEDIUM", "action": "Reorder top moving items", "reason": f"{low_stock} low-stock SKUs"})
        
    dead_stock_val = inventory.get("dead_stock_value", 0)
    if dead_stock_val > 20000:
        score -= 10
        risks.append({"category": "Inventory", "risk": "Excessive Dead Stock", "severity": "MEDIUM", "action": "Liquidate old inventory", "reason": f"excessive inventory value (₹{dead_stock_val:,.2f})"})

    # Customer Risk
    if customers:
        active = customers.get("active_customers", 0)
        total_rev = customers.get("total_revenue", 0)
        if active > 0 and customers.get("high_value_customers", 0) > 0:
            top_customers = [c for c in customers.get("customers", []) if c.get("Segment") == "High-Value Customer"]
            if top_customers:
                top_cust_rev = sum([c.get("Total_Spent", 0) for c in top_customers])
                if total_rev > 0 and (top_cust_rev / total_rev) > 0.5:
                    score -= 15
                    risks.append({"category": "Customer", "risk": "Customer Concentration", "severity": "HIGH", "action": "Diversify customer base", "reason": "over 50% revenue from top customers"})
    
    # Payables / Operational Risk
    payables_total = payables.get("total_payables", 0)
    cash = financial.get("cash_flow", 0)
    if payables_total > (cash * 2) and cash > 0:
        score -= 15
        risks.append({"category": "Operational", "risk": "High Payables Burden", "severity": "HIGH", "action": "Renegotiate payment terms", "reason": "payables exceed 2x cash flow"})
        
    return {
        "score": max(0, min(100, score)),
        "risk_list": risks
    }

def analyze_loans(data):
    """
    Loan Engine
    """
    loan_df = data[data['Record_Type'] == 'Loan'].copy()
    
    total_principal = 0
    outstanding_principal = 0
    monthly_emi = 0
    total_interest_paid = 0
    loans = []
    
    if not loan_df.empty:
        for _, row in loan_df.iterrows():
            def clean_amt(val):
                return pd.to_numeric(str(val).replace('₹', '').replace(',', '').strip(), errors='coerce') if pd.notna(val) else 0

            principal = clean_amt(row.get('Principal_Amount', 0))
            outstanding = clean_amt(row.get('Outstanding_Principal', 0))
            emi = clean_amt(row.get('Monthly_EMI', 0))
            rate = pd.to_numeric(str(row.get('Interest_Rate', 0)).replace('%', '').strip(), errors='coerce') if pd.notna(row.get('Interest_Rate')) else 0
            
            total_principal += principal
            outstanding_principal += outstanding
            monthly_emi += emi
            
            # Rough estimation of total interest paid so far based on principal reduction
            principal_paid = principal - outstanding
            if principal_paid > 0 and emi > 0:
                # Approximate number of months paid
                months_paid = principal_paid / (emi - (outstanding * (rate / 100.0) / 12.0))
                if months_paid > 0:
                     total_interest_paid += (emi * months_paid) - principal_paid
            
            loans.append({
                "Loan_Name": row.get('Loan_Type', 'Unknown Loan'),
                "Lender": row.get('Loan_Provider', 'Unknown'),
                "Principal": principal,
                "Outstanding": outstanding,
                "Interest_Rate": rate,
                "Monthly_Payment": emi,
                "Start_Date": str(row.get('Start_Date', 'N/A')),
                "End_Date": "N/A", # Needs tenure
                "Status": "Active" if outstanding > 0 else "Closed"
            })
            
    # Calculate monthly interest burden on current outstanding
    monthly_interest = 0
    for l in loans:
        monthly_interest += l['Outstanding'] * (l['Interest_Rate'] / 100.0) / 12.0
            
    return {
        "total_principal": total_principal,
        "outstanding_principal": outstanding_principal,
        "monthly_interest": monthly_interest,
        "total_interest_paid": total_interest_paid,
        "monthly_emi": monthly_emi,
        "active_loans": len([l for l in loans if l['Status'] == 'Active']),
        "loans": loans
    }

def analyze_data_quality(data):
    """
    Data Quality Engine
    """
    if data is None or data.empty:
        return {"score": 0, "total_records": 0, "columns": [], "recommendations": []}
        
    total_records = len(data)
    recommendations = set()
    cols_data = []
    
    missing_points = 0
    invalid_points = 0
    duplicate_rows = data.duplicated().sum()
    
    if duplicate_rows > 0:
        recommendations.add("Remove duplicate transactions")
        missing_points += (duplicate_rows / total_records) * 50
    
    for col in data.columns:
        missing = data[col].isna().sum()
        missing_pct = (missing / total_records) * 100
        invalid = 0
        
        # Check specific conditions
        if col in ['Purchase_Price', 'Selling_Price', 'Quantity', 'Amount']:
            # Try to convert to numeric to find negatives
            nums = pd.to_numeric(data[col].astype(str).str.replace(r'[₹,%]', '', regex=True).str.strip(), errors='coerce')
            invalid = (nums < 0).sum()
            if invalid > 0:
                invalid_points += (invalid / total_records) * 100
                recommendations.add(f"Validate negative values in {col}")
                
        if col == 'Customer_ID' and missing > 0:
            recommendations.add("Fill missing customer IDs")
        if col in ['Product_ID', 'SKU'] and missing > 0:
            recommendations.add("Fill missing product/SKU IDs")
        if col == 'Date':
            invalid_dates = pd.to_datetime(data[col], errors='coerce').isna().sum() - missing
            if invalid_dates > 0:
                invalid += invalid_dates
                invalid_points += (invalid_dates / total_records) * 100
                recommendations.add("Correct invalid dates")
                
        if missing > 0:
            missing_points += missing_pct * 0.5
            
        quality = "Good"
        if missing_pct > 20 or invalid > (total_records * 0.05):
            quality = "Critical"
        elif missing_pct > 5 or invalid > 0:
            quality = "Warning"
            
        cols_data.append({
            "Column": col,
            "Missing": missing,
            "Missing_Pct": missing_pct,
            "Invalid": invalid,
            "Unique": data[col].nunique(),
            "Quality": quality
        })
        
    score = max(0, min(100, 100 - missing_points - invalid_points))
    
    return {
        "score": score,
        "total_records": total_records,
        "missing_values": data.isna().sum().sum(),
        "duplicate_records": duplicate_rows,
        "invalid_values": sum([c['Invalid'] for c in cols_data]),
        "columns_analyzed": len(data.columns),
        "columns": cols_data,
        "recommendations": list(recommendations)
    }

def check_scheme_eligibility(business, financial, customers=None):
    """
    10. Scheme Engine
    """
    schemes = [
        {"scheme_name": "MUDRA Yojana", "eligible": True, "missing_docs": ["Updated GST Return", "Business Pan Card"], "type": "GOVT"},
        {"scheme_name": "PMEGP", "eligible": business.get("Sector", "") == "Manufacturing", "reason": "Manufacturing sector only", "type": "GOVT"}
    ]
    
    # Business promotional schemes
    promotions = []
    
    # Data-driven recommendations
    if customers:
        high_val = customers.get("high_value_customers", 0)
        if high_val > 0:
            promotions.append({
                "Scheme Name": "Bulk Purchase Scheme",
                "Target Customers": "High-volume customers",
                "Target Products": "Top selling products",
                "Reason": "Customers with high historical order quantities may respond to volume incentives.",
                "Recommended Period": "End of month",
                "Expected Objective": "Increase order volume",
                "Priority": "High",
                "Type": "DATA-DRIVEN"
            })
            
        inactive = customers.get("total_customers", 0) - customers.get("active_customers", 0)
        if inactive > 10:
            promotions.append({
                "Scheme Name": "Win-back Campaign",
                "Target Customers": "Inactive Customers",
                "Target Products": "Standard inventory",
                "Reason": f"You have {inactive} inactive customers who haven't purchased recently.",
                "Recommended Period": "Immediate",
                "Expected Objective": "Customer reactivation",
                "Priority": "Medium",
                "Type": "DATA-DRIVEN"
            })
            
    # Market-based recommendations
    promotions.append({
        "Scheme Name": "Diwali Special Offer",
        "Target Customers": "All retail customers",
        "Target Products": "Electronics / High-margin items",
        "Reason": "Major Indian festival driving significant retail sales.",
        "Recommended Period": "Pre-Diwali week",
        "Expected Objective": "Boost seasonal revenue",
        "Priority": "High",
        "Type": "MARKET-BASED"
    })
    
    return {
        "govt_schemes": schemes,
        "promotions": promotions
    }



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

def analyze_customers(data):
    """
    13. Customer Engine (CRM)
    """
    if data.empty or 'Record_Type' not in data.columns:
        return {"total_customers": 0, "active_customers": 0, "new_customers": 0, "high_value_customers": 0, "total_revenue": 0, "aov": 0, "customers": []}

    sales_df = data[data['Record_Type'] == 'Sale'].copy()
    cust_df = data[data['Record_Type'] == 'Receivable'].copy() # We mapped Customers to Receivable in consolidate script
    
    if cust_df.empty:
        return {"total_customers": 0, "active_customers": 0, "new_customers": 0, "high_value_customers": 0, "total_revenue": 0, "aov": 0, "customers": []}

    # Clean sales amounts
    if not sales_df.empty:
        sales_df['Quantity_Num'] = pd.to_numeric(sales_df['Quantity'], errors='coerce').fillna(0)
        
        # Pre-compute product selling prices for accurate revenue (we can also just use Total_Amount if it's there and valid, but prompt asked for strict math)
        # However, the strict math is Qty * SP * (1-Discount/100).
        # Let's extract numbers from 'Selling_Price' and 'Total_Amount'
        def extract_num(val):
            return pd.to_numeric(str(val).replace('₹', '').replace(',', '').strip(), errors='coerce')
        
        sales_df['Selling_Price_Num'] = sales_df['Selling_Price'].apply(extract_num).fillna(0)
        
        if 'Discount_Percent' in sales_df.columns:
            sales_df['Discount_Num'] = pd.to_numeric(sales_df['Discount_Percent'], errors='coerce').fillna(0)
        else:
            sales_df['Discount_Num'] = 0

        sales_df['Revenue'] = sales_df['Quantity_Num'] * sales_df['Selling_Price_Num'] * (1 - (sales_df['Discount_Num'] / 100.0))
        if 'Date' in sales_df.columns:
            sales_df['Date_Parsed'] = pd.to_datetime(sales_df['Date'], errors='coerce')
        else:
            sales_df['Date_Parsed'] = pd.NaT
    else:
        sales_df = pd.DataFrame(columns=['Customer_ID', 'Revenue', 'Quantity_Num', 'Date_Parsed', 'Product_ID'])

    customers_list = []
    total_customers = len(cust_df)
    active_customers = 0
    new_customers = 0
    high_value_customers = 0
    total_revenue = 0
    total_orders_global = 0

    now = pd.to_datetime('2026-08-30')

    # Optimize by pre-aggregating sales
    sales_agg = {}
    if not sales_df.empty and 'Customer_ID' in sales_df.columns:
        agg_df = sales_df.groupby('Customer_ID').agg(
            orders=('Revenue', 'size'),
            spent=('Revenue', 'sum'),
            qty_purchased=('Quantity_Num', 'sum'),
            first_purchase=('Date_Parsed', 'min'),
            last_purchase=('Date_Parsed', 'max')
        ).reset_index()
        
        # Most purchased product
        if 'Product_ID' in sales_df.columns:
            prod_counts = sales_df.groupby(['Customer_ID', 'Product_ID'])['Quantity_Num'].sum().reset_index()
            idx = prod_counts.groupby('Customer_ID')['Quantity_Num'].idxmax()
            most_purchased_df = prod_counts.loc[idx].set_index('Customer_ID')['Product_ID']
            agg_df['most_purchased'] = agg_df['Customer_ID'].map(most_purchased_df)
        
        sales_agg = agg_df.set_index('Customer_ID').to_dict(orient='index')

    for _, c_row in cust_df.iterrows():
        c_id = c_row.get('Customer_ID', 'UNKNOWN')
        c_name = c_row.get('Customer_Name', 'Unknown')
        c_business = c_row.get('Business_Name', 'Unknown')
        c_phone = c_row.get('Contact_Number', 'N/A')
        c_email = c_row.get('Email', 'N/A')
        c_city = c_row.get('City', 'Unknown')
        c_type = c_row.get('Customer_Type', 'Unknown')
        c_reg = pd.to_datetime(c_row.get('Registration_Date', None), errors='coerce')
        c_rating = c_row.get('Customer_Rating', 0)
        
        c_stats = sales_agg.get(c_id, {})
        orders = c_stats.get('orders', 0)
        spent = c_stats.get('spent', 0)
        qty_purchased = c_stats.get('qty_purchased', 0)
        first_purchase = c_stats.get('first_purchase', pd.NaT)
        last_purchase = c_stats.get('last_purchase', pd.NaT)
        most_purchased = c_stats.get('most_purchased', "N/A")
        if pd.isna(most_purchased):
            most_purchased = "N/A"
            
        aov = (spent / orders) if orders > 0 else 0
            
        # Segmentation Logic
        days_since_last = (now - last_purchase).days if pd.notna(last_purchase) else 999
        days_since_reg = (now - c_reg).days if pd.notna(c_reg) else 999
        
        if orders == 0:
            segment = "Inactive Customer"
            status = "Inactive"
        elif days_since_last > 60:
            segment = "Inactive Customer"
            status = "Inactive"
        elif orders == 1:
            segment = "One-Time Customer"
            status = "Active"
        elif days_since_last > 30:
            segment = "At-Risk Customer"
            status = "At Risk"
        elif spent > 50000:
            segment = "High-Value Customer"
            status = "Active"
        else:
            segment = "Regular Customer"
            status = "Active"
            
        if days_since_reg <= 30:
            status = "New"
            if segment not in ["High-Value Customer"]:
                segment = "New Customer"

        if status in ["Active", "New"]:
            active_customers += 1
        if segment == "New Customer":
            new_customers += 1
        if segment == "High-Value Customer":
            high_value_customers += 1
            
        total_revenue += spent
        total_orders_global += orders
        
        customers_list.append({
            "Customer_ID": c_id,
            "Customer_Name": c_name,
            "Business_Name": c_business,
            "Phone": c_phone,
            "Email": c_email,
            "City": c_city,
            "Customer_Type": c_type,
            "Registration_Date": c_reg.strftime('%Y-%m-%d') if pd.notna(c_reg) else "N/A",
            "Customer_Rating": c_rating,
            "Total_Orders": orders,
            "Total_Spent": spent,
            "AOV": aov,
            "Total_Quantity": qty_purchased,
            "First_Purchase_Date": first_purchase.strftime('%Y-%m-%d') if pd.notna(first_purchase) else "N/A",
            "Last_Purchase_Date": last_purchase.strftime('%Y-%m-%d') if pd.notna(last_purchase) else "N/A",
            "Most_Purchased_Product": most_purchased,
            "Segment": segment,
            "Status": status
        })

    # Sort customers by spent descending
    customers_list.sort(key=lambda x: x['Total_Spent'], reverse=True)

    return {
        "total_customers": total_customers,
        "active_customers": active_customers,
        "new_customers": new_customers,
        "high_value_customers": high_value_customers,
        "total_revenue": total_revenue,
        "total_orders": total_orders_global,
        "aov": (total_revenue / total_orders_global) if total_orders_global > 0 else 0,
        "customers": customers_list
    }

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
    customers = analyze_customers(data)
    
    risks = detect_risks(financial, receivables, payables, inventory, forecast, customers)
    schemes = check_scheme_eligibility(business, financial, customers)
    loans = analyze_loans(data)
    data_quality = analyze_data_quality(data)
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
        "loans": loans,
        "data_quality": data_quality,
        "health_score": health_score
    }
    

    result = {
        "business": business,
        "financial": financial,
        "receivables": receivables,
        "payables": payables,
        "inventory": inventory,
        "forecast": forecast,
        "customers": customers,
        "risks": risks,
        "schemes": schemes,
        "loans": loans,
        "data_quality": data_quality,
        "health_score": health_score
    }
    
    print("Pipeline execution complete.")
    return result

if __name__ == "__main__":
    df = load_master_csv("rural_business_master_data.csv")
    res = run_pipeline(df)
    print(res)
