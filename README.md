# Finance Cortex AI

A comprehensive personal finance management application powered by AI for intelligent transaction categorization, budgeting insights, and investment recommendations.

## 🌟 Features

### 🤖 AI-Powered Transaction Categorization
- Automatic transaction categorization using GPT-4
- Support for CSV and PDF bank statement uploads
- High-confidence categorization with manual override options

### 📊 Smart Budgeting & Insights
- Create and manage monthly budgets by category
- Real-time budget tracking and alerts
- AI-generated spending insights and recommendations

### 📈 Investment Recommendations
- Personalized investment advice based on risk tolerance and goals
- Real-time stock market data integration
- Portfolio analysis and rebalancing suggestions

### 🎯 Goal Tracking
- Set and track financial goals
- Progress monitoring with visual indicators
- Achievement notifications and celebrations

### 🔔 Intelligent Notifications
- Email and SMS budget alerts
- Investment opportunity notifications
- Weekly financial summaries

### 📱 Modern Web Interface
- Responsive Streamlit-based UI
- Interactive charts and visualizations
- Mobile-friendly design

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL database
- OpenAI API key
- Alpha Vantage API key (optional)
- Twilio account (optional, for SMS)

### Installation

1. **Clone the repository:**

git clone <repository-url>
cd finance_advisor


2. **Install dependencies:**

pip install -r requirements.txt

3. **Set up the database:**
Create PostgreSQL database
createdb finance_advisor

Run migrations
psql -d finance_advisor -f database/migrations.sql


4. **Configure secrets:**
Create a `secrets.toml` file in the root directory:
[postgresql]
host = "localhost"
port = 5432
database = "finance_advisor"
username = "your_username"
password = "your_password"

[openai]
api_key = "your_openai_api_key"

[alpha_vantage]
api_key = "your_alpha_vantage_key"

[twilio]
account_sid = "your_twilio_account_sid"
auth_token = "your_twilio_auth_token"
phone_number = "+1234567890"

[email]
smtp_server = "smtp.gmail.com"
smtp_port = 587
address = "your_email@gmail.com"
password = "your_app_password"


5. **Run the application:**
streamlit run app.py


## 📁 Project Structure

finance_advisor/
├── app.py # Main Streamlit application
├── auth/ # Authentication system
│ ├── authentication.py # User login/registration
│ └── user_management.py # Profile management
├── database/ # Database layer
│ ├── connection.py # Database connection
│ ├── models.py # Data models
│ └── migrations.sql # Database schema
├── services/ # Business logic
│ ├── transaction_parser.py # AI transaction categorization
│ ├── ai_advisor.py # Financial insights
│ ├── investment_service.py # Investment recommendations
│ └── notification_service.py # Notifications
├── utils/ # Utility functions
│ ├── file_processor.py # File upload handling
│ └── helpers.py # Helper functions
├── config/ # Configuration
│ └── settings.py # App settings
├── requirements.txt # Python dependencies
├── secrets.toml # Configuration secrets
└── README.md # This file



## 🔧 Configuration

### Environment Variables

The application uses `secrets.toml` for configuration. Key settings include:

- **Database**: PostgreSQL connection details
- **OpenAI**: API key for GPT-4 integration
- **Alpha Vantage**: API key for stock market data
- **Twilio**: SMS notification settings
- **Email**: SMTP settings for email notifications

### API Keys Setup

1. **OpenAI API Key**: Required for AI features
   - Sign up at [OpenAI](https://openai.com)
   - Generate API key in dashboard
   - Add to `secrets.toml`

2. **Alpha Vantage API Key**: Optional for investment features
   - Sign up at [Alpha Vantage](https://www.alphavantage.co)
   - Get free API key
   - Add to `secrets.toml`

3. **Twilio Account**: Optional for SMS notifications
   - Sign up at [Twilio](https://www.twilio.com)
   - Get Account SID, Auth Token, and phone number
   - Add to `secrets.toml`

## 💡 Usage

### 1. Account Creation
- Navigate to the application URL
- Click "Sign Up" tab
- Fill in registration details
- Verify email (if configured)

### 2. Upload Transactions
- Go to "Transactions" page
- Upload CSV or PDF bank statements
- AI will automatically categorize transactions
- Review and adjust categories if needed

### 3. Set Up Budgets
- Navigate to "Budgets" page
- Create monthly budgets by category
- Monitor spending against budgets
- Receive alerts when approaching limits

### 4. Track Goals
- Go to "Goals" page
- Set financial goals with target amounts and dates
- Update progress regularly
- Celebrate achievements

### 5. Get AI Insights
- Visit "AI Insights" page
- Review spending patterns and trends
- Get personalized recommendations
- View financial health score

### 6. Investment Planning
- Navigate to "Investments" page
- Complete investment profile
- Get AI-powered recommendations
- Track market data

## 🔒 Security

- Passwords are hashed using bcrypt
- Session management with Streamlit
- SQL injection protection with parameterized queries
- API keys stored securely in configuration
- User data isolation by user ID

## 🧪 Testing

Run tests (when implemented):
pytest tests/

## 📊 Database Schema

The application uses PostgreSQL with the following main tables:

- `users`: User accounts and profiles
- `transactions`: Financial transactions
- `budgets`: Monthly spending budgets
- `financial_goals`: Savings and financial goals
- `investment_recommendations`: AI-generated investment advice
- `user_preferences`: Notification and app preferences

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed description
4. Include error logs and configuration (without sensitive data)

## 🔮 Future Enhancements

- [ ] Mobile app development
- [ ] Bank account integration via Plaid
- [ ] Advanced investment portfolio tracking
- [ ] Tax optimization suggestions
- [ ] Multi-currency support
- [ ] Family account sharing
- [ ] Advanced reporting and analytics
- [ ] Machine learning spending predictions
- [ ] Integration with financial advisors
- [ ] Cryptocurrency tracking

## 📝 Changelog

### Version 1.0.0
- Initial release
- AI-powered transaction categorization
- Budget management
- Goal tracking
- Investment recommendations
- Notification system
- User authentication
- Data export functionality

---

**Built with ❤️ using Streamlit, PostgreSQL, and OpenAI GPT-4**
## Created by Jai Chaudhary

Finance Cortex AI © 2025