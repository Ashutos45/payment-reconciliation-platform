from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
import pandas as pd
from typing import Dict, Any

from app.db.database import get_db
from app.db.models import Transaction, ReconciliationResult, TransactionException
from app.services.report_service import ReportService
from app.core.logger import logger

router = APIRouter()

@router.get("/export")
async def export_report(db: Session = Depends(get_db)):
    """
    Generate and download the reconciliation report as an Excel file.
    """
    logger.info("Request received to export report")
    
    try:
        # Fetch data
        internal_records = db.query(Transaction).filter(Transaction.source == "internal").all()
        bank_records = db.query(Transaction).filter(Transaction.source == "bank").all()
        
        matches = db.query(ReconciliationResult).all()
        exceptions = db.query(TransactionException).all()
        
        if not internal_records and not bank_records:
            raise HTTPException(status_code=400, detail="No data available to export")
            
        # Reconstruct metrics
        total_internal = len(internal_records)
        total_bank = len(bank_records)
        
        exact_matches = [m for m in matches if m.status == "Exact Match"]
        fuzzy_matches = [m for m in matches if m.status == "Fuzzy Match"]
        
        # We assume any transaction ID not in results is unmatched
        matched_internal_ids = set([m.internal_tx_id for m in matches if m.internal_tx_id])
        matched_bank_ids = set([m.bank_tx_id for m in matches if m.bank_tx_id])
        
        unmatched_internal = [
            {"transaction_id": r.transaction_id, "amount": r.amount, "timestamp": str(r.timestamp), "status": r.status} 
            for r in internal_records if r.transaction_id not in matched_internal_ids
        ]
        
        unmatched_bank = [
            {"transaction_id": r.transaction_id, "amount": r.amount, "timestamp": str(r.timestamp), "status": r.status} 
            for r in bank_records if r.transaction_id not in matched_bank_ids
        ]
        
        total_matched = len(exact_matches) + len(fuzzy_matches)
        match_rate = (total_matched / total_internal * 100) if total_internal > 0 else 0
        
        metrics = {
            "total_internal_transactions": total_internal,
            "total_bank_transactions": total_bank,
            "exact_matches": len(exact_matches),
            "fuzzy_matches": len(fuzzy_matches),
            "unmatched_internal": len(unmatched_internal),
            "unmatched_bank": len(unmatched_bank),
            "match_rate_percentage": round(match_rate, 2)
        }
        
        matches_list = [
            {"internal_tx_id": m.internal_tx_id, "bank_tx_id": m.bank_tx_id, "status": m.status, "score": m.match_score}
            for m in matches
        ]
        
        exceptions_list = [
            {"transaction_id": e.transaction_id, "exception_type": e.exception_type, "details": e.details}
            for e in exceptions
        ]
        
        # Generate Excel
        excel_bytes = ReportService.generate_excel_report(
            metrics=metrics,
            matches=matches_list,
            unmatched_internal=unmatched_internal,
            unmatched_bank=unmatched_bank,
            exceptions=exceptions_list
        )
        
        headers = {
            'Content-Disposition': 'attachment; filename="reconciliation_report.xlsx"'
        }
        
        return Response(content=excel_bytes, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to generate export: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate report")
