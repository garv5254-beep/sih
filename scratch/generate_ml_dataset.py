import pandas as pd
import random
import os
import numpy as np
from datetime import datetime, timedelta

def clean_curr(x):
    if isinstance(x, str):
        return x.replace('₹', '').replace(',', '').replace(' ', '').strip()
    return x

def get_target_margin(product_name):
    name = str(product_name).lower()
    if 'cement' in name or 'tmt' in name:
        return random.uniform(5.0, 8.0)
    elif 'pipe' in name or 'roofing' in name or 'adhesive' in name or 'tank' in name:
        return random.uniform(8.0, 12.0)
    else:
        return random.uniform(10.0, 15.0) # LED, Wire, Paint, Switch, Tap, Tape, MCB

def generate_ml_dataset():
    # 1. READ AND ENHANCE INVENTORY
    products = pd.read_csv('BizMetrics_realistic_inventory_12_SKUs.csv')
    
    products['Purchase_Price_Num'] = products['Purchase_Price'].apply(clean_curr).astype(float)
    
    new_sp_nums = []
    new_sps = []
    new_margins = []
    
    for _, row in products.iterrows():
        pp = row['Purchase_Price_Num']
        target_margin = get_target_margin(row.get('Product_Name', row.get('Product', 'Unknown')))
        
        # Calculate Selling Price and round up to a commercial price (e.g. nearest int)
        sp = pp * (1 + target_margin / 100.0)
        sp = round(sp)
        
        # Recalculate exact margin
        actual_margin = ((sp - pp) / pp) * 100.0
        
        new_sp_nums.append(sp)
        new_sps.append(f"₹ {int(sp)}")
        new_margins.append(actual_margin)

    products['Selling_Price_Num'] = new_sp_nums
    products['Selling_Price'] = new_sps
    products['Profit_Margin'] = new_margins
    
    # Assert validation
    assert products['Profit_Margin'].max() <= 15.0, "Margin exceeded 15%!"
    
    print("\nInventory Margin Validation")
    print(f"SKUs: {len(products)}")
    print(f"Minimum Margin: {products['Profit_Margin'].min():.2f}%")
    print(f"Maximum Margin: {products['Profit_Margin'].max():.2f}%")
    print(f"Average Margin: {products['Profit_Margin'].mean():.2f}%")
    print(f"Median Margin: {products['Profit_Margin'].median():.2f}%\n")
    
    # Add Supplier_ID and Lead_Time_Days
    suppliers = ['SUPP001', 'SUPP002', 'SUPP003']
    products['Supplier_ID'] = [random.choice(suppliers) for _ in range(len(products))]
    products['Lead_Time_Days'] = [random.randint(3, 10) for _ in range(len(products))]
    
    # Keep numerical values out of final CSV to maintain schema, or let them stay if needed.
    # It's better to keep Selling_Price as string if schema expects it.
    out_products = products.drop(columns=['Purchase_Price_Num', 'Selling_Price_Num', 'Profit_Margin'])
    out_products.to_csv('02_products_inventory.csv', index=False)
    
    # 2. GENERATE 90 DAYS OF SALES
    customers = [f'CUST{i:03d}' for i in range(1, 41)]
    end_date = datetime(2026, 8, 30)
    start_date = end_date - timedelta(days=90)
    
    sales_data = []
    sale_idx = 1
    
    fast_skus = ['PROD001', 'PROD008', 'PROD003', 'PROD005', 'PROD004']
    slow_skus = ['PROD010', 'PROD011', 'PROD012']
    
    current_date = start_date
    while current_date <= end_date:
        num_transactions = int(np.random.normal(15, 5))
        num_transactions = max(3, min(30, num_transactions))
        
        if current_date.month == 8 and current_date.day > 15:
            num_transactions = int(num_transactions * 1.3)
            
        for _ in range(num_transactions):
            rand_val = random.random()
            if rand_val < 0.6:
                prod_id = random.choice(fast_skus)
            elif rand_val < 0.9:
                med_skus = [p for p in products['Product_ID'] if p not in fast_skus and p not in slow_skus]
                prod_id = random.choice(med_skus)
            else:
                prod_id = random.choice(slow_skus)
                
            prod = products[products['Product_ID'] == prod_id].iloc[0]
            sp = prod['Selling_Price_Num']
            
            if prod_id == 'PROD003':
                qty = random.randint(10, 50)
            elif prod_id == 'PROD005':
                qty = random.randint(3, 15)
            elif prod_id in fast_skus:
                qty = random.randint(2, 10)
            else:
                qty = random.randint(1, 5)
                
            amount = qty * sp
            
            discount = random.choices([0, 5, 10], weights=[0.8, 0.1, 0.1])[0]
            amount = amount * (1 - discount/100.0)
            
            mode = random.choices(['Cash', 'UPI', 'Credit'], weights=[0.6, 0.3, 0.1])[0]
            if mode == 'Credit':
                status = 'Pending'
                credit = amount
            else:
                status = 'Completed'
                credit = 0
                
            sales_data.append({
                'Sale_ID': f'SALE{sale_idx:04d}',
                'Business_ID': 'BUS001',
                'Date': current_date.strftime('%Y-%m-%d'),
                'Customer_ID': random.choice(customers),
                'Product_ID': prod_id,
                'Quantity': qty,
                'Selling_Price': f"₹ {int(sp)}",
                'Discount_Percent': discount,
                'Total_Amount': f"₹ {int(amount)}",
                'Payment_Mode': mode,
                'Payment_Status': status,
                'Credit_Amount': f"₹ {int(credit)}" if credit > 0 else '0',
                'Notes': 'Standard Sale'
            })
            sale_idx += 1
            
        current_date += timedelta(days=1)
        
    df_sales = pd.DataFrame(sales_data)
    df_sales.to_csv('03_sales_transactions.csv', index=False)
    print(f"Generated {len(df_sales)} sales over 90 days.")

if __name__ == '__main__':
    generate_ml_dataset()
    os.system('python consolidate_data.py')
    os.system('copy rural_business_master_data.csv data\\rural_business_master_data.csv')
    print("Done!")
