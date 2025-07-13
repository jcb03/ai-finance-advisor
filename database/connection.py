"""connection.py - Database connection"""

import psycopg2
import streamlit as st
from psycopg2.extras import RealDictCursor
import logging
from typing import Optional
from config.settings import Settings

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Singleton database connection class"""
    _instance = None
    _connection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def get_connection(self) -> Optional[psycopg2.extensions.connection]:
        """Get database connection"""
        if self._connection is None or self._connection.closed:
            try:
                # Get database config using the new method
                db_config = Settings.database_config()
                
                self._connection = psycopg2.connect(
                    host=db_config['host'],
                    port=db_config['port'],
                    database=db_config['database'],
                    user=db_config['username'],
                    password=db_config['password'],
                    cursor_factory=RealDictCursor
                )
                logger.info("Database connection established")
            except psycopg2.Error as e:
                logger.error(f"Database connection failed: {e}")
                st.error(f"Database connection failed: {e}")
                return None
        return self._connection
    
    def close_connection(self):
        """Close database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[list]:
        """Execute a SELECT query and return results"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except psycopg2.Error as e:
            logger.error(f"Query execution failed: {e}")
            return None
    
    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Execute an INSERT/UPDATE/DELETE query"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return True
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Update execution failed: {e}")
            return False

@st.cache_resource
def get_db_connection():
    """Get cached database connection"""
    return DatabaseConnection().get_connection()

def get_db_instance():
    """Get database instance"""
    return DatabaseConnection()
