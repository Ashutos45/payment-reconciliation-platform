from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class ReconciliationResultBase(BaseModel):
    internal_tx_id: Optional[str] = None
    bank_tx_id: Optional[str] = None
    status: str
    match_score: Optional[float] = None

class ReconciliationResultCreate(ReconciliationResultBase):
    pass

class ReconciliationResultSchema(ReconciliationResultBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExceptionBase(BaseModel):
    transaction_id: str
    exception_type: str
    details: str

class ExceptionCreate(ExceptionBase):
    pass

class ExceptionSchema(ExceptionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
