"""authentication.py - User authentication logic"""

"""User authentication logic"""

import streamlit as st
import bcrypt
from typing import Optional
from database.models import User, UserPreferences
import re
import logging
from utils.helpers import create_footer
logger = logging.getLogger(__name__)

class AuthenticationManager:
    """Handles user authentication and session management"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        return True, "Password is valid"
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return True  # Phone is optional
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid length (10-15 digits)
        return 10 <= len(digits_only) <= 15
    
    @staticmethod
    def register_user(email: str, password: str, first_name: str, 
                     last_name: str, phone_number: str = None) -> tuple[bool, str]:
        """Register a new user"""
        # Validate input
        if not AuthenticationManager.validate_email(email):
            return False, "Invalid email format"
        
        is_valid_password, password_message = AuthenticationManager.validate_password(password)
        if not is_valid_password:
            return False, password_message
        
        if not AuthenticationManager.validate_phone(phone_number):
            return False, "Invalid phone number format"
        
        if not first_name.strip() or not last_name.strip():
            return False, "First name and last name are required"
        
        # Check if user already exists
        existing_user = User.get_by_email(email.lower())
        if existing_user:
            return False, "Email already registered"
        
        # Hash password and create user
        try:
            password_hash = AuthenticationManager.hash_password(password)
            user = User.create(
                email.lower(), 
                password_hash, 
                first_name.strip(), 
                last_name.strip(), 
                phone_number.strip() if phone_number else None
            )
            
            if user:
                # Create default preferences
                UserPreferences.create_default(user.id)
                return True, "Registration successful"
            else:
                return False, "Registration failed. Please try again."
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, "Registration failed due to system error"
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[User]:
        """Authenticate a user"""
        if not email or not password:
            return None
        
        try:
            user = User.get_by_email(email.lower())
            if user and AuthenticationManager.verify_password(password, user.password_hash):
                return user
        except Exception as e:
            logger.error(f"Authentication error: {e}")
        
        return None
    
    @staticmethod
    def login_user(user: User):
        """Set user session"""
        st.session_state.user_id = user.id
        st.session_state.user_email = user.email
        st.session_state.user_name = f"{user.first_name} {user.last_name}"
        st.session_state.user_first_name = user.first_name
        st.session_state.user_last_name = user.last_name
        st.session_state.user_phone = user.phone_number
        st.session_state.authenticated = True
        st.session_state.login_time = st.session_state.get('login_time', None)
    
    @staticmethod
    def logout_user():
        """Clear user session"""
        keys_to_clear = [
            'user_id', 'user_email', 'user_name', 'user_first_name', 
            'user_last_name', 'user_phone', 'authenticated', 'login_time'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)
    
    @staticmethod
    def get_current_user_id() -> Optional[int]:
        """Get current user ID"""
        return st.session_state.get('user_id')
    
    @staticmethod
    def get_current_user() -> Optional[User]:
        """Get current user object"""
        user_id = AuthenticationManager.get_current_user_id()
        if user_id:
            return User.get_by_id(user_id)
        return None
    
    @staticmethod
    def require_authentication():
        """Decorator to require authentication"""
        if not AuthenticationManager.is_authenticated():
            st.error("Please log in to access this page")
            st.stop()

def show_login_form():
    """Display login form"""
    st.subheader("🔐 Login")
    
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            login_button = st.form_submit_button("Login", use_container_width=True)
        with col2:
            forgot_password = st.form_submit_button("Forgot Password?", use_container_width=True)
        
        if login_button:
            if not email or not password:
                st.error("Please fill in all fields")
            else:
                with st.spinner("Logging in..."):
                    user = AuthenticationManager.authenticate_user(email, password)
                    if user:
                        AuthenticationManager.login_user(user)
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
        
        if forgot_password:
            st.info("Password reset functionality will be implemented soon")

def show_register_form():
    """Display registration form"""
    st.subheader("📝 Create Account")
    
    with st.form("register_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name *", placeholder="Enter your first name")
        with col2:
            last_name = st.text_input("Last Name *", placeholder="Enter your last name")
        
        email = st.text_input("Email *", placeholder="Enter your email")
        phone_number = st.text_input("Phone Number (Optional)", placeholder="+1234567890")
        
        col3, col4 = st.columns(2)
        with col3:
            password = st.text_input("Password *", type="password", placeholder="Create a password")
        with col4:
            confirm_password = st.text_input("Confirm Password *", type="password", placeholder="Confirm your password")
        
        # Password requirements
        st.caption("Password must be at least 8 characters with uppercase, lowercase, and number")
        
        # Terms and conditions
        terms_accepted = st.checkbox("I agree to the Terms and Conditions")
        
        register_button = st.form_submit_button("Create Account", use_container_width=True)
        
        if register_button:
            if not all([first_name, last_name, email, password, confirm_password]):
                st.error("Please fill in all required fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif not terms_accepted:
                st.error("Please accept the Terms and Conditions")
            else:
                with st.spinner("Creating account..."):
                    success, message = AuthenticationManager.register_user(
                        email, password, first_name, last_name, phone_number
                    )
                    if success:
                        st.success(message + " Please login with your credentials.")
                        st.balloons()
                    else:
                        st.error(message)

def show_auth_page():
    """Display authentication page"""

    # Header
    st.title("🏦 AI-Powered Personal Finance Advisor")
    st.markdown("---")
    
    # Description
    st.markdown("""
    ### Welcome to Your Personal Finance Assistant
    
    **Features:**
    - 🤖 AI-powered transaction categorization
    - 📊 Smart budgeting and spending insights
    - 💰 Personalized investment recommendations
    - 🎯 Goal tracking and progress monitoring
    - 📱 Real-time notifications and alerts
    """)
    
    st.markdown("---")
    
    # Authentication tabs
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        show_register_form()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Secure • Private • AI-Powered"
        "</div>", 
        unsafe_allow_html=True
    )

    create_footer()