import streamlit as st
import pandas as pd
from pathlib import Path
import hashlib
from pipeline import analyze_inventory, run_pipeline, validate_and_clean

def find_master_csv():
    """Finds the master CSV robustly from the project root."""
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    
    possible_paths = [
        PROJECT_ROOT / "rural_business_master_data.csv",
        PROJECT_ROOT / "data" / "rural_business_master_data.csv",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
            
    return None

def generate_missing_mobile_numbers(df, csv_path):
    """Persist one canonical demo mobile number per customer ID."""
    modified = False

    customer_id_col = next((col for col in df.columns if col.lower() in {'customer_id', 'customerid'}), None)
    record_type_col = next((col for col in df.columns if col.lower() == 'record_type'), None)
    mobile_col = next((col for col in df.columns if col.lower() == 'mobile_number'), None)
    source_contact_col = next((col for col in df.columns if col.lower() in {
        'contact_number', 'mobile', 'phone', 'phone_number', 'customer_phone'
    }), None)

    if mobile_col is None:
        mobile_col = 'Mobile_Number'
        df[mobile_col] = None
        modified = True

    df[mobile_col] = df[mobile_col].astype("string")

    if customer_id_col is None:
        return df

    for idx, row in df.iterrows():
        record_type = str(row.get(record_type_col, '')).strip().lower() if record_type_col else ''
        if record_type not in ['receivable', 'customer']:
            continue

        cust_id = str(row.get(customer_id_col, '')).strip()
        if not cust_id or cust_id == 'nan':
            continue

        existing_mobile = row.get(mobile_col, '')
        source_mobile = row.get(source_contact_col, '') if source_contact_col else ''
        existing = str(existing_mobile).strip()
        if not existing or existing.lower() in {'nan', 'none'}:
            existing = str(source_mobile).strip()
        if existing.endswith('.0'):
            existing = existing[:-2]

        digits_only = ''.join(c for c in existing if c.isdigit())
        if len(digits_only) == 10 and digits_only[0] in '6789':
            if str(row.get(mobile_col, '')).strip() != digits_only:
                df.at[idx, mobile_col] = digits_only
                modified = True
        else:
            hash_val = int(hashlib.sha256(cust_id.encode()).hexdigest(), 16)
            last_9 = f"{(hash_val % 1000000000):09d}"
            first_digit = str(6 + (hash_val % 4))
            demo_num = first_digit + last_9
            df.at[idx, mobile_col] = demo_num
            modified = True

    if modified:
        df.to_csv(csv_path, index=False)
        return pd.read_csv(csv_path, dtype={mobile_col: "string"})
    return df

@st.cache_data(show_spinner=False)
def load_master_data(csv_path, file_signature):
    """Load and clean the master data once per CSV version."""
    df = pd.read_csv(csv_path, dtype={"Mobile_Number": "string", "Contact_Number": "string"})
    df = generate_missing_mobile_numbers(df, csv_path)
    return validate_and_clean(df)


@st.cache_data(show_spinner=False)
def get_cached_pipeline_result(csv_path, file_signature, include_inventory_ml=False):
    """Run deterministic pipeline work once per CSV version and ML mode."""
    clean_df = load_master_data(csv_path, file_signature)
    result = run_pipeline(clean_df, include_inventory_ml=include_inventory_ml)
    return clean_df, result


@st.cache_data(show_spinner=False)
def get_cached_inventory_analysis(data):
    """Run inventory ML only when the Inventory page requests it."""
    return analyze_inventory(data, include_ml=True)

def refresh_application_data():
    """Refreshes the application data and pipeline results into session state."""
    csv_path = find_master_csv()
    if csv_path is None:
        raise FileNotFoundError("rural_business_master_data.csv was not found.")
        
    file_stat = csv_path.stat()
    file_signature = (file_stat.st_mtime_ns, file_stat.st_size)
    clean_df, result = get_cached_pipeline_result(str(csv_path), file_signature, include_inventory_ml=False)
    
    st.session_state["pipeline_result"] = result
    st.session_state["raw_data"] = clean_df
    st.session_state["dataset_path"] = str(csv_path)
