import pandas as pd
import random
import os
from datetime import datetime, timedelta

def clean_curr(x):
    if isinstance(x, str):
        return x.replace('₹', '').replace(',', '').replace(' ', '').strip()
    return x

# 1. GENERATE NEW SALES DATA (Target ~10 Lakhs)
def generate_sales():
    products = pd.read_csv('02_products_inventory.csv')
    products['Selling_Price_Num'] = products['Selling_Price'].apply(clean_curr).astype(float)
    
    customers = ['CUST001', 'CUST002', 'CUST003', 'CUST004', 'CUST005']
    
    start_date = datetime(2026, 8, 1)
    
    sales_data = []
    total_sales = 0
    sale_idx = 1
    
    while total_sales < 1000000:
        prod = products.sample(1).iloc[0]
        qty = random.randint(5, 50)
        sp = prod['Selling_Price_Num']
        
        discount = random.choice([0, 0, 5, 10])
        amount = (qty * sp) * (1 - discount/100)
        
        mode = random.choices(['Cash', 'UPI', 'Credit'], weights=[0.4, 0.4, 0.2])[0]
        
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
            'Discount_Percent': discount,
            'Total_Amount': f"₹ {int(amount)}",
            'Payment_Mode': mode,
            'Payment_Status': status,
            'Credit_Amount': f"₹ {int(credit)}" if credit > 0 else '0',
            'Notes': 'Standard Sale'
        })
        
        total_sales += amount
        sale_idx += 1
        
    df = pd.DataFrame(sales_data)
    df.to_csv('03_sales_transactions.csv', index=False)
    print(f"Generated {len(df)} sales totaling ~{total_sales}")
    return df

# 2. GENERATE NEW EXPENSES (Target ~5.5 Lakhs)
def generate_expenses():
    expenses_data = [
        ('Rent', 120000, 'Fixed', 'Yes'),
        ('Electricity', 25000, 'Variable', 'No'),
        ('Salary', 200000, 'Fixed', 'Yes'),
        ('Transport', 45000, 'Variable', 'No'),
        ('Maintenance', 30000, 'Variable', 'No'),
        ('Marketing', 50000, 'Variable', 'No'),
        ('Packaging', 40000, 'Variable', 'No'),
        ('Utilities', 15000, 'Fixed', 'Yes'),
        ('Miscellaneous', 25000, 'Variable', 'No')
    ]
    
    records = []
    start_date = datetime(2026, 8, 1)
    
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
        
    df = pd.DataFrame(records)
    df.to_csv('04_expenses.csv', index=False)
    print(f"Generated expenses totaling ~5.5 Lakhs")
    
# 3. FIX RECEIVABLES
def fix_receivables(sales_df):
    cust_totals = {}
    for _, row in sales_df.iterrows():
        cid = row['Customer_ID']
        if cid not in cust_totals:
            cust_totals[cid] = {'sales': 0, 'credit': 0}
            
        amt = float(clean_curr(row['Total_Amount']))
        cred = float(clean_curr(row['Credit_Amount']))
        
        cust_totals[cid]['sales'] += amt
        cust_totals[cid]['credit'] += cred
        
    records = []
    for i, (cid, data) in enumerate(cust_totals.items()):
        due = data['credit']
        paid = data['sales'] - due
        records.append({
            'Customer_ID': cid,
            'Customer_Name': f'Demo Customer {i+1}',
            'Contact_Number': f'98765432{i:02d}',
            'Customer_Type': 'Regular',
            'Total_Credit_Sales': f"₹ {int(data['sales'])}",
            'Total_Payments_Received': f"₹ {int(paid)}",
            'Outstanding_Amount': f"₹ {int(due)}",
            'Last_Payment_Date': '2026-08-25',
            'Days_Overdue': random.randint(0, 15) if due > 0 else 0
        })
        
    df = pd.DataFrame(records)
    df.to_csv('05_customers_receivables.csv', index=False)
    print("Fixed receivables")

# 4. FIX INVENTORY
def fix_inventory():
    df = pd.read_csv('02_products_inventory.csv')
    df['Minimum_Stock'] = 20
    df['Reorder_Level'] = 30
    df['Current_Stock'] = df['Current_Stock'].apply(lambda x: random.randint(35, 150))
    # Make a couple of items low stock
    df.loc[0, 'Current_Stock'] = 15
    df.loc[1, 'Current_Stock'] = 25
    df.to_csv('02_products_inventory.csv', index=False)
    print("Fixed inventory")

# 5. FIX PAYABLES
def fix_payables():
    records = [
        {'Vendor_ID': 'SUPP001', 'Vendor_Name': 'Alpha Build', 'Material_Type': 'Cement', 'Total_Ordered_Amount': '₹ 450000', 'Total_Paid_Amount': '₹ 400000', 'Outstanding_Balance': '₹ 50000', 'Next_Payment_Date': '2026-09-15', 'Credit_Days_Allowed': 30},
        {'Vendor_ID': 'SUPP002', 'Vendor_Name': 'Omega Wires', 'Material_Type': 'Electrical', 'Total_Ordered_Amount': '₹ 200000', 'Total_Paid_Amount': '₹ 180000', 'Outstanding_Balance': '₹ 20000', 'Next_Payment_Date': '2026-09-10', 'Credit_Days_Allowed': 30},
        {'Vendor_ID': 'SUPP003', 'Vendor_Name': 'Delta Hardware', 'Material_Type': 'Tools', 'Total_Ordered_Amount': '₹ 150000', 'Total_Paid_Amount': '₹ 150000', 'Outstanding_Balance': '₹ 0', 'Next_Payment_Date': '', 'Credit_Days_Allowed': 15}
    ]
    df = pd.DataFrame(records)
    df.to_csv('06_vendors_payables.csv', index=False)
    print("Fixed payables")
    
# 6. FIX LOANS
def fix_loans():
    records = [
        {'Loan_ID': 'LN001', 'Business_ID': 'BUS001', 'Loan_Provider': 'SBI Bank', 'Principal_Amount': '₹ 1500000', 'Interest_Rate': '9.5%', 'Tenure_Months': 60, 'Monthly_EMI': '₹ 31500', 'Outstanding_Principal': '₹ 1100000', 'Start_Date': '2024-01-01', 'Next_Due_Date': '2026-09-05', 'Loan_Type': 'Term Loan', 'Status': 'Active'}
    ]
    df = pd.DataFrame(records)
    df.to_csv('07_loans_emi.csv', index=False)
    print("Fixed loans")

if __name__ == '__main__':
    fix_inventory()
    sales = generate_sales()
    generate_expenses()
    fix_receivables(sales)
    fix_payables()
    fix_loans()
    
    # Run consolidate
    os.system('python consolidate_data.py')
    
    # Move to data
    if os.path.exists('rural_business_master_data.csv'):
        os.rename('rural_business_master_data.csv', 'data/rural_business_master_data.csv')
        print("Moved master dataset to data/")
    print("All done!")
