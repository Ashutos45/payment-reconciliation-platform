import pandas as pd
from typing import Dict, Any, Tuple
from rapidfuzz import fuzz
from app.core.config import settings
from app.core.logger import logger

class MatchingService:
    def __init__(self, internal_df: pd.DataFrame, bank_df: pd.DataFrame):
        self.internal_df = internal_df.copy()
        self.bank_df = bank_df.copy()
        
        # Track matches
        self.exact_matches = []
        self.fuzzy_matches = []
        
        # Ensure 'matched' flag exists
        self.internal_df['matched'] = False
        self.bank_df['matched'] = False

    def _is_amount_within_tolerance(self, amount1: float, amount2: float) -> bool:
        """Check if difference is within amount tolerance."""
        return abs(amount1 - amount2) <= settings.AMOUNT_TOLERANCE

    def _is_time_within_tolerance(self, time1: pd.Timestamp, time2: pd.Timestamp) -> bool:
        """Check if difference is within time tolerance."""
        diff_minutes = abs((time1 - time2).total_seconds() / 60)
        return diff_minutes <= settings.TIME_TOLERANCE_MINUTES

    def _run_exact_matching(self) -> None:
        """
        Exact matching based on exact transaction_id, amount, and timestamp.
        """
        logger.info("Starting Exact Matching phase")
        
        # Merge on transaction_id
        # We only consider rows that haven't been matched yet
        unmatched_int = self.internal_df[~self.internal_df['matched']]
        unmatched_bnk = self.bank_df[~self.bank_df['matched']]
        
        # Join on exact ID
        merged = pd.merge(
            unmatched_int, 
            unmatched_bnk, 
            on='transaction_id', 
            suffixes=('_int', '_bnk')
        )
        
        exact_count = 0
        for _, row in merged.iterrows():
            if (
                self._is_amount_within_tolerance(row['amount_int'], row['amount_bnk']) and
                self._is_time_within_tolerance(row['timestamp_int'], row['timestamp_bnk'])
            ):
                # We have an exact match
                tx_id = row['transaction_id']
                
                # Mark as matched in original dataframes
                int_idx = self.internal_df[self.internal_df['transaction_id'] == tx_id].index[0]
                bnk_idx = self.bank_df[self.bank_df['transaction_id'] == tx_id].index[0]
                
                self.internal_df.at[int_idx, 'matched'] = True
                self.bank_df.at[bnk_idx, 'matched'] = True
                
                self.exact_matches.append({
                    'internal_tx_id': tx_id,
                    'bank_tx_id': tx_id,
                    'status': 'Exact Match',
                    'match_score': 100.0
                })
                exact_count += 1
                
        logger.info(f"Exact matching completed. Found {exact_count} exact matches.")

    def _run_fuzzy_matching(self) -> None:
        """
        Fuzzy matching for records that failed exact match.
        Matches on partial transaction IDs using RapidFuzz.
        """
        logger.info("Starting Fuzzy Matching phase")
        
        unmatched_int = self.internal_df[~self.internal_df['matched']]
        unmatched_bnk = self.bank_df[~self.bank_df['matched']]
        
        fuzzy_count = 0
        
        # Convert to records for iteration
        for int_idx, int_row in unmatched_int.iterrows():
            best_match_idx = None
            best_score = 0
            
            for bnk_idx, bnk_row in unmatched_bnk.iterrows():
                # We only want to fuzzy match if amounts and time are within tolerance
                # even if the ID got mangled
                if (
                    self._is_amount_within_tolerance(int_row['amount'], bnk_row['amount']) and
                    self._is_time_within_tolerance(int_row['timestamp'], bnk_row['timestamp'])
                ):
                    # Compare transaction IDs fuzzily
                    score = fuzz.ratio(str(int_row['transaction_id']), str(bnk_row['transaction_id']))
                    
                    if score > best_score and score >= 80: # 80 is our threshold for fuzzy match
                        best_score = score
                        best_match_idx = bnk_idx
            
            if best_match_idx is not None:
                # Mark as matched
                self.internal_df.at[int_idx, 'matched'] = True
                self.bank_df.at[best_match_idx, 'matched'] = True
                # Remove from future comparisons
                unmatched_bnk = unmatched_bnk.drop(best_match_idx)
                
                self.fuzzy_matches.append({
                    'internal_tx_id': int_row['transaction_id'],
                    'bank_tx_id': self.bank_df.at[best_match_idx, 'transaction_id'],
                    'status': 'Fuzzy Match',
                    'match_score': round(best_score, 2)
                })
                fuzzy_count += 1
                
        logger.info(f"Fuzzy matching completed. Found {fuzzy_count} fuzzy matches.")

    def reconcile(self) -> Dict[str, Any]:
        """
        Executes the full reconciliation process.
        """
        logger.info("Starting Reconciliation process")
        
        self._run_exact_matching()
        self._run_fuzzy_matching()
        
        # Determine unmatched records
        unmatched_internal = self.internal_df[~self.internal_df['matched']].to_dict('records')
        unmatched_bank = self.bank_df[~self.bank_df['matched']].to_dict('records')
        
        total_matched = len(self.exact_matches) + len(self.fuzzy_matches)
        total_internal = len(self.internal_df)
        match_rate = (total_matched / total_internal * 100) if total_internal > 0 else 0
        
        return {
            "metrics": {
                "total_internal_transactions": total_internal,
                "total_bank_transactions": len(self.bank_df),
                "exact_matches": len(self.exact_matches),
                "fuzzy_matches": len(self.fuzzy_matches),
                "unmatched_internal": len(unmatched_internal),
                "unmatched_bank": len(unmatched_bank),
                "match_rate_percentage": round(match_rate, 2)
            },
            "matches": self.exact_matches + self.fuzzy_matches,
            "unmatched_internal_records": unmatched_internal,
            "unmatched_bank_records": unmatched_bank
        }
