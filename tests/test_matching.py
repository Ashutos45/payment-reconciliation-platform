import pandas as pd
from app.services.matching_service import MatchingService

def test_exact_match():
    internal_df = pd.DataFrame([
        {"transaction_id": "1", "amount": 100.0, "timestamp": pd.to_datetime("2026-05-12 10:00:00")}
    ])
    bank_df = pd.DataFrame([
        {"transaction_id": "1", "amount": 100.0, "timestamp": pd.to_datetime("2026-05-12 10:00:00")}
    ])
    
    matcher = MatchingService(internal_df, bank_df)
    results = matcher.reconcile()
    
    assert results['metrics']['exact_matches'] == 1
    assert results['metrics']['fuzzy_matches'] == 0
    assert results['metrics']['unmatched_internal'] == 0

def test_fuzzy_match():
    internal_df = pd.DataFrame([
        {"transaction_id": "TXN123456", "amount": 100.0, "timestamp": pd.to_datetime("2026-05-12 10:00:00")}
    ])
    bank_df = pd.DataFrame([
        {"transaction_id": "TXN123456-B", "amount": 100.0, "timestamp": pd.to_datetime("2026-05-12 10:00:00")}
    ])
    
    matcher = MatchingService(internal_df, bank_df)
    results = matcher.reconcile()
    
    assert results['metrics']['exact_matches'] == 0
    assert results['metrics']['fuzzy_matches'] == 1
    assert results['metrics']['unmatched_internal'] == 0
