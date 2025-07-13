"""Main Streamlit application"""
import streamlit as st

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="AI Personal Finance Advisor",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    create_metric_card, create_info_box, create_warning_box, 
    create_footer
)
from services.transaction_parser import TransactionParser
from services.ai_advisor import AIFinancialAdvisor
from services.investment_service import InvestmentService
from services.notification_service import NotificationService
from database.models import Transaction, Budget, FinancialGoal, User
from config.settings import Settings

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
    create_footer()

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
    create_footer()

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
    create_footer()

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
    create_footer()

def show_investments_page(user_id: int, services):
    """Investments page with recommendations"""
    st.header("📈 Investment Recommendations")
    
    try:
        # Initialize session state keys BEFORE any widgets
        if 'investment_recommendations' not in st.session_state:
            st.session_state.investment_recommendations = None
        
        if 'investment_profile' not in st.session_state:
            st.session_state.investment_profile = None
        
        # Investment profile form
        st.subheader("📋 Investment Profile")
        
        with st.form("investment_profile_form", clear_on_submit=False):
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
            
            submitted = st.form_submit_button("🤖 Get AI Recommendations", type="primary")
            
            if submitted:
                user_profile = {
                    'age': age,
                    'risk_tolerance': risk_tolerance,
                    'amount': investment_amount,
                    'time_horizon': time_horizon,
                    'experience': experience,
                    'income': income,
                    'goals': goals
                }
                
                with st.spinner("Generating personalized investment recommendations..."):
                    recommendations = services['investment_service'].get_investment_recommendations(user_profile)
                    
                    if recommendations:
                        # Use dictionary-style assignment to avoid widget conflicts
                        st.session_state['investment_recommendations'] = recommendations
                        st.session_state['investment_profile'] = user_profile
                        st.success("✅ Investment recommendations generated!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to generate recommendations. Please try again.")
        
        st.divider()
        
        # Display recommendations if they exist
        if st.session_state.get('investment_recommendations') and st.session_state.get('investment_profile'):
            recommendations = st.session_state['investment_recommendations']
            profile = st.session_state['investment_profile']
            
            st.subheader("🎯 Recommended Portfolio")
            
            # Portfolio allocation chart
            if recommendations:
                allocation_data = {
                    rec.get('name', rec.get('symbol', 'Unknown')): rec.get('allocation_percentage', 0) 
                    for rec in recommendations
                }
                fig = ChartHelper.create_spending_pie_chart(allocation_data, "Recommended Portfolio Allocation")
                st.plotly_chart(fig, use_container_width=True)
            
            # Display individual recommendations
            st.subheader("📊 Investment Recommendations")
            
            for i, rec in enumerate(recommendations):
                with st.expander(f"💼 {rec.get('name', 'Investment')} ({rec.get('symbol', 'N/A')})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Type:** {rec.get('type', 'N/A')}")
                        st.write(f"**Allocation:** {rec.get('allocation_percentage', 0):.1f}%")
                        st.write(f"**Risk Level:** {rec.get('risk_level', 'N/A')}")
                    
                    with col2:
                        if rec.get('current_price'):
                            st.write(f"**Current Price:** ${rec['current_price']:.2f}")
                        if rec.get('expected_return'):
                            st.write(f"**Expected Return:** {rec['expected_return']:.1f}%")
                        if rec.get('time_horizon'):
                            st.write(f"**Time Horizon:** {rec['time_horizon']}")
                    
                    if rec.get('reasoning'):
                        st.write(f"**Reasoning:** {rec['reasoning']}")
            
            # Asset allocation strategy
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
            
            with col2:
                st.write("**Dollar Amounts:**")
                for category, amount in allocation['amounts'].items():
                    st.write(f"• {category.replace('_', ' ').title()}: ${amount:,.0f}")
        
        else:
            st.info("📝 Fill out the investment profile form above to get personalized AI-powered investment recommendations.")
    
    except Exception as e:
        logger.error(f"Error in investments page: {e}")
        st.error(f"Error loading investments: {e}")
    create_footer()

def show_insights_page(user_id: int, services):
    """AI Insights page with comprehensive financial analysis"""
    st.header("🤖 AI-Powered Financial Insights")
    
    try:
        # Check if user has sufficient data
        transactions = Transaction.get_by_user(user_id, limit=100)
        
        if len(transactions) < 5:
            create_info_box(
                "Insufficient Data",
                "Upload more transactions to get AI-powered insights. You need at least 5 transactions for meaningful analysis.",
                "📊"
            )
            return
        
        # Create tabs for different insights
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Spending Analysis", 
            "💡 AI Recommendations", 
            "🔮 Future Predictions", 
            "❤️ Financial Health"
        ])
        
        with tab1:
            show_spending_analysis(user_id, services)
        
        with tab2:
            show_ai_recommendations(user_id, services)
        
        with tab3:
            show_future_predictions(user_id, services)
        
        with tab4:
            show_financial_health_analysis(user_id, services)
            
    except Exception as e:
        logger.error(f"Error in AI insights page: {e}")
        st.error(f"Error loading AI insights: {e}")
    create_footer()

