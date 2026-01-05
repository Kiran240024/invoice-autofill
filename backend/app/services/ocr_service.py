from app.core.config import  BASE_DIR
from app.utils.pdf_utils import pdf_to_images, extract_text_from_pdf
from pathlib import Path
from app.db.base import InvoiceFile
from sqlalchemy.orm import Session
import os
import cv2
from app.utils.image_utils import image_preprocessing

def process_invoice_ocr(db: Session,invoice_id: int):
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
    output_path=BASE_DIR/"storage/temp"/str(invoice_file.id) #temporary folder for pdf pages
    output_path.mkdir(parents=True, exist_ok=True)
    
    text_from_pdf=extract_text_from_pdf(pdf_path) #checking if pdf is digital or scanned
     #case 1: digital pdf, text extracted directly
    if text_from_pdf.strip():
        invoice_file.status="text extracted from digital pdf"
        db.commit()
        return
    
    #case 2: scanned pdf, convert to images and preprocess each image
    image_paths=pdf_to_images(pdf_path,output_path)
    for index,img_path in enumerate(image_paths,start=1):
        preprocessed_path=(BASE_DIR / "storage/pre-processed" / f"{invoice_file.id}_page_{index}.png")
        success= image_preprocessing(img_path,preprocessed_path)
        if not success:
            raise RuntimeError(f"Failed to write processed image for page {index}")
    invoice_file.status="preprocessed"
    db.commit()
    # Next perform ocr and update invoice_file.status="processed" and then commit db


def _process_image_invoice(db: Session,invoice_file: InvoiceFile):
    raw_image_path = invoice_file.file_path
    img = cv2.imread(str(raw_image_path))
    if img is None:
        raise ValueError(f"Failed to read image: {raw_image_path}")
    preprocessed_path=(BASE_DIR / "storage/pre-processed" / f"{invoice_file.id}.png") #single image
    success= image_preprocessing(raw_image_path,preprocessed_path)
    if not success:
        raise RuntimeError("Failed to write processed image")
    invoice_file.status="preprocessed"
    db.commit()
    # Next perform ocr and update invoice_file.status="processed" and then commit db