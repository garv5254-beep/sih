import pandas as pd
import random
import os
from datetime import datetime, timedelta

def generate_customers():
    # Realistic Indian names, business types, and locations
    names = ["Rajesh Kumar", "Amit Sharma", "Suresh Patel", "Anil Gupta", "Ramesh Singh", "Vijay Verma", "Sanjay Joshi", "Dinesh Reddy", "Prakash Rao", "Ashok Desai"]
    business_suffixes = ["Hardware Store", "Distributors", "Traders", "Enterprises", "Plumbing Supplier", "Electricals", "Contractors", "Builders", "Retail Shop", "Wholesale"]
    cities = ["Raipur", "Bilaspur", "Bhilai", "Korba", "Durg", "Rajnandgaon", "Jagdalpur", "Ambikapur"]
    
    types = ["Retailer", "Contractor", "Builder", "Wholesaler", "Institutional Buyer"]
    
    customers = []
    
    # We need CUST001 to CUST036 to match the sales generation
    for i in range(1, 37):
        b_suffix = random.choice(business_suffixes)
        name = random.choice(names)
        b_name = f"{name.split(' ')[0]} {b_suffix}"
        
        # Random dates between 2024-01-01 and 2026-06-01 for registration
        days_ago = random.randint(100, 900)
        reg_date = (datetime(2026, 8, 30) - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        rating = round(random.uniform(3.5, 5.0), 1)
        
        phone = f"987654{random.randint(1000, 9999)}"
        email = f"{b_name.replace(' ', '').lower()}@example.com"
        
        customers.append({
            "Customer_ID": f"CUST{i:03d}",
            "Customer_Name": name,
            "Business_Name": b_name,
            "Contact_Number": phone,
            "Email": email,
            "City": random.choice(cities),
            "Customer_Type": random.choice(types),
            "Registration_Date": reg_date,
            "Customer_Rating": rating
        })
        
    df_cust = pd.DataFrame(customers)
    # Save as 05_customers_receivables.csv (which implies we are dropping the hardcoded receivable fields, since we calculate them dynamically in pipeline anyway, or we can just append dummy receivable fields so the consolidation script doesn't complain, though we should probably rename this conceptually. I will add some dummy receivable fields just in case they are strictly needed by the schema).
    
    df_cust['Outstanding_Amount'] = 0
    # Actually wait, let's just write to 05_customers.csv, but the existing file is 05_customers_receivables.csv. Let's stick to the existing file.
    
    df_cust.to_csv('data/05_customers_receivables.csv', index=False)
    print("Generated 36 realistic B2B customers in data/05_customers_receivables.csv")

if __name__ == '__main__':
    generate_customers()
    os.system('python consolidate_data.py')
    os.system('copy rural_business_master_data.csv data\rural_business_master_data.csv')
    print("Consolidation complete.")
