from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.db.models import Transaction, ReconciliationResult, TransactionException

router = APIRouter()

@router.get("/metrics")
async def get_dashboard_metrics(db: Session = Depends(get_db)):
    """
    Get aggregated metrics for the dashboard.
    """
    total_internal = db.query(Transaction).filter(Transaction.source == "internal").count()
    total_bank = db.query(Transaction).filter(Transaction.source == "bank").count()
    
    exact_matches = db.query(ReconciliationResult).filter(ReconciliationResult.status == "Exact Match").count()
    fuzzy_matches = db.query(ReconciliationResult).filter(ReconciliationResult.status == "Fuzzy Match").count()
    
    total_exceptions = db.query(TransactionException).count()
    
    # Exceptions by type
    exceptions_by_type = db.query(
        TransactionException.exception_type, 
        func.count(TransactionException.id)
    ).group_by(TransactionException.exception_type).all()
    
    exceptions_dict = {type_: count for type_, count in exceptions_by_type}
    
    total_matched = exact_matches + fuzzy_matches
    match_rate = (total_matched / total_internal * 100) if total_internal > 0 else 0
    
    # Calculate unmatched amount
    # Simplified approach: Sum of amounts in internal transactions not in exact/fuzzy matches
    matched_internal_ids = db.query(ReconciliationResult.internal_tx_id).filter(ReconciliationResult.internal_tx_id.isnot(None)).all()
    matched_ids_list = [id_[0] for id_ in matched_internal_ids]
    
    unmatched_amount = db.query(func.sum(Transaction.amount)).filter(
        Transaction.source == "internal",
        Transaction.transaction_id.notin_(matched_ids_list) if matched_ids_list else True
    ).scalar() or 0.0

    return {
        "total_internal": total_internal,
        "total_bank": total_bank,
        "exact_matches": exact_matches,
        "fuzzy_matches": fuzzy_matches,
        "total_matched": total_matched,
        "match_rate": round(match_rate, 2),
        "total_exceptions": total_exceptions,
        "exceptions_by_type": exceptions_dict,
        "unmatched_amount": unmatched_amount
    }
