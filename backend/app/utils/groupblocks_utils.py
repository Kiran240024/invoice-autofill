from typing import List, Dict
import re

# -----------------------------
# CONFIG
# -----------------------------

SECTION_HEADERS = {
    "SELLER": [
        "INVOICE",
        "CIN NO",
        "IEC NO"
    ],
    "BILLED_TO": [
        "BILLED TO",
        "CONSIGNEE"
    ],
    "DELIVERY_AT": [
        "DELIVERY AT"
    ],
    "ITEMS_TABLE": [
        "DESCRIPTION OF GOODS",
        "HSN",
        "QTY",
        "RATE",
        "TAXABLE"
    ],
    "TOTALS": [
        "GRAND TOTAL",
        "ROUND OFF"
    ],
    "TAX": [
        "CGST",
        "SGST",
        "IGST",
        "VALUE IN WORDS"
    ],
    "FOOTER": [
        "CERTIFIED THAT",
        "PREPARED BY",
        "CHECKED BY",
        "AUTHORISED SIGNATORY"
    ]
}
SELLER_ONLY_KEYWORDS= [
    "BANK",
    "A/C",
    "ACCOUNT",
    "IFSC",
    "BRANCH",
    "CONTRACT",
    "LORRY",
    "LOT",
    "AGENT",
    "BAG",
    "TUBE"
]

ROLE_TOKENS = {
    "SELLER": ["SOLD BY"],
    "BILLED_TO": ["BILLING ADDRESS"],
    "DELIVERY_AT": ["SHIPPING ADDRESS"]
}


# -----------------------------
# HELPERS
# -----------------------------

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.upper()).strip()


def detect_section(text: str) -> str | None:
    t = normalize(text)
    for section, keys in SECTION_HEADERS.items():
        for k in keys:
            if k in t:
                return section
    return None


def split_columns_from_line(text: str) -> List[str]:
    """
    Column split strategy for line-level OCR.
    Uses | if present, else returns full text as single column.
    """
    if "|" in text:
        return [c.strip() for c in text.split("|") if c.strip()]
    return [text.strip()]


# -----------------------------
# PHASE 2 CORE PIPELINE
# -----------------------------

