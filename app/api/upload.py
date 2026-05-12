from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import os
import shutil
from typing import Dict, Any

from app.core.logger import logger
from app.core.config import settings
from app.db.database import get_db
from app.db.models import Transaction
from app.services.ingestion_service import IngestionService
from app.schemas.response import UploadResponse

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    internal_file: UploadFile = File(...),
    bank_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload both internal and bank transaction files.
    The files are temporarily saved, processed, and loaded into the database.
    """
    logger.info("Received request to upload transaction files")
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    internal_path = os.path.join(settings.UPLOAD_DIR, "internal_temp_" + internal_file.filename)
    bank_path = os.path.join(settings.UPLOAD_DIR, "bank_temp_" + bank_file.filename)
    
    try:
        # Save files
        with open(internal_path, "wb") as buffer:
            shutil.copyfileobj(internal_file.file, buffer)
            
        with open(bank_path, "wb") as buffer:
            shutil.copyfileobj(bank_file.file, buffer)
            
        # Ingest and clean files
        internal_df = IngestionService.ingest_file(internal_path, "internal")
        bank_df = IngestionService.ingest_file(bank_path, "bank")
        
        # Clear existing DB data for simplicity in this workflow
        # In a real system, you might append and run incrementally
        db.query(Transaction).delete()
        
        # Bulk insert
        internal_records = internal_df.to_dict(orient="records")
        bank_records = bank_df.to_dict(orient="records")
        
        db.bulk_insert_mappings(Transaction, internal_records + bank_records)
        db.commit()
        
        logger.info(f"Successfully processed {len(internal_records)} internal and {len(bank_records)} bank records.")
        
        return UploadResponse(
            message="Files uploaded and processed successfully",
            internal_records=len(internal_records),
            bank_records=len(bank_records)
        )
        
    except ValueError as ve:
        logger.warning(f"Validation error during upload: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception(f"Upload failed with unexpected error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred during file processing: {str(e)}")
    finally:
        # Cleanup temp files
        if os.path.exists(internal_path):
            os.remove(internal_path)
        if os.path.exists(bank_path):
            os.remove(bank_path)
