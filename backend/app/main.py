from fastapi import FastAPI
from app.api.routes.upload import router as upload_router
  # adjust import to your router path
from app.db.session import engine
from app.db import Base
# Create all tables (if not using Alembic migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Invoice Processing API",
    version="1.0.0"
)

# Include your router
app.include_router(upload_router, prefix="/api")

# Optional root endpoint
@app.get("/")
def root():
    return {"message": "Invoice Upload API is running"}
