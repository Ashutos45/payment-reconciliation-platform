from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class TransactionBase(BaseModel):
    transaction_id: str
    amount: float
    currency: str
    timestamp: datetime
    status: str
    merchant: str
    source: str # 'internal' or 'bank'

class TransactionCreate(TransactionBase):
    pass

class TransactionSchema(TransactionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
