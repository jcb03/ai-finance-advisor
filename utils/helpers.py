"""helpers.py - Utility functions"""

"""Utility functions"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

class DateHelper:
    """Date utility functions"""
    
    @staticmethod
    def get_current_month_range() -> tuple[date, date]:
        """Get start and end date of current month"""
        today = date.today()
        start_date = today.replace(day=1)
        
        # Get last day of month
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        return start_date, end_date
    
    @staticmethod
    def get_last_n_months(n: int) -> tuple[date, date]:
        """Get date range for last n months"""
        today = date.today()
        end_date = today
        
        # Calculate start date
        year = today.year
        month = today.month - n
        
        while month <= 0:
            month += 12
            year -= 1
        
        start_date = date(year, month, 1)
        
        return start_date, end_date
    
    @staticmethod
    def format_date_range(start_date: date, end_date: date) -> str:
        """Format date range for display"""
        if start_date == end_date:
            return start_date.strftime("%B %d, %Y")
        elif start_date.year == end_date.year:
            if start_date.month == end_date.month:
                return f"{start_date.strftime('%B %d')} - {end_date.strftime('%d, %Y')}"
            else:
                return f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
        else:
            return f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"

class ChartHelper:
    """Chart utility functions"""
    
    @staticmethod
    def create_spending_pie_chart(category_data: Dict[str, float], title: str = "Spending by Category") -> go.Figure:
        """Create pie chart for spending by category"""
        if not category_data:
            fig = go.Figure()
            fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
            return fig
        
        categories = list(category_data.keys())
        amounts = list(category_data.values())
        
        fig = px.pie(
            values=amounts,
            names=categories,
            title=title,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
        )
        
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.01)
        )
        
        return fig
    
    @staticmethod
    def create_spending_trend_chart(monthly_data: Dict[str, float], title: str = "Monthly Spending Trend") -> go.Figure:
        """Create line chart for spending trends"""
        if not monthly_data:
            fig = go.Figure()
            fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
            return fig
        
        months = list(monthly_data.keys())
        amounts = list(monthly_data.values())
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=months,
            y=amounts,
            mode='lines+markers',
            name='Spending',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            hovermode='x unified'
        )
        
        fig.update_traces(
            hovertemplate='<b>%{x}</b><br>Amount: $%{y:,.2f}<extra></extra>'
        )
        
        return fig
    
    @staticmethod
    def create_budget_progress_chart(budgets: List[Dict], title: str = "Budget Progress") -> go.Figure:
        """Create horizontal bar chart for budget progress"""
        if not budgets:
            fig = go.Figure()
            fig.add_annotation(text="No budgets available", x=0.5, y=0.5, showarrow=False)
            return fig
        
        categories = [budget['category'] for budget in budgets]
        spent = [budget['spent'] for budget in budgets]
        limits = [budget['limit'] for budget in budgets]
        
        fig = go.Figure()
        
        # Add spent amounts
        fig.add_trace(go.Bar(
            y=categories,
            x=spent,
            name='Spent',
            orientation='h',
            marker_color='#ff7f0e'
        ))
        
        # Add budget limits
        fig.add_trace(go.Bar(
            y=categories,
            x=limits,
            name='Budget Limit',
            orientation='h',
            marker_color='#2ca02c',
            opacity=0.6
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Amount ($)",
            yaxis_title="Category",
            barmode='overlay',
            hovermode='y unified'
        )
        
        return fig
    
    @staticmethod
    def create_goal_progress_chart(goals: List[Dict], title: str = "Goal Progress") -> go.Figure:
        """Create progress chart for financial goals"""
        if not goals:
            fig = go.Figure()
            fig.add_annotation(text="No goals available", x=0.5, y=0.5, showarrow=False)
            return fig
        
        goal_names = [goal['name'] for goal in goals]
        current_amounts = [goal['current'] for goal in goals]
        target_amounts = [goal['target'] for goal in goals]
        progress_percentages = [(current/target)*100 if target > 0 else 0 for current, target in zip(current_amounts, target_amounts)]
        
        fig = go.Figure()
        
        # Add progress bars
        colors = ['#2ca02c' if p >= 100 else '#ff7f0e' if p >= 75 else '#d62728' if p < 25 else '#1f77b4' for p in progress_percentages]
        
        fig.add_trace(go.Bar(
            y=goal_names,
            x=progress_percentages,
            orientation='h',
            marker_color=colors,
            text=[f"{p:.1f}%" for p in progress_percentages],
            textposition='inside'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Progress (%)",
            yaxis_title="Goals",
            xaxis=dict(range=[0, 100])
        )
        
        return fig

class FormatHelper:
    """Formatting utility functions"""
    
    @staticmethod
    def format_currency(amount: float, currency: str = "$") -> str:
        """Format amount as currency"""
        if amount >= 0:
            return f"{currency}{amount:,.2f}"
        else:
            return f"-{currency}{abs(amount):,.2f}"
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 1) -> str:
        """Format value as percentage"""
        return f"{value:.{decimal_places}f}%"
    
    @staticmethod
    def format_large_number(number: float) -> str:
        """Format large numbers with K, M, B suffixes"""
        if abs(number) >= 1_000_000_000:
            return f"{number/1_000_000_000:.1f}B"
        elif abs(number) >= 1_000_000:
            return f"{number/1_000_000:.1f}M"
        elif abs(number) >= 1_000:
            return f"{number/1_000:.1f}K"
        else:
            return f"{number:.0f}"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50) -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

class ValidationHelper:
    """Validation utility functions"""
    
    @staticmethod
    def validate_amount(amount: str) -> tuple[bool, float]:
        """Validate amount input"""
        try:
            # Remove currency symbols and spaces
            cleaned = re.sub(r'[$€£¥₹,\s]', '', amount.strip())
            value = float(cleaned)
            
            if value < 0:
                return False, 0.0
            
            return True, value
        except ValueError:
            return False, 0.0
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date) -> tuple[bool, str]:
        """Validate date range"""
        if start_date > end_date:
            return False, "Start date cannot be after end date"
        
        if end_date > date.today():
            return False, "End date cannot be in the future"
        
        # Check if range is too large (more than 5 years)
        if (end_date - start_date).days > 5 * 365:
            return False, "Date range cannot exceed 5 years"
        
        return True, "Valid date range"

class NotificationHelper:
    """Notification utility functions"""
    
    @staticmethod
    def show_success_toast(message: str):
        """Show success toast notification"""
        st.success(f"✅ {message}")
    
    @staticmethod
    def show_error_toast(message: str):
        """Show error toast notification"""
        st.error(f"❌ {message}")
    
    @staticmethod
    def show_warning_toast(message: str):
        """Show warning toast notification"""
        st.warning(f"⚠️ {message}")
    
    @staticmethod
    def show_info_toast(message: str):
        """Show info toast notification"""
        st.info(f"ℹ️ {message}")

class DataHelper:
    """Data processing utility functions"""
    
    @staticmethod
    def calculate_spending_insights(transactions: List[Dict]) -> Dict[str, Any]:
        """Calculate spending insights from transactions"""
        if not transactions:
            return {}
        
        df = pd.DataFrame(transactions)
        
        # Filter spending transactions (positive amounts)
        spending_df = df[df['amount'] > 0]
        
        if spending_df.empty:
            return {}
        
        insights = {
            'total_spending': spending_df['amount'].sum(),
            'average_transaction': spending_df['amount'].mean(),
            'largest_transaction': spending_df['amount'].max(),
            'most_frequent_category': spending_df['category'].mode().iloc[0] if not spending_df['category'].mode().empty else 'Unknown',
            'transaction_count': len(spending_df),
            'spending_by_category': spending_df.groupby('category')['amount'].sum().to_dict(),
            'daily_average': spending_df['amount'].sum() / max(1, (spending_df['transaction_date'].max() - spending_df['transaction_date'].min()).days + 1)
        }
        
        return insights
    
    @staticmethod
    def detect_spending_anomalies(transactions: List[Dict], threshold: float = 2.0) -> List[Dict]:
        """Detect anomalous spending transactions"""
        if not transactions:
            return []
        
        df = pd.DataFrame(transactions)
        spending_df = df[df['amount'] > 0]
        
        if len(spending_df) < 10:  # Need sufficient data
            return []
        
        # Calculate z-score for amounts
        mean_amount = spending_df['amount'].mean()
        std_amount = spending_df['amount'].std()
        
        if std_amount == 0:
            return []
        
        spending_df['z_score'] = (spending_df['amount'] - mean_amount) / std_amount
        
        # Find anomalies
        anomalies = spending_df[abs(spending_df['z_score']) > threshold]
        
        return anomalies.to_dict('records')
    
    @staticmethod
    def generate_spending_summary(transactions: List[Dict], period: str = "month") -> Dict[str, Any]:
        """Generate spending summary for a period"""
        if not transactions:
            return {}
        
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
        # Group by period
        if period == "month":
            df['period'] = df['transaction_date'].dt.to_period('M')
        elif period == "week":
            df['period'] = df['transaction_date'].dt.to_period('W')
        elif period == "day":
            df['period'] = df['transaction_date'].dt.to_period('D')
        
        # Calculate summary
        summary = df.groupby('period').agg({
            'amount': ['sum', 'mean', 'count'],
            'category': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown'
        }).round(2)
        
        return summary.to_dict()

def show_loading_spinner(message: str = "Loading..."):
    """Show loading spinner with message"""
    return st.spinner(message)

def create_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Create a metric card"""
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color
    )

