import os
import pandas as pd
from typing import List, Optional
from app.core.logger import logger

REQUIRED_COLUMNS = [
    "transaction_id",
    "amount",
    "currency",
    "timestamp",
    "status",
    "merchant"
]

class IngestionService:
    @staticmethod
    def _read_file(file_path: str) -> pd.DataFrame:
        """Read CSV or Excel file based on extension safely."""
        _, ext = os.path.splitext(file_path)
        logger.debug(f"Attempting to read file {file_path} with extension {ext}")
        try:
            if ext.lower() == '.csv':
                # Use on_bad_lines to prevent crashing on malformed CSV files
                return pd.read_csv(file_path, on_bad_lines='skip')
            elif ext.lower() in ['.xls', '.xlsx']:
                return pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        except Exception as e:
            logger.exception(f"Error reading file {file_path}")
            raise ValueError(f"Could not read file {os.path.basename(file_path)}. Detail: {str(e)}")

    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> None:
        """Ensure all required columns exist in the DataFrame."""
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            error_msg = f"Missing required columns: {', '.join(missing_cols)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    @staticmethod
    def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """Clean the dataframe by handling missing values and data types."""
        # Drop rows where critical identifying information is missing
        initial_count = len(df)
        df = df.dropna(subset=['transaction_id', 'amount', 'timestamp'])
        logger.debug(f"Dropped {initial_count - len(df)} rows due to missing critical columns")
        
        # Ensure timestamp is datetime
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            invalid_dates = df['timestamp'].isna().sum()
            if invalid_dates > 0:
                logger.warning(f"Found {invalid_dates} rows with invalid dates. Dropping them.")
                df = df.dropna(subset=['timestamp'])
        except Exception as e:
            logger.exception(f"Error parsing timestamps")
            raise ValueError(f"Invalid timestamp format found. Detail: {str(e)}")
            
        # Ensure amount is numeric
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Fill missing string values
        df['currency'] = df['currency'].fillna('UNKNOWN')
        df['status'] = df['status'].fillna('UNKNOWN')
        df['merchant'] = df['merchant'].fillna('UNKNOWN')
        
        # Convert transaction_id to string to prevent formatting issues
        df['transaction_id'] = df['transaction_id'].astype(str)
        
        return df

    @classmethod
    def ingest_file(cls, file_path: str, source_type: str) -> pd.DataFrame:
        """
        Main entrypoint to ingest, validate, and clean a file.
        source_type is typically 'internal' or 'bank'
        """
        logger.info(f"Starting ingestion for file: {file_path} [Source: {source_type}]")
        
        # 1. Read the file
        df = cls._read_file(file_path)
        logger.debug(f"Read {len(df)} rows from {file_path}")
        
        # 2. Validate columns
        cls._validate_columns(df)
        
        # 3. Clean and format data
        cleaned_df = cls._clean_data(df)
        
        # 4. Add the source type
        cleaned_df['source'] = source_type
        
        logger.info(f"Successfully ingested {len(cleaned_df)} records from {file_path}")
        return cleaned_df
