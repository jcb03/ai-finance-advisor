# config/settings.py

from typing import Dict, Any

class Settings:
    """Application settings and configuration"""

    @staticmethod
    def get_database_config() -> Dict[str, Any]:
        import streamlit as st
        return {
            'host': st.secrets["postgresql"]["host"],
            'port': st.secrets["postgresql"]["port"],
            'database': st.secrets["postgresql"]["database"],
            'username': st.secrets["postgresql"]["username"],
            'password': st.secrets["postgresql"]["password"]
        }

    @staticmethod
    def get_openai_api_key() -> str:
        import streamlit as st
        return st.secrets["openai"]["api_key"]

    @staticmethod
    def get_alpha_vantage_api_key() -> str:
        import streamlit as st
        return st.secrets["alpha_vantage"]["api_key"]

    @staticmethod
    def get_twilio_settings() -> Dict[str, str]:
        import streamlit as st
        return {
            'account_sid': st.secrets["twilio"]["account_sid"],
            'auth_token': st.secrets["twilio"]["auth_token"],
            'phone_number': st.secrets["twilio"]["phone_number"]
        }

    @staticmethod
    def get_email_settings() -> Dict[str, Any]:
        import streamlit as st
        return {
            'smtp_server': st.secrets["email"]["smtp_server"],
            'smtp_port': st.secrets["email"]["smtp_port"],
            'address': st.secrets["email"]["address"],
            'password': st.secrets["email"]["password"]
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
            'database': bool(db['host'] and db['database']),
            'openai': bool(openai),
            'alpha_vantage': bool(alpha),
            'twilio': bool(twilio['account_sid'] and twilio['auth_token']),
            'email': bool(email['smtp_server'] and email['address'])
        }
