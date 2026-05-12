from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import TransactionException
from app.schemas.reconciliation import ExceptionSchema

router = APIRouter()

@router.get("/exceptions", response_model=List[ExceptionSchema])
async def get_exceptions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all exceptions detected during the latest reconciliation run.
    """
    exceptions = db.query(TransactionException).offset(skip).limit(limit).all()
    return exceptions
