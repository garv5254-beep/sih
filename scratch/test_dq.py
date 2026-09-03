import pandas as pd
import numpy as np

def analyze_data_quality(data):
    """
    Data Quality Engine - Context Aware Scoring
    """
    if data is None or data.empty:
        return {"score": 0, "total_records": 0, "missing_values": 0, "duplicate_records": 0, 
                "invalid_values": 0, "columns_analyzed": 0, "columns": [], "recommendations": []}
        
    total_records = len(data)
    recommendations = set()
    cols_data = []
    
    # Define required fields per record type
    req_map = {
        'sale': ['sale_id', 'date', 'product_id', 'quantity', 'selling_price'],
        'inventory': ['product_id', 'product_name', 'current_stock', 'minimum_stock', 'reorder_level', 'purchase_price', 'selling_price'],
        'receivable': ['customer_id', 'credit_amount', 'due_date', 'amount_paid', 'payment_status'],
        'expense': ['expense_id', 'category', 'amount'],
        'loan': ['loan_id', 'principal_amount', 'interest_rate', 'monthly_emi', 'start_date', 'outstanding_principal'],
        'scheme': ['scheme_name', 'type'],
        'customer': ['customer_id', 'customer_name', 'contact_number', 'city']
    }
    
    # 1. Context-aware missing values (30%)
    total_required_expected = 0
    total_required_missing = 0
    
    # Dictionary to track legitimate missing vs total for column-level table
    col_required_expected = {c: 0 for c in data.columns}
    col_required_missing = {c: 0 for c in data.columns}
    
    if 'record_type' in data.columns:
        for rtype, group in data.groupby(data['record_type'].astype(str).str.lower()):
            req_cols = req_map.get(rtype, [])
            for c in req_cols:
                if c in data.columns:
                    expected = len(group)
                    missing = group[c].isna().sum() + (group[c].astype(str).str.strip() == '').sum()
                    
                    total_required_expected += expected
                    total_required_missing += missing
                    col_required_expected[c] += expected
                    col_required_missing[c] += missing
    
    missing_penalty = 0
    if total_required_expected > 0:
        missing_penalty = (total_required_missing / total_required_expected) * 30
        if missing_penalty > 0:
            recommendations.add("Some records are missing required fields specific to their transaction type.")
            
    # 2. Duplicate records (20%)
    dup_penalty = 0
    total_dups = 0
    key_cols = ['sale_id', 'product_id', 'customer_id', 'expense_id', 'loan_id']
    for kc in key_cols:
        if kc in data.columns:
            # Check for duplicates, ignoring NaNs
            valid_mask = data[kc].notna() & (data[kc].astype(str).str.strip() != '')
            dups = data.loc[valid_mask, kc].duplicated().sum()
            total_dups += dups
            if dups > 0:
                recommendations.add(f"Duplicate transaction identifiers detected in {kc}. Review these before financial reporting.")
                
    if total_records > 0:
        # A 5% duplicate rate loses all 20 points
        dup_rate = total_dups / total_records
        dup_penalty = min(20, (dup_rate / 0.05) * 20)
        
    # 3. Invalid dates (15%) & 4. Invalid numerics (15%)
    date_penalty = 0
    num_penalty = 0
    total_invalid = 0
    
    date_cols = ['date', 'due_date', 'payment_date', 'registration_date', 'start_date', 'next_payment_date', 'next_due_date']
    num_cols = ['quantity', 'selling_price', 'purchase_price', 'amount', 'credit_amount', 'amount_paid', 'outstanding_amount', 'principal_amount', 'monthly_emi', 'current_stock', 'minimum_stock']
    
    col_invalid_count = {c: 0 for c in data.columns}
    
    for c in data.columns:
        invalid_count = 0
        if c in date_cols:
            # Check how many are NOT null but failed parsing (NaT)
            # Actually, pd.to_datetime coerces errors to NaT, so if original wasn't null but coerced is NaT -> invalid
            orig_notna = data[c].notna() & (data[c].astype(str).str.strip() != '')
            coerced = pd.to_datetime(data[c], errors='coerce')
            invalid_count = (orig_notna & coerced.isna()).sum()
            if invalid_count > 0:
                recommendations.add(f"Some records contain invalid dates in '{c}'. Correct these to improve trend calculations.")
                
        elif c in num_cols:
            orig_notna = data[c].notna() & (data[c].astype(str).str.strip() != '')
            coerced = pd.to_numeric(data[c], errors='coerce')
            # Invalid if unparseable OR negative (for most business fields)
            unparseable = orig_notna & coerced.isna()
            negative = coerced < 0
            invalid_count = (unparseable | negative).sum()
            if invalid_count > 0:
                recommendations.add(f"Invalid numeric values (negative or unparseable text) detected in '{c}'.")
                
        col_invalid_count[c] = invalid_count
        total_invalid += invalid_count
        
    if total_records > 0:
        # 5% invalid date rate loses 15 points
        date_invalid = sum(col_invalid_count[c] for c in date_cols if c in col_invalid_count)
        date_rate = date_invalid / total_records
        date_penalty = min(15, (date_rate / 0.05) * 15)
        
        # 5% invalid num rate loses 15 points
        num_invalid = sum(col_invalid_count[c] for c in num_cols if c in col_invalid_count)
        num_rate = num_invalid / total_records
        num_penalty = min(15, (num_rate / 0.05) * 15)

    # 5. Missing Important IDs (10%)
    id_penalty = 0
    missing_ids = 0
    for id_col in ['customer_id', 'product_id', 'business_id']:
        if id_col in data.columns:
            # Check if required but missing
            missing_ids += col_required_missing.get(id_col, 0)
            
    if total_required_expected > 0:
        id_rate = missing_ids / total_required_expected
        id_penalty = min(10, (id_rate / 0.05) * 10)
        
    # 6. Schema Completeness (10%)
    schema_penalty = 0
    expected_core_cols = ['record_type', 'date', 'product_id', 'quantity', 'total_amount']
    missing_schema = [c for c in expected_core_cols if c not in data.columns]
    if missing_schema:
        schema_penalty = 10
        recommendations.add("Dataset is missing fundamental core columns (e.g. record_type, date, total_amount).")
        
    if not recommendations:
        recommendations.add("Data quality is strong. No major integrity issues were detected.")

    score = 100 - (missing_penalty + dup_penalty + date_penalty + num_penalty + id_penalty + schema_penalty)
    score = max(0, min(100, score))
    
    # Build columns data
    for col in data.columns:
        expected = col_required_expected.get(col, 0)
        req_missing = col_required_missing.get(col, 0)
        invalid = col_invalid_count.get(col, 0)
        
        if expected > 0:
            missing_pct = (req_missing / expected) * 100
        else:
            missing_pct = 0
            
        quality = "Good"
        if missing_pct > 20 or invalid > (total_records * 0.05):
            quality = "Critical"
        elif missing_pct > 5 or invalid > 0:
            quality = "Warning"
            
        cols_data.append({
            "Column": col,
            "Missing": req_missing,
            "Missing_Pct": missing_pct,
            "Invalid": invalid,
            "Unique": data[col].nunique(),
            "Quality": quality
        })
        
    return {
        "score": score,
        "total_records": total_records,
        "missing_values": total_required_missing,
        "duplicate_records": total_dups,
        "invalid_values": total_invalid,
        "columns_analyzed": len(data.columns),
        "columns": cols_data,
        "recommendations": list(recommendations)
    }

if __name__ == '__main__':
    from pipeline import load_master_csv, validate_and_clean
    df = load_master_csv('rural_business_master_data.csv')
    df = validate_and_clean(df)
    res = analyze_data_quality(df)
    print("Score:", res['score'])
    print("Missing values:", res['missing_values'])
    print("Duplicates:", res['duplicate_records'])
    print("Invalid:", res['invalid_values'])
    print("Recommendations:", res['recommendations'])
