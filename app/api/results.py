from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import ReconciliationResult
from app.schemas.reconciliation import ReconciliationResultSchema

router = APIRouter()

@router.get("/results", response_model=List[ReconciliationResultSchema])
async def get_results(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all matches and unmatched records from the latest reconciliation run.
    """
    results = db.query(ReconciliationResult).offset(skip).limit(limit).all()
    return results
