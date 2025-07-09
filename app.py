"""Main Streamlit application"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import custom modules
from auth.authentication import AuthenticationManager, show_auth_page
from auth.user_management import show_profile_settings
from utils.file_processor import FileProcessor
from utils.helpers import (
    DateHelper, ChartHelper, FormatHelper, ValidationHelper,
    NotificationHelper, DataHelper, show_loading_spinner,
    create_metric_card, create_info_box, create_warning_box
)
from services.transaction_parser import TransactionParser
from services.ai_advisor import AIFinancialAdvisor
from services.investment_service import InvestmentService
from services.notification_service import NotificationService
from database.models import Transaction, Budget, FinancialGoal, User
from config.settings import Settings

# Page configuration
st.set_page_config(
    page_title="AI Personal Finance Advisor",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
@st.cache_resource
def get_services():
    """Initialize and cache services"""
    return {
        'file_processor': FileProcessor(),
        'transaction_parser': TransactionParser(),
        'ai_advisor': AIFinancialAdvisor(),
        'investment_service': InvestmentService(),
        'notification_service': NotificationService()
    }

def main():
    """Main application function"""
    try:
        # Check authentication
        if not AuthenticationManager.is_authenticated():
            show_auth_page()
            return
        
        # Initialize services
        services = get_services()
        
        # Show main dashboard
        show_dashboard(services)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"An error occurred: {e}")

def show_dashboard(services):
    """Main dashboard page"""
    st.title("🏦 AI-Powered Personal Finance Advisor")
    
    user_id = AuthenticationManager.get_current_user_id()
    user_name = st.session_state.get('user_name', 'User')
    
    # Sidebar navigation
    with st.sidebar:
        st.header(f"Welcome, {user_name.split()[0]}!")
        
        # Navigation menu
        page = st.selectbox(
            "Navigate to:",
            [
                "📊 Overview", 
                "💳 Transactions", 
                "💰 Budgets", 
                "🎯 Goals", 
                "📈 Investments", 
                "🤖 AI Insights",
                "⚙️ Settings"
            ]
        )
        
        st.divider()
        
        # Quick stats
        st.subheader("Quick Stats")
        try:
            recent_transactions = Transaction.get_by_user(user_id, limit=30)
            total_spent = sum(float(t.amount) for t in recent_transactions if float(t.amount) > 0)
            st.metric("30-Day Spending", f"${total_spent:,.2f}")
            
            budgets = Budget.get_by_user(user_id)
            st.metric("Active Budgets", len(budgets))
            
            goals = FinancialGoal.get_by_user(user_id)
            active_goals = len([g for g in goals if g.status == 'active'])
            st.metric("Active Goals", active_goals)
        except Exception as e:
            logger.error(f"Error loading quick stats: {e}")
        
        st.divider()
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            AuthenticationManager.logout_user()
            st.rerun()
    
    # Main content based on selected page
    page_key = page.split()[1]  # Extract key from "📊 Overview" -> "Overview"
    
    if page_key == "Overview":
        show_overview_page(user_id, services)
    elif page_key == "Transactions":
        show_transactions_page(user_id, services)
    elif page_key == "Budgets":
        show_budgets_page(user_id, services)
    elif page_key == "Goals":
        show_goals_page(user_id, services)
    elif page_key == "Investments":
        show_investments_page(user_id, services)
    elif page_key == "Insights":
        show_insights_page(user_id, services)
    elif page_key == "Settings":
        show_settings_page(user_id, services)

def show_overview_page(user_id: int, services):
    """Overview page with key metrics and charts"""
    st.header("📊 Financial Overview")
    
    try:
        # Get data
        transactions = Transaction.get_by_user(user_id, limit=100)
        budgets = Budget.get_by_user(user_id)
        goals = FinancialGoal.get_by_user(user_id)
        
        # Calculate metrics
        current_month_start, current_month_end = DateHelper.get_current_month_range()
        current_month_transactions = [
            t for t in transactions 
            if current_month_start <= t.transaction_date <= current_month_end
        ]
        
        total_spent = sum(float(t.amount) for t in current_month_transactions if float(t.amount) > 0)
        total_income = sum(abs(float(t.amount)) for t in current_month_transactions if float(t.amount) < 0)
        net_income = total_income - total_spent
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_metric_card("Monthly Spending", f"${total_spent:,.2f}")
        
        with col2:
            create_metric_card("Monthly Income", f"${total_income:,.2f}")
        
        with col3:
            delta_color = "normal" if net_income >= 0 else "inverse"
            create_metric_card("Net Income", f"${net_income:,.2f}", delta_color=delta_color)
        
        with col4:
            create_metric_card("Transactions", str(len(current_month_transactions)))
        
        st.divider()
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            # Spending by category chart
            if current_month_transactions:
                spending_data = {}
                for t in current_month_transactions:
                    if float(t.amount) > 0:
                        category = t.category or 'Other'
                        spending_data[category] = spending_data.get(category, 0) + float(t.amount)
                
                if spending_data:
                    fig = ChartHelper.create_spending_pie_chart(spending_data, "Monthly Spending by Category")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No spending data available for this month")
            else:
                st.info("No transactions found for this month")
        
        with col2:
            # Monthly trend chart
            if transactions:
                monthly_data = {}
                for t in transactions:
                    if float(t.amount) > 0:
                        month_key = t.transaction_date.strftime('%Y-%m')
                        monthly_data[month_key] = monthly_data.get(month_key, 0) + float(t.amount)
                
                if monthly_data:
                    fig = ChartHelper.create_spending_trend_chart(monthly_data, "Spending Trend (Last 6 Months)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No spending trend data available")
            else:
                st.info("No transaction history available")
        
        st.divider()
        
        # Recent transactions and alerts
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Recent Transactions")
            if transactions:
                recent_df = pd.DataFrame([{
                    'Date': t.transaction_date.strftime('%m/%d/%Y'),
                    'Description': t.description[:40] + '...' if len(t.description) > 40 else t.description,
                    'Category': t.category or 'Other',
                    'Amount': FormatHelper.format_currency(float(t.amount))
                } for t in transactions[:10]])
                
                st.dataframe(recent_df, use_container_width=True, hide_index=True)
            else:
                create_info_box(
                    "No Transactions", 
                    "Upload your bank statements to get started with transaction tracking!",
                    "📄"
                )
        
        with col2:
            st.subheader("Alerts & Notifications")
            
            # Budget alerts
            try:
                alerts = services['ai_advisor'].check_budget_alerts(user_id)
                if alerts:
                    for alert in alerts[:3]:  # Show top 3 alerts
                        if alert['alert_type'] == 'overspent':
                            create_warning_box(
                                f"{alert['category']} Budget",
                                f"Overspent by ${alert['overspent_amount']:,.2f}",
                                "🚨"
                            )
                        else:
                            st.warning(f"⚠️ **{alert['category']}**: ${alert['remaining_budget']:,.2f} remaining")
                else:
                    st.success("✅ All budgets are on track!")
            except Exception as e:
                logger.error(f"Error loading budget alerts: {e}")
                st.error("Error loading budget alerts")
            
            # Goal progress
            if goals:
                st.write("**Goal Progress:**")
                for goal in goals[:3]:  # Show top 3 goals
                    progress = (float(goal.current_amount or 0) / float(goal.target_amount)) * 100
                    st.progress(min(progress / 100, 1.0))
                    st.caption(f"{goal.goal_name}: {progress:.1f}%")
            else:
                create_info_box(
                    "No Goals Set",
                    "Set financial goals to track your progress!",
                    "🎯"
                )
        
    except Exception as e:
        logger.error(f"Error in overview page: {e}")
        st.error(f"Error loading overview: {e}")

def show_transactions_page(user_id: int, services):
    """Transactions page with upload and management"""
    st.header("💳 Transaction Management")
    
    # File upload section
    with st.expander("📄 Upload Bank Statements", expanded=True):
        st.write("Upload your bank statement in CSV or PDF format to automatically categorize transactions.")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'pdf', 'xlsx'],
            help="Supported formats: CSV, PDF, Excel"
        )
        
        if uploaded_file is not None:
            # Validate file
            is_valid, message = services['file_processor'].validate_file(uploaded_file)
            
            if not is_valid:
                st.error(message)
                return
            
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            
            # Process file button
            if st.button("🤖 Process & Categorize Transactions", type="primary"):
                with show_loading_spinner("Processing your file..."):
                    try:
                        transactions = []
                        
                        # Process based on file type
                        if uploaded_file.type == "text/csv":
                            df = services['file_processor'].process_csv_file(uploaded_file)
                            if df is not None:
                                transactions = services['file_processor'].parse_transactions_from_csv(df)
                        
                        elif uploaded_file.type == "application/pdf":
                            text = services['file_processor'].process_pdf_file(uploaded_file)
                            if text:
                                transactions = services['file_processor'].parse_transactions_from_pdf(text)
                        
                        elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
                            df = services['file_processor'].process_excel_file(uploaded_file)
                            if df is not None:
                                transactions = services['file_processor'].parse_transactions_from_csv(df)
                        
                        if transactions:
                            # Validate transactions
                            valid_transactions, errors = services['transaction_parser'].validate_transactions(transactions)
                            
                            if errors:
                                st.warning(f"⚠️ Found {len(errors)} validation errors:")
                                for error in errors[:5]:  # Show first 5 errors
                                    st.write(f"• {error}")
                            
                            if valid_transactions:
                                # Show preview
                                st.write(f"📊 Found {len(valid_transactions)} valid transactions")
                                preview_df = services['file_processor'].preview_transactions(valid_transactions)
                                st.dataframe(preview_df, use_container_width=True)
                                
                                # Process and categorize
                                categorized_transactions = services['transaction_parser'].process_and_categorize(
                                    valid_transactions, user_id
                                )
                                
                                # Save to database
                                if Transaction.create_bulk(categorized_transactions):
                                    st.success(f"✅ Successfully processed {len(categorized_transactions)} transactions!")
                                    st.balloons()
                                    
                                    # Show stats
                                    stats = services['file_processor'].get_file_stats(categorized_transactions)
                                    if stats:
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Total Transactions", stats['total_transactions'])
                                        with col2:
                                            st.metric("Date Range", f"{stats['date_range']['start']} to {stats['date_range']['end']}")
                                        with col3:
                                            st.metric("Total Amount", f"${stats['total_credits']:,.2f}")
                                    
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to save transactions to database")
                            else:
                                st.error("❌ No valid transactions found")
                        else:
                            st.error("❌ No transactions found in the uploaded file")
                    
                    except Exception as e:
                        logger.error(f"Error processing file: {e}")
                        st.error(f"❌ Error processing file: {e}")
    
    st.divider()
    
    # Transaction filters and display
    st.subheader("📋 Your Transactions")
    
    try:
        # Get transactions
        transactions = Transaction.get_by_user(user_id, limit=500)
        
        if not transactions:
            create_info_box(
                "No Transactions Found",
                "Upload your bank statements to start tracking your transactions!",
                "📄"
            )
            return
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            categories = list(set(t.category for t in transactions if t.category))
            selected_category = st.selectbox("Filter by Category", ["All"] + sorted(categories))
        
        with col2:
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now().date() - timedelta(days=30), datetime.now().date()),
                max_value=datetime.now().date()
            )
        
        with col3:
            amount_filter = st.selectbox(
                "Amount Filter",
                ["All", "Income Only", "Expenses Only", "Large Transactions (>$100)"]
            )
        
        # Apply filters
        filtered_transactions = transactions
        
        if selected_category != "All":
            filtered_transactions = [t for t in filtered_transactions if t.category == selected_category]
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_transactions = [
                t for t in filtered_transactions 
                if start_date <= t.transaction_date <= end_date
            ]
        
        if amount_filter == "Income Only":
            filtered_transactions = [t for t in filtered_transactions if float(t.amount) < 0]
        elif amount_filter == "Expenses Only":
            filtered_transactions = [t for t in filtered_transactions if float(t.amount) > 0]
        elif amount_filter == "Large Transactions (>$100)":
            filtered_transactions = [t for t in filtered_transactions if abs(float(t.amount)) > 100]
        
        # Display transactions
        if filtered_transactions:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_transactions = len(filtered_transactions)
            total_expenses = sum(float(t.amount) for t in filtered_transactions if float(t.amount) > 0)
            total_income = sum(abs(float(t.amount)) for t in filtered_transactions if float(t.amount) < 0)
            avg_transaction = sum(abs(float(t.amount)) for t in filtered_transactions) / total_transactions
            
            with col1:
                st.metric("Total Transactions", total_transactions)
            with col2:
                st.metric("Total Expenses", f"${total_expenses:,.2f}")
            with col3:
                st.metric("Total Income", f"${total_income:,.2f}")
            with col4:
                st.metric("Avg Transaction", f"${avg_transaction:,.2f}")
            
            # Transaction table
            df = pd.DataFrame([{
                'Date': t.transaction_date.strftime('%m/%d/%Y'),
                'Description': t.description,
                'Category': t.category or 'Other',
                'Amount': float(t.amount),
                'Confidence': f"{t.confidence_score}%" if t.confidence_score else "N/A"
            } for t in filtered_transactions])
            
            # Format amount column
            df['Amount'] = df['Amount'].apply(lambda x: FormatHelper.format_currency(x))
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Date": st.column_config.TextColumn("Date", width="small"),
                    "Description": st.column_config.TextColumn("Description", width="large"),
                    "Category": st.column_config.TextColumn("Category", width="medium"),
                    "Amount": st.column_config.TextColumn("Amount", width="small"),
                    "Confidence": st.column_config.TextColumn("AI Confidence", width="small")
                }
            )
            
            # Export functionality
            if st.button("📥 Export to CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        else:
            st.info("No transactions match the selected filters.")
    
    except Exception as e:
        logger.error(f"Error in transactions page: {e}")
        st.error(f"Error loading transactions: {e}")

def show_budgets_page(user_id: int, services):
    """Budgets page with creation and management"""
    st.header("💰 Budget Management")
    
    try:
        # Create new budget section
        with st.expander("➕ Create New Budget", expanded=False):
            with st.form("budget_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    category = st.selectbox(
                        "Category",
                        Settings.TRANSACTION_CATEGORIES,
                        help="Select the spending category for this budget"
                    )
                
                with col2:
                    monthly_limit = st.number_input(
                        "Monthly Limit ($)",
                        min_value=0.0,
                        step=10.0,
                        help="Set your monthly spending limit for this category"
                    )
                
                if st.form_submit_button("Create Budget", type="primary"):
                    if monthly_limit > 0:
                        budget = Budget.create(user_id, category, monthly_limit)
                        if budget:
                            st.success(f"✅ Budget created for {category}: ${monthly_limit:,.2f}")
                            st.rerun()
                        else:
                            st.error("❌ Failed to create budget")
                    else:
                        st.error("Please enter a valid budget amount")
        
        st.divider()
        
        # Display existing budgets
        budgets = Budget.get_by_user(user_id)
        
        if not budgets:
            create_info_box(
                "No Budgets Created",
                "Create your first budget to start tracking your spending limits!",
                "💰"
            )
            return
        
        # Get current month spending
        current_month_start, current_month_end = DateHelper.get_current_month_range()
        transactions = Transaction.get_by_user(
            user_id,
            limit=1000,
            start_date=current_month_start,
            end_date=current_month_end
        )
        
        # Calculate spending by category
        category_spending = {}
        for transaction in transactions:
            if float(transaction.amount) > 0:  # Only expenses
                category = transaction.category or 'Other'
                category_spending[category] = category_spending.get(category, 0) + float(transaction.amount)
        
        # Budget overview metrics
        total_budget = sum(float(b.monthly_limit) for b in budgets)
        total_spent = sum(category_spending.get(b.category, 0) for b in budgets)
        budgets_over_limit = sum(1 for b in budgets if category_spending.get(b.category, 0) > float(b.monthly_limit))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Budget", f"${total_budget:,.2f}")
        with col2:
            st.metric("Total Spent", f"${total_spent:,.2f}")
        with col3:
            st.metric("Budgets Over Limit", budgets_over_limit)
        
        st.divider()
        
        # Individual budget cards
        st.subheader("📊 Budget Status")
        
        # Create budget data for chart
        budget_chart_data = []
        
        for budget in budgets:
            spent = category_spending.get(budget.category, 0)
            limit = float(budget.monthly_limit)
            remaining = limit - spent
            progress = min(spent / limit, 1.0) if limit > 0 else 0
            
            budget_chart_data.append({
                'category': budget.category,
                'spent': spent,
                'limit': limit
            })
            
            # Budget card
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(f"💳 {budget.category}")
                    
                    # Progress bar
                    if progress >= 1.0:
                        st.error(f"🚨 Over budget by ${spent - limit:,.2f}")
                        st.progress(1.0)
                    elif progress >= 0.9:
                        st.warning(f"⚠️ {progress:.1%} of budget used")
                        st.progress(progress)
                    else:
                        st.success(f"✅ {progress:.1%} of budget used")
                        st.progress(progress)
                    
                    # Metrics
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    with metric_col1:
                        st.metric("Budget", f"${limit:,.2f}")
                    with metric_col2:
                        st.metric("Spent", f"${spent:,.2f}")
                    with metric_col3:
                        st.metric("Remaining", f"${remaining:,.2f}")
                
                with col2:
                    st.write("")  # Spacing
                    st.write("")  # Spacing
                    
                    # Action buttons
                    if st.button(f"Edit", key=f"edit_{budget.id}"):
                        st.session_state[f'edit_budget_{budget.id}'] = True
                    
                    if st.button(f"Delete", key=f"delete_{budget.id}", type="secondary"):
                        if budget.delete():
                            st.success("Budget deleted")
                            st.rerun()
                        else:
                            st.error("Failed to delete budget")
                
                # Edit budget form
                if st.session_state.get(f'edit_budget_{budget.id}', False):
                    with st.form(f"edit_budget_form_{budget.id}"):
                        new_limit = st.number_input(
                            "New Monthly Limit ($)",
                            value=float(budget.monthly_limit),
                            min_value=0.0,
                            step=10.0
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Update"):
                                updated_budget = Budget.create(user_id, budget.category, new_limit)
                                if updated_budget:
                                    st.success("Budget updated!")
                                    st.session_state[f'edit_budget_{budget.id}'] = False
                                    st.rerun()
                                else:
                                    st.error("Failed to update budget")
                        
                        with col2:
                            if st.form_submit_button("Cancel"):
                                st.session_state[f'edit_budget_{budget.id}'] = False
                                st.rerun()
                
                st.divider()
        
        # Budget overview chart
        if budget_chart_data:
            st.subheader("📈 Budget Overview Chart")
            fig = ChartHelper.create_budget_progress_chart(budget_chart_data, "Budget vs Spending")
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        logger.error(f"Error in budgets page: {e}")
        st.error(f"Error loading budgets: {e}")

def show_goals_page(user_id: int, services):
    """Financial goals page"""
    st.header("🎯 Financial Goals")
    
    try:
        # Create new goal section
        with st.expander("➕ Create New Goal", expanded=False):
            with st.form("goal_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    goal_name = st.text_input("Goal Name", placeholder="e.g., Emergency Fund, Vacation, New Car")
                    target_amount = st.number_input("Target Amount ($)", min_value=0.0, step=100.0)
                
                with col2:
                    target_date = st.date_input("Target Date", min_value=datetime.now().date())
                    current_amount = st.number_input("Current Amount ($)", min_value=0.0, step=10.0)
                
                if st.form_submit_button("Create Goal", type="primary"):
                    if goal_name and target_amount > 0:
                        goal = FinancialGoal.create(user_id, goal_name, target_amount, target_date, current_amount)
                        if goal:
                            st.success(f"✅ Goal created: {goal_name}")
                            st.rerun()
                        else:
                            st.error("❌ Failed to create goal")
                    else:
                        st.error("Please fill in all required fields")
        
        st.divider()
        
        # Display existing goals
        goals = FinancialGoal.get_by_user(user_id)
        
        if not goals:
            create_info_box(
                "No Goals Set",
                "Create your first financial goal to start tracking your progress!",
                "🎯"
            )
            return
        
        # Goals overview metrics
        total_target = sum(float(g.target_amount) for g in goals if g.status == 'active')
        total_current = sum(float(g.current_amount or 0) for g in goals if g.status == 'active')
        completed_goals = len([g for g in goals if g.status == 'completed'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Target", f"${total_target:,.2f}")
        with col2:
            st.metric("Total Saved", f"${total_current:,.2f}")
        with col3:
            st.metric("Completed Goals", completed_goals)
        
        st.divider()
        
        # Individual goal cards
        st.subheader("📋 Your Goals")
        
        goal_chart_data = []
        
        for goal in goals:
            current_amount = float(goal.current_amount or 0)
            target_amount = float(goal.target_amount)
            progress = current_amount / target_amount if target_amount > 0 else 0
            
            goal_chart_data.append({
                'name': goal.goal_name,
                'current': current_amount,
                'target': target_amount
            })
            
            # Goal card
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Goal header with status
                    if goal.status == 'completed':
                        st.subheader(f"✅ {goal.goal_name} (Completed)")
                    else:
                        st.subheader(f"🎯 {goal.goal_name}")
                    
                    # Progress bar
                    if progress >= 1.0:
                        st.success(f"🎉 Goal achieved! {progress:.1%}")
                        st.progress(1.0)
                    elif progress >= 0.75:
                        st.info(f"📈 {progress:.1%} complete - Almost there!")
                        st.progress(progress)
                    else:
                        st.info(f"📊 {progress:.1%} complete")
                        st.progress(progress)
                    
                    # Metrics
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    with metric_col1:
                        st.metric("Target", f"${target_amount:,.2f}")
                    with metric_col2:
                        st.metric("Current", f"${current_amount:,.2f}")
                    with metric_col3:
                        remaining = target_amount - current_amount
                        st.metric("Remaining", f"${remaining:,.2f}")
                    
                    # Target date info
                    if goal.target_date:
                        days_remaining = (goal.target_date - datetime.now().date()).days
                        if days_remaining > 0:
                            st.info(f"📅 {days_remaining} days remaining until target date")
                        else:
                            st.warning(f"⏰ Target date passed {abs(days_remaining)} days ago")
                
                with col2:
                    st.write("")  # Spacing
                    st.write("")  # Spacing
                    
                    # Action buttons
                    if st.button(f"Update Progress", key=f"update_{goal.id}"):
                        st.session_state[f'update_goal_{goal.id}'] = True
                    
                    if goal.status == 'active' and st.button(f"Mark Complete", key=f"complete_{goal.id}"):
                        if goal.update_status('completed'):
                            st.success("Goal marked as completed!")
                            st.rerun()
                    
                    if st.button(f"Delete", key=f"delete_goal_{goal.id}", type="secondary"):
                        if goal.delete():
                            st.success("Goal deleted")
                            st.rerun()
                        else:
                            st.error("Failed to delete goal")
                
                # Update progress form
                if st.session_state.get(f'update_goal_{goal.id}', False):
                    with st.form(f"update_goal_form_{goal.id}"):
                        new_amount = st.number_input(
                            "Current Amount ($)",
                            value=current_amount,
                            min_value=0.0,
                            step=10.0
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Update"):
                                if goal.update_progress(new_amount):
                                    st.success("Progress updated!")
                                    st.session_state[f'update_goal_{goal.id}'] = False
                                    
                                    # Check if goal is achieved
                                    if new_amount >= target_amount:
                                        goal.update_status('completed')
                                        st.balloons()
                                        st.success("🎉 Congratulations! Goal achieved!")
                                    
                                    st.rerun()
                                else:
                                    st.error("Failed to update progress")
                        
                        with col2:
                            if st.form_submit_button("Cancel"):
                                st.session_state[f'update_goal_{goal.id}'] = False
                                st.rerun()
                
                st.divider()
        
        # Goals overview chart
        if goal_chart_data:
            st.subheader("📊 Goals Progress Chart")
            fig = ChartHelper.create_goal_progress_chart(goal_chart_data, "Financial Goals Progress")
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        logger.error(f"Error in goals page: {e}")
        st.error(f"Error loading goals: {e}")

def show_investments_page(user_id: int, services):
    """Investments page with recommendations"""
    st.header("📈 Investment Recommendations")
    
    try:
        # Investment profile form
        st.subheader("📋 Investment Profile")
        
        with st.form("investment_profile"):
            col1, col2 = st.columns(2)
            
            with col1:
                age = st.number_input("Age", min_value=18, max_value=100, value=30)
                risk_tolerance = st.selectbox("Risk Tolerance", Settings.RISK_LEVELS)
                investment_amount = st.number_input("Investment Amount ($)", min_value=100.0, step=100.0, value=1000.0)
            
            with col2:
                time_horizon = st.selectbox("Time Horizon", Settings.TIME_HORIZONS)
                experience = st.selectbox("Investment Experience", ["Beginner", "Intermediate", "Advanced"])
                income = st.number_input("Annual Income ($)", min_value=0.0, step=1000.0, value=50000.0)
            
            goals = st.text_area("Investment Goals", placeholder="e.g., Retirement, House down payment, Emergency fund")
            
            if st.form_submit_button("🤖 Get AI Recommendations", type="primary"):
                user_profile = {
                    'age': age,
                    'risk_tolerance': risk_tolerance,
                    'amount': investment_amount,
                    'time_horizon': time_horizon,
                    'experience': experience,
                    'income': income,
                    'goals': goals
                }
                
                with show_loading_spinner("Generating personalized investment recommendations..."):
                    recommendations = services['investment_service'].get_investment_recommendations(user_profile)
                    
                    if recommendations:
                        st.session_state['investment_recommendations'] = recommendations
                        st.session_state['investment_profile'] = user_profile
                        st.success("✅ Investment recommendations generated!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to generate recommendations. Please try again.")
        
        st.divider()
        
        # Display recommendations
        if 'investment_recommendations' in st.session_state:
            recommendations = st.session_state['investment_recommendations']
            profile = st.session_state['investment_profile']
            
            st.subheader("🎯 Recommended Portfolio")
            
            # Portfolio allocation chart
            if recommendations:
                allocation_data = {rec.get('name', rec.get('symbol', 'Unknown')): rec.get('allocation_percentage', 0) for rec in recommendations}
                fig = ChartHelper.create_spending_pie_chart(allocation_data, "Recommended Portfolio Allocation")
                st.plotly_chart(fig, use_container_width=True)
            
            # Recommended asset allocation
            allocation = services['investment_service'].calculate_investment_allocation(
                profile['amount'], 
                profile['risk_tolerance'], 
                profile['age']
            )
            
            st.subheader("📊 Asset Allocation Strategy")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Recommended Allocation:**")
                st.write(f"• Stocks: {allocation['total_stocks']:.1f}%")
                st.write(f"• Bonds: {allocation['total_bonds']:.1f}%")
                
                st.write("**Stock Breakdown:**")
                for category, percentage in allocation['percentages'].items():
                    if 'stock' in category or 'market' in category:
                        st.write(f"• {category.replace('_', ' ').title()}: {percentage:.1f}%")
            
            with col2:
                st.write("**Dollar Amounts:**")
                for category, amount in allocation['amounts'].items():
                    st.write(f"• {category.replace('_', ' ').title()}: ${amount:,.2f}")
            
            st.divider()
            
            # Individual recommendations
            st.subheader("💡 Individual Recommendations")
            
            for i, rec in enumerate(recommendations):
                with st.expander(f"{rec.get('name', rec.get('symbol', 'Unknown'))} - {rec.get('allocation_percentage', 0)}%"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Symbol:** {rec.get('symbol', 'N/A')}")
                        st.write(f"**Type:** {rec.get('type', 'N/A')}")
                        st.write(f"**Risk Level:** {rec.get('risk_level', 'N/A')}")
                        st.write(f"**Time Horizon:** {rec.get('time_horizon', 'N/A')}")
                        
                        # Real-time price if available
                        if rec.get('current_price'):
                            change_color = "🟢" if rec.get('daily_change', 0) >= 0 else "🔴"
                            st.write(f"**Current Price:** ${rec['current_price']:.2f} {change_color}")
                    
                    with col2:
                        st.write(f"**Allocation:** {rec.get('allocation_percentage', 0)}%")
                        amount = profile['amount'] * (rec.get('allocation_percentage', 0) / 100)
                        st.write(f"**Investment Amount:** ${amount:,.2f}")
                        
                        if rec.get('expected_return'):
                            st.write(f"**Expected Return:** {rec['expected_return']}%")
                    
                    st.write(f"**Reasoning:** {rec.get('reasoning', 'No reasoning provided')}")
        
        st.divider()
        
        # Stock lookup tool
        st.subheader("🔍 Stock Lookup")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            symbol = st.text_input("Enter stock symbol (e.g., AAPL, GOOGL, TSLA)", placeholder="AAPL")
        
        with col2:
            st.write("")  # Spacing
            lookup_button = st.button("Get Stock Data", type="secondary")
        
        if lookup_button and symbol:
            with show_loading_spinner(f"Fetching data for {symbol.upper()}..."):
                stock_data = services['investment_service'].get_stock_data(symbol.upper())
                
                if stock_data:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Symbol", stock_data['symbol'])
                    with col2:
                        st.metric(
                            "Price", 
                            f"${stock_data['price']:.2f}",
                            delta=f"{stock_data['change_percent']:.2f}%"
                        )
                    with col3:
                        st.metric("Volume", f"{stock_data['volume']:,}")
                    with col4:
                        st.metric("High/Low", f"${stock_data['high']:.2f} / ${stock_data['low']:.2f}")
                else:
                    st.error(f"❌ Could not fetch data for {symbol.upper()}")
        
        # Market overview
        st.subheader("📊 Market Overview")
        
        with show_loading_spinner("Loading market data..."):
            market_data = services['investment_service'].get_market_overview()
            
            if market_data:
                cols = st.columns(len(market_data))
                
                for i, (index, data) in enumerate(market_data.items()):
                    with cols[i]:
                        change_color = "normal" if data['change_percent'] >= 0 else "inverse"
                        st.metric(
                            index,
                            f"${data['price']:.2f}",
                            delta=f"{data['change_percent']:.2f}%",
                            delta_color=change_color
                        )
            else:
                st.info("Market data unavailable")
    
    except Exception as e:
        logger.error(f"Error in investments page: {e}")
        st.error(f"Error loading investments: {e}")

def show_insights_page(user_id: int, services):
    """AI insights page"""
    st.header("🤖 AI Financial Insights")
    
    try:
        # Analysis options
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_period = st.selectbox(
                "Analysis Period",
                ["Last 3 months", "Last 6 months", "Last 12 months"],
                index=1
            )
        
        with col2:
            st.write("")  # Spacing
            if st.button("🔄 Refresh Analysis", type="primary"):
                st.rerun()
        
        # Convert period to months
        period_map = {
            "Last 3 months": 3,
            "Last 6 months": 6,
            "Last 12 months": 12
        }
        months = period_map[analysis_period]
        
        # Spending pattern analysis
        st.subheader("📊 Spending Pattern Analysis")
        
        with show_loading_spinner("Analyzing your spending patterns..."):
            analysis = services['ai_advisor'].analyze_spending_patterns(user_id, months)
            
            if 'error' not in analysis:
                # Key insights
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**📈 Financial Summary:**")
                    st.metric("Total Income", f"${analysis['total_income']:,.2f}")
                    st.metric("Total Expenses", f"${analysis['total_expenses']:,.2f}")
                    st.metric("Net Income", f"${analysis['net_income']:,.2f}")
                    st.metric("Avg Monthly Spending", f"${analysis['average_monthly_spending']:,.2f}")
                
                with col2:
                    # Top spending categories
                    if analysis['category_spending']:
                        st.write("**🏷️ Top Spending Categories:**")
                        sorted_categories = sorted(
                            analysis['category_spending'].items(), 
                            key=lambda x: x[1], 
                            reverse=True
                        )
                        for category, amount in sorted_categories[:5]:
                            st.write(f"• {category}: ${amount:,.2f}")
                
                # AI insights
                st.subheader("🧠 AI Insights")
                st.write(analysis['insights'])
                
                # Spending charts
                col1, col2 = st.columns(2)
                
                with col1:
                    if analysis['category_spending']:
                        fig = ChartHelper.create_spending_pie_chart(
                            analysis['category_spending'], 
                            f"Spending by Category ({analysis_period})"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if analysis['monthly_spending']:
                        fig = ChartHelper.create_spending_trend_chart(
                            analysis['monthly_spending'], 
                            f"Monthly Spending Trend ({analysis_period})"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"Analysis failed: {analysis['error']}")
        
        st.divider()
        
        # Financial health score
        st.subheader("💚 Financial Health Score")
        
        with show_loading_spinner("Calculating your financial health score..."):
            health_analysis = services['ai_advisor'].analyze_financial_health(user_id)
            
            if 'error' not in health_analysis:
                # Health score display
                score = health_analysis['health_score']
                status = health_analysis['health_status']
                color = health_analysis['health_color']
                
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    # Create a gauge-like display
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = score,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Financial Health Score"},
                        delta = {'reference': 70},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': color},
                            'steps': [
                                {'range': [0, 40], 'color': "lightgray"},
                                {'range': [40, 70], 'color': "yellow"},
                                {'range': [70, 100], 'color': "lightgreen"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Health metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Savings Rate", f"{health_analysis['savings_rate']:.1f}%")
                
                with col2:
                    st.metric("Expense Ratio", f"{health_analysis['expense_ratio']:.1f}%")
                
                with col3:
                    if health_analysis.get('budget_adherence'):
                        st.metric("Budget Adherence", f"{health_analysis['budget_adherence']:.1f}%")
                    else:
                        st.metric("Budget Adherence", "No budgets set")
                
                # Health recommendations
                if health_analysis['recommendations']:
                    st.write("**💡 Recommendations:**")
                    for rec in health_analysis['recommendations']:
                        st.write(f"• {rec}")
            else:
                st.error(f"Health analysis failed: {health_analysis['error']}")
        
        st.divider()
        
        # Savings recommendations
        st.subheader("💰 Personalized Savings Recommendations")
        
        with show_loading_spinner("Generating savings recommendations..."):
            recommendations = services['ai_advisor'].generate_savings_recommendations(user_id)
            
            if recommendations:
                for i, rec in enumerate(recommendations):
                    with st.expander(f"💡 {rec['category']} - Save ${rec['estimated_savings']:,.2f}/month"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Category:** {rec['category']}")
                            st.write(f"**Difficulty:** {rec['difficulty']}")
                            if rec.get('timeline'):
                                st.write(f"**Timeline:** {rec['timeline']}")
                        
                        with col2:
                            st.write(f"**Monthly Savings:** ${rec['estimated_savings']:,.2f}")
                            if rec.get('impact'):
                                st.write(f"**Impact:** {rec['impact']}")
                        
                        st.write(f"**Action:** {rec['recommendation']}")
            else:
                st.info("No savings recommendations available. Upload more transaction data for better insights.")
        
        st.divider()
        
        # Future spending predictions
        st.subheader("🔮 Spending Predictions")
        
        with show_loading_spinner("Predicting future spending..."):
            predictions = services['ai_advisor'].predict_future_spending(user_id, months_ahead=3)
            
            if 'error' not in predictions:
                st.write(f"**Prediction Period:** {predictions['prediction_period']}")
                st.write(f"**Confidence Level:** {predictions['confidence_level']:.1f}%")
                
                # Total predictions chart
                if predictions['total_predictions']:
                    months_labels = [f"Month {i+1}" for i in range(len(predictions['total_predictions']))]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=months_labels,
                        y=predictions['total_predictions'],
                        name='Predicted Spending',
                        marker_color='lightblue'
                    ))
                    
                    fig.update_layout(
                        title="Predicted Monthly Spending",
                        xaxis_title="Month",
                        yaxis_title="Amount ($)",
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Category predictions
                if predictions['category_predictions']:
                    st.write("**Category Predictions:**")
                    
                    for category, pred_data in predictions['category_predictions'].items():
                        with st.expander(f"{category} - {pred_data['trend'].title()} trend"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric("Current Monthly Avg", f"${pred_data['current_monthly_average']:,.2f}")
                                st.metric("Trend", pred_data['trend'].title())
                            
                            with col2:
                                st.metric("Confidence", f"{pred_data['confidence']:.1f}%")
                                if pred_data['predicted_values']:
                                    st.metric("Next Month Prediction", f"${pred_data['predicted_values'][0]:,.2f}")
            else:
                st.info(f"Prediction unavailable: {predictions['error']}")
        
        st.divider()
        
        # Budget alerts
        st.subheader("🚨 Budget Alerts")
        
        alerts = services['ai_advisor'].check_budget_alerts(user_id)
        
        if alerts:
            for alert in alerts:
                if alert['alert_type'] == 'overspent':
                    st.error(
                        f"🚨 **{alert['category']}** - Overspent by ${alert['overspent_amount']:,.2f} "
                        f"({alert['overspent_percentage']:.1f}% over budget)"
                    )
                elif alert['alert_type'] == 'near_limit':
                    st.warning(
                        f"⚠️ **{alert['category']}** - {alert['usage_percentage']:.1f}% of budget used "
                        f"(${alert['remaining_budget']:,.2f} remaining)"
                    )
                else:
                    st.info(
                        f"ℹ️ **{alert['category']}** - {alert['usage_percentage']:.1f}% of budget used"
                    )
        else:
            st.success("✅ All budgets are on track!")
    
    except Exception as e:
        logger.error(f"Error in insights page: {e}")
        st.error(f"Error loading insights: {e}")

def show_settings_page(user_id: int, services):
    """Settings page"""
    st.header("⚙️ Settings")
    
    # Settings tabs
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Profile", "🔔 Notifications", "🔧 Preferences", "📊 Data"])
    
    with tab1:
        show_profile_settings()
    
    with tab2:
        show_notification_settings(user_id, services)
    
    with tab3:
        show_app_preferences(user_id)
    
    with tab4:
        show_data_management(user_id, services)

def show_notification_settings(user_id: int, services):
    """Notification settings"""
    st.subheader("🔔 Notification Settings")
    
    try:
        from database.models import UserPreferences
        
        preferences = UserPreferences.get_by_user(user_id)
        if not preferences:
            preferences = UserPreferences.create_default(user_id)
        
        if preferences:
            with st.form("notification_settings"):
                st.write("**Email Notifications:**")
                email_notifications = st.checkbox(
                    "Enable email notifications",
                    value=preferences.notification_email
                )
                
                budget_alerts = st.checkbox(
                    "Budget alerts",
                    value=preferences.budget_alerts,
                    disabled=not email_notifications
                )
                
                investment_alerts = st.checkbox(
                    "Investment alerts",
                    value=preferences.investment_alerts,
                    disabled=not email_notifications
                )
                
                st.write("**SMS Notifications:**")
                user = User.get_by_id(user_id)
                sms_enabled = user and user.phone_number
                
                sms_notifications = st.checkbox(
                    "Enable SMS notifications",
                    value=preferences.notification_sms and sms_enabled,
                    disabled=not sms_enabled,
                    help="Add phone number in profile to enable SMS"
                )
                
                if st.form_submit_button("Save Notification Settings"):
                    from auth.user_management import UserManager
                    
                    success, message = UserManager.update_user_preferences(
                        user_id,
                        email_notifications,
                        sms_notifications,
                        budget_alerts,
                        investment_alerts
                    )
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        st.divider()
        
        # Test notifications
        st.subheader("🧪 Test Notifications")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Test Email Notification"):
                with st.spinner("Sending test email..."):
                    results = services['notification_service'].test_notification_settings(user_id)
                    if results.get('email'):
                        st.success("✅ Test email sent successfully!")
                    else:
                        st.error("❌ Failed to send test email")
        
        with col2:
            if st.button("Test SMS Notification"):
                with st.spinner("Sending test SMS..."):
                    results = services['notification_service'].test_notification_settings(user_id)
                    if results.get('sms'):
                        st.success("✅ Test SMS sent successfully!")
                    else:
                        st.error("❌ Failed to send test SMS")
    
    except Exception as e:
        logger.error(f"Error in notification settings: {e}")
        st.error(f"Error loading notification settings: {e}")

def show_app_preferences(user_id: int):
    """Application preferences"""
    st.subheader("🔧 Application Preferences")
    
    # Currency preference
    currency = st.selectbox(
        "Currency",
        ["USD ($)", "EUR (€)", "GBP (£)", "JPY (¥)", "CAD ($)", "AUD ($)"],
        index=0
    )
    
    # Date format
    date_format = st.selectbox(
        "Date Format",
        ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"],
        index=0
    )
    
    # Theme (placeholder - Streamlit handles themes)
    theme = st.selectbox(
        "Theme",
        ["Auto", "Light", "Dark"],
        index=0,
        help="Theme is controlled by Streamlit settings"
    )
    
    # Default analysis period
    default_period = st.selectbox(
        "Default Analysis Period",
        ["Last 3 months", "Last 6 months", "Last 12 months"],
        index=1
    )
    
    # Auto-categorization confidence threshold
    confidence_threshold = st.slider(
        "AI Categorization Confidence Threshold",
        min_value=50,
        max_value=100,
        value=80,
        help="Transactions with confidence below this threshold will be flagged for review"
    )
    
    if st.button("Save Preferences"):
        # Save preferences to session state (in a real app, save to database)
        st.session_state.update({
            'currency': currency,
            'date_format': date_format,
            'theme': theme,
            'default_period': default_period,
            'confidence_threshold': confidence_threshold
        })
        st.success("✅ Preferences saved!")

def show_data_management(user_id: int, services):
    """Data management and export"""
    st.subheader("📊 Data Management")
    
    try:
        # Data export
        st.write("**📥 Export Data:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export Transactions"):
                transactions = Transaction.get_by_user(user_id, limit=10000)
                if transactions:
                    df = pd.DataFrame([{
                        'Date': t.transaction_date,
                        'Description': t.description,
                        'Category': t.category,
                        'Amount': float(t.amount),
                        'Account': t.account_type,
                        'Confidence': t.confidence_score
                    } for t in transactions])
                    
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Transactions CSV",
                        data=csv,
                        file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No transactions to export")
        
        with col2:
            if st.button("Export Budgets"):
                budgets = Budget.get_by_user(user_id)
                if budgets:
                    df = pd.DataFrame([{
                        'Category': b.category,
                        'Monthly_Limit': float(b.monthly_limit),
                        'Current_Spent': float(b.current_spent or 0),
                        'Created_Date': b.created_at
                    } for b in budgets])
                    
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Budgets CSV",
                        data=csv,
                        file_name=f"budgets_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No budgets to export")
        
        with col3:
            if st.button("Export Goals"):
                goals = FinancialGoal.get_by_user(user_id)
                if goals:
                    df = pd.DataFrame([{
                        'Goal_Name': g.goal_name,
                        'Target_Amount': float(g.target_amount),
                        'Current_Amount': float(g.current_amount or 0),
                        'Target_Date': g.target_date,
                        'Status': g.status,
                        'Created_Date': g.created_at
                    } for g in goals])
                    
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Goals CSV",
                        data=csv,
                        file_name=f"goals_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No goals to export")
        
        st.divider()
        
        # Data statistics
        st.write("**📈 Data Statistics:**")
        
        transactions = Transaction.get_by_user(user_id, limit=10000)
        budgets = Budget.get_by_user(user_id)
        goals = FinancialGoal.get_by_user(user_id)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transactions", len(transactions))
        
        with col2:
            st.metric("Active Budgets", len(budgets))
        
        with col3:
            st.metric("Financial Goals", len(goals))
        
        with col4:
            if transactions:
                date_range = max(t.transaction_date for t in transactions) - min(t.transaction_date for t in transactions)
                st.metric("Data Span", f"{date_range.days} days")
            else:
                st.metric("Data Span", "0 days")
        
        st.divider()
        
        # Data cleanup
        st.write("**🧹 Data Cleanup:**")
        
        st.warning("⚠️ These actions cannot be undone. Please export your data before proceeding.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Delete All Transactions", type="secondary"):
                st.session_state['confirm_delete_transactions'] = True
        
        with col2:
            if st.button("🗑️ Delete All Data", type="secondary"):
                st.session_state['confirm_delete_all'] = True
        
        # Confirmation dialogs
        if st.session_state.get('confirm_delete_transactions', False):
            st.error("⚠️ Are you sure you want to delete ALL transactions?")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Yes, Delete All Transactions", type="primary"):
                    # Delete all transactions for user
                    from database.connection import get_db_instance
                    db = get_db_instance()
                    success = db.execute_update("DELETE FROM transactions WHERE user_id = %s", (user_id,))
                    
                    if success:
                        st.success("All transactions deleted")
                        st.session_state['confirm_delete_transactions'] = False
                        st.rerun()
                    else:
                        st.error("Failed to delete transactions")
            
            with col2:
                if st.button("Cancel"):
                    st.session_state['confirm_delete_transactions'] = False
                    st.rerun()
        
        if st.session_state.get('confirm_delete_all', False):
            st.error("⚠️ Are you sure you want to delete ALL your data? This includes transactions, budgets, and goals.")
            
            password_confirm = st.text_input("Enter your password to confirm:", type="password")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Yes, Delete Everything", type="primary"):
                    if password_confirm:
                        user = User.get_by_id(user_id)
                        if user and AuthenticationManager.verify_password(password_confirm, user.password_hash):
                            # Delete all user data
                            from database.connection import get_db_instance
                            db = get_db_instance()
                            
                            # Delete in order due to foreign key constraints
                            db.execute_update("DELETE FROM investment_recommendations WHERE user_id = %s", (user_id,))
                            db.execute_update("DELETE FROM financial_goals WHERE user_id = %s", (user_id,))
                            db.execute_update("DELETE FROM budgets WHERE user_id = %s", (user_id,))
                            db.execute_update("DELETE FROM transactions WHERE user_id = %s", (user_id,))
                            db.execute_update("DELETE FROM user_preferences WHERE user_id = %s", (user_id,))
                            
                            st.success("All data deleted successfully")
                            st.session_state['confirm_delete_all'] = False
                            st.rerun()
                        else:
                            st.error("Incorrect password")
                    else:
                        st.error("Please enter your password")
            
            with col2:
                if st.button("Cancel"):
                    st.session_state['confirm_delete_all'] = False
                    st.rerun()
    
    except Exception as e:
        logger.error(f"Error in data management: {e}")
        st.error(f"Error in data management: {e}")

if __name__ == "__main__":
    main()