def create_info_box(title: str, content: str, icon: str = "ℹ️"):
    """Create an info box"""
    st.info(f"{icon} **{title}**\n\n{content}")

def create_warning_box(title: str, content: str, icon: str = "⚠️"):
    """Create a warning box"""
    st.warning(f"{icon} **{title}**\n\n{content}")

def create_error_box(title: str, content: str, icon: str = "❌"):
    """Create an error box"""
    st.error(f"{icon} **{title}**\n\n{content}")

def create_footer():
    """Create a footer using Streamlit components"""
    import streamlit as st
    
    # Add spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create footer container
    with st.container():
        st.markdown("---")
        
        # Title
        st.markdown("### 🔗 Connect with the Developer")
        
        # Social links in columns
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        
        with col2:
            st.markdown("""
            <a href="https://www.linkedin.com/in/jai-chaudhary-54bb86221/" target="_blank" style="text-decoration: none;">
                <div style="text-align: center; padding: 10px; background: #0077B5; color: white; border-radius: 10px; margin: 5px;">
                    <strong>🔗 LinkedIn</strong>
                </div>
            </a>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <a href="https://github.com/jcb03" target="_blank" style="text-decoration: none;">
                <div style="text-align: center; padding: 10px; background: #333; color: white; border-radius: 10px; margin: 5px;">
                    <strong>💻 GitHub</strong>
                </div>
            </a>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <a href="https://learn.microsoft.com/en-us/users/jaichaudhary-6371/" target="_blank" style="text-decoration: none;">
                <div style="text-align: center; padding: 10px; background: #00BCF2; color: white; border-radius: 10px; margin: 5px;">
                    <strong>📚 Microsoft Learn</strong>
                </div>
            </a>
            """, unsafe_allow_html=True)
        
        # Attribution
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #666; font-size: 14px;'>"
            "<p><strong>Made with ❤️ by Jai Chaudhary</strong></p>"
            "<p style='font-size: 12px;'>AI-Powered Personal Finance Advisor © 2025</p>"
            "</div>",
            unsafe_allow_html=True
        )

