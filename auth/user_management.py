"""user_management.py - User CRUD operations"""

"""User CRUD operations"""

import streamlit as st
from typing import Optional, Dict, Any
from database.models import User, UserPreferences
from auth.authentication import AuthenticationManager
import logging

logger = logging.getLogger(__name__)

class UserManager:
    """Handles user management operations"""
    
    @staticmethod
    def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile information"""
        user = User.get_by_id(user_id)
        if not user:
            return None
        
        preferences = UserPreferences.get_by_user(user_id)
        
        return {
            'user': user,
            'preferences': preferences,
            'full_name': f"{user.first_name} {user.last_name}",
            'member_since': user.created_at.strftime('%B %Y') if user.created_at else 'Unknown'
        }
    
    @staticmethod
    def update_user_profile(user_id: int, first_name: str, last_name: str, 
                          phone_number: str = None) -> tuple[bool, str]:
        """Update user profile"""
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # Validate input
        if not first_name.strip() or not last_name.strip():
            return False, "First name and last name are required"
        
        if phone_number and not AuthenticationManager.validate_phone(phone_number):
            return False, "Invalid phone number format"
        
        try:
            user.first_name = first_name.strip()
            user.last_name = last_name.strip()
            user.phone_number = phone_number.strip() if phone_number else None
            
            if user.update():
                # Update session state
                st.session_state.user_name = f"{first_name} {last_name}"
                st.session_state.user_first_name = first_name
                st.session_state.user_last_name = last_name
                st.session_state.user_phone = phone_number
                
                return True, "Profile updated successfully"
            else:
                return False, "Failed to update profile"
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            return False, "Profile update failed due to system error"
    
    @staticmethod
    def update_user_preferences(user_id: int, notification_email: bool = True,
                              notification_sms: bool = False, budget_alerts: bool = True,
                              investment_alerts: bool = True) -> tuple[bool, str]:
        """Update user preferences"""
        preferences = UserPreferences.get_by_user(user_id)
        
        if not preferences:
            # Create default preferences if they don't exist
            preferences = UserPreferences.create_default(user_id)
            if not preferences:
                return False, "Failed to create user preferences"
        
        try:
            preferences.notification_email = notification_email
            preferences.notification_sms = notification_sms
            preferences.budget_alerts = budget_alerts
            preferences.investment_alerts = investment_alerts
            
            if preferences.update():
                return True, "Preferences updated successfully"
            else:
                return False, "Failed to update preferences"
        except Exception as e:
            logger.error(f"Preferences update error: {e}")
            return False, "Preferences update failed due to system error"
    
    @staticmethod
    def change_password(user_id: int, current_password: str, 
                       new_password: str) -> tuple[bool, str]:
        """Change user password"""
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # Verify current password
        if not AuthenticationManager.verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect"
        
        # Validate new password
        is_valid, message = AuthenticationManager.validate_password(new_password)
        if not is_valid:
            return False, message
        
        try:
            # Hash new password
            new_password_hash = AuthenticationManager.hash_password(new_password)
            
            # Update password in database
            from database.connection import get_db_instance
            db = get_db_instance()
            success = db.execute_update(
                "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (new_password_hash, user_id)
            )
            
            if success:
                return True, "Password changed successfully"
            else:
                return False, "Failed to change password"
        except Exception as e:
            logger.error(f"Password change error: {e}")
            return False, "Password change failed due to system error"
    
    @staticmethod
    def delete_user_account(user_id: int, password: str) -> tuple[bool, str]:
        """Delete user account (with password confirmation)"""
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # Verify password
        if not AuthenticationManager.verify_password(password, user.password_hash):
            return False, "Password is incorrect"
        
        try:
            # Delete user (cascade will handle related records)
            from database.connection import get_db_instance
            db = get_db_instance()
            success = db.execute_update("DELETE FROM users WHERE id = %s", (user_id,))
            
            if success:
                # Clear session
                AuthenticationManager.logout_user()
                return True, "Account deleted successfully"
            else:
                return False, "Failed to delete account"
        except Exception as e:
            logger.error(f"Account deletion error: {e}")
            return False, "Account deletion failed due to system error"

def show_profile_settings():
    """Display user profile settings"""
    st.subheader("👤 Profile Settings")
    
    user_id = AuthenticationManager.get_current_user_id()
    if not user_id:
        st.error("Please log in to access profile settings")
        return
    
    profile = UserManager.get_user_profile(user_id)
    if not profile:
        st.error("Failed to load profile")
        return
    
    user = profile['user']
    preferences = profile['preferences']
    
    # Profile Information
    st.write("### Personal Information")
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name", value=user.first_name)
        with col2:
            last_name = st.text_input("Last Name", value=user.last_name)
        
        email = st.text_input("Email", value=user.email, disabled=True)
        phone_number = st.text_input("Phone Number", value=user.phone_number or "")
        
        if st.form_submit_button("Update Profile"):
            success, message = UserManager.update_user_profile(
                user_id, first_name, last_name, phone_number
            )
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    st.divider()
    
    # Notification Preferences
    st.write("### Notification Preferences")
    
    if preferences:
        with st.form("preferences_form"):
            notification_email = st.checkbox(
                "Email Notifications", 
                value=preferences.notification_email
            )
            notification_sms = st.checkbox(
                "SMS Notifications", 
                value=preferences.notification_sms,
                disabled=not user.phone_number
            )
            budget_alerts = st.checkbox(
                "Budget Alerts", 
                value=preferences.budget_alerts
            )
            investment_alerts = st.checkbox(
                "Investment Alerts", 
                value=preferences.investment_alerts
            )
            
            if st.form_submit_button("Update Preferences"):
                success, message = UserManager.update_user_preferences(
                    user_id, notification_email, notification_sms, 
                    budget_alerts, investment_alerts
                )
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    st.divider()
    
    # Change Password
    st.write("### Change Password")
    
    with st.form("password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Change Password"):
            if not all([current_password, new_password, confirm_password]):
                st.error("Please fill in all password fields")
            elif new_password != confirm_password:
                st.error("New passwords do not match")
            else:
                success, message = UserManager.change_password(
                    user_id, current_password, new_password
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    st.divider()
    
    # Account Information
    st.write("### Account Information")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Member Since:** {profile['member_since']}")
    with col2:
        st.info(f"**Account Status:** Active")
    
    # Danger Zone
    st.write("### Danger Zone")
    st.warning("⚠️ Account deletion is permanent and cannot be undone")
    
    if st.button("Delete Account", type="secondary"):
        st.session_state.show_delete_confirmation = True
    
    if st.session_state.get('show_delete_confirmation', False):
        with st.form("delete_account_form"):
            st.error("Are you sure you want to delete your account?")
            st.write("This action cannot be undone. All your data will be permanently deleted.")
            
            password_confirm = st.text_input("Enter your password to confirm", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Delete Account", type="primary"):
                    if not password_confirm:
                        st.error("Please enter your password")
                    else:
                        success, message = UserManager.delete_user_account(user_id, password_confirm)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_delete_confirmation = False
                    st.rerun()
