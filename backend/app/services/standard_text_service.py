from app.utils.text_normalization import get_normalized_ocr_words
from sqlalchemy.orm import Session
from app.utils.text_extraction_utils import reconstruct_lines
from app.utils.filter_lines_utils import filter_lines
from app.utils.groupblocks_utils import group_invoice_blocks

def extract_processing_of_word(db: Session, invoice_id: int):
    normalized_words = get_normalized_ocr_words(db, invoice_id)
    lines = reconstruct_lines(normalized_words)
    filterd_lines=filter_lines(lines)
    blocks=group_invoice_blocks(filterd_lines)
    return blocks