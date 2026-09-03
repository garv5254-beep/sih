import os
import glob
import re
import pandas as pd

def main():
    csv_path = 'data/rural_business_master_data.csv'
    if not os.path.exists(csv_path):
        print("CSV not found")
        return
        
    df = pd.read_csv(csv_path, nrows=0)
    cols = df.columns.tolist()
    
    # We want to replace exactly these strings in the codebase
    # However, some might be used in strings, so we only target typical dataframe access/assignment patterns
    # e.g. df['Product_ID'] -> df['product_id']
    # e.g. 'Product_ID' in df.columns -> 'product_id' in df.columns
    
    files = glob.glob('**/*.py', recursive=True)
    files = [f for f in files if 'env' not in f and '.git' not in f and 'scratch' not in f]
    
    total_replaced = 0
    for fpath in files:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        
        for col in cols:
            # Replace exactly the string literal for the column
            # Match 'Col_Name' or "Col_Name"
            pattern1 = rf"'{col}'"
            pattern2 = rf'"{col}"'
            
            new_content = re.sub(pattern1, f"'{col.lower()}'", new_content)
            new_content = re.sub(pattern2, f'"{col.lower()}"', new_content)
            
        if new_content != content:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {fpath}")
            total_replaced += 1
            
    print(f"Total files modified: {total_replaced}")

if __name__ == '__main__':
    main()
