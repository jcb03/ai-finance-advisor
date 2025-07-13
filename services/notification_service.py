"""notification_service.py - Notifications"""

import streamlit as st
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
import logging
from config.settings import Settings
from database.models import User, UserPreferences

logger = logging.getLogger(__name__)

class NotificationService:
    """Handles various types of notifications"""
    
    def __init__(self):
        # Twilio configuration
        twilio_config = Settings.twilio_config()
        self.twilio_account_sid = twilio_config['account_sid']
        self.twilio_auth_token = twilio_config['auth_token']
        self.twilio_phone_number = twilio_config['phone_number']
        
        # Email configuration
        email_config = Settings.email_config()
        self.smtp_server = email_config['smtp_server']
        self.smtp_port = email_config['smtp_port']
        self.email_address = email_config['address']
        self.email_password = email_config['password']
        
        # Initialize Twilio client
        if self.twilio_account_sid and self.twilio_auth_token:
            try:
                self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
            except Exception as e:
                logger.error(f"Twilio initialization failed: {e}")
                self.twilio_client = None
        else:
            self.twilio_client = None
    
    def send_sms_notification(self, phone_number: str, message: str) -> bool:
        """Send SMS notification using Twilio"""
        if not self.twilio_client:
            logger.warning("Twilio not configured. SMS notifications disabled.")
            return False
        
        try:
            # Format phone number
            if not phone_number.startswith('+'):
                phone_number = '+1' + phone_number.replace('-', '').replace(' ', '')
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=phone_number
            )
            
            logger.info(f"SMS sent successfully to {phone_number}: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS to {phone_number}: {e}")
            return False
    
    def send_email_notification(self, email: str, subject: str, message: str, html_message: str = None) -> bool:
        """Send email notification"""
        if not all([self.smtp_server, self.email_address, self.email_password]):
            logger.warning("Email not configured. Email notifications disabled.")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = email
            msg['Subject'] = subject
            
            # Add plain text part
            text_part = MIMEText(message, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_message:
                html_part = MIMEText(html_message, 'html')
                msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {email}: {e}")
            return False
    
    def send_budget_alert(self, user_id: int, alert: Dict):
        """Send budget alert notification"""
        try:
            user = User.get_by_id(user_id)
            preferences = UserPreferences.get_by_user(user_id)
            
            if not user or not preferences:
                return False
            
            # Prepare message content
            if alert['alert_type'] == 'overspent':
                subject = f"🚨 Budget Alert: {alert['category']} Overspent"
                message = f"""
Hi {user.first_name},

You have exceeded your budget for {alert['category']}.

Budget Details:
• Budget Limit: ${alert['budget_limit']:,.2f}
• Amount Spent: ${alert['amount_spent']:,.2f}
• Overspent by: ${alert['overspent_amount']:,.2f}

Consider reviewing your spending in this category to get back on track.

Best regards,
AI Finance Advisor
                """.strip()
                
                html_message = f"""
                <html>
                <body>
                    <h2>🚨 Budget Alert: {alert['category']} Overspent</h2>
                    <p>Hi {user.first_name},</p>
                    <p>You have exceeded your budget for <strong>{alert['category']}</strong>.</p>
                    
                    <h3>Budget Details:</h3>
                    <ul>
                        <li>Budget Limit: <strong>${alert['budget_limit']:,.2f}</strong></li>
                        <li>Amount Spent: <strong>${alert['amount_spent']:,.2f}</strong></li>
                        <li>Overspent by: <strong style="color: red;">${alert['overspent_amount']:,.2f}</strong></li>
                    </ul>
                    
                    <p>Consider reviewing your spending in this category to get back on track.</p>
                    
                    <p>Best regards,<br>AI Finance Advisor</p>
                </body>
                </html>
                """
                
            else:  # warning or near_limit
                subject = f"⚠️ Budget Warning: {alert['category']} Approaching Limit"
                message = f"""
Hi {user.first_name},

You are approaching your budget limit for {alert['category']}.

Budget Details:
• Budget Limit: ${alert['budget_limit']:,.2f}
• Amount Spent: ${alert['amount_spent']:,.2f}
• Remaining Budget: ${alert['remaining_budget']:,.2f}
• Usage: {alert['usage_percentage']:.1f}%

Consider monitoring your spending in this category.

Best regards,
AI Finance Advisor
                """.strip()
                
                html_message = f"""
                <html>
                <body>
                    <h2>⚠️ Budget Warning: {alert['category']} Approaching Limit</h2>
                    <p>Hi {user.first_name},</p>
                    <p>You are approaching your budget limit for <strong>{alert['category']}</strong>.</p>
                    
                    <h3>Budget Details:</h3>
                    <ul>
                        <li>Budget Limit: <strong>${alert['budget_limit']:,.2f}</strong></li>
                        <li>Amount Spent: <strong>${alert['amount_spent']:,.2f}</strong></li>
                        <li>Remaining Budget: <strong>${alert['remaining_budget']:,.2f}</strong></li>
                        <li>Usage: <strong>{alert['usage_percentage']:.1f}%</strong></li>
                    </ul>
                    
                    <p>Consider monitoring your spending in this category.</p>
                    
                    <p>Best regards,<br>AI Finance Advisor</p>
                </body>
                </html>
                """
            
            # Send notifications based on preferences
            success = True
            
            if preferences.notification_email and preferences.budget_alerts:
                success &= self.send_email_notification(user.email, subject, message, html_message)
            
            if preferences.notification_sms and preferences.budget_alerts and user.phone_number:
                sms_message = f"Budget Alert: {alert['category']} - ${alert['amount_spent']:,.2f} spent of ${alert['budget_limit']:,.2f} budget."
                success &= self.send_sms_notification(user.phone_number, sms_message)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending budget alert: {e}")
            return False
    
    def send_investment_opportunity_alert(self, user_id: int, opportunity: Dict):
        """Send investment opportunity notification"""
        try:
            user = User.get_by_id(user_id)
            preferences = UserPreferences.get_by_user(user_id)
            
            if not user or not preferences:
                return False
            
            subject = f"💰 Investment Opportunity: {opportunity['symbol']}"
            message = f"""
Hi {user.first_name},

Investment Opportunity Alert:

Symbol: {opportunity['symbol']}
Current Price: ${opportunity['price']:.2f}
Recommendation: {opportunity['recommendation']}
Reasoning: {opportunity['reasoning']}

Consider reviewing this opportunity in your investment dashboard.

Best regards,
AI Finance Advisor
            """.strip()
            
            html_message = f"""
            <html>
            <body>
                <h2>💰 Investment Opportunity: {opportunity['symbol']}</h2>
                <p>Hi {user.first_name},</p>
                
                <h3>Investment Opportunity Alert:</h3>
                <ul>
                    <li><strong>Symbol:</strong> {opportunity['symbol']}</li>
                    <li><strong>Current Price:</strong> ${opportunity['price']:.2f}</li>
                    <li><strong>Recommendation:</strong> {opportunity['recommendation']}</li>
                    <li><strong>Reasoning:</strong> {opportunity['reasoning']}</li>
                </ul>
                
                <p>Consider reviewing this opportunity in your investment dashboard.</p>
                
                <p>Best regards,<br>AI Finance Advisor</p>
            </body>
            </html>
            """
            
            # Send notifications based on preferences
            success = True
            
            if preferences.notification_email and preferences.investment_alerts:
                success &= self.send_email_notification(user.email, subject, message, html_message)
            
            if preferences.notification_sms and preferences.investment_alerts and user.phone_number:
                sms_message = f"Investment Alert: {opportunity['symbol']} - {opportunity['recommendation']}"
                success &= self.send_sms_notification(user.phone_number, sms_message)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending investment opportunity alert: {e}")
            return False
    
    def send_goal_achievement_notification(self, user_id: int, goal: Dict):
        """Send goal achievement notification"""
        try:
            user = User.get_by_id(user_id)
            preferences = UserPreferences.get_by_user(user_id)
            
            if not user or not preferences:
                return False
            
            subject = f"🎉 Goal Achieved: {goal['name']}"
            message = f"""
Hi {user.first_name},

Congratulations! You have achieved your financial goal: {goal['name']}

Goal Details:
• Target Amount: ${goal['target_amount']:,.2f}
• Current Amount: ${goal['current_amount']:,.2f}
• Achievement Date: {goal['achievement_date']}

Keep up the great work with your financial planning!

Best regards,
AI Finance Advisor
            """.strip()
            
            html_message = f"""
            <html>
            <body>
                <h2>🎉 Goal Achieved: {goal['name']}</h2>
                <p>Hi {user.first_name},</p>
                
                <p><strong>Congratulations!</strong> You have achieved your financial goal: <strong>{goal['name']}</strong></p>
                
                <h3>Goal Details:</h3>
                <ul>
                    <li>Target Amount: <strong>${goal['target_amount']:,.2f}</strong></li>
                    <li>Current Amount: <strong>${goal['current_amount']:,.2f}</strong></li>
                    <li>Achievement Date: <strong>{goal['achievement_date']}</strong></li>
                </ul>
                
                <p>Keep up the great work with your financial planning!</p>
                
                <p>Best regards,<br>AI Finance Advisor</p>
            </body>
            </html>
            """
            
            # Send notifications based on preferences
            success = True
            
            if preferences.notification_email:
                success &= self.send_email_notification(user.email, subject, message, html_message)
            
            if preferences.notification_sms and user.phone_number:
                sms_message = f"🎉 Congratulations! You achieved your goal: {goal['name']} (${goal['target_amount']:,.2f})"
                success &= self.send_sms_notification(user.phone_number, sms_message)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending goal achievement notification: {e}")
            return False
    
    def send_weekly_summary(self, user_id: int, summary: Dict):
        """Send weekly financial summary"""
        try:
            user = User.get_by_id(user_id)
            preferences = UserPreferences.get_by_user(user_id)
            
            if not user or not preferences or not preferences.notification_email:
                return False
            
            subject = f"📊 Weekly Financial Summary - {summary['week_ending']}"
            message = f"""
Hi {user.first_name},

Here's your weekly financial summary:

Spending Summary:
• Total Spent: ${summary['total_spent']:,.2f}
• Top Category: {summary['top_category']} (${summary['top_category_amount']:,.2f})
• Transactions: {summary['transaction_count']}

Budget Status:
• Budgets on Track: {summary['budgets_on_track']}
• Budgets Over Limit: {summary['budgets_over_limit']}

Goals Progress:
• Active Goals: {summary['active_goals']}
• Goals Achieved This Week: {summary['goals_achieved']}

Keep up the great work managing your finances!

Best regards,
AI Finance Advisor
            """.strip()
            
            html_message = f"""
            <html>
            <body>
                <h2>📊 Weekly Financial Summary - {summary['week_ending']}</h2>
                <p>Hi {user.first_name},</p>
                
                <p>Here's your weekly financial summary:</p>
                
                <h3>💰 Spending Summary:</h3>
                <ul>
                    <li>Total Spent: <strong>${summary['total_spent']:,.2f}</strong></li>
                    <li>Top Category: <strong>{summary['top_category']}</strong> (${summary['top_category_amount']:,.2f})</li>
                    <li>Transactions: <strong>{summary['transaction_count']}</strong></li>
                </ul>
                
                <h3>📊 Budget Status:</h3>
                <ul>
                    <li>Budgets on Track: <strong style="color: green;">{summary['budgets_on_track']}</strong></li>
                    <li>Budgets Over Limit: <strong style="color: red;">{summary['budgets_over_limit']}</strong></li>
                </ul>
                
                <h3>🎯 Goals Progress:</h3>
                <ul>
                    <li>Active Goals: <strong>{summary['active_goals']}</strong></li>
                    <li>Goals Achieved This Week: <strong>{summary['goals_achieved']}</strong></li>
                </ul>
                
                <p>Keep up the great work managing your finances!</p>
                
                <p>Best regards,<br>AI Finance Advisor</p>
            </body>
            </html>
            """
            
            return self.send_email_notification(user.email, subject, message, html_message)
            
        except Exception as e:
            logger.error(f"Error sending weekly summary: {e}")
            return False
    
    def show_in_app_notification(self, message: str, notification_type: str = "info"):
        """Display in-app notification using Streamlit"""
        if notification_type == "success":
            st.success(message)
        elif notification_type == "warning":
            st.warning(message)
        elif notification_type == "error":
            st.error(message)
        else:
            st.info(message)
    
    def create_notification_toast(self, title: str, message: str, type: str = "info"):
        """Create a toast notification"""
        icons = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️"
        }
        
        icon = icons.get(type, "ℹ️")
        full_message = f"{icon} **{title}**\n\n{message}"
        
        self.show_in_app_notification(full_message, type)
    
    def test_notification_settings(self, user_id: int) -> Dict[str, bool]:
        """Test notification settings"""
        user = User.get_by_id(user_id)
        if not user:
            return {"error": "User not found"}
        
        results = {}
        
        # Test email
        if self.email_address and self.email_password:
            test_subject = "Test Email from AI Finance Advisor"
            test_message = f"Hi {user.first_name},\n\nThis is a test email to verify your notification settings.\n\nBest regards,\nAI Finance Advisor"
            results['email'] = self.send_email_notification(user.email, test_subject, test_message)
        else:
            results['email'] = False
        
        # Test SMS
        if user.phone_number and self.twilio_client:
            test_sms = f"Hi {user.first_name}, this is a test SMS from AI Finance Advisor to verify your notification settings."
            results['sms'] = self.send_sms_notification(user.phone_number, test_sms)
        else:
            results['sms'] = False
        
        return results
