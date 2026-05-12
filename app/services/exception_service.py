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
                "severity": "HIGH",
                "details": f"Transaction present in internal system but missing in bank statement. Amount: {record['amount']}",
                "recommendation": "Investigate missing bank data with banking partner or verify internal validity."
            })
            
        for record in unmatched_bank:
            exceptions.append({
                "transaction_id": record["transaction_id"],
                "exception_type": "Missing Transaction",
                "severity": "HIGH",
                "details": f"Transaction present in bank statement but missing in internal system. Amount: {record['amount']}",
                "recommendation": "Identify why this transaction was not recorded in the internal ledger."
            })

        # 2. Duplicate Transaction
        internal_dupes = internal_df[internal_df.duplicated('transaction_id', keep=False)]
        for _, row in internal_dupes.iterrows():
            exceptions.append({
                "transaction_id": row['transaction_id'],
                "exception_type": "Duplicate Transaction",
                "severity": "HIGH",
                "details": f"Duplicate transaction found in internal records. Amount: {row['amount']}",
                "recommendation": "Review and prune duplicate internal records to prevent double-counting."
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
                        "severity": "MEDIUM",
                        "details": f"Internal amount: {int_tx['amount']}, Bank amount: {bnk_tx['amount']}",
                        "recommendation": "Reconcile the exact amount difference. Potential partial refund or fee deduction."
                    })
                
                # Check Delayed Settlement
                time_diff_mins = abs((int_tx['timestamp'] - bnk_tx['timestamp']).total_seconds() / 60)
                if time_diff_mins > settings.TIME_TOLERANCE_MINUTES:
                    exceptions.append({
                        "transaction_id": match['internal_tx_id'],
                        "exception_type": "Delayed Settlement",
                        "severity": "LOW",
                        "details": f"Settlement delayed by {time_diff_mins:.2f} minutes",
                        "recommendation": "Ensure payment gateway processing delays are within expected SLAs."
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
                    "severity": "HIGH",
                    "details": f"Internal status: {int_tx['status']}, Bank status: {bnk_tx['status']}",
                    "recommendation": "Bank has not reflected the refund. Check gateway settlement status."
                })
            elif 'refund' in str(bnk_tx['status']).lower() and 'refund' not in str(int_tx['status']).lower():
                exceptions.append({
                    "transaction_id": match['internal_tx_id'],
                    "exception_type": "Refund Mismatch",
                    "severity": "HIGH",
                    "details": f"Internal status: {int_tx['status']}, Bank status: {bnk_tx['status']}",
                    "recommendation": "Internal system missing refund status. Update internal ledger."
                })

        logger.info(f"Detected {len(exceptions)} exceptions")
        return exceptions
