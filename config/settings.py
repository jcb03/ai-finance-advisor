"""settings.py - Complete configuration settings for AI Personal Finance Advisor"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class Settings:
    """Application settings and configuration with comprehensive error handling"""

    # =============================================================================
    # DYNAMIC CONFIGURATION METHODS (Runtime secrets access)
    # =============================================================================

    @classmethod
    def database_config(cls) -> Optional[Dict[str, Any]]:
        """Get database configuration with error handling"""
        try:
            config = {
                'host': st.secrets["postgresql"]["host"],
                'port': int(st.secrets["postgresql"]["port"]),
                'database': st.secrets["postgresql"]["database"],
                'username': st.secrets["postgresql"]["username"],
                'password': st.secrets["postgresql"]["password"]
            }
            
            # Validate required fields
            if not all([config['host'], config['database'], config['username']]):
                logger.error("Missing required database configuration fields")
                return None
                
            return config
            
        except KeyError as e:
            logger.error(f"Missing database configuration key: {e}")
            st.error(f"Database configuration error: Missing {e}")
            return None
        except Exception as e:
            logger.error(f"Database configuration error: {e}")
            st.error(f"Database configuration error: {e}")
            return None

    @classmethod
    def openai_api_key(cls) -> Optional[str]:
        """Get OpenAI API key with validation"""
        try:
            api_key = st.secrets["openai"]["api_key"]
            
            # Basic validation
            if not api_key or not api_key.startswith("sk-"):
                logger.warning("Invalid OpenAI API key format")
                return None
                
            return api_key
            
        except KeyError:
            logger.warning("OpenAI API key not configured")
            return None
        except Exception as e:
            logger.error(f"OpenAI configuration error: {e}")
            return None

    @classmethod
    def alpha_vantage_api_key(cls) -> Optional[str]:
        """Get Alpha Vantage API key (optional service)"""
        try:
            return st.secrets.get("alpha_vantage", {}).get("api_key", "")
        except Exception as e:
            logger.warning(f"Alpha Vantage configuration error: {e}")
            return ""

    @classmethod
    def twilio_config(cls) -> Dict[str, str]:
        """Get Twilio configuration with defaults"""
        try:
            twilio_secrets = st.secrets.get("twilio", {})
            config = {
                'account_sid': twilio_secrets.get("account_sid", ""),
                'auth_token': twilio_secrets.get("auth_token", ""),
                'phone_number': twilio_secrets.get("phone_number", "")
            }
            
            # Validate phone number format if provided
            if config['phone_number'] and not config['phone_number'].startswith('+'):
                logger.warning("Twilio phone number should start with '+' (country code)")
            
            return config
            
        except Exception as e:
            logger.warning(f"Twilio configuration error: {e}")
            return {'account_sid': '', 'auth_token': '', 'phone_number': ''}

    @classmethod
    def email_config(cls) -> Dict[str, Any]:
        """Get email configuration with defaults"""
        try:
            email_secrets = st.secrets.get("email", {})
            config = {
                'smtp_server': email_secrets.get("smtp_server", ""),
                'smtp_port': int(email_secrets.get("smtp_port", 587)),
                'address': email_secrets.get("address", ""),
                'password': email_secrets.get("password", "")
            }
            
            # Validate email format if provided
            if config['address'] and '@' not in config['address']:
                logger.warning("Invalid email address format")
            
            return config
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Email configuration error: {e}")
            return {'smtp_server': '', 'smtp_port': 587, 'address': '', 'password': ''}
        except Exception as e:
            logger.warning(f"Email configuration error: {e}")
            return {'smtp_server': '', 'smtp_port': 587, 'address': '', 'password': ''}

    # =============================================================================
    # STATIC APPLICATION SETTINGS
    # =============================================================================

    # Application metadata
    APP_NAME = "AI-Powered Personal Finance Advisor"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "Intelligent personal finance management with AI-powered insights"
    APP_AUTHOR = "Finance AI Team"
    
    # Transaction categories for expense tracking
    TRANSACTION_CATEGORIES = [
        "Groceries", "Housing", "Transportation", "Entertainment",
        "Healthcare", "Shopping", "Utilities", "Restaurants",
        "Gas", "Insurance", "Education", "Travel", "Investments",
        "Subscriptions", "Income", "Other", "ATM/Cash", "Fees",
        "Personal Care", "Gifts", "Charity", "Home Improvement",
        "Pet Care", "Professional Services", "Taxes"
    ]
    
    # Investment risk tolerance levels
    RISK_LEVELS = ["Conservative", "Moderate", "Aggressive"]
    
    # Investment time horizons
    TIME_HORIZONS = ["< 1 year", "1-3 years", "3-5 years", "5+ years"]
    
    # Supported file formats for transaction import
    SUPPORTED_FILE_FORMATS = {
        'csv': ['text/csv', 'application/vnd.ms-excel'],
        'excel': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'pdf': ['application/pdf']
    }
    
    # Default budget categories and suggested limits
    DEFAULT_BUDGET_CATEGORIES = {
        "Housing": 30.0,      # % of income
        "Transportation": 15.0,
        "Groceries": 12.0,
        "Utilities": 8.0,
        "Entertainment": 5.0,
        "Healthcare": 5.0,
        "Shopping": 5.0,
        "Restaurants": 5.0,
        "Other": 15.0
    }
    
    # Financial health scoring thresholds
    FINANCIAL_HEALTH_THRESHOLDS = {
        'excellent': 80,
        'good': 60,
        'fair': 40,
        'poor': 0
    }
    
    # AI model configurations
    AI_MODEL_SETTINGS = {
        'openai_model': 'gpt-4',
        'temperature': 0.1,
        'max_tokens': 1000,
        'categorization_confidence_threshold': 80
    }
    
    # Notification settings
    NOTIFICATION_TYPES = {
        'budget_alert': 'Budget Alert',
        'goal_achievement': 'Goal Achievement',
        'investment_opportunity': 'Investment Opportunity',
        'weekly_summary': 'Weekly Summary',
        'monthly_report': 'Monthly Report'
    }
    
    # Chart color schemes
    CHART_COLORS = {
        'primary': '#1f77b4',
        'secondary': '#ff7f0e',
        'success': '#2ca02c',
        'warning': '#d62728',
        'info': '#9467bd',
        'light': '#8c564b',
        'dark': '#e377c2'
    }
    
    # Date format options
    DATE_FORMATS = {
        'display': '%B %d, %Y',
        'input': '%Y-%m-%d',
        'filename': '%Y%m%d',
        'api': '%Y-%m-%d'
    }

    # =============================================================================
    # VALIDATION AND UTILITY METHODS
    # =============================================================================

    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """Validate all configuration settings"""
        validations = {}
        
        # Database validation
        db_config = cls.database_config()
        validations['database'] = bool(db_config and db_config.get('host'))
        
        # OpenAI validation
        openai_key = cls.openai_api_key()
        validations['openai'] = bool(openai_key and openai_key.startswith('sk-'))
        
        # Alpha Vantage validation (optional)
        alpha_key = cls.alpha_vantage_api_key()
        validations['alpha_vantage'] = bool(alpha_key)
        
        # Twilio validation (optional)
        twilio_config = cls.twilio_config()
        validations['twilio'] = bool(
            twilio_config.get('account_sid') and 
            twilio_config.get('auth_token') and 
            twilio_config.get('phone_number')
        )
        
        # Email validation (optional)
        email_config = cls.email_config()
        validations['email'] = bool(
            email_config.get('smtp_server') and 
            email_config.get('address') and 
            email_config.get('password')
        )
        
        return validations

    @classmethod
    def get_config_status(cls) -> Dict[str, str]:
        """Get human-readable configuration status"""
        validations = cls.validate_config()
        status = {}
        
        for service, is_valid in validations.items():
            if is_valid:
                status[service] = "✅ Configured"
            else:
                if service in ['alpha_vantage', 'twilio', 'email']:
                    status[service] = "⚠️ Optional - Not configured"
                else:
                    status[service] = "❌ Required - Not configured"
        
        return status

    @classmethod
    def get_required_services(cls) -> List[str]:
        """Get list of required services for basic functionality"""
        return ['database', 'openai']

    @classmethod
    def get_optional_services(cls) -> List[str]:
        """Get list of optional services for enhanced functionality"""
        return ['alpha_vantage', 'twilio', 'email']

    @classmethod
    def is_production_ready(cls) -> bool:
        """Check if all required services are configured"""
        validations = cls.validate_config()
        required_services = cls.get_required_services()
        
        return all(validations.get(service, False) for service in required_services)

    @classmethod
    def get_feature_availability(cls) -> Dict[str, bool]:
        """Get availability of features based on configuration"""
        validations = cls.validate_config()
        
        return {
            'core_functionality': validations.get('database', False) and validations.get('openai', False),
            'transaction_categorization': validations.get('openai', False),
            'investment_recommendations': validations.get('openai', False),
            'stock_market_data': validations.get('alpha_vantage', False),
            'sms_notifications': validations.get('twilio', False),
            'email_notifications': validations.get('email', False),
            'ai_insights': validations.get('openai', False)
        }

    @classmethod
    def log_configuration_status(cls):
        """Log current configuration status"""
        status = cls.get_config_status()
        logger.info("Configuration Status:")
        for service, status_msg in status.items():
            logger.info(f"  {service}: {status_msg}")
        
        if cls.is_production_ready():
            logger.info("✅ Application is production ready")
        else:
            logger.warning("⚠️ Application missing required configuration")

    @classmethod
    def get_app_info(cls) -> Dict[str, Any]:
        """Get comprehensive application information"""
        return {
            'name': cls.APP_NAME,
            'version': cls.APP_VERSION,
            'description': cls.APP_DESCRIPTION,
            'author': cls.APP_AUTHOR,
            'configuration_status': cls.get_config_status(),
            'feature_availability': cls.get_feature_availability(),
            'is_production_ready': cls.is_production_ready(),
            'startup_time': datetime.now().isoformat()
        }

    # =============================================================================
    # ENVIRONMENT-SPECIFIC SETTINGS
    # =============================================================================

    @classmethod
    def get_environment(cls) -> str:
        """Detect current environment"""
        try:
            # Check if running on Streamlit Cloud
            if 'streamlit.io' in st.secrets.get('general', {}).get('domain', ''):
                return 'production'
            # Check for local development indicators
            elif st.secrets.get('postgresql', {}).get('host') == 'localhost':
                return 'development'
            else:
                return 'staging'
        except:
            return 'development'

    @classmethod
    def get_debug_mode(cls) -> bool:
        """Check if debug mode is enabled"""
        env = cls.get_environment()
        return env == 'development'

    @classmethod
    def get_log_level(cls) -> str:
        """Get appropriate log level for environment"""
        env = cls.get_environment()
        return 'DEBUG' if env == 'development' else 'INFO'

# =============================================================================
# CONFIGURATION INITIALIZATION
# =============================================================================

def initialize_settings():
    """Initialize settings and perform startup checks"""
    try:
        # Log configuration status
        Settings.log_configuration_status()
        
        # Check if production ready
        if not Settings.is_production_ready():
            required_services = Settings.get_required_services()
            missing_services = [
                service for service in required_services 
                if not Settings.validate_config().get(service, False)
            ]
            
            st.error(
                f"⚠️ Missing required configuration for: {', '.join(missing_services)}\n\n"
                "Please check your .streamlit/secrets.toml file."
            )
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Settings initialization failed: {e}")
        st.error(f"Configuration error: {e}")
        return False

# Auto-initialize when module is imported (optional)
if __name__ != "__main__":
    # Only auto-initialize in non-test environments
    try:
        initialize_settings()
    except Exception as e:
        logger.warning(f"Auto-initialization failed: {e}")