def phase2_block_builder(lines: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Input: line-level OCR rows
    Output: semantic blocks with columns
    """

    # Sort top-to-bottom, page-aware
    lines = sorted(lines, key=lambda l: (l["page"], l["y"]))

    blocks: Dict[str, List[Dict]] = {}
    current_section = "UNKNOWN"

    for line in lines:
        text = line["text"].strip()
        if not text:
            continue

        #  Detect section transitions
        detected = detect_section(text)
        if detected:
            current_section = detected
            blocks.setdefault(current_section, [])

        blocks.setdefault(current_section, [])

        #  Column split (TEXTUAL, not geometric)
        columns = split_columns_from_line(text)

        blocks[current_section].append({
            "page": line["page"],
            "y": line["y"],
            "columns": columns,
            "roles": line.get("roles", [])
        })

    return blocks

def is_label_driven_invoice(blocks) -> bool:
    text = " ".join(
        " ".join(col)
        for blk in blocks.get("SELLER", [])
        for col in blk["columns"]
    ).upper()

    return any(k in text for k in [
        "SOLD BY",
        "BILLING ADDRESS",
        "SHIPPING ADDRESS"
    ])


# -----------------------------
# POST-CLEANUP (OPTIONAL BUT IMPORTANT)
# -----------------------------

def merge_multiline_blocks(blocks: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """
    Merges consecutive lines into paragraph-like blocks
    (useful for SELLER, FOOTER)
    """
    merged = {}

    for section, rows in blocks.items():
        merged_rows = []
        buffer = None

        for r in rows:
            if buffer is None:
                buffer = r
                continue

            # Same page & close vertically → merge
            if r["page"] == buffer["page"] and abs(r["y"] - buffer["y"]) <= 15:
                buffer["columns"] += r["columns"]
            else:
                merged_rows.append(buffer)
                buffer = r

        if buffer:
            merged_rows.append(buffer)

        merged[section] = merged_rows

    return merged

def promote_unknown_blocks(blocks):
    seller_y = min(b["y"] for b in blocks.get("SELLER", [])) if blocks.get("SELLER") else 1e9

    promoted = []
    remaining_unknown = []

    for blk in blocks.get("UNKNOWN", []):
        text = " ".join(blk["columns"]).lower()

        if (
            blk["y"] < seller_y
            and any(k in text for k in ["company", "private", "limited", "unit", "formerly"])
        ):
            promoted.append(blk)
        else:
            remaining_unknown.append(blk)

    blocks["SELLER"] = promoted + blocks.get("SELLER", [])
    blocks["UNKNOWN"] = remaining_unknown
    return blocks

def extract_invoice_metadata(blocks):
    meta = []

    new_seller = []
    for blk in blocks.get("SELLER", []):
        cols = []
        for c in blk["columns"]:
            if "invoice no" in c.lower():
                meta.append({
                    "page": blk["page"],
                    "y": blk["y"],
                    "columns": [c]
                })
            else:
                cols.append(c)

        if cols:
            blk["columns"] = cols
            new_seller.append(blk)

    blocks["SELLER"] = new_seller
    blocks["INVOICE_METADATA"] = meta
    return blocks


GST_REGEX = r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b"
PAN_REGEX = r"\b[A-Z]{5}\d{4}[A-Z]\b"
def enrich_gst_pan_into_party_blocks(blocks):
    """
    Moves GST / PAN text into existing SELLER / BILLED_TO / DELIVERY_AT blocks
    instead of creating separate GST sections.
    """

    def extract_ids(columns):
        gst = []
        pan = []
        rest = []

        for c in columns:
            if re.search(GST_REGEX, c):
                gst.append(c)
            elif re.search(PAN_REGEX, c):
                pan.append(c)
            else:
                rest.append(c)

        return rest, gst, pan

    for section in ["SELLER", "BILLED_TO", "DELIVERY_AT"]:
        cleaned_rows = []

        for blk in blocks.get(section, []):
            rest, gst, pan = extract_ids(blk["columns"])

            # Reattach GST/PAN at the END of same block
            new_columns = rest + gst + pan

            blk["columns"] = new_columns
            cleaned_rows.append(blk)

        blocks[section] = cleaned_rows

    return blocks

def split_billed_delivery_columns(blocks: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    billed = []
    delivery = []
    seller_extra = []

    for blk in blocks.get("BILLED_TO", []):
        full_text = " ".join(blk["columns"]).upper()

        # 🚨 SELLER-ONLY override
        if any(k in full_text for k in SELLER_ONLY_KEYWORDS):
            seller_extra.append(blk)
            continue

        cols = blk["columns"]

        if len(cols) == 1:
            billed.append(blk)
            continue

        if len(cols) >= 2:
            billed.append({
                "page": blk["page"],
                "y": blk["y"],
                "columns": [cols[0]]
            })

            delivery.append({
                "page": blk["page"],
                "y": blk["y"],
                "columns": [cols[1]]
            })

    blocks["BILLED_TO"] = billed
    blocks["DELIVERY_AT"] = delivery
    blocks.setdefault("SELLER", []).extend(seller_extra)

    return blocks

def flatten_blocks_to_lines(blocks):
    """
    Converts merged blocks back into ordered, label-aware lines.
    Only used for label-driven invoices.
    """
    lines = []
    for section_rows in blocks.values():
        for blk in section_rows:
            for col in blk["columns"]:
                lines.append({
                    "page": blk["page"],
                    "y": blk["y"],
                    "text": col
                })
    return sorted(lines, key=lambda x: (x["page"], x["y"]))



def resolve_label_driven_invoice(blocks):
    """
    Final authority for e-commerce invoices.
    Ignores sections, uses explicit labels only.
    """
    lines = flatten_blocks_to_lines(blocks)

    seller, billed, delivery = [], [], []
    current = "SELLER"

    for line in lines:
        roles=line.get("roles", [])
        if "SELLER" in roles:
            current = "SELLER"
        elif "BILLED_TO" in roles:
            current = "BILLED_TO"
        elif "DELIVERY_AT" in roles:
            current = "DELIVERY_AT"
        
        target=(
            seller if current == "SELLER" else
            billed if current == "BILLED_TO" else
            delivery
        )
        target.append({
            "page": line["page"],
            "y": line["y"],
            "columns": [line["text"]]
        })

    blocks["SELLER"] = seller
    blocks["BILLED_TO"] = billed
    blocks["DELIVERY_AT"] = delivery
    return blocks



# -----------------------------
# PUBLIC ENTRYPOINT
# -----------------------------

def run_phase_2(lines: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Full Phase 2 pipeline
    """
    blocks = phase2_block_builder(lines)
    blocks = merge_multiline_blocks(blocks)
    blocks= promote_unknown_blocks(blocks)
    blocks= extract_invoice_metadata(blocks)
    blocks= enrich_gst_pan_into_party_blocks(blocks)
    if is_label_driven_invoice(blocks):
        blocks= resolve_label_driven_invoice(blocks)
    else:
        blocks= split_billed_delivery_columns(blocks)
    return blocks

'''def assign_spans_to_sections(spans):
    blocks = {
        "SELLER": [],
        "BILLED_TO": [],
        "DELIVERY_AT": [],
        "INVOICE_METADATA": [],
        "ITEMS_TABLE": [],
        "BANK": [],
        "UNKNOWN": []
    }

    ROLE_TO_SECTION = {
        "SELLER": "SELLER",
        "BILLED_TO": "BILLED_TO",
        "DELIVERY_AT": "DELIVERY_AT",
        "INVOICE_META": "INVOICE_METADATA",
        "ITEM": "ITEMS_TABLE",
        "BANK": "BANK"
    }

    for s in spans:
        section = ROLE_TO_SECTION.get(s["role"], "UNKNOWN")
        blocks[section].append({
            "page": s["page"],
            "y": s["y"],
            "columns": [s["text"]]
        })

    return blocks'''

