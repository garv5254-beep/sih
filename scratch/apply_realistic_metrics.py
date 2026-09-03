import pandas as pd
import random
import os
from datetime import datetime, timedelta

def clean_curr(x):
    if isinstance(x, str):
        return x.replace('₹', '').replace(',', '').replace(' ', '').strip()
    return x

def apply_realistic_metrics():
    # 1. READ NEW INVENTORY
    os.system('copy BizMetrics_realistic_inventory_12_SKUs.csv 02_products_inventory.csv')
    products = pd.read_csv('02_products_inventory.csv')
    products['Selling_Price_Num'] = products['Selling_Price'].apply(clean_curr).astype(float)
    
    # 2. GENERATE SALES (Target: ~4,85,000)
    customers = [f'CUST{i:03d}' for i in range(1, 37)] # 36 customers
    start_date = datetime(2026, 8, 1)
    
    sales_data = []
    total_sales = 0
    sale_idx = 1
    
    while total_sales < 485000:
        prod = products.sample(1).iloc[0]
        sp = prod['Selling_Price_Num']
        # to not overshoot heavily
        max_qty = int(min(50, (485000 - total_sales) / sp + 1))
        qty = random.randint(1, max(1, max_qty))
        
        amount = qty * sp
        mode = random.choices(['Cash', 'UPI', 'Credit'], weights=[0.5, 0.3, 0.2])[0]
        
        if mode == 'Credit':
            status = 'Pending'
            credit = amount
        else:
            status = 'Completed'
            credit = 0
            
        date_str = (start_date + timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
        
        sales_data.append({
            'Sale_ID': f'SALE{sale_idx:03d}',
            'Business_ID': 'BUS001',
            'Date': date_str,
            'Customer_ID': random.choice(customers),
            'Product_ID': prod['Product_ID'],
            'Quantity': qty,
            'Selling_Price': f"₹ {int(sp)}",
            'Discount_Percent': 0,
            'Total_Amount': f"₹ {int(amount)}",
            'Payment_Mode': mode,
            'Payment_Status': status,
            'Credit_Amount': f"₹ {int(credit)}" if credit > 0 else '0',
            'Notes': 'Standard Sale'
        })
        
        total_sales += amount
        sale_idx += 1
        
    df_sales = pd.DataFrame(sales_data)
    df_sales.to_csv('03_sales_transactions.csv', index=False)

    # 3. EXPENSES (Revenue = 485000, Net Profit = 130000 -> Expenses = 355000)
    # Fixed = 155000, Variable = 200000
    expenses_data = [
        ('Rent', 60000, 'Fixed', 'Yes'),
        ('Salary', 95000, 'Fixed', 'Yes'),
        ('Electricity', 30000, 'Variable', 'No'),
        ('Transport', 50000, 'Variable', 'No'),
        ('Maintenance', 45000, 'Variable', 'No'),
        ('Marketing', 25000, 'Variable', 'No'),
        ('Miscellaneous', 50000, 'Variable', 'No')
    ]
    records = []
    for i, (cat, amt, vtype, is_fixed) in enumerate(expenses_data):
        date_str = (start_date + timedelta(days=random.randint(0, 20))).strftime('%Y-%m-%d')
        records.append({
            'Expense_ID': f'EXP{i+1:03d}',
            'Business_ID': 'BUS001',
            'Date': date_str,
            'Category': cat,
            'Description': f'{cat} Expense',
            'Amount': f"₹ {amt}",
            'Payment_Status': 'Paid',
            'Is_Fixed': is_fixed,
            'Notes': 'Standard monthly'
        })
    pd.DataFrame(records).to_csv('04_expenses.csv', index=False)

    # 4. RECEIVABLES (Target: 58,200)
    # Target overdue: 6200
    records = []
    # Make two records to split the 58,200, one overdue by 6200, another 52000 not overdue
    records.append({'Customer_ID': 'CUST001', 'Customer_Name': 'Alpha Build', 'Contact_Number': '9876543201', 'Customer_Type': 'Contractor', 'Total_Credit_Sales': '₹ 150000', 'Total_Payments_Received': '₹ 91800', 'Outstanding_Amount': '₹ 58200', 'Last_Payment_Date': '2026-08-20', 'Days_Overdue': 12, 'Payment_Status': 'Overdue'}) # Wait, just make 6200 overdue, so Days_overdue=12 for a specific record.
    records = [
        {'Customer_ID': 'CUST001', 'Customer_Name': 'Alpha Build', 'Contact_Number': '9876543201', 'Customer_Type': 'Contractor', 'Total_Credit_Sales': '₹ 100000', 'Total_Payments_Received': '₹ 93800', 'Outstanding_Amount': '₹ 6200', 'Last_Payment_Date': '2026-08-20', 'Days_Overdue': 12, 'Payment_Status': 'Overdue'},
        {'Customer_ID': 'CUST002', 'Customer_Name': 'Beta Builders', 'Contact_Number': '9876543202', 'Customer_Type': 'Contractor', 'Total_Credit_Sales': '₹ 200000', 'Total_Payments_Received': '₹ 148000', 'Outstanding_Amount': '₹ 52000', 'Last_Payment_Date': '2026-08-25', 'Days_Overdue': 0, 'Payment_Status': 'Pending'}
    ]
    pd.DataFrame(records).to_csv('05_customers_receivables.csv', index=False)

    # 5. PAYABLES (Target: 39,200)
    records = [
        {'Vendor_ID': 'SUPP001', 'Vendor_Name': 'Omega Suppliers', 'Material_Type': 'Hardware', 'Total_Ordered_Amount': '₹ 300000', 'Total_Paid_Amount': '₹ 260800', 'Outstanding_Balance': '₹ 39200', 'Next_Payment_Date': '2026-09-15', 'Credit_Days_Allowed': 30}
    ]
    pd.DataFrame(records).to_csv('06_vendors_payables.csv', index=False)

    # 6. LOANS (Debt Outstanding: 285000, Debt burden 9.8% -> EMI = ~47500. So we need monthly EMI 47500)
    records = [
        {'Loan_ID': 'LN001', 'Business_ID': 'BUS001', 'Loan_Provider': 'SBI Bank', 'Principal_Amount': '₹ 500000', 'Interest_Rate': '12%', 'Tenure_Months': 12, 'Monthly_EMI': '₹ 47530', 'Outstanding_Principal': '₹ 285000', 'Start_Date': '2026-01-01', 'Next_Due_Date': '2026-09-05', 'Loan_Type': 'Working Capital', 'Status': 'Active'}
    ]
    pd.DataFrame(records).to_csv('07_loans_emi.csv', index=False)

if __name__ == '__main__':
    apply_realistic_metrics()
    os.system('python consolidate_data.py')
    os.system('copy rural_business_master_data.csv data\rural_business_master_data.csv')
