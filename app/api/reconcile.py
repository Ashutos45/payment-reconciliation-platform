from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from app.core.logger import logger
from app.db.database import get_db
from app.db.models import Transaction, ReconciliationResult, TransactionException
from app.services.matching_service import MatchingService
from app.services.exception_service import ExceptionService
from app.schemas.response import ReconciliationResponse, ReconciliationMetrics

router = APIRouter()

@router.post("/reconcile", response_model=ReconciliationResponse)
async def run_reconciliation(db: Session = Depends(get_db)):
    """
    Run the reconciliation engine on the data currently in the database.
    """
    logger.info("Received request to run reconciliation")
    
    try:
        # Load data from DB into Pandas
        internal_records = db.query(Transaction).filter(Transaction.source == "internal").all()
        bank_records = db.query(Transaction).filter(Transaction.source == "bank").all()
        
        if not internal_records or not bank_records:
            raise HTTPException(
                status_code=400, 
                detail="Missing data. Please upload both internal and bank transaction files first."
            )
            
        # Convert to pandas dataframes
        internal_df = pd.DataFrame([{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in internal_records])
        bank_df = pd.DataFrame([{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in bank_records])
        
        # 1. Run Matching Service
        matcher = MatchingService(internal_df, bank_df)
        reconciliation_results = matcher.reconcile()
        
        # 2. Run Exception Detection Service
        exceptions = ExceptionService.detect_exceptions(
            internal_df, 
            bank_df,
            reconciliation_results['matches'],
            reconciliation_results['unmatched_internal_records'],
            reconciliation_results['unmatched_bank_records']
        )
        
        # 3. Save Results to Database
        # Clear old results
        db.query(ReconciliationResult).delete()
        db.query(TransactionException).delete()
        
        # Insert new results
        db.bulk_insert_mappings(ReconciliationResult, reconciliation_results['matches'])
        db.bulk_insert_mappings(TransactionException, exceptions)
        db.commit()
        
        metrics = reconciliation_results['metrics']
        
        logger.info("Reconciliation completed successfully.")
        
        return ReconciliationResponse(
            message="Reconciliation completed successfully",
            metrics=ReconciliationMetrics(**metrics)
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Reconciliation process failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Reconciliation failed due to an internal error.")
