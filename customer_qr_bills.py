"""
BizMetrics - Single-file Customer QR + Bill Integration
Generated from:
  - 05_customers_receivables.csv
  - 03_sales_transactions.csv

This file is self-contained for the QR images. It does NOT require
the QR PNG files to be present separately.

Usage in Streamlit:
    from customer_qr_bills import get_customer_qr, get_customer_bills
    st.image(get_customer_qr("CUST001"))
    bills = get_customer_bills("CUST001")
"""

import base64
import io
from io import BytesIO
from PIL import Image
from pathlib import Path
import pandas as pd
import streamlit as st
import qrcode
import urllib.parse
from urllib.parse import quote


def _normalize_mobile(value):
    if pd.isna(value):
        return "Not Available"
    mobile = str(value).strip()
    if mobile.endswith(".0"):
        mobile = mobile[:-2]
    digits = "".join(character for character in mobile if character.isdigit())
    return digits if len(digits) == 10 and digits[0] in "6789" else "Not Available"


def _whatsapp_phone(value):
    """Return an Indian number in wa.me format, or an empty string."""
    if pd.isna(value):
        return ""
    phone = str(value).strip().replace(" ", "").replace("-", "")
    if phone.endswith(".0"):
        phone = phone[:-2]
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("91") and len(phone) == 12:
        local = phone[2:]
    elif len(phone) == 10 and phone[0] in "6789":
        local = phone
    else:
        return ""
    return "91" + local if len(local) == 10 and local[0] in "6789" and local.isdigit() else ""


def _whatsapp_url(customer_name, mobile_number):
    phone = _whatsapp_phone(mobile_number)
    if not phone:
        return ""
    message = (
        f"Hello {customer_name},\n\n"
        "Here is your digital customer QR profile from Garv Electronics & Hardware.\n\n"
        "Please keep this QR for future reference.\n\n"
        "Thank you."
    )
    return f"https://wa.me/{phone}?text={quote(message)}"


def _get_customer_profile(customer_id):
    raw_data = st.session_state.get("raw_data", pd.DataFrame())
    if raw_data.empty or "customer_id" not in raw_data.columns:
        return {}
    customer_rows = raw_data[
        raw_data["customer_id"].astype(str).str.strip() == str(customer_id).strip()
    ]
    if customer_rows.empty:
        return {}
    record_types = customer_rows.get("record_type", pd.Series(index=customer_rows.index, dtype=str)).astype(str).str.lower()
    preferred_rows = customer_rows[record_types.isin(["receivable", "customer"])]
    if not preferred_rows.empty:
        customer_rows = preferred_rows
    mobile_column = "mobile_number" if "mobile_number" in customer_rows.columns else None
    if mobile_column:
        valid_mobile_rows = customer_rows[customer_rows[mobile_column].notna()]
        if not valid_mobile_rows.empty:
            customer_rows = valid_mobile_rows
    return customer_rows.iloc[0].to_dict()

@st.cache_data(show_spinner=False)
def get_customer_qr(customer_id: str):
    """Return the customer's QR as PNG bytes."""
    key = str(customer_id).strip()
    
    # Generate QR dynamically
    import qrcode
    from io import BytesIO
    import urllib.parse
    
    base_url = "https://bizmetrics.app/customer/"
    url = urllib.parse.urljoin(base_url, urllib.parse.quote(key))
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@st.cache_data(show_spinner=False)
def load_bills_and_products():
    if "raw_data" in st.session_state:
        raw_data = st.session_state["raw_data"]
        # Ensure record_type exists
        if "record_type" not in raw_data.columns:
            return pd.DataFrame(), pd.DataFrame()
            
        is_sale = raw_data["record_type"].astype(str).str.lower() == "sale"
        is_inv = raw_data["record_type"].astype(str).str.lower() == "inventory"
        
        sales_df = raw_data[is_sale].copy()
        products_df = raw_data[is_inv].copy()
        
        # In master CSV, columns might be different case (e.g. product_id instead of Product_ID)
        # We need to map them back to what get_customer_bills expects.
        col_map = {
            "sale_id": "Sale_ID",
            "customer_id": "Customer_ID",
            "product_id": "Product_ID",
            "quantity": "Quantity",
            "selling_price": "Selling_Price",
            "discount_percent": "Discount_Percent",
            "date": "Date",
            "payment_mode": "Payment_Mode",
            "payment_status": "Payment_Status",
            "credit_amount": "Credit_Amount",
            "product_name": "Product_Name",
            "notes": "Notes",
            "record_type": "record_type"
        }
        
        # Rename columns if they exist
        sales_df = sales_df.rename(columns={c: col_map[c] for c in col_map if c in sales_df.columns})
        products_df = products_df.rename(columns={c: col_map[c] for c in col_map if c in products_df.columns})
        
        return sales_df, products_df
    return pd.DataFrame(), pd.DataFrame()

