"""models.py - Database models"""

"""Database models"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
import psycopg2
from database.connection import get_db_instance
import logging

logger = logging.getLogger(__name__)

class BaseModel:
    """Base model class with common functionality"""
    
    @staticmethod
    def _execute_query(query: str, params: tuple = None) -> Optional[List[Dict]]:
        """Execute SELECT query"""
        db = get_db_instance()
        return db.execute_query(query, params)
    
    @staticmethod
    def _execute_update(query: str, params: tuple = None) -> bool:
        """Execute INSERT/UPDATE/DELETE query"""
        db = get_db_instance()
        return db.execute_update(query, params)

class User(BaseModel):
    """User model"""
    
    def __init__(self, id=None, email=None, password_hash=None, 
                 first_name=None, last_name=None, phone_number=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def create(email: str, password_hash: str, first_name: str, 
               last_name: str, phone_number: str = None) -> Optional['User']:
        """Create a new user"""
        query = """
            INSERT INTO users (email, password_hash, first_name, last_name, phone_number)
            VALUES (%s, %s, %s, %s, %s) RETURNING *
        """
        
        result = User._execute_query(query, (email, password_hash, first_name, last_name, phone_number))
        if result:
            return User(**result[0])
        return None
    
    @staticmethod
    def get_by_email(email: str) -> Optional['User']:
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = %s"
        result = User._execute_query(query, (email,))
        if result:
            return User(**result[0])
        return None
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional['User']:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = %s"
        result = User._execute_query(query, (user_id,))
        if result:
            return User(**result[0])
        return None
    
    def update(self) -> bool:
        """Update user information"""
        query = """
            UPDATE users 
            SET first_name = %s, last_name = %s, phone_number = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        return User._execute_update(query, (self.first_name, self.last_name, self.phone_number, self.id))

class Transaction(BaseModel):
    """Transaction model"""
    
    def __init__(self, id=None, user_id=None, description=None, amount=None,
                 category=None, transaction_date=None, account_type=None, 
                 confidence_score=None, created_at=None):
        self.id = id
        self.user_id = user_id
        self.description = description
        self.amount = amount
        self.category = category
        self.transaction_date = transaction_date
        self.account_type = account_type
        self.confidence_score = confidence_score
        self.created_at = created_at
    
    @staticmethod
    def create(user_id: int, description: str, amount: float, category: str,
               transaction_date: date, account_type: str = "Bank Account",
               confidence_score: int = 0) -> Optional['Transaction']:
        """Create a new transaction"""
        query = """
            INSERT INTO transactions (user_id, description, amount, category, 
                                    transaction_date, account_type, confidence_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *
        """
        
        result = Transaction._execute_query(query, (
            user_id, description, amount, category, 
            transaction_date, account_type, confidence_score
        ))
        if result:
            return Transaction(**result[0])
        return None
    
    @staticmethod
    def create_bulk(transactions: List[Dict]) -> bool:
        """Create multiple transactions"""
        if not transactions:
            return False
        
        query = """
            INSERT INTO transactions (user_id, description, amount, category, 
                                    transaction_date, account_type, confidence_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        db = get_db_instance()
        conn = db.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                for transaction in transactions:
                    cursor.execute(query, (
                        transaction['user_id'],
                        transaction['description'],
                        transaction['amount'],
                        transaction['category'],
                        transaction['transaction_date'],
                        transaction.get('account_type', 'Bank Account'),
                        transaction.get('confidence_score', 0)
                    ))
                conn.commit()
                return True
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Error creating bulk transactions: {e}")
            return False
    
    @staticmethod
    def get_by_user(user_id: int, limit: int = 100, category: str = None,
                   start_date: date = None, end_date: date = None) -> List['Transaction']:
        """Get transactions by user with optional filters"""
        query = "SELECT * FROM transactions WHERE user_id = %s"
        params = [user_id]
        
        if category:
            query += " AND category = %s"
            params.append(category)
        
        if start_date:
            query += " AND transaction_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND transaction_date <= %s"
            params.append(end_date)
        
        query += " ORDER BY transaction_date DESC LIMIT %s"
        params.append(limit)
        
        result = Transaction._execute_query(query, tuple(params))
        return [Transaction(**row) for row in result] if result else []
    
    @staticmethod
    def get_spending_by_category(user_id: int, start_date: date = None, 
                               end_date: date = None) -> Dict[str, float]:
        """Get spending by category"""
        query = """
            SELECT category, SUM(amount) as total
            FROM transactions 
            WHERE user_id = %s AND amount > 0
        """
        params = [user_id]
        
        if start_date:
            query += " AND transaction_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND transaction_date <= %s"
            params.append(end_date)
        
        query += " GROUP BY category"
        
        result = Transaction._execute_query(query, tuple(params))
        return {row['category']: float(row['total']) for row in result} if result else {}

class Budget(BaseModel):
    """Budget model"""
    
    def __init__(self, id=None, user_id=None, category=None, 
                 monthly_limit=None, current_spent=None, 
                 created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.category = category
        self.monthly_limit = monthly_limit
        self.current_spent = current_spent
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def create(user_id: int, category: str, monthly_limit: float) -> Optional['Budget']:
        """Create a new budget"""
        query = """
            INSERT INTO budgets (user_id, category, monthly_limit)
            VALUES (%s, %s, %s) 
            ON CONFLICT (user_id, category) 
            DO UPDATE SET monthly_limit = EXCLUDED.monthly_limit
            RETURNING *
        """
        
        result = Budget._execute_query(query, (user_id, category, monthly_limit))
        if result:
            return Budget(**result[0])
        return None
    
    @staticmethod
    def get_by_user(user_id: int) -> List['Budget']:
        """Get budgets by user"""
        query = "SELECT * FROM budgets WHERE user_id = %s ORDER BY category"
        result = Budget._execute_query(query, (user_id,))
        return [Budget(**row) for row in result] if result else []
    
    @staticmethod
    def update_spent_amount(user_id: int, category: str, amount: float) -> bool:
        """Update current spent amount for a budget"""
        query = """
            UPDATE budgets 
            SET current_spent = %s, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND category = %s
        """
        return Budget._execute_update(query, (amount, user_id, category))
    
    def delete(self) -> bool:
        """Delete budget"""
        query = "DELETE FROM budgets WHERE id = %s"
        return Budget._execute_update(query, (self.id,))

class FinancialGoal(BaseModel):
    """Financial goal model"""
    
    def __init__(self, id=None, user_id=None, goal_name=None, target_amount=None,
                 current_amount=None, target_date=None, status=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.goal_name = goal_name
        self.target_amount = target_amount
        self.current_amount = current_amount
        self.target_date = target_date
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def create(user_id: int, goal_name: str, target_amount: float, 
               target_date: date = None, current_amount: float = 0) -> Optional['FinancialGoal']:
        """Create a new financial goal"""
        query = """
            INSERT INTO financial_goals (user_id, goal_name, target_amount, target_date, current_amount)
            VALUES (%s, %s, %s, %s, %s) RETURNING *
        """
        
        result = FinancialGoal._execute_query(query, (
            user_id, goal_name, target_amount, target_date, current_amount
        ))
        if result:
            return FinancialGoal(**result[0])
        return None
    
    @staticmethod
    def get_by_user(user_id: int) -> List['FinancialGoal']:
        """Get financial goals by user"""
        query = "SELECT * FROM financial_goals WHERE user_id = %s ORDER BY created_at DESC"
        result = FinancialGoal._execute_query(query, (user_id,))
        return [FinancialGoal(**row) for row in result] if result else []
    
    def update_progress(self, current_amount: float) -> bool:
        """Update goal progress"""
        query = """
            UPDATE financial_goals 
            SET current_amount = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        return FinancialGoal._execute_update(query, (current_amount, self.id))
    
    def update_status(self, status: str) -> bool:
        """Update goal status"""
        query = """
            UPDATE financial_goals 
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        return FinancialGoal._execute_update(query, (status, self.id))
    
    def delete(self) -> bool:
        """Delete goal"""
        query = "DELETE FROM financial_goals WHERE id = %s"
        return FinancialGoal._execute_update(query, (self.id,))

class InvestmentRecommendation(BaseModel):
    """Investment recommendation model"""
    
    def __init__(self, id=None, user_id=None, symbol=None, name=None,
                 recommendation_type=None, reasoning=None, confidence_score=None,
                 allocation_percentage=None, created_at=None):
        self.id = id
        self.user_id = user_id
        self.symbol = symbol
        self.name = name
        self.recommendation_type = recommendation_type
        self.reasoning = reasoning
        self.confidence_score = confidence_score
        self.allocation_percentage = allocation_percentage
        self.created_at = created_at
    
    @staticmethod
    def create(user_id: int, symbol: str, name: str, recommendation_type: str,
               reasoning: str, confidence_score: int, allocation_percentage: float) -> Optional['InvestmentRecommendation']:
        """Create a new investment recommendation"""
        query = """
            INSERT INTO investment_recommendations 
            (user_id, symbol, name, recommendation_type, reasoning, confidence_score, allocation_percentage)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *
        """
        
        result = InvestmentRecommendation._execute_query(query, (
            user_id, symbol, name, recommendation_type, reasoning, 
            confidence_score, allocation_percentage
        ))
        if result:
            return InvestmentRecommendation(**result[0])
        return None
    
    @staticmethod
    def get_by_user(user_id: int, limit: int = 50) -> List['InvestmentRecommendation']:
        """Get investment recommendations by user"""
        query = """
            SELECT * FROM investment_recommendations 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """
        result = InvestmentRecommendation._execute_query(query, (user_id, limit))
        return [InvestmentRecommendation(**row) for row in result] if result else []

class UserPreferences(BaseModel):
    """User preferences model"""
    
    def __init__(self, id=None, user_id=None, notification_email=None,
                 notification_sms=None, budget_alerts=None, investment_alerts=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.notification_email = notification_email
        self.notification_sms = notification_sms
        self.budget_alerts = budget_alerts
        self.investment_alerts = investment_alerts
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def create_default(user_id: int) -> Optional['UserPreferences']:
        """Create default preferences for a user"""
        query = """
            INSERT INTO user_preferences (user_id)
            VALUES (%s) RETURNING *
        """
        
        result = UserPreferences._execute_query(query, (user_id,))
        if result:
            return UserPreferences(**result[0])
        return None
    
    @staticmethod
    def get_by_user(user_id: int) -> Optional['UserPreferences']:
        """Get user preferences"""
        query = "SELECT * FROM user_preferences WHERE user_id = %s"
        result = UserPreferences._execute_query(query, (user_id,))
        if result:
            return UserPreferences(**result[0])
        return None
    
    def update(self) -> bool:
        """Update user preferences"""
        query = """
            UPDATE user_preferences 
            SET notification_email = %s, notification_sms = %s, 
                budget_alerts = %s, investment_alerts = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
        """
        return UserPreferences._execute_update(query, (
            self.notification_email, self.notification_sms,
            self.budget_alerts, self.investment_alerts, self.user_id
        ))
