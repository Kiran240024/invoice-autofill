import re

keywords=[
    "invoice","date","gst","gstin","total","amount","due","bill","to","from",
    "address","ship","tax","number","no.","invoice#","invoice number","irn",
    "rate","qty","quantity","description","hsn","eway","billed","buyer","receiver",
    "bank","account","ifsc","branch","terms","condition","cgst","sgst","igst",
    "subtotal","item","sl no","email","pin","pincode","post"
]

company_keywords=[
    "company","corp","ltd","inc","llc","pvt","enterprise","pvt ltd","co.","inc.",
    "corporation","industries","group","solutions","services","associates","textiles",
    "technologies","systems","international","global","mills","synthetics","traders"
]

def is_company_name(text: str) -> bool:
    """Check if line appears to be a company name"""
    lower = text.lower()
    
    # Check for company-related keywords
    if any(kw in lower for kw in company_keywords):
        return True
    
    # Check if line is mostly capitalized (common for company names)
    # At least 4 characters and more than 50% uppercase letters
    letters = [c for c in text if c.isalpha()]
    if len(letters) >= 4:
        uppercase_count = sum(1 for c in letters if c.isupper())
        if uppercase_count / len(letters) > 0.5:
            return True
    
    return False


def filter_lines(lines: list[dict]) -> list[dict]:
    """Filter lines to keep only meaningful invoice data.
    
    Keeps:
    - Lines with numbers (amounts, quantities, dates, etc.)
    - Lines with invoice keywords
    - Company names
    - Lines with contact info (email, phone, address)
    
    Removes:
    - Very short lines (< 5 chars)
    - Punctuation-only lines
    - Common noise patterns
    """
    filtered_lines = []
    
    for line in lines:
        text = line['text'].strip()
        lower = text.lower()

        # Drop very short lines
        if len(text) < 5:
            continue

        # Drop punctuation only lines
        if not re.search(r'[a-zA-Z0-9]', text):
            continue

        # Keep lines with numbers (amounts, quantities, dates, HSN codes, etc.)
        if re.search(r'\d', text):
            filtered_lines.append(line)
            continue

        # Keep lines with invoice-related keywords
        if any(kw in lower for kw in keywords):
            filtered_lines.append(line)
            continue

        # Keep company names
        if is_company_name(text):
            filtered_lines.append(line)
            continue
        
        # Drop everything else (noise)
        continue

    return filtered_lines
