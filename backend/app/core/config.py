from pathlib import Path

#base directory
BASE_DIR = Path(__file__).resolve().parent.parent

#storage paths
STORAGE_DIR=BASE_DIR / "storage/invoices/originals"
PDF_STORAGE_DIR=STORAGE_DIR/"pdf"
IMAGE_STORAGE=STORAGE_DIR/"images"

#valid file extensions
ALLOWED_MIME_TYPES={
    "application/pdf":"pdf",
    "image/jpeg":"jpeg",
    "image/png":"png"
}

#max allowed file size in bytes
MAX_FILE_SIZE=10*1024*1024  #10 MB