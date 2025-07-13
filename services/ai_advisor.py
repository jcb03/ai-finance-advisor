"""ai_advisor.py - AI-powered insights and recommendations"""

import streamlit as st
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Optional, Any
import pandas as pd
from datetime import datetime, timedelta, date
from database.models import Transaction, Budget
from config.settings import Settings
import json
import logging

logger = logging.getLogger(__name__)

class AIFinancialAdvisor:
    """AI-powered financial advisor for insights and recommendations"""
    
    def __init__(self):
        self.client = OpenAI(api_key=Settings.openai_api_key())
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            api_key=Settings.openai_api_key()  # ✅ Fixed: Use method instead of attribute
        )
    
    def analyze_spending_patterns(self, user_id: int, months: int = 3) -> Dict[str, Any]:
        """Analyze user's spending patterns over specified months"""
        try:
            # Get date range
            end_date = date.today()
            start_date = end_date - timedelta(days=months * 30)
            
            # Get transactions
            transactions = Transaction.get_by_user(
                user_id, 
                limit=1000, 
                start_date=start_date, 
                end_date=end_date
            )
            
            if not transactions:
                return {"error": "No transactions found for analysis"}
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame([{
                'description': t.description,
                'amount': float(t.amount),
                'category': t.category or 'Other',
                'date': t.transaction_date
            } for t in transactions])
            
            # Separate income and expenses
            expenses_df = df[df['amount'] > 0]
            income_df = df[df['amount'] < 0]
            
            # Calculate spending by category
            category_spending = expenses_df.groupby('category')['amount'].sum().to_dict()
            
            # Calculate monthly trends
            df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
            monthly_spending = expenses_df.groupby('month')['amount'].sum().to_dict()
            monthly_spending = {str(k): float(v) for k, v in monthly_spending.items()}
            
            # Calculate weekly trends
            df['week'] = pd.to_datetime(df['date']).dt.to_period('W')
            weekly_spending = expenses_df.groupby('week')['amount'].sum().to_dict()
            weekly_spending = {str(k): float(v) for k, v in weekly_spending.items()}
            
            # Calculate income vs expenses
            total_income = abs(income_df['amount'].sum()) if not income_df.empty else 0
            total_expenses = expenses_df['amount'].sum() if not expenses_df.empty else 0
            
            # Generate AI insights
            insights = self._generate_spending_insights(
                category_spending, 
                monthly_spending, 
                weekly_spending,
                total_income,
                total_expenses
            )
            
            return {
                'category_spending': category_spending,
                'monthly_spending': monthly_spending,
                'weekly_spending': weekly_spending,
                'total_income': total_income,
                'total_expenses': total_expenses,
                'net_income': total_income - total_expenses,
                'insights': insights,
                'total_transactions': len(transactions),
                'analysis_period': f"{start_date} to {end_date}",
                'average_monthly_spending': total_expenses / months if months > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing spending patterns: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _generate_spending_insights(self, category_spending: Dict[str, float], 
                                  monthly_spending: Dict[str, float],
                                  weekly_spending: Dict[str, float],
                                  total_income: float,
                                  total_expenses: float) -> str:
        """Generate AI-powered spending insights"""
        prompt = f"""
        Analyze the following financial data and provide personalized insights:
        
        Category Spending: {category_spending}
        Monthly Spending Trend: {monthly_spending}
        Weekly Spending Trend: {weekly_spending}
        Total Income: ${total_income:,.2f}
        Total Expenses: ${total_expenses:,.2f}
        Net Income: ${total_income - total_expenses:,.2f}
        
        Provide insights on:
        1. Spending patterns and trends (increasing/decreasing)
        2. Top spending categories and their analysis
        3. Income vs expenses ratio
        4. Areas where the user might be overspending
        5. Recommendations for budget optimization
        6. Potential savings opportunities
        7. Financial health assessment
        
        Keep the response concise, actionable, and positive. Use bullet points for clarity.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a personal financial advisor providing insights based on spending data. Be encouraging and provide actionable advice."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return f"Unable to generate insights at this time. Error: {str(e)}"
    
    def check_budget_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """Check for budget overspending alerts"""
        try:
            budgets = Budget.get_by_user(user_id)
            alerts = []
            
            if not budgets:
                return alerts
            
            # Get current month transactions
            current_month = datetime.now().replace(day=1).date()
            end_of_month = (current_month.replace(month=current_month.month % 12 + 1) - timedelta(days=1)) if current_month.month < 12 else current_month.replace(year=current_month.year + 1, month=1) - timedelta(days=1)
            
            transactions = Transaction.get_by_user(
                user_id, 
                limit=1000, 
                start_date=current_month,
                end_date=end_of_month
            )
            
            # Calculate spending by category for current month
            category_spending = {}
            for transaction in transactions:
                if transaction.amount > 0:  # Only expenses
                    category = transaction.category or 'Other'
                    category_spending[category] = category_spending.get(category, 0) + float(transaction.amount)
            
            # Check against budgets
            for budget in budgets:
                spent = category_spending.get(budget.category, 0)
                budget_limit = float(budget.monthly_limit)
                
                if spent > budget_limit:
                    alerts.append({
                        'category': budget.category,
                        'budget_limit': budget_limit,
                        'amount_spent': spent,
                        'overspent_amount': spent - budget_limit,
                        'overspent_percentage': ((spent - budget_limit) / budget_limit) * 100,
                        'alert_type': 'overspent',
                        'severity': 'high'
                    })
                elif spent > budget_limit * 0.9:  # 90% threshold
                    alerts.append({
                        'category': budget.category,
                        'budget_limit': budget_limit,
                        'amount_spent': spent,
                        'remaining_budget': budget_limit - spent,
                        'usage_percentage': (spent / budget_limit) * 100,
                        'alert_type': 'near_limit',
                        'severity': 'medium'
                    })
                elif spent > budget_limit * 0.75:  # 75% threshold
                    alerts.append({
                        'category': budget.category,
                        'budget_limit': budget_limit,
                        'amount_spent': spent,
                        'remaining_budget': budget_limit - spent,
                        'usage_percentage': (spent / budget_limit) * 100,
                        'alert_type': 'warning',
                        'severity': 'low'
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking budget alerts: {e}")
            return []
    
    def generate_savings_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate personalized savings recommendations"""
        try:
            analysis = self.analyze_spending_patterns(user_id)
            
            if 'error' in analysis:
                return []
            
            category_spending = analysis['category_spending']
            total_expenses = analysis['total_expenses']
            total_income = analysis['total_income']
            
            prompt = f"""
            Based on the following spending data, generate 3-5 specific, actionable savings recommendations:
            
            Category Spending: {category_spending}
            Total Monthly Expenses: ${total_expenses:,.2f}
            Total Monthly Income: ${total_income:,.2f}
            
            For each recommendation, provide:
            1. Category to focus on
            2. Specific action to take
            3. Estimated monthly savings amount
            4. Difficulty level (Easy/Medium/Hard)
            5. Implementation timeline (Immediate/1 week/1 month)
            
            Focus on realistic, achievable recommendations that won't drastically impact quality of life.
            
            Return as JSON array with format:
            [
                {{
                    "category": "category_name",
                    "recommendation": "specific action to take",
                    "estimated_savings": 50.00,
                    "difficulty": "Easy",
                    "timeline": "1 week",
                    "impact": "Low impact on lifestyle"
                }}
            ]
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial advisor providing practical savings recommendations. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            recommendations = json.loads(response.choices[0].message.content)
            
            # Validate recommendations
            validated_recommendations = []
            for rec in recommendations:
                if all(key in rec for key in ['category', 'recommendation', 'estimated_savings', 'difficulty']):
                    validated_recommendations.append(rec)
            
            return validated_recommendations
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in savings recommendations: {e}")
            return []
        except Exception as e:
            logger.error(f"Error generating savings recommendations: {e}")
            return []
    
    def predict_future_spending(self, user_id: int, months_ahead: int = 3) -> Dict[str, Any]:
        """Predict future spending based on historical patterns"""
        try:
            # Get historical data (last 6 months)
            end_date = date.today()
            start_date = end_date - timedelta(days=180)
            
            transactions = Transaction.get_by_user(
                user_id,
                limit=2000,
                start_date=start_date,
                end_date=end_date
            )
            
            if not transactions:
                return {"error": "Insufficient data for prediction"}
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'amount': float(t.amount),
                'category': t.category or 'Other',
                'date': t.transaction_date
            } for t in transactions if t.amount > 0])  # Only expenses
            
            if df.empty:
                return {"error": "No expense data found"}
            
            # Group by month and category
            df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
            monthly_category_spending = df.groupby(['month', 'category'])['amount'].sum().unstack(fill_value=0)
            
            # Calculate trends and predictions
            predictions = {}
            
            for category in monthly_category_spending.columns:
                values = monthly_category_spending[category].values
                
                # Simple linear trend calculation
                if len(values) >= 3:
                    # Calculate average growth rate
                    growth_rates = []
                    for i in range(1, len(values)):
                        if values[i-1] > 0:
                            growth_rate = (values[i] - values[i-1]) / values[i-1]
                            growth_rates.append(growth_rate)
                    
                    avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0
                    current_value = values[-1]
                    
                    # Predict future values
                    future_values = []
                    for month in range(1, months_ahead + 1):
                        predicted_value = current_value * (1 + avg_growth_rate) ** month
                        future_values.append(max(0, predicted_value))  # Ensure non-negative
                    
                    predictions[category] = {
                        'current_monthly_average': float(current_value),
                        'predicted_values': future_values,
                        'trend': 'increasing' if avg_growth_rate > 0.05 else 'decreasing' if avg_growth_rate < -0.05 else 'stable',
                        'confidence': min(100, max(50, 100 - abs(avg_growth_rate) * 100))
                    }
            
            # Calculate total predictions
            total_predictions = []
            for month in range(months_ahead):
                month_total = sum(pred['predicted_values'][month] for pred in predictions.values())
                total_predictions.append(month_total)
            
            return {
                'category_predictions': predictions,
                'total_predictions': total_predictions,
                'prediction_period': f"Next {months_ahead} months",
                'confidence_level': sum(pred['confidence'] for pred in predictions.values()) / len(predictions) if predictions else 0
            }
            
        except Exception as e:
            logger.error(f"Error predicting future spending: {e}")
            return {"error": f"Prediction failed: {str(e)}"}
    
    def analyze_financial_health(self, user_id: int) -> Dict[str, Any]:
        """Analyze overall financial health"""
        try:
            analysis = self.analyze_spending_patterns(user_id, months=6)
            
            if 'error' in analysis:
                return analysis
            
            total_income = analysis['total_income']
            total_expenses = analysis['total_expenses']
            net_income = analysis['net_income']
            
            # Calculate financial health metrics
            savings_rate = (net_income / total_income * 100) if total_income > 0 else 0
            expense_ratio = (total_expenses / total_income * 100) if total_income > 0 else 0
            
            # Determine financial health score (0-100)
            health_score = 0
            
            # Savings rate component (40% of score)
            if savings_rate >= 20:
                health_score += 40
            elif savings_rate >= 10:
                health_score += 30
            elif savings_rate >= 5:
                health_score += 20
            elif savings_rate > 0:
                health_score += 10
            
            # Expense ratio component (30% of score)
            if expense_ratio <= 70:
                health_score += 30
            elif expense_ratio <= 80:
                health_score += 20
            elif expense_ratio <= 90:
                health_score += 10
            
            # Budget adherence component (30% of score)
            budget_alerts = self.check_budget_alerts(user_id)
            overspent_budgets = len([alert for alert in budget_alerts if alert['alert_type'] == 'overspent'])
            total_budgets = len(Budget.get_by_user(user_id))
            
            if total_budgets > 0:
                budget_adherence = ((total_budgets - overspent_budgets) / total_budgets) * 100
                health_score += (budget_adherence / 100) * 30
            else:
                health_score += 15  # Neutral score if no budgets set
            
            # Determine health status
            if health_score >= 80:
                health_status = "Excellent"
                health_color = "green"
            elif health_score >= 60:
                health_status = "Good"
                health_color = "blue"
            elif health_score >= 40:
                health_status = "Fair"
                health_color = "orange"
            else:
                health_status = "Needs Improvement"
                health_color = "red"
            
            return {
                'health_score': round(health_score, 1),
                'health_status': health_status,
                'health_color': health_color,
                'savings_rate': round(savings_rate, 1),
                'expense_ratio': round(expense_ratio, 1),
                'net_income': net_income,
                'budget_adherence': round(budget_adherence, 1) if total_budgets > 0 else None,
                'recommendations': self._generate_health_recommendations(health_score, savings_rate, expense_ratio)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing financial health: {e}")
            return {"error": f"Health analysis failed: {str(e)}"}
    
    def _generate_health_recommendations(self, health_score: float, savings_rate: float, expense_ratio: float) -> List[str]:
        """Generate recommendations based on financial health"""
        recommendations = []
        
        if health_score < 40:
            recommendations.append("🚨 Your financial health needs immediate attention. Consider creating a strict budget and reducing non-essential expenses.")
        
        if savings_rate < 10:
            recommendations.append("💰 Try to increase your savings rate to at least 10% of your income. Start with small amounts and gradually increase.")
        
        if expense_ratio > 90:
            recommendations.append("📉 Your expenses are very high relative to income. Look for areas to cut costs immediately.")
        
        if savings_rate < 5:
            recommendations.append("🎯 Set up automatic transfers to a savings account to build the habit of saving.")
        
        if health_score >= 60:
            recommendations.append("👍 You're doing well! Consider investing your savings for long-term growth.")
        
        if health_score >= 80:
            recommendations.append("🌟 Excellent financial health! Consider advanced investment strategies and long-term financial planning.")
        
        return recommendations
