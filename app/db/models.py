from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True)
    amount = Column(Float)
    currency = Column(String)
    timestamp = Column(DateTime)
    status = Column(String)
    merchant = Column(String)
    source = Column(String, index=True) # E.g., 'internal' or 'bank'
    
    # Track when this record was added to our system
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    id = Column(Integer, primary_key=True, index=True)
    
    # Store references to original transaction IDs (not the database primary key)
    # for easier tracing. Can be null if unmatched on one side.
    internal_tx_id = Column(String, nullable=True, index=True)
    bank_tx_id = Column(String, nullable=True, index=True)
    
    # 'Exact Match', 'Fuzzy Match', 'Unmatched'
    status = Column(String, index=True)
    match_score = Column(Float, nullable=True) # 100 for exact, <100 for fuzzy
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TransactionException(Base):
    __tablename__ = "exceptions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True) # The original transaction_id
    
    # 'Missing Transaction', 'Duplicate Transaction', 'Amount Mismatch', 'Delayed Settlement'
    exception_type = Column(String, index=True)
    
    # JSON-like string or just text detailing the exception
    details = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
