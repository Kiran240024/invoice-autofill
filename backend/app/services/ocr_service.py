from app.core.config import PDF_STORAGE_DIR, IMAGE_STORAGE_DIR, BASE_DIR
from app.utils.pdf_utils import pdf_to_images
from pathlib import Path
from app.db.base import InvoiceFile
from app.db.session import init_db
from sqlalchemy.orm import Session
import os
import cv2
from utils.ocr_processing_utils import deskew, rescale_for_ocr
def process_invoice_pdf(db: Session,invoice_id: int):
    # Fetch the invoice file record from the database
    invoice_file = db.query(InvoiceFile).filter(InvoiceFile.id == invoice_id).first()
    if not invoice_file:
        raise ValueError(f"Invoice file with ID {invoice_id} not found.")
    invoice_file.status="processing"
    db.commit() 
    extension=os.path.splitext(invoice_file.original_filename)[1].lower()
    if extension==".pdf":
        _process_pdf_invoice(db,invoice_file)
    elif extension in [".png",".jpg",".jpeg"]:
        _process_image_invoice(db,invoice_file)
    else:
        raise ValueError(f"Unsupported file type: {extension}") 
    
    return {
        "invoice_id": invoice_file.id,
        "status": invoice_file.status
    }

def _process_pdf_invoice(db: Session,invoice_file: InvoiceFile):
    pdf_path = Path(invoice_file.file_path)
    output_path=BASE_DIR/"storage/temp/pdf_images"/str(invoice_file.id)
    output_path.mkdir(parents=True, exist_ok=True)
    # we convert to images first on the assumption that pdf is scanned and needs ocr 
    raw_image_paths = pdf_to_images(pdf_path, output_path)
    for idx,image_path in enumerate(raw_image_paths,start=1):
        img = cv2.imread(str(image_path))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        median_filtered = cv2.medianBlur(gray, 3) 
        binary = cv2.adaptiveThreshold(
        median_filtered, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 25, 2
        )
        kernel_bg = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        clean_bg = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_bg)
        deskewed=deskew(clean_bg)
        rescaled = rescale_for_ocr(deskewed)
        preprocessed_path = (
        BASE_DIR / "storage/processing_files" / f"{invoice_file.id}_page_{idx}.png"
        )

        preprocessed_path.parent.mkdir(parents=True, exist_ok=True)

        success = cv2.imwrite(str(preprocessed_path), rescaled)

        if not success:
            raise RuntimeError("Failed to write processed image")
        
    invoice_file.status="preprocessed"
    db.commit()
    # Next perform ocr and update invoice_file.status="processed" and then commit db

def _process_image_invoice(db: Session,invoice_file: InvoiceFile):
    raw_image_path = invoice_file.file_path
    img = cv2.imread(str(raw_image_path))
    if img is None:
        raise ValueError(f"Failed to read image: {raw_image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    median_filtered = cv2.medianBlur(gray, 3) 
    binary = cv2.adaptiveThreshold(
    median_filtered, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY, 25, 2
    )
    kernel_bg = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    clean_bg = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_bg)
    deskewed=deskew(clean_bg)
    rescaled = rescale_for_ocr(deskewed)
    preprocessed_path=(BASE_DIR / "storage/processing_files" / f"{invoice_file.id}.png")
    preprocessed_path.parent.mkdir(parents=True, exist_ok=True)
    success=cv2.imwrite(str(preprocessed_path), rescaled)
    if not success:
        raise RuntimeError("Failed to write processed image")
    
    invoice_file.status="preprocessed"
    db.commit()
    # Next perform ocr and update invoice_file.status="processed" and then commit db