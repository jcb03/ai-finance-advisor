"""file_processor.py - File upload and processing"""

"""File upload and processing"""

import pandas as pd
import PyPDF2
import io
import streamlit as st
from typing import List, Dict, Optional, Tuple
import re
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class FileProcessor:
    """Handles file upload and processing for bank statements"""
    
    SUPPORTED_CSV_FORMATS = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
    
    SUPPORTED_PDF_FORMATS = ['application/pdf']
    
    @staticmethod
    def validate_file(uploaded_file) -> Tuple[bool, str]:
        """Validate uploaded file"""
        if not uploaded_file:
            return False, "No file uploaded"
        
        # Check file size (max 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            return False, "File size too large. Maximum 10MB allowed."
        
        # Check file type
        if uploaded_file.type not in FileProcessor.SUPPORTED_CSV_FORMATS + FileProcessor.SUPPORTED_PDF_FORMATS:
            return False, f"Unsupported file type: {uploaded_file.type}"
        
        return True, "File is valid"
    
    @staticmethod
    def process_csv_file(uploaded_file) -> Optional[pd.DataFrame]:
        """Process uploaded CSV file"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)  # Reset file pointer
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    logger.info(f"Successfully read CSV with encoding: {encoding}")
                    return df
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error reading CSV with encoding {encoding}: {e}")
                    continue
            
            # If all encodings fail, try with error handling
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='utf-8', errors='ignore')
            return df
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {e}")
            st.error(f"Error processing CSV file: {e}")
            return None
    
    @staticmethod
    def process_excel_file(uploaded_file) -> Optional[pd.DataFrame]:
        """Process uploaded Excel file"""
        try:
            df = pd.read_excel(uploaded_file)
            return df
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            st.error(f"Error processing Excel file: {e}")
            return None
    
    @staticmethod
    def process_pdf_file(uploaded_file) -> Optional[str]:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            text = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
                    continue
            
            if not text.strip():
                st.warning("No text could be extracted from the PDF. The file might be image-based.")
                return None
            
            return text
        except Exception as e:
            logger.error(f"Error processing PDF file: {e}")
            st.error(f"Error processing PDF file: {e}")
            return None
    
    @staticmethod
    def detect_csv_format(df: pd.DataFrame) -> str:
        """Detect the format of the CSV file"""
        columns = [col.lower().strip() for col in df.columns]
        
        # Common bank statement formats
        formats = {
            'chase': ['date', 'description', 'amount', 'type', 'balance'],
            'bofa': ['date', 'description', 'amount', 'running_bal'],
            'wells_fargo': ['date', 'amount', 'description'],
            'citi': ['date', 'description', 'debit', 'credit'],
            'generic': ['date', 'description', 'amount']
        }
        
        for format_name, required_cols in formats.items():
            if all(any(req_col in col for col in columns) for req_col in required_cols):
                return format_name
        
        return 'unknown'
    
    @staticmethod
    def standardize_csv_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Standardize CSV column names"""
        df = df.copy()
        
        # Column mapping for different variations
        column_mapping = {
            'date': ['date', 'transaction_date', 'trans_date', 'posting_date', 'post_date', 'transaction date'],
            'description': ['description', 'memo', 'details', 'transaction_details', 'payee', 'merchant'],
            'amount': ['amount', 'transaction_amount', 'trans_amount'],
            'debit': ['debit', 'withdrawal', 'out', 'outgoing'],
            'credit': ['credit', 'deposit', 'in', 'incoming'],
            'balance': ['balance', 'running_balance', 'account_balance', 'running_bal'],
            'category': ['category', 'type', 'transaction_type']
        }
        
        # Convert column names to lowercase for matching
        df.columns = df.columns.str.lower().str.strip()
        
        # Standardize column names
        for standard_col, variations in column_mapping.items():
            for variation in variations:
                if variation in df.columns:
                    df = df.rename(columns={variation: standard_col})
                    break
        
        return df
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """Parse date string in various formats"""
        if pd.isna(date_str) or not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # Common date formats
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m/%d/%y',
            '%d/%m/%Y',
            '%d/%m/%y',
            '%m-%d-%Y',
            '%m-%d-%y',
            '%d-%m-%Y',
            '%d-%m-%y',
            '%Y/%m/%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        # Try pandas date parser as fallback
        try:
            return pd.to_datetime(date_str).date()
        except:
            logger.warning(f"Could not parse date: {date_str}")
            return None
    
    @staticmethod
    def parse_amount(amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        if pd.isna(amount_str) or not amount_str:
            return None
        
        amount_str = str(amount_str).strip()
        
        # Remove currency symbols and spaces
        amount_str = re.sub(r'[$€£¥₹,\s]', '', amount_str)
        
        # Handle parentheses as negative (accounting format)
        if amount_str.startswith('(') and amount_str.endswith(')'):
            amount_str = '-' + amount_str[1:-1]
        
        try:
            return float(amount_str)
        except ValueError:
            logger.warning(f"Could not parse amount: {amount_str}")
            return None
    
    @staticmethod
    def parse_transactions_from_csv(df: pd.DataFrame) -> List[Dict]:
        """Parse transactions from CSV DataFrame"""
        transactions = []
        
        if df.empty:
            return transactions
        
        # Standardize columns
        df = FileProcessor.standardize_csv_columns(df)
        
        # Check for required columns
        required_columns = ['date', 'description']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {missing_columns}")
            return transactions
        
        # Handle different amount column scenarios
        amount_column = None
        if 'amount' in df.columns:
            amount_column = 'amount'
        elif 'debit' in df.columns and 'credit' in df.columns:
            # Combine debit and credit columns
            df['amount'] = df['credit'].fillna(0) - df['debit'].fillna(0)
            amount_column = 'amount'
        else:
            st.error("No amount column found. Please ensure your CSV has 'amount', or 'debit' and 'credit' columns.")
            return transactions
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Parse date
                transaction_date = FileProcessor.parse_date(row['date'])
                if not transaction_date:
                    logger.warning(f"Skipping row {index}: Invalid date")
                    continue
                
                # Parse amount
                amount = FileProcessor.parse_amount(row[amount_column])
                if amount is None:
                    logger.warning(f"Skipping row {index}: Invalid amount")
                    continue
                
                # Clean description
                description = str(row['description']).strip()
                if not description or description.lower() in ['nan', 'none', '']:
                    logger.warning(f"Skipping row {index}: Empty description")
                    continue
                
                # Get category if available
                category = None
                if 'category' in df.columns and pd.notna(row['category']):
                    category = str(row['category']).strip()
                
                transaction = {
                    'description': description,
                    'amount': amount,
                    'transaction_date': transaction_date,
                    'category': category,
                    'account_type': 'Bank Account'
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                logger.warning(f"Error processing row {index}: {e}")
                continue
        
        return transactions
    
    @staticmethod
    def parse_transactions_from_pdf(text: str) -> List[Dict]:
        """Parse transactions from PDF text"""
        transactions = []
        
        if not text:
            return transactions
        
        # Common patterns for bank statements
        patterns = [
            # MM/DD/YYYY Description Amount
            r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+(-?\$?[\d,]+\.?\d*)',
            # MM-DD-YYYY Description Amount
            r'(\d{1,2}-\d{1,2}-\d{2,4})\s+(.+?)\s+(-?\$?[\d,]+\.?\d*)',
            # DD/MM/YYYY Description Amount
            r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+(-?\$?[\d,]+\.?\d*)',
            # YYYY-MM-DD Description Amount
            r'(\d{4}-\d{1,2}-\d{1,2})\s+(.+?)\s+(-?\$?[\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                try:
                    date_str, description, amount_str = match
                    
                    # Parse date
                    transaction_date = FileProcessor.parse_date(date_str)
                    if not transaction_date:
                        continue
                    
                    # Parse amount
                    amount = FileProcessor.parse_amount(amount_str)
                    if amount is None:
                        continue
                    
                    # Clean description
                    description = description.strip()
                    if not description:
                        continue
                    
                    transaction = {
                        'description': description,
                        'amount': amount,
                        'transaction_date': transaction_date,
                        'category': None,
                        'account_type': 'Bank Account'
                    }
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    logger.warning(f"Error parsing PDF transaction: {e}")
                    continue
        
        return transactions
    
    @staticmethod
    def preview_transactions(transactions: List[Dict], limit: int = 5) -> pd.DataFrame:
        """Preview parsed transactions"""
        if not transactions:
            return pd.DataFrame()
        
        preview_data = transactions[:limit]
        df = pd.DataFrame(preview_data)
        
        # Format for display
        if 'amount' in df.columns:
            df['amount'] = df['amount'].apply(lambda x: f"${x:,.2f}")
        
        return df
    
    @staticmethod
    def get_file_stats(transactions: List[Dict]) -> Dict:
        """Get statistics about parsed transactions"""
        if not transactions:
            return {}
        
        df = pd.DataFrame(transactions)
        
        stats = {
            'total_transactions': len(transactions),
            'date_range': {
                'start': df['transaction_date'].min(),
                'end': df['transaction_date'].max()
            },
            'amount_range': {
                'min': df['amount'].min(),
                'max': df['amount'].max()
            },
            'total_credits': df[df['amount'] > 0]['amount'].sum() if len(df[df['amount'] > 0]) > 0 else 0,
            'total_debits': abs(df[df['amount'] < 0]['amount'].sum()) if len(df[df['amount'] < 0]) > 0 else 0,
            'unique_descriptions': df['description'].nunique()
        }
        
        return stats
