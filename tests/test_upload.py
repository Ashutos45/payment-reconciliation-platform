import pytest
import pandas as pd
import os
from app.services.ingestion_service import IngestionService

def test_csv_ingestion(tmp_path):
    # Create a temporary CSV
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text("transaction_id,amount,currency,timestamp,status,merchant\n1,100,USD,2026-05-12 10:00:00,SUCCESS,Amazon")
    
    df = IngestionService.ingest_file(str(csv_file), "internal")
    
    assert len(df) == 1
    assert df.iloc[0]['transaction_id'] == "1"
    assert df.iloc[0]['source'] == "internal"

def test_missing_columns(tmp_path):
    csv_file = tmp_path / "bad_data.csv"
    # Missing 'merchant' column
    csv_file.write_text("transaction_id,amount,currency,timestamp,status\n1,100,USD,2026-05-12 10:00:00,SUCCESS")
    
    with pytest.raises(ValueError, match="Missing required columns: merchant"):
        IngestionService.ingest_file(str(csv_file), "internal")
