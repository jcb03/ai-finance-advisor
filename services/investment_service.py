"""investment_service.py - Investment recommendations"""

"""Investment recommendations"""

import streamlit as st
import requests
from openai import OpenAI
from typing import Dict, List, Optional, Any
import json
from datetime import datetime, date
import logging
from config.settings import Settings

logger = logging.getLogger(__name__)

class InvestmentService:
    """Handles investment recommendations and market data"""
    
    def __init__(self):
        self.client = OpenAI(api_key=Settings.OPENAI_API_KEY)
        self.alpha_vantage_key = Settings.ALPHA_VANTAGE_API_KEY
        
        # Investment categories
        self.investment_types = {
            'stocks': 'Individual Stocks',
            'etfs': 'Exchange-Traded Funds',
            'bonds': 'Bonds',
            'mutual_funds': 'Mutual Funds',
            'reits': 'Real Estate Investment Trusts',
            'commodities': 'Commodities',
            'crypto': 'Cryptocurrency'
        }
    
    def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch stock data from Alpha Vantage"""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return None
        
        try:
            # Get daily time series
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                latest_date = max(time_series.keys())
                latest_data = time_series[latest_date]
                
                # Get previous day for change calculation
                dates = sorted(time_series.keys(), reverse=True)
                prev_date = dates[1] if len(dates) > 1 else latest_date
                prev_data = time_series[prev_date]
                
                current_price = float(latest_data['4. close'])
                prev_price = float(prev_data['4. close'])
                change = current_price - prev_price
                change_percent = (change / prev_price) * 100
                
                return {
                    'symbol': symbol.upper(),
                    'price': current_price,
                    'change': change,
                    'change_percent': change_percent,
                    'volume': int(latest_data['5. volume']),
                    'high': float(latest_data['2. high']),
                    'low': float(latest_data['3. low']),
                    'open': float(latest_data['1. open']),
                    'date': latest_date,
                    'currency': 'USD'
                }
            else:
                logger.error(f"Error fetching data for {symbol}: {data.get('Error Message', 'Unknown error')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Network error fetching stock data: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    def get_market_overview(self) -> Dict[str, Any]:
        """Get market overview data"""
        try:
            # Major indices to track
            indices = ['SPY', 'QQQ', 'DIA', 'IWM']  # S&P 500, NASDAQ, Dow, Russell 2000
            market_data = {}
            
            for index in indices:
                data = self.get_stock_data(index)
                if data:
                    market_data[index] = data
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {}
    
    def get_investment_recommendations(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate investment recommendations using GPT function calling"""
        
        functions = [
            {
                "name": "recommend_investments",
                "description": "Recommend investment options based on user profile",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recommendations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string"},
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "allocation_percentage": {"type": "number"},
                                    "reasoning": {"type": "string"},
                                    "risk_level": {"type": "string"},
                                    "expected_return": {"type": "number"},
                                    "time_horizon": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        ]
        
        prompt = f"""
        Based on the following user profile, recommend a diversified investment portfolio:
        
        Age: {user_profile.get('age', 'Not specified')}
        Risk Tolerance: {user_profile.get('risk_tolerance', 'Moderate')}
        Investment Goals: {user_profile.get('goals', 'Long-term growth')}
        Investment Amount: ${user_profile.get('amount', 1000):,.2f}
        Time Horizon: {user_profile.get('time_horizon', '5+ years')}
        Current Income: ${user_profile.get('income', 0):,.2f}
        Investment Experience: {user_profile.get('experience', 'Beginner')}
        
        Provide 5-8 investment recommendations including:
        - Low-cost index funds/ETFs for core holdings
        - Individual stocks for growth potential
        - Bonds for stability (if appropriate for age/risk tolerance)
        - REITs for diversification
        
        Ensure allocations sum to 100% and match the user's risk tolerance.
        For conservative investors: More bonds and dividend stocks
        For aggressive investors: More growth stocks and emerging markets
        For moderate investors: Balanced mix
        
        Consider the user's age for stock/bond allocation (rule of thumb: bond % = age, but adjust based on risk tolerance).
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional investment advisor. Provide diversified, appropriate recommendations based on the user's profile."},
                    {"role": "user", "content": prompt}
                ],
                functions=functions,
                function_call={"name": "recommend_investments"},
                temperature=0.3,
                max_tokens=1500
            )
            
            function_call = response.choices[0].message.function_call
            recommendations = json.loads(function_call.arguments)
            
            # Validate and enrich recommendations
            validated_recommendations = []
            for rec in recommendations.get('recommendations', []):
                # Get real-time data if available
                if rec.get('symbol'):
                    market_data = self.get_stock_data(rec['symbol'])
                    if market_data:
                        rec['current_price'] = market_data['price']
                        rec['daily_change'] = market_data['change_percent']
                
                validated_recommendations.append(rec)
            
            return validated_recommendations
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in investment recommendations: {e}")
            return []
        except Exception as e:
            logger.error(f"Error generating investment recommendations: {e}")
            return []
    
    def analyze_portfolio_performance(self, portfolio: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze portfolio performance and risk"""
        if not portfolio:
            return {}
        
        total_value = 0
        portfolio_data = []
        
        for holding in portfolio:
            symbol = holding.get('symbol', '')
            shares = holding.get('shares', 0)
            
            if not symbol or shares <= 0:
                continue
            
            stock_data = self.get_stock_data(symbol)
            if stock_data:
                current_value = stock_data['price'] * shares
                total_value += current_value
                
                portfolio_data.append({
                    'symbol': symbol,
                    'shares': shares,
                    'current_price': stock_data['price'],
                    'value': current_value,
                    'daily_change': stock_data['change_percent'],
                    'percentage': 0  # Will calculate after total
                })
        
        # Calculate percentages
        for item in portfolio_data:
            item['percentage'] = (item['value'] / total_value) * 100 if total_value > 0 else 0
        
        # Calculate portfolio metrics
        total_daily_change = sum(
            (item['daily_change'] * item['percentage'] / 100) 
            for item in portfolio_data
        )
        
        # Generate AI analysis
        analysis = self._generate_portfolio_analysis(portfolio_data, total_value, total_daily_change)
        
        return {
            'total_value': total_value,
            'daily_change_percent': total_daily_change,
            'holdings': portfolio_data,
            'analysis': analysis,
            'diversification_score': self._calculate_diversification_score(portfolio_data),
            'risk_level': self._assess_portfolio_risk(portfolio_data)
        }
    
    def _generate_portfolio_analysis(self, portfolio_data: List[Dict], total_value: float, daily_change: float) -> str:
        """Generate AI-powered portfolio analysis"""
        prompt = f"""
        Analyze the following investment portfolio:
        
        Total Value: ${total_value:,.2f}
        Daily Change: {daily_change:.2f}%
        Holdings: {portfolio_data}
        
        Provide analysis on:
        1. Portfolio diversification and concentration risk
        2. Risk assessment based on holdings
        3. Performance insights
        4. Rebalancing recommendations
        5. Suggestions for improvement
        
        Keep the response concise and actionable.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a portfolio analysis expert providing insights on investment portfolios."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating portfolio analysis: {e}")
            return f"Portfolio analysis unavailable: {str(e)}"
    
    def _calculate_diversification_score(self, portfolio_data: List[Dict]) -> float:
        """Calculate diversification score (0-100)"""
        if not portfolio_data:
            return 0
        
        # Simple diversification score based on concentration
        max_allocation = max(item['percentage'] for item in portfolio_data)
        num_holdings = len(portfolio_data)
        
        # Penalize concentration
        concentration_penalty = max_allocation / 100
        
        # Reward number of holdings (up to a point)
        holdings_bonus = min(num_holdings / 10, 1)
        
        # Calculate score
        score = (1 - concentration_penalty) * holdings_bonus * 100
        
        return min(100, max(0, score))
    
    def _assess_portfolio_risk(self, portfolio_data: List[Dict]) -> str:
        """Assess overall portfolio risk level"""
        if not portfolio_data:
            return "Unknown"
        
        # Simple risk assessment based on volatility and concentration
        max_allocation = max(item['percentage'] for item in portfolio_data)
        avg_daily_change = sum(abs(item['daily_change']) for item in portfolio_data) / len(portfolio_data)
        
        if max_allocation > 50 or avg_daily_change > 5:
            return "High"
        elif max_allocation > 30 or avg_daily_change > 3:
            return "Moderate"
        else:
            return "Low"
    
    def get_investment_news(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Get investment news (placeholder - would integrate with news API)"""
        # This would integrate with a news API like Alpha Vantage News or NewsAPI
        # For now, return placeholder data
        return [
            {
                'title': 'Market Update: Tech Stocks Rally',
                'summary': 'Technology stocks showed strong performance today...',
                'source': 'Financial News',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'relevance': 'high'
            }
        ]
    
    def calculate_investment_allocation(self, amount: float, risk_tolerance: str, age: int) -> Dict[str, float]:
        """Calculate recommended asset allocation"""
        # Basic asset allocation based on age and risk tolerance
        if risk_tolerance.lower() == 'conservative':
            stock_percentage = max(20, 100 - age - 10)
        elif risk_tolerance.lower() == 'aggressive':
            stock_percentage = min(90, 100 - age + 20)
        else:  # moderate
            stock_percentage = 100 - age
        
        bond_percentage = 100 - stock_percentage
        
        # Further breakdown
        allocation = {
            'domestic_stocks': stock_percentage * 0.6,
            'international_stocks': stock_percentage * 0.3,
            'emerging_markets': stock_percentage * 0.1,
            'bonds': bond_percentage * 0.8,
            'reits': bond_percentage * 0.2
        }
        
        # Calculate dollar amounts
        dollar_allocation = {
            category: (percentage / 100) * amount 
            for category, percentage in allocation.items()
        }
        
        return {
            'percentages': allocation,
            'amounts': dollar_allocation,
            'total_stocks': stock_percentage,
            'total_bonds': bond_percentage
        }
