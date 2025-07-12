"""settings.py - Configuration settings"""

import os
from typing import Dict, Any

class Settings:
    """Application settings and configuration"""

    @staticmethod
    def get_database_config():
        import streamlit as st
        return {
            'host': st.secrets.get("postgresql", {}).get("host", "localhost"),
            'port': st.secrets.get("postgresql", {}).get("port", 5432),
            'database': st.secrets.get("postgresql", {}).get("database", "finance_advisor"),
            'username': st.secrets.get("postgresql", {}).get("username", "postgres"),
            'password': st.secrets.get("postgresql", {}).get("password", "password")
        }

    @staticmethod
    def get_openai_api_key():
        import streamlit as st
        return st.secrets.get("openai", {}).get("api_key", "")

    @staticmethod
    def get_alpha_vantage_api_key():
        import streamlit as st
        return st.secrets.get("alpha_vantage", {}).get("api_key", "")

    @staticmethod
    def get_twilio_settings():
        import streamlit as st
        return {
            'account_sid': st.secrets.get("twilio", {}).get("account_sid", ""),
            'auth_token': st.secrets.get("twilio", {}).get("auth_token", ""),
            'phone_number': st.secrets.get("twilio", {}).get("phone_number", "")
        }

    @staticmethod
    def get_email_settings():
        import streamlit as st
        return {
            'smtp_server': st.secrets.get("email", {}).get("smtp_server", ""),
            'smtp_port': st.secrets.get("email", {}).get("smtp_port", 587),
            'address': st.secrets.get("email", {}).get("address", ""),
            'password': st.secrets.get("email", {}).get("password", "")
        }

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
    def validate_config(cls):
        db = cls.get_database_config()
        openai = cls.get_openai_api_key()
        alpha = cls.get_alpha_vantage_api_key()
        twilio = cls.get_twilio_settings()
        email = cls.get_email_settings()
        return {
            'database': bool(db['host'] and db['database']),
            'openai': bool(openai),
            'alpha_vantage': bool(alpha),
            'twilio': bool(twilio['account_sid'] and twilio['auth_token']),
            'email': bool(email['smtp_server'] and email['address'])
        }
