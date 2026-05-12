import pandas as pd
from typing import List, Dict, Any
from app.core.logger import logger
from app.core.config import settings

class ExceptionService:
    @staticmethod
    def detect_exceptions(
        internal_df: pd.DataFrame, 
        bank_df: pd.DataFrame, 
        matches: List[Dict[str, Any]], 
        unmatched_internal: List[Dict[str, Any]], 
        unmatched_bank: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect business exceptions from the reconciliation results.
        """
        logger.info("Starting exception detection")
        exceptions = []

        # 1. Missing Transaction (in internal but not in bank, and vice versa)
        for record in unmatched_internal:
            exceptions.append({
                "transaction_id": record["transaction_id"],
                "exception_type": "Missing Transaction",
                "details": f"Transaction present in internal system but missing in bank statement. Amount: {record['amount']}"
            })
            
        for record in unmatched_bank:
            exceptions.append({
                "transaction_id": record["transaction_id"],
                "exception_type": "Missing Transaction",
                "details": f"Transaction present in bank statement but missing in internal system. Amount: {record['amount']}"
            })

        # 2. Duplicate Transaction
        internal_dupes = internal_df[internal_df.duplicated('transaction_id', keep=False)]
        for _, row in internal_dupes.iterrows():
            exceptions.append({
                "transaction_id": row['transaction_id'],
                "exception_type": "Duplicate Transaction",
                "details": f"Duplicate transaction found in internal records. Amount: {row['amount']}"
            })

        # 3. Amount Mismatch & Delayed Settlement (for fuzzy matches mostly)
        for match in matches:
            if match['status'] == 'Fuzzy Match':
                int_tx = internal_df[internal_df['transaction_id'] == match['internal_tx_id']].iloc[0]
                bnk_tx = bank_df[bank_df['transaction_id'] == match['bank_tx_id']].iloc[0]
                
                # Check Amount Mismatch
                if abs(int_tx['amount'] - bnk_tx['amount']) > settings.AMOUNT_TOLERANCE:
                    exceptions.append({
                        "transaction_id": match['internal_tx_id'],
                        "exception_type": "Amount Mismatch",
                        "details": f"Internal amount: {int_tx['amount']}, Bank amount: {bnk_tx['amount']}"
                    })
                
                # Check Delayed Settlement
                time_diff_mins = abs((int_tx['timestamp'] - bnk_tx['timestamp']).total_seconds() / 60)
                if time_diff_mins > settings.TIME_TOLERANCE_MINUTES:
                    exceptions.append({
                        "transaction_id": match['internal_tx_id'],
                        "exception_type": "Delayed Settlement",
                        "details": f"Settlement delayed by {time_diff_mins:.2f} minutes"
                    })
                    
        # 4. Refund Mismatch (Check status differences)
        # e.g., if one side says REFUND and the other says SUCCESS
        for match in matches:
            # Only exact and fuzzy matches have both sides
            int_tx = internal_df[internal_df['transaction_id'] == match['internal_tx_id']].iloc[0]
            bnk_tx = bank_df[bank_df['transaction_id'] == match['bank_tx_id']].iloc[0]
            
            if 'refund' in str(int_tx['status']).lower() and 'refund' not in str(bnk_tx['status']).lower():
                exceptions.append({
                    "transaction_id": match['internal_tx_id'],
                    "exception_type": "Refund Mismatch",
                    "details": f"Internal status: {int_tx['status']}, Bank status: {bnk_tx['status']}"
                })
            elif 'refund' in str(bnk_tx['status']).lower() and 'refund' not in str(int_tx['status']).lower():
                exceptions.append({
                    "transaction_id": match['internal_tx_id'],
                    "exception_type": "Refund Mismatch",
                    "details": f"Internal status: {int_tx['status']}, Bank status: {bnk_tx['status']}"
                })

        logger.info(f"Detected {len(exceptions)} exceptions")
        return exceptions
