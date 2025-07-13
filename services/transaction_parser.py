"""transaction_parser.py - Transaction parsing and categorization"""

"""Transaction parsing and categorization"""

import streamlit as st
from openai import OpenAI
from typing import List, Dict, Optional
import json
from datetime import datetime
import logging
from config.settings import Settings

logger = logging.getLogger(__name__)

class TransactionCategorizer:
    """Handles AI-powered transaction categorization"""
    
    def __init__(self):
        self.client = OpenAI(api_key=Settings.openai_api_key())  # Use method
        self.categories = Settings.TRANSACTION_CATEGORIES 
    
    def categorize_transaction(self, description: str, amount: float) -> Dict:
        """Categorize a single transaction using GPT-4"""
        try:
            # Determine if it's income or expense
            transaction_type = "income" if amount < 0 else "expense"
            
            prompt = f"""
            Categorize this financial transaction:
            Description: {description}
            Amount: ${abs(amount):.2f}
            Type: {transaction_type}
            
            Available categories: {', '.join(self.categories)}
            
            Rules:
            - For income transactions (negative amounts), use "Income" category
            - For expense transactions (positive amounts), choose the most appropriate category
            - Consider merchant names, transaction descriptions, and common spending patterns
            - Be consistent with similar transactions
            
            Return a JSON object with:
            - "category": the most appropriate category from the list
            - "confidence": confidence score (0-100)
            - "reasoning": brief explanation of why this category was chosen
            
            Example: {{"category": "Groceries", "confidence": 95, "reasoning": "Purchase at supermarket chain"}}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial transaction categorization expert. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate result
            if result.get('category') not in self.categories:
                result['category'] = 'Other'
                result['confidence'] = 50
                result['reasoning'] = 'Category not in predefined list'
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in categorization: {e}")
            return {
                "category": "Other",
                "confidence": 0,
                "reasoning": "JSON parsing failed"
            }
        except Exception as e:
            logger.error(f"Error categorizing transaction: {e}")
            return {
                "category": "Other",
                "confidence": 0,
                "reasoning": f"Categorization failed: {str(e)}"
            }
    
    def categorize_transactions_batch(self, transactions: List[Dict]) -> List[Dict]:
        """Categorize multiple transactions with progress tracking"""
        if not transactions:
            return []
        
        categorized_transactions = []
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            for i, transaction in enumerate(transactions):
                status_text.text(f"Categorizing transaction {i+1} of {len(transactions)}: {transaction['description'][:50]}...")
                
                # Skip if already categorized
                if transaction.get('category'):
                    categorized_transactions.append(transaction)
                else:
                    categorization = self.categorize_transaction(
                        transaction['description'], 
                        transaction['amount']
                    )
                    
                    transaction.update({
                        'category': categorization['category'],
                        'confidence_score': categorization['confidence']
                    })
                    
                    categorized_transactions.append(transaction)
                
                # Update progress
                progress_bar.progress((i + 1) / len(transactions))
            
            status_text.text("✅ Categorization complete!")
            
        except Exception as e:
            logger.error(f"Error in batch categorization: {e}")
            status_text.text(f"❌ Error during categorization: {e}")
        
        return categorized_transactions
    
    def recategorize_transaction(self, transaction_id: int, new_category: str) -> bool:
        """Manually recategorize a transaction"""
        try:
            from database.models import Transaction
            from database.connection import get_db_instance
            
            db = get_db_instance()
            success = db.execute_update(
                "UPDATE transactions SET category = %s WHERE id = %s",
                (new_category, transaction_id)
            )
            
            return success
        except Exception as e:
            logger.error(f"Error recategorizing transaction: {e}")
            return False
    
    def get_categorization_stats(self, user_id: int) -> Dict:
        """Get categorization statistics for a user"""
        try:
            from database.models import Transaction
            
            transactions = Transaction.get_by_user(user_id, limit=1000)
            
            if not transactions:
                return {}
            
            total_transactions = len(transactions)
            categorized_transactions = len([t for t in transactions if t.category and t.category != 'Other'])
            avg_confidence = sum(t.confidence_score or 0 for t in transactions) / total_transactions
            
            category_counts = {}
            for transaction in transactions:
                category = transaction.category or 'Uncategorized'
                category_counts[category] = category_counts.get(category, 0) + 1
            
            return {
                'total_transactions': total_transactions,
                'categorized_transactions': categorized_transactions,
                'categorization_rate': (categorized_transactions / total_transactions) * 100,
                'average_confidence': avg_confidence,
                'category_distribution': category_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting categorization stats: {e}")
            return {}

class TransactionParser:
    """Main transaction parser class"""
    
    def __init__(self):
        self.categorizer = TransactionCategorizer()
    
    def process_and_categorize(self, transactions: List[Dict], user_id: int) -> List[Dict]:
        """Process and categorize transactions for a user"""
        if not transactions:
            return []
        
        # Add user_id to each transaction
        for transaction in transactions:
            transaction['user_id'] = user_id
        
        # Categorize transactions
        st.info("🤖 AI is analyzing and categorizing your transactions...")
        categorized_transactions = self.categorizer.categorize_transactions_batch(transactions)
        
        return categorized_transactions
    
    def validate_transactions(self, transactions: List[Dict]) -> tuple[List[Dict], List[str]]:
        """Validate transactions and return valid ones with error messages"""
        valid_transactions = []
        errors = []
        
        for i, transaction in enumerate(transactions):
            try:
                # Check required fields
                if not transaction.get('description'):
                    errors.append(f"Row {i+1}: Missing description")
                    continue
                
                if transaction.get('amount') is None:
                    errors.append(f"Row {i+1}: Missing amount")
                    continue
                
                if not transaction.get('transaction_date'):
                    errors.append(f"Row {i+1}: Missing transaction date")
                    continue
                
                # Validate amount
                try:
                    amount = float(transaction['amount'])
                    transaction['amount'] = amount
                except (ValueError, TypeError):
                    errors.append(f"Row {i+1}: Invalid amount format")
                    continue
                
                # Validate date
                if not isinstance(transaction['transaction_date'], (datetime, type(datetime.now().date()))):
                    errors.append(f"Row {i+1}: Invalid date format")
                    continue
                
                valid_transactions.append(transaction)
                
            except Exception as e:
                errors.append(f"Row {i+1}: Validation error - {str(e)}")
        
        return valid_transactions, errors
    
    def get_duplicate_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Identify potential duplicate transactions"""
        duplicates = []
        
        for i, transaction1 in enumerate(transactions):
            for j, transaction2 in enumerate(transactions[i+1:], i+1):
                # Check for potential duplicates
                if (transaction1['description'] == transaction2['description'] and
                    abs(transaction1['amount'] - transaction2['amount']) < 0.01 and
                    abs((transaction1['transaction_date'] - transaction2['transaction_date']).days) <= 1):
                    
                    duplicates.append({
                        'transaction1': transaction1,
                        'transaction2': transaction2,
                        'similarity_score': 0.95
                    })
        
        return duplicates
    
    def merge_similar_descriptions(self, transactions: List[Dict]) -> Dict[str, List[str]]:
        """Group similar transaction descriptions"""
        from difflib import SequenceMatcher
        
        description_groups = {}
        processed_descriptions = set()
        
        for transaction in transactions:
            description = transaction['description']
            
            if description in processed_descriptions:
                continue
            
            # Find similar descriptions
            similar_descriptions = [description]
            
            for other_transaction in transactions:
                other_description = other_transaction['description']
                
                if (other_description != description and 
                    other_description not in processed_descriptions):
                    
                    similarity = SequenceMatcher(None, description.lower(), other_description.lower()).ratio()
                    
                    if similarity > 0.8:  # 80% similarity threshold
                        similar_descriptions.append(other_description)
                        processed_descriptions.add(other_description)
            
            if len(similar_descriptions) > 1:
                description_groups[description] = similar_descriptions
            
            processed_descriptions.add(description)
        
        return description_groups
