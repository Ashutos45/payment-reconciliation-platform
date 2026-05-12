from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class ReconciliationResultBase(BaseModel):
    internal_tx_id: Optional[str] = Field(None, description="Internal Transaction ID", example="TXN-1001")
    bank_tx_id: Optional[str] = Field(None, description="Bank Transaction ID", example="TXN-1001")
    status: str = Field(..., description="Overall Match Status", example="Exact Match")
    match_type: Optional[str] = Field(None, description="Granular match type", example="Exact Amount, Exact ID")
    match_score: Optional[float] = Field(None, description="Confidence score of the match 0-100", example=100.0)

class ReconciliationResultCreate(ReconciliationResultBase):
    pass

class ReconciliationResultSchema(ReconciliationResultBase):
    id: int = Field(..., description="Database primary key")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ExceptionBase(BaseModel):
    transaction_id: str = Field(..., description="Transaction ID causing exception", example="TXN-1001")
    exception_type: str = Field(..., description="Type of exception", example="Missing Transaction")
    severity: str = Field("MEDIUM", description="Severity of exception: HIGH, MEDIUM, LOW", example="HIGH")
    details: str = Field(..., description="Detailed description", example="Transaction present in internal but missing in bank")
    recommendation: Optional[str] = Field(None, description="Actionable recommendation", example="Investigate with banking partner")

class ExceptionCreate(ExceptionBase):
    pass

class ExceptionSchema(ExceptionBase):
    id: int = Field(..., description="Database primary key")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
