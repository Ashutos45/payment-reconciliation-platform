from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.sql import func
from app.db.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    timestamp = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default="UNKNOWN")
    merchant = Column(String, nullable=True)
    source = Column(String, index=True, nullable=False) # 'internal' or 'bank'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Composite index to speed up lookups during matching
    __table_args__ = (
        Index('ix_transaction_id_source', 'transaction_id', 'source'),
    )

class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    id = Column(Integer, primary_key=True, index=True)
    
    internal_tx_id = Column(String, nullable=True, index=True)
    bank_tx_id = Column(String, nullable=True, index=True)
    
    status = Column(String, index=True, nullable=False) # 'Exact Match', 'Fuzzy Match', 'Unmatched'
    match_type = Column(String, nullable=True) # Granular type if needed
    match_score = Column(Float, nullable=True) # 0 to 100 confidence score
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('ix_recon_internal_bank', 'internal_tx_id', 'bank_tx_id'),
    )

class TransactionException(Base):
    __tablename__ = "exceptions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True, nullable=False)
    
    exception_type = Column(String, index=True, nullable=False)
    severity = Column(String, index=True, nullable=False, default="MEDIUM") # HIGH, MEDIUM, LOW
    details = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
