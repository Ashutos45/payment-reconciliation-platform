import pandas as pd
from typing import Dict, Any, List
import io
from app.core.logger import logger

class ReportService:
    @staticmethod
    def generate_excel_report(
        metrics: Dict[str, Any],
        matches: List[Dict[str, Any]],
        unmatched_internal: List[Dict[str, Any]],
        unmatched_bank: List[Dict[str, Any]],
        exceptions: List[Dict[str, Any]]
    ) -> bytes:
        """
        Generates an Excel file containing reconciliation results across multiple sheets.
        Returns the Excel file as bytes.
        """
        logger.info("Generating Excel report")
        
        output = io.BytesIO()
        
        # Use xlsxwriter engine for multiple sheets and formatting
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            
            # 1. Summary Metrics Sheet
            metrics_df = pd.DataFrame([metrics])
            metrics_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # 2. Matched Transactions Sheet
            if matches:
                matches_df = pd.DataFrame(matches)
                matches_df.to_excel(writer, sheet_name='Matched', index=False)
            else:
                pd.DataFrame({"Message": ["No matched transactions"]}).to_excel(writer, sheet_name='Matched', index=False)
                
            # 3. Unmatched Transactions Sheet
            unmatched_all = []
            for record in unmatched_internal:
                record_copy = record.copy()
                record_copy['source'] = 'internal'
                unmatched_all.append(record_copy)
            for record in unmatched_bank:
                record_copy = record.copy()
                record_copy['source'] = 'bank'
                unmatched_all.append(record_copy)
                
            if unmatched_all:
                unmatched_df = pd.DataFrame(unmatched_all)
                unmatched_df.to_excel(writer, sheet_name='Unmatched', index=False)
            else:
                pd.DataFrame({"Message": ["No unmatched transactions"]}).to_excel(writer, sheet_name='Unmatched', index=False)
                
            # 4. Exceptions Sheet
            if exceptions:
                exceptions_df = pd.DataFrame(exceptions)
                exceptions_df.to_excel(writer, sheet_name='Exceptions', index=False)
            else:
                pd.DataFrame({"Message": ["No exceptions detected"]}).to_excel(writer, sheet_name='Exceptions', index=False)
                
            # Formatting
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': False,
                'valign': 'top',
                'fg_color': '#4F81BD',
                'font_color': 'white',
                'border': 1
            })
            
            # Auto-adjust column widths and apply header format
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                
                # We need to know the dataframe to adjust widths
                if sheet_name == 'Summary':
                    df = metrics_df
                elif sheet_name == 'Matched' and matches:
                    df = matches_df
                elif sheet_name == 'Unmatched' and unmatched_all:
                    df = unmatched_df
                elif sheet_name == 'Exceptions' and exceptions:
                    df = exceptions_df
                else:
                    worksheet.set_column('A:Z', 20)
                    continue
                    
                # Write headers with format
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Adjust column widths based on content
                for i, col in enumerate(df.columns):
                    column_len = max(
                        df[col].astype(str).map(len).max(),
                        len(str(col))
                    ) + 2
                    worksheet.set_column(i, i, min(column_len, 50)) # Cap at 50 to avoid massive columns
                
        logger.info("Excel report generated successfully")
        return output.getvalue()
