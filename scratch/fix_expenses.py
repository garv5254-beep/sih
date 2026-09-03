import pandas as pd
import os

def fix_expenses():
    df = pd.read_csv('04_expenses.csv')
    # Change amounts
    new_amounts = {
        'Rent': '₹ 8000',
        'Salary': '₹ 12000',
        'Electricity': '₹ 3000',
        'Transport': '₹ 8000',
        'Maintenance': '₹ 5000',
        'Marketing': '₹ 0',
        'Miscellaneous': '₹ 4000'
    }
    df['Amount'] = df['Category'].map(new_amounts).fillna('₹ 1000')
    df.to_csv('04_expenses.csv', index=False)
    
if __name__ == '__main__':
    fix_expenses()
    os.system('python consolidate_data.py')
    print("Fixed 04_expenses.csv")
