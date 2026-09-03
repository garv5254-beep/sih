import pandas as pd
import random
import os
from datetime import datetime, timedelta

def clean_curr(x):
    if isinstance(x, str):
        return x.replace('₹', '').replace(',', '').replace(' ', '').strip()
    return x

def fix_all():
    # 1. NEW INVENTORY DATA (12 SKUs)
    inventory_data = [
        {"Product_ID": "PROD001", "Product_Name": "Steel Pipes - 1 inch", "Category": "Building Materials", "Sector": "Hardware", "Unit": "Piece", "Purchase_Price": "₹ 145", "Selling_Price": "₹ 220", "Current_Stock": 125, "Minimum_Stock": 30, "Maximum_Stock": 200, "Reorder_Level": 50, "Status": "Healthy", "Description": "Galvanized steel pipes used for plumbing and construction work."},
        {"Product_ID": "PROD002", "Product_Name": "PVC Pipe - 1 inch", "Category": "Plumbing", "Sector": "Hardware", "Unit": "Piece", "Purchase_Price": "₹ 85", "Selling_Price": "₹ 135", "Current_Stock": 180, "Minimum_Stock": 40, "Maximum_Stock": 300, "Reorder_Level": 70, "Status": "Healthy", "Description": "Lightweight PVC pipes commonly used for water supply and drainage."},
        {"Product_ID": "PROD003", "Product_Name": "Electrical Wire - 2.5 sq mm", "Category": "Electrical", "Sector": "Hardware", "Unit": "Meter", "Purchase_Price": "₹ 8", "Selling_Price": "₹ 15", "Current_Stock": 450, "Minimum_Stock": 100, "Maximum_Stock": 800, "Reorder_Level": 200, "Status": "Healthy", "Description": "Copper electrical wire for domestic and commercial wiring."},
        {"Product_ID": "PROD004", "Product_Name": "LED Bulb - 9W", "Category": "Electrical", "Sector": "Hardware", "Unit": "Piece", "Purchase_Price": "₹ 55", "Selling_Price": "₹ 90", "Current_Stock": 210, "Minimum_Stock": 50, "Maximum_Stock": 300, "Reorder_Level": 80, "Status": "Healthy", "Description": "Energy-efficient LED bulb suitable for homes and small businesses."},
        {"Product_ID": "PROD005", "Product_Name": "Cement - 50 kg", "Category": "Construction", "Sector": "Hardware", "Unit": "Bag", "Purchase_Price": "₹ 350", "Selling_Price": "₹ 425", "Current_Stock": 65, "Minimum_Stock": 20, "Maximum_Stock": 150, "Reorder_Level": 30, "Status": "Healthy", "Description": "Standard construction cement for masonry and concrete applications."},
        {"Product_ID": "PROD006", "Product_Name": "Wall Paint - 20 L", "Category": "Paint & Hardware", "Sector": "Hardware", "Unit": "Bucket", "Purchase_Price": "₹ 1850", "Selling_Price": "₹ 2450", "Current_Stock": 28, "Minimum_Stock": 8, "Maximum_Stock": 50, "Reorder_Level": 12, "Status": "Healthy", "Description": "Interior/exterior wall paint for residential and commercial buildings."},
        {"Product_ID": "PROD007", "Product_Name": "GI Roofing Sheet", "Category": "Roofing", "Sector": "Hardware", "Unit": "Piece", "Purchase_Price": "₹ 620", "Selling_Price": "₹ 850", "Current_Stock": 42, "Minimum_Stock": 10, "Maximum_Stock": 100, "Reorder_Level": 18, "Status": "Healthy", "Description": "Galvanized roofing sheets for sheds, shops and rural structures."},
        {"Product_ID": "PROD008", "Product_Name": "PVC Elbow - 1 inch", "Category": "Plumbing", "Sector": "Hardware", "Unit": "Piece", "Purchase_Price": "₹ 12", "Selling_Price": "₹ 22", "Current_Stock": 320, "Minimum_Stock": 80, "Maximum_Stock": 500, "Reorder_Level": 120, "Status": "Healthy", "Description": "90-degree PVC connector used to change the direction of pipelines."},
        {"Product_ID": "PROD009", "Product_Name": "Electrical Switch - 6A", "Category": "Electrical", "Sector": "Hardware", "Unit": "Piece", "Purchase_Price": "₹ 28", "Selling_Price": "₹ 50", "Current_Stock": 145, "Minimum_Stock": 30, "Maximum_Stock": 300, "Reorder_Level": 60, "Status": "Healthy", "Description": "Standard 6A switch for residential electrical installations."},
        {"Product_ID": "PROD010", "Product_Name": "TMT Steel Bar - 8 mm", "Category": "Building Materials", "Sector": "Hardware", "Unit": "Piece", "Purchase_Price": "₹ 410", "Selling_Price": "₹ 520", "Current_Stock": 18, "Minimum_Stock": 10, "Maximum_Stock": 100, "Reorder_Level": 12, "Status": "Low Stock", "Description": "Reinforcement steel bar used in concrete construction."},
        {"Product_ID": "PROD011", "Product_Name": "Brass Tap - 15 mm", "Category": "Plumbing", "Sector": "Hardware", "Unit": "Piece", "Purchase_Price": "₹ 180", "Selling_Price": "₹ 295", "Current_Stock": 25, "Minimum_Stock": 10, "Maximum_Stock": 80, "Reorder_Level": 15, "Status": "Low Stock", "Description": "Durable brass water tap for household and commercial plumbing."},
        {"Product_ID": "PROD012", "Product_Name": "Tile Adhesive - 20 kg", "Category": "Construction", "Sector": "Hardware", "Unit": "Bag", "Purchase_Price": "₹ 285", "Selling_Price": "₹ 390", "Current_Stock": 58, "Minimum_Stock": 15, "Maximum_Stock": 100, "Reorder_Level": 25, "Status": "Healthy", "Description": "Cement-based adhesive for fixing ceramic and floor tiles."}
    ]
    pd.DataFrame(inventory_data).to_csv('02_products_inventory.csv', index=False)
    
    # 2. REGENERATE SALES
    products = pd.DataFrame(inventory_data)
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
        
    df_sales = pd.DataFrame(sales_data)
    df_sales.to_csv('03_sales_transactions.csv', index=False)
    
    # Run consolidate
    os.system('python consolidate_data.py')

if __name__ == '__main__':
    fix_all()
