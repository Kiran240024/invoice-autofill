from app.core.config import PDF_STORAGE_DIR, IMAGE_STORAGE_DIR, BASE_DIR
from app.utils.pdf_utils import pdf_to_images
from pathlib import Path
from app.db.base import InvoiceFile
from app.db.session import init_db
from sqlalchemy.orm import Session
import os

def process_invoice_pdf(db: Session,invoice_id: int):
    # Fetch the invoice file record from the database
    invoice_file = db.query(InvoiceFile).filter(InvoiceFile.id == invoice_id).first()
    if not invoice_file:
        raise ValueError(f"Invoice file with ID {invoice_id} not found.")
    invoice_file.status="processing"
    db.commit() 
    extension=os.path.splitext(invoice_file.original_filename)[1].lower()
    if extension==".pdf":
        return _process_pdf_invoice(db,invoice_file)
    elif extension in [".png",".jpg",".jpeg"]:
        return _process_image_invoice(db,invoice_file)
    else:
        raise ValueError(f"Unsupported file type: {extension}") 

def _process_pdf_invoice(db: Session,invoice_file: InvoiceFile):
    pdf_path = Path(invoice_file.file_path)
    output_path=BASE_DIR/"storage/temp/pdf_images"

    # we convert to images first on the assumption that pdf is scanned and needs ocr 
    image_paths = pdf_to_images(pdf_path, output_path)
    # Here you would typically call your OCR processing function on the image_paths
    # For demonstration, we'll just update the status to 'processed'
    invoice_file.status="processed"
    db.commit()
    return image_paths

def _process_image_invoice(db: Session,invoice_file: InvoiceFile):
    # Here you would typically call your OCR processing function on the image file
    # For demonstration, we'll just update the status to 'processed'
    invoice_file.status="processed"
    db.commit()
    return [invoice_file.file_path]