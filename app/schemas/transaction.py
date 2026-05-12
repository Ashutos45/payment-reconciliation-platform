from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class TransactionBase(BaseModel):
    transaction_id: str = Field(..., description="Unique identifier for the transaction", example="TXN-1001")
    amount: float = Field(..., description="Transaction amount", example=50.00)
    currency: str = Field(..., description="Currency code", example="USD")
    timestamp: datetime = Field(..., description="Time of the transaction")
    status: str = Field(..., description="Transaction status", example="SUCCESS")
    merchant: Optional[str] = Field(None, description="Merchant name", example="Amazon")
    source: str = Field(..., description="Source of transaction: 'internal' or 'bank'", example="internal")

class TransactionCreate(TransactionBase):
    pass

class TransactionSchema(TransactionBase):
    id: int = Field(..., description="Database primary key")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
