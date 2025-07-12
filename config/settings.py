# config/settings.py

from typing import Dict, Any, Optional

class Settings:
    """Application settings and configuration"""

    @staticmethod
    def get_database_config() -> Dict[str, Any]:
        import streamlit as st
        db = st.secrets.get("postgresql", {})
        return {
            'host': db.get("host", "localhost"),
            'port': db.get("port", 5432),
            'database': db.get("database", "finance_advisor"),
            'username': db.get("username", "finance_user"),
            'password': db.get("password", "")
        }

    @staticmethod
    def get_openai_api_key() -> Optional[str]:
        import streamlit as st
        return st.secrets.get("openai", {}).get("api_key", "")

    @staticmethod
    def get_alpha_vantage_api_key() -> Optional[str]:
        import streamlit as st
        return st.secrets.get("alpha_vantage", {}).get("api_key", "")

    @staticmethod
    def get_twilio_settings() -> Dict[str, str]:
        import streamlit as st
        twilio = st.secrets.get("twilio", {})
        return {
            'account_sid': twilio.get("account_sid", ""),
            'auth_token': twilio.get("auth_token", ""),
            'phone_number': twilio.get("phone_number", "")
        }

    @staticmethod
    def get_email_settings() -> Dict[str, Any]:
        import streamlit as st
        email = st.secrets.get("email", {})
        return {
            'smtp_server': email.get("smtp_server", ""),
            'smtp_port': email.get("smtp_port", 587),
            'address': email.get("address", ""),
            'password': email.get("password", "")
        }

    # Application settings
    APP_NAME = "AI-Powered Personal Finance Advisor"
    APP_VERSION = "1.0.0"

    TRANSACTION_CATEGORIES = [
        "Groceries", "Housing", "Transportation", "Entertainment",
        "Healthcare", "Shopping", "Utilities", "Restaurants",
        "Gas", "Insurance", "Education", "Travel", "Investments",
        "Subscriptions", "Income", "Other"
    ]

    RISK_LEVELS = ["Conservative", "Moderate", "Aggressive"]
    TIME_HORIZONS = ["< 1 year", "1-3 years", "3-5 years", "5+ years"]

    @classmethod
    def validate_config(cls):
        db = cls.get_database_config()
        openai = cls.get_openai_api_key()
        alpha = cls.get_alpha_vantage_api_key()
        twilio = cls.get_twilio_settings()
        email = cls.get_email_settings()
        return {
            'database': bool(db['host'] and db['database'] and db['username']),
            'openai': bool(openai),
            'alpha_vantage': bool(alpha),
            'twilio': bool(twilio['account_sid'] and twilio['auth_token'] and twilio['phone_number']),
            'email': bool(email['smtp_server'] and email['address'] and email['password'])
        }
