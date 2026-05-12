from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class UploadResponse(BaseModel):
    message: str
    internal_records: int
    bank_records: int

class ReconciliationMetrics(BaseModel):
    total_internal_transactions: int
    total_bank_transactions: int
    exact_matches: int
    fuzzy_matches: int
    unmatched_internal: int
    unmatched_bank: int
    match_rate_percentage: float

class ReconciliationResponse(BaseModel):
    message: str
    metrics: ReconciliationMetrics

class ExceptionSummaryResponse(BaseModel):
    total_exceptions: int
    exceptions_by_type: Dict[str, int]
    recent_exceptions: List[Dict[str, Any]]
