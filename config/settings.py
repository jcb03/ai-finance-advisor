"""settings.py - Configuration settings"""

"""Configuration settings"""

import streamlit as st
import os
from typing import Dict, Any

class Settings:
    """Application settings and configuration"""
    
    # Database settings
    DATABASE_CONFIG = {
        'host': st.secrets.get("postgresql", {}).get("host", "localhost"),
        'port': st.secrets.get("postgresql", {}).get("port", 5432),
        'database': st.secrets.get("postgresql", {}).get("database", "finance_advisor"),
        'username': st.secrets.get("postgresql", {}).get("username", "postgres"),
        'password': st.secrets.get("postgresql", {}).get("password", "password")
    }
    
    # API Keys
    OPENAI_API_KEY = st.secrets.get("openai", {}).get("api_key", "")
    ALPHA_VANTAGE_API_KEY = st.secrets.get("alpha_vantage", {}).get("api_key", "")
    
    # Twilio settings
    TWILIO_ACCOUNT_SID = st.secrets.get("twilio", {}).get("account_sid", "")
    TWILIO_AUTH_TOKEN = st.secrets.get("twilio", {}).get("auth_token", "")
    TWILIO_PHONE_NUMBER = st.secrets.get("twilio", {}).get("phone_number", "")
    
    # Email settings
    EMAIL_SMTP_SERVER = st.secrets.get("email", {}).get("smtp_server", "")
    EMAIL_SMTP_PORT = st.secrets.get("email", {}).get("smtp_port", 587)
    EMAIL_ADDRESS = st.secrets.get("email", {}).get("address", "")
    EMAIL_PASSWORD = st.secrets.get("email", {}).get("password", "")
    
    # Application settings
    APP_NAME = "AI-Powered Personal Finance Advisor"
    APP_VERSION = "1.0.0"
    
    # Transaction categories
    TRANSACTION_CATEGORIES = [
        "Groceries", "Housing", "Transportation", "Entertainment",
        "Healthcare", "Shopping", "Utilities", "Restaurants",
        "Gas", "Insurance", "Education", "Travel", "Investments",
        "Subscriptions", "Income", "Other"
    ]
    
    # Investment risk levels
    RISK_LEVELS = ["Conservative", "Moderate", "Aggressive"]
    
    # Time horizons
    TIME_HORIZONS = ["< 1 year", "1-3 years", "3-5 years", "5+ years"]

    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """Validate configuration settings"""
        return {
            'database': bool(cls.DATABASE_CONFIG['host'] and cls.DATABASE_CONFIG['database']),
            'openai': bool(cls.OPENAI_API_KEY),
            'alpha_vantage': bool(cls.ALPHA_VANTAGE_API_KEY),
            'twilio': bool(cls.TWILIO_ACCOUNT_SID and cls.TWILIO_AUTH_TOKEN),
            'email': bool(cls.EMAIL_SMTP_SERVER and cls.EMAIL_ADDRESS)
        }
