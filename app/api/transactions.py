from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.database import get_db
from app.db.models import Transaction, ReconciliationResult, TransactionException
from app.schemas.transaction import TransactionSchema
from app.core.logger import logger

router = APIRouter(tags=["Transactions"])

@router.get("/transactions/{transaction_id}", summary="Search Transaction Details")
def get_transaction_details(
    transaction_id: str = Path(..., description="The ID of the transaction to search for"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Search for a specific transaction by its transaction_id.
    Returns the core transaction details, its reconciliation status, and any associated business exceptions.
    """
    logger.info(f"Searching for transaction: {transaction_id}")
    
    # 1. Find the transaction
    # Since there might be both internal and bank records for the same ID, fetch all
    tx_records = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).all()
    
    if not tx_records:
        logger.warning(f"Transaction not found: {transaction_id}")
        raise HTTPException(status_code=404, detail="Transaction not found in the system.")

    # 2. Find the reconciliation result
    recon_result = db.query(ReconciliationResult).filter(
        (ReconciliationResult.internal_tx_id == transaction_id) | 
        (ReconciliationResult.bank_tx_id == transaction_id)
    ).first()

    # 3. Find any exceptions
    exceptions = db.query(TransactionException).filter(
        TransactionException.transaction_id == transaction_id
    ).all()

    # Format response
    response = {
        "transaction_id": transaction_id,
        "records": [
            {
                "source": tx.source,
                "amount": tx.amount,
                "currency": tx.currency,
                "timestamp": tx.timestamp,
                "status": tx.status,
                "merchant": tx.merchant
            } for tx in tx_records
        ],
        "reconciliation": None,
        "exceptions": []
    }

    if recon_result:
        response["reconciliation"] = {
            "status": recon_result.status,
            "match_type": recon_result.match_type,
            "match_score": recon_result.match_score
        }

    if exceptions:
        response["exceptions"] = [
            {
                "type": exc.exception_type,
                "severity": exc.severity,
                "details": exc.details,
                "recommendation": exc.recommendation
            } for exc in exceptions
        ]

    return response
