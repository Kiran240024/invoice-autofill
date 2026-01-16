from app.utils.text_normalization import get_normalized_ocr_words
from sqlalchemy.orm import Session
from app.utils.text_extraction_utils import reconstruct_lines

def extract_processing_of_word(db: Session, invoice_id: int):
    normalized_words = get_normalized_ocr_words(db, invoice_id)
    lines = reconstruct_lines(normalized_words)
    return lines
