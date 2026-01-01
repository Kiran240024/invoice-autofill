from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
import os
from app.db.base import InvoiceFile
from app.utils.file_utils import (
    get_file_size_bytes,
    is_allowed_file,
    get_file_category,
    generate_safe_filename,
    save_file
)

BASE_UPLOAD_DIR = "backend/app/storage/invoices/original"
MAX_FILE_SIZE_MB = 10  # maximum allowed file size in MB

def upload_invoice_service(file: UploadFile, db: Session):
    # 1. Validate file type
    if not is_allowed_file(file.content_type):
        raise HTTPException(
            status_code=400,
            detail="Only PDF, PNG, and JPG files are allowed"
        )

    # 2. Validate file size
    size_mb = get_file_size_bytes(file) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
        )
    # 3. Decide subfolder based on file type
    category = get_file_category(file.content_type)  
    # example: "pdf" or "image"
    if not category:
        raise HTTPException(status_code=400, detail="Unsupported file type")


    upload_dir = os.path.join(BASE_UPLOAD_DIR, category)
    os.makedirs(upload_dir, exist_ok=True)

    # 4. Generate safe filename
    stored_filename = generate_safe_filename(file.filename)
    file_path = os.path.join(upload_dir, stored_filename)
   

    # 5. Save the file to disk
    save_file(file, file_path)

    # 6. Save metadata to database
    invoice_file = InvoiceFile(
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_type=file.content_type,
        status="uploaded"
    )

    db.add(invoice_file)
    db.commit()
    db.refresh(invoice_file)

    # 7. Return response
    return {
        "message": "Invoice uploaded successfully",
        "invoice_id": invoice_file.id,
        "status": invoice_file.status,
        "category": category
    }