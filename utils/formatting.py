def format_currency(value, language="English"):
    if value is None:
        return "N/A"
    
    try:
        val = float(value)
    except (ValueError, TypeError):
        return "N/A"
        
    abs_val = abs(val)
    
    if abs_val >= 10000000:
        formatted = f"₹{val / 10000000:,.2f} Crore"
    elif abs_val >= 100000:
        formatted = f"₹{val / 100000:,.2f} Lakh"
    else:
        # Quick hack for Indian formatting
        s, *d = str(int(val)).partition(".")
        r = ",".join([s[x-2:x] for x in range(-3, -len(s), -2)][::-1] + [s[-3:]])
        formatted = f"₹{r}"
        if d and d[1]:
            formatted += "." + d[1]

    return formatted

TRANSLATIONS = {
    "English": {
        "overview": "Overview",
        "business_profile": "Business Profile",
        "financial_health": "Financial Health",
        "sales_revenue": "Sales & Revenue",
        "customers": "Customers",
        "inventory": "Inventory",
        "vendors_payables": "Vendors & Payables",
        "forecasting": "Forecasting",
        "risk_analysis": "Risk Analysis",
        "government_schemes": "Government Schemes",
        "ai_advisor": "AI Advisor",
        "data_quality": "Data Quality",
        "loans_emi": "Loans & EMI"
    },
    "हिन्दी": {
        "overview": "अवलोकन",
        "business_profile": "व्यापार प्रोफ़ाइल",
        "financial_health": "वित्तीय स्वास्थ्य",
        "sales_revenue": "बिक्री और राजस्व",
        "customers": "ग्राहक",
        "inventory": "इन्वेंटरी",
        "vendors_payables": "विक्रेता और देयताएं",
        "forecasting": "पूर्वानुमान",
        "risk_analysis": "जोखिम विश्लेषण",
        "government_schemes": "सरकारी योजनाएं",
        "ai_advisor": "एआई सलाहकार",
        "data_quality": "डेटा गुणवत्ता",
        "loans_emi": "ऋण और ईएमआई"
    }
}

def t(key, lang="English"):
    """Translation function"""
    try:
        return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)
    except Exception:
        return key
