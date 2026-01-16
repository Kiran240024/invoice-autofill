import unicodedata
from sqlalchemy.orm import Session
from app.db.base import InvoiceOCRData

def get_normalized_ocr_words(db: Session, invoice_id: int):
    rows = (
        db.query(InvoiceOCRData)
        .filter(InvoiceOCRData.invoice_id == invoice_id)
        .order_by(
            InvoiceOCRData.page_number,
            InvoiceOCRData.y,
            InvoiceOCRData.x
        )
        .all()
    )

    normalized_words = []

    for row in rows:
        normalized_text = normalize_unicode(row.text)

        

        normalized_words.append({
            "text":normalized_text ,
            "x": row.x,
            "y": row.y,
            "width": row.width,
            "height": row.height,
            "confidence": row.confidence,
            "page": row.page_number,
        })
    return normalized_words


def normalize_unicode(text: str) -> str:
    """
    Normalize unicode OCR artifacts safely.
    Fixes ligatures, full-width chars, and compatibility symbols.
    """
    if not text:
        return ""
    # Unicode compatibility normalization
    text = unicodedata.normalize("NFKC", text)
    # Rare OCR ligatures that sometimes survive NFKC
    LIGATURE_FIXES = {
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬀ": "ff",
        "ﬃ": "ffi",
        "ﬄ": "ffl",
    }
    for k, v in LIGATURE_FIXES.items():
        text = text.replace(k, v)
    return text