@st.cache_data(show_spinner=False)
def get_customer_bills(customer_id: str):
    """Return all transaction/bill records for one customer with exact calculated amounts."""
    sales_df, products_df = load_bills_and_products()
    if sales_df.empty or "Customer_ID" not in sales_df.columns:
        return pd.DataFrame()
        
    c_id = str(customer_id).strip()
    sales_df["Customer_ID"] = sales_df["Customer_ID"].astype(str).str.strip()
    cust_sales = sales_df[sales_df["Customer_ID"] == c_id].copy()
    
    if cust_sales.empty:
        return cust_sales

    # Parse money
    def parse_money(s):
        if s is None:
            return 0.0
        return pd.to_numeric(
            s.astype(str)
             .str.replace("₹", "", regex=False)
             .str.replace(",", "", regex=False)
             .str.replace(" ", "", regex=False),
            errors="coerce"
        ).fillna(0.0)

    qty = pd.to_numeric(cust_sales.get("Quantity", pd.Series([1]*len(cust_sales))), errors="coerce").fillna(1)
    sp = parse_money(cust_sales.get("Selling_Price", pd.Series([0]*len(cust_sales))))
    disc = pd.to_numeric(cust_sales.get("Discount_Percent", pd.Series([0]*len(cust_sales))), errors="coerce").fillna(0)
    
    # Financial calculation (BizMetrics formula)
    gross = qty * sp
    disc_amt = gross * disc / 100.0
    final_amt = gross - disc_amt
    
    cust_sales["Bill_Amount"] = final_amt
    cust_sales["Date"] = pd.to_datetime(cust_sales.get("Date", pd.Series([None]*len(cust_sales))), errors="coerce")
    
    # Merge Product Names
    if not products_df.empty and "Product_ID" in products_df.columns and "Product_Name" in products_df.columns:
        product_map = products_df.set_index("Product_ID")["Product_Name"].to_dict()
        cust_sales["Product_Name"] = cust_sales["Product_ID"].map(product_map).fillna(cust_sales["Product_ID"])
    else:
        cust_sales["Product_Name"] = cust_sales.get("Product_ID", "")
        
    # Outstanding Logic
    outstanding = pd.Series([0.0]*len(cust_sales), index=cust_sales.index)
    
    for idx, row in cust_sales.iterrows():
        mode = str(row.get("Payment_Mode", "")).lower()
        status = str(row.get("Payment_Status", "")).lower()
        amt = row["Bill_Amount"]
        
        if status in ["pending", "unpaid", "overdue"]:
            out = parse_money(pd.Series([row.get("Credit_Amount", amt)])).iloc[0]
            outstanding[idx] = out if out > 0 else amt
        elif mode == "credit" and status != "completed":
            out = parse_money(pd.Series([row.get("Credit_Amount", amt)])).iloc[0]
            outstanding[idx] = out if out > 0 else amt
        else:
            outstanding[idx] = 0.0

    cust_sales["Outstanding"] = outstanding
    cust_sales["Paid_Amount"] = cust_sales["Bill_Amount"] - cust_sales["Outstanding"]

    cust_sales = cust_sales.sort_values(by="Date", ascending=False)
    return cust_sales