def show_spending_analysis(user_id: int, services):
    """Display AI-powered spending analysis"""
    st.subheader("📊 Spending Pattern Analysis")
    
    with st.spinner("🤖 AI is analyzing your spending patterns..."):
        analysis = services['ai_advisor'].analyze_spending_patterns(user_id, months=3)
        
        if 'error' in analysis:
            st.error(f"Analysis failed: {analysis['error']}")
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Expenses", 
                f"${analysis['total_expenses']:,.2f}",
                "Last 3 months"
            )
        
        with col2:
            st.metric(
                "Total Income", 
                f"${analysis['total_income']:,.2f}",
                f"${analysis['net_income']:,.2f} net"
            )
        
        with col3:
            st.metric(
                "Transactions", 
                analysis['total_transactions'],
                f"Avg ${analysis['average_monthly_spending']:,.0f}/month"
            )
        
        with col4:
            savings_rate = (analysis['net_income'] / analysis['total_income'] * 100) if analysis['total_income'] > 0 else 0
            st.metric(
                "Savings Rate", 
                f"{savings_rate:.1f}%",
                "Of total income"
            )
        
        st.divider()
        
        # AI Insights
        st.subheader("🧠 AI Analysis")
        if analysis.get('insights'):
            st.markdown(analysis['insights'])
        else:
            st.info("No specific insights available for this period.")
        
        # Category breakdown chart
        if analysis.get('category_spending'):
            st.subheader("💰 Spending by Category")
            fig = ChartHelper.create_spending_pie_chart(
                analysis['category_spending'], 
                "Spending Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

def show_ai_recommendations(user_id: int, services):
    """Display AI-generated savings recommendations"""
    st.subheader("💡 Personalized Savings Recommendations")
    
    with st.spinner("🤖 Generating personalized recommendations..."):
        recommendations = services['ai_advisor'].generate_savings_recommendations(user_id)
        
        if not recommendations:
            st.info("Unable to generate recommendations. Upload more transactions for better insights.")
            return
        
        st.success(f"✨ Found {len(recommendations)} personalized recommendations for you!")
        
        for i, rec in enumerate(recommendations, 1):
            with st.expander(f"💰 Recommendation {i}: {rec.get('category', 'General')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Action:** {rec.get('recommendation', 'No recommendation available')}")
                    st.write(f"**Impact:** {rec.get('impact', 'Positive impact on finances')}")
                
                with col2:
                    st.metric("Potential Savings", f"${rec.get('estimated_savings', 0):.2f}/month")
                    st.write(f"**Difficulty:** {rec.get('difficulty', 'Medium')}")
                    st.write(f"**Timeline:** {rec.get('timeline', '1 month')}")

def show_future_predictions(user_id: int, services):
    """Display AI-powered spending predictions"""
    st.subheader("🔮 Future Spending Predictions")
    
    # Prediction controls
    col1, col2 = st.columns(2)
    with col1:
        months_ahead = st.selectbox("Prediction Period", [1, 2, 3, 6], index=2)
    with col2:
        if st.button("🔄 Update Predictions"):
            st.rerun()
    
    with st.spinner("🤖 Predicting your future spending..."):
        predictions = services['ai_advisor'].predict_future_spending(user_id, months_ahead)
        
        if 'error' in predictions:
            st.error(f"Prediction failed: {predictions['error']}")
            return
        
        # Overall prediction summary
        if predictions.get('total_predictions'):
            st.subheader("📈 Predicted Monthly Spending")
            
            months = [f"Month {i+1}" for i in range(len(predictions['total_predictions']))]
            amounts = predictions['total_predictions']
            
            # Create prediction chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=months,
                y=amounts,
                name='Predicted Spending',
                marker_color='lightblue'
            ))
            
            fig.update_layout(
                title="Predicted Spending by Month",
                xaxis_title="Month",
                yaxis_title="Amount ($)",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Confidence level
            confidence = predictions.get('confidence_level', 0)
            if confidence > 70:
                st.success(f"🎯 High confidence prediction ({confidence:.0f}%)")
            elif confidence > 50:
                st.warning(f"⚠️ Moderate confidence prediction ({confidence:.0f}%)")
            else:
                st.info(f"📊 Low confidence prediction ({confidence:.0f}%) - More data needed")

def show_financial_health_analysis(user_id: int, services):
    """Display financial health analysis"""
    st.subheader("❤️ Financial Health Score")
    
    with st.spinner("🤖 Analyzing your financial health..."):
        health_analysis = services['ai_advisor'].analyze_financial_health(user_id)
        
        if 'error' in health_analysis:
            st.error(f"Health analysis failed: {health_analysis['error']}")
            return
        
        # Health score display
        score = health_analysis.get('health_score', 0)
        status = health_analysis.get('health_status', 'Unknown')
        color = health_analysis.get('health_color', 'gray')
        
        # Large health score display
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; border-radius: 10px; background-color: {color}20;">
                <h1 style="color: {color}; margin: 0;">{score}/100</h1>
                <h3 style="color: {color}; margin: 0;">{status}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Detailed metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            savings_rate = health_analysis.get('savings_rate', 0)
            st.metric("Savings Rate", f"{savings_rate:.1f}%", "Of income")
        
        with col2:
            expense_ratio = health_analysis.get('expense_ratio', 0)
            st.metric("Expense Ratio", f"{expense_ratio:.1f}%", "Of income")
        
        with col3:
            budget_adherence = health_analysis.get('budget_adherence')
            if budget_adherence is not None:
                st.metric("Budget Adherence", f"{budget_adherence:.1f}%", "On track")
            else:
                st.metric("Budget Adherence", "N/A", "No budgets set")
        
        # Health recommendations
        recommendations = health_analysis.get('recommendations', [])
        if recommendations:
            st.subheader("💊 Health Improvement Recommendations")
            for rec in recommendations:
                st.write(f"• {rec}")
        
        # Budget alerts
        st.subheader("🚨 Current Alerts")
        alerts = services['ai_advisor'].check_budget_alerts(user_id)
        
        if alerts:
            for alert in alerts:
                if alert['alert_type'] == 'overspent':
                    st.error(f"🚨 **{alert['category']}**: Overspent by ${alert['overspent_amount']:.2f}")
                elif alert['alert_type'] == 'near_limit':
                    st.warning(f"⚠️ **{alert['category']}**: {alert['usage_percentage']:.1f}% of budget used")
                else:
                    st.info(f"📊 **{alert['category']}**: {alert['usage_percentage']:.1f}% of budget used")
        else:
            st.success("✅ All budgets are on track!")

def show_settings_page(user_id: int, services):
    """Settings page with profile and preferences"""
    st.header("⚙️ Settings & Preferences")
    
    try:
        # User profile settings
        show_profile_settings()
        
        st.divider()
        
        # App preferences
        st.subheader("🔧 Application Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Data Management:**")
            if st.button("📥 Export All Data"):
                # Export functionality
                transactions = Transaction.get_by_user(user_id, limit=1000)
                budgets = Budget.get_by_user(user_id)
                goals = FinancialGoal.get_by_user(user_id)
                
                # Create export data
                export_data = {
                    'transactions': len(transactions),
                    'budgets': len(budgets),
                    'goals': len(goals),
                    'export_date': datetime.now().isoformat()
                }
                
                st.json(export_data)
                st.success("Data export completed!")
            
            if st.button("🗑️ Clear All Data", type="secondary"):
                st.warning("This action cannot be undone!")
        
        with col2:
            st.write("**Notification Test:**")
            if st.button("📧 Test Email"):
                result = services['notification_service'].test_notification_settings(user_id)
                if result.get('email'):
                    st.success("✅ Email test successful!")
                else:
                    st.error("❌ Email test failed")
            
            if st.button("📱 Test SMS"):
                result = services['notification_service'].test_notification_settings(user_id)
                if result.get('sms'):
                    st.success("✅ SMS test successful!")
                else:
                    st.error("❌ SMS test failed")
        
        st.divider()
        
        # App information
        st.subheader("ℹ️ Application Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**App Name:** {Settings.APP_NAME}")
            st.write(f"**Version:** {Settings.APP_VERSION}")
            st.write(f"**User ID:** {user_id}")
        
        with col2:
            config_status = Settings.get_config_status()
            st.write("**Service Status:**")
            for service, status in config_status.items():
                st.write(f"• {service}: {status}")
    
    except Exception as e:
        logger.error(f"Error in settings page: {e}")
        st.error(f"Error loading settings: {e}")
    create_footer()
    
if __name__ == "__main__":
    main()