def get_bill_summary(bills: pd.DataFrame):
    if bills.empty:
        return {
            "total_bills": 0,
            "total_purchase": 0.0,
            "avg_bill": 0.0,
            "last_purchase": "N/A",
            "outstanding": 0.0,
            "paid_amount": 0.0
        }
        
    tot_bills = len(bills)
    tot_purchase = bills["Bill_Amount"].sum()
    avg_bill = tot_purchase / tot_bills if tot_bills > 0 else 0.0
    outstanding = bills["Outstanding"].sum()
    paid = bills["Paid_Amount"].sum()
    
    last_p = bills["Date"].dropna().max()
    last_p_str = last_p.strftime("%Y-%m-%d") if pd.notnull(last_p) else "N/A"
    
    return {
        "total_bills": tot_bills,
        "total_purchase": tot_purchase,
        "avg_bill": avg_bill,
        "last_purchase": last_p_str,
        "outstanding": outstanding,
        "paid_amount": paid
    }

def render_customer_qr_and_bills(customer_id: str):
    """
    Drop-in Streamlit component:
      - Shows the selected customer's QR.
      - Shows every transaction/bill record for that customer.
      - Shows summary metrics.
    """
    customer_id = str(customer_id).strip()
    profile = _get_customer_profile(customer_id)
    mobile_number = profile.get("mobile_number", "")
    customer_name = profile.get("business_name", profile.get("customer_name", "Customer"))

    st.subheader("🔳 Customer QR")
    qr = get_customer_qr(customer_id)

    if qr:
        try:
            qr_image = Image.open(BytesIO(qr))
            qr_image.load()
            st.image(qr_image, width=280, caption=f"QR — {customer_id}")
        except Exception as e:
            st.warning(f"Unable to display customer QR: {e}")
            
        whatsapp_url = _whatsapp_url(customer_name, mobile_number)
        qr_actions = st.columns(2)
        with qr_actions[0]:
            st.download_button(
                "⬇ Download QR",
                data=qr,
                file_name=f"{customer_id}_QR.png",
                mime="image/png",
                width="stretch",
            )
        with qr_actions[1]:
            if whatsapp_url:
                st.link_button("💬 Send QR on WhatsApp", whatsapp_url, width="stretch")
            else:
                st.warning("⚠ WhatsApp unavailable")
        st.caption("After WhatsApp opens, attach the downloaded QR image and press Send.")
    else:
        st.warning(f"No QR found for {customer_id}.")

    bills = get_customer_bills(customer_id)
    summary = get_bill_summary(bills)
    st.subheader("👤 Digital Customer Profile")
    profile_columns = st.columns(2)
    profile_values = [
        ("Customer Name", customer_name),
        ("Customer ID", customer_id),
        ("Mobile Number", _normalize_mobile(mobile_number)),
        ("Customer Type", profile.get("customer_type", "Not Available")),
        ("Total Orders", summary["total_bills"]),
        ("Total Spent", f"₹{summary['total_purchase']:,.0f}"),
        ("Outstanding", f"₹{summary['outstanding']:,.0f}"),
    ]
    for index, (label, value) in enumerate(profile_values):
        with profile_columns[index % 2]:
            st.metric(label, str(value) if pd.notna(value) else "Not Available")

    st.divider()
    st.subheader("🧾 Purchase Summary")

    a, b, c, d, e = st.columns(5)
    a.metric("Total Bills", summary["total_bills"])
    b.metric("Total Purchase", f"₹{summary['total_purchase']:,.0f}")
    c.metric("Average Bill", f"₹{summary['avg_bill']:,.0f}")
    d.metric("Paid Amount", f"₹{summary['paid_amount']:,.0f}")
    e.metric("Outstanding", f"₹{summary['outstanding']:,.0f}")
    
    st.markdown(f"**Last Purchase:** {summary['last_purchase']}")

    if bills.empty:
        st.info("No purchase records found for this customer.")
        return

    st.divider()
    st.subheader("📊 Bill History")
    
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        date_sort = st.selectbox("Sort By", ["Latest", "Oldest", "Highest Amount", "Lowest Amount"])
    with f2:
        pm_opts = ["All"] + sorted([x for x in bills["Payment_Mode"].dropna().unique() if x])
        pm_filter = st.selectbox("Payment Mode", pm_opts)
    with f3:
        ps_opts = ["All"] + sorted([x for x in bills["Payment_Status"].dropna().unique() if x])
        ps_filter = st.selectbox("Payment Status", ps_opts)
    with f4:
        prod_opts = ["All"] + sorted([x for x in bills["Product_Name"].dropna().unique() if x])
        prod_filter = st.selectbox("Product", prod_opts)
        
    filtered_bills = bills.copy()
    if pm_filter != "All":
        filtered_bills = filtered_bills[filtered_bills["Payment_Mode"] == pm_filter]
    if ps_filter != "All":
        filtered_bills = filtered_bills[filtered_bills["Payment_Status"] == ps_filter]
    if prod_filter != "All":
        filtered_bills = filtered_bills[filtered_bills["Product_Name"] == prod_filter]
        
    if date_sort == "Latest":
        filtered_bills = filtered_bills.sort_values(by="Date", ascending=False)
    elif date_sort == "Oldest":
        filtered_bills = filtered_bills.sort_values(by="Date", ascending=True)
    elif date_sort == "Highest Amount":
        filtered_bills = filtered_bills.sort_values(by="Bill_Amount", ascending=False)
    elif date_sort == "Lowest Amount":
        filtered_bills = filtered_bills.sort_values(by="Bill_Amount", ascending=True)

    display_df = pd.DataFrame()
    display_df["Sale ID"] = filtered_bills["Sale_ID"]
    display_df["Date"] = filtered_bills["Date"].dt.strftime("%Y-%m-%d").fillna("N/A")
    display_df["Customer ID"] = filtered_bills["Customer_ID"]
    display_df["Product"] = filtered_bills["Product_Name"]
    display_df["Qty"] = filtered_bills.get("Quantity", 1)
    
    def fmt(val):
        try:
            return f"₹{float(val):,.2f}"
        except:
            return val

    display_df["Unit Price"] = filtered_bills.get("Selling_Price", 0).apply(fmt)
    display_df["Discount"] = filtered_bills.get("Discount_Percent", 0).astype(str) + "%"
    display_df["Bill Amount"] = filtered_bills["Bill_Amount"].apply(fmt)
    display_df["Payment"] = filtered_bills.get("Payment_Mode", "")
    display_df["Status"] = filtered_bills.get("Payment_Status", "")
    display_df["Outstanding"] = filtered_bills["Outstanding"].apply(fmt)
    display_df["Sale Type"] = filtered_bills.get("Notes", filtered_bills.get("record_type", ""))

    for col in display_df.columns:
        display_df[col] = display_df[col].fillna("").astype(str)
        
    st.dataframe(display_df, width="stretch", hide_index=True)
    
    st.divider()
    st.subheader("📄 Selected Bill Details")
    
    if not filtered_bills.empty:
        selected_sale_id = st.selectbox("Select a Bill / Sale ID to view details:", filtered_bills["Sale_ID"].tolist())
        if selected_sale_id:
            bill_row = filtered_bills[filtered_bills["Sale_ID"] == selected_sale_id].iloc[0]
            
            bc1, bc2 = st.columns(2)
            with bc1:
                st.markdown(f"**Sale ID:** {bill_row.get('Sale_ID', 'N/A')}")
                st.markdown(f"**Customer:** {bill_row.get('Customer_ID', 'N/A')}")
                date_val = bill_row['Date'].strftime('%Y-%m-%d') if pd.notnull(bill_row['Date']) else 'N/A'
                st.markdown(f"**Date:** {date_val}")
                st.markdown(f"**Product:** {bill_row.get('Product_Name', 'N/A')}")
                st.markdown(f"**Quantity:** {bill_row.get('Quantity', '1')}")
                st.markdown(f"**Unit Price:** {fmt(bill_row.get('Selling_Price', 0))}")
            with bc2:
                st.markdown(f"**Discount:** {bill_row.get('Discount_Percent', 0)}%")
                st.markdown(f"**Total:** {fmt(bill_row['Bill_Amount'])}")
                st.markdown(f"**Payment Mode:** {bill_row.get('Payment_Mode', 'N/A')}")
                st.markdown(f"**Payment Status:** {bill_row.get('Payment_Status', 'N/A')}")
                st.markdown(f"**Outstanding:** {fmt(bill_row['Outstanding'])}")
                st.markdown(f"**Notes:** {bill_row.get('Notes', '')}")
    else:
        st.info("No bills match the selected filters.")
