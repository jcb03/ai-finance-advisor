import os

def create_project_structure():
    """Create the complete directory structure for the finance advisor project in current directory"""
    
    # Define the directory structure (without finance_advisor prefix)
    structure = [
        "app.py",
        "auth/__init__.py",
        "auth/authentication.py",
        "auth/user_management.py",
        "database/__init__.py",
        "database/connection.py",
        "database/models.py",
        "database/migrations.sql",
        "services/__init__.py",
        "services/transaction_parser.py",
        "services/ai_advisor.py",
        "services/investment_service.py",
        "services/notification_service.py",
        "utils/__init__.py",
        "utils/file_processor.py",
        "utils/helpers.py",
        "config/__init__.py",
        "config/settings.py",
        "requirements.txt",
        "secrets.toml",
        "README.md"
    ]
    
    # Create directories and files
    for path in structure:
        dir_path = os.path.dirname(path)
        
        # Create directory if it doesn't exist
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
        
        # Create file if it doesn't exist
        if not os.path.exists(path):
            with open(path, 'w') as f:
                # Add basic content based on file type
                if path.endswith("__init__.py"):
                    f.write('"""Package initialization file"""\n')
                elif path.endswith(".py"):
                    f.write(f'"""{os.path.basename(path)} - {get_file_description(path)}"""\n\n')
                elif path.endswith(".sql"):
                    f.write("-- Database migration file\n")
                elif path.endswith(".toml"):
                    f.write("# Configuration secrets file\n")
                elif path.endswith(".txt"):
                    f.write("# Project dependencies\n")
                elif path.endswith(".md"):
                    f.write("# AI-Powered Personal Finance Advisor\n\n")
                else:
                    f.write("")
            print(f"Created file: {path}")
    
    print("\n✅ Project structure created successfully!")
    return True

def get_file_description(path):
    """Get description for each file based on its name"""
    descriptions = {
        "app.py": "Main Streamlit application",
        "authentication.py": "User authentication logic",
        "user_management.py": "User CRUD operations",
        "connection.py": "Database connection",
        "models.py": "Database models",
        "transaction_parser.py": "Transaction parsing and categorization",
        "ai_advisor.py": "AI-powered insights and recommendations",
        "investment_service.py": "Investment recommendations",
        "notification_service.py": "Notifications",
        "file_processor.py": "File upload and processing",
        "helpers.py": "Utility functions",
        "settings.py": "Configuration settings"
    }
    
    filename = os.path.basename(path)
    return descriptions.get(filename, "Module file")

def list_project_structure(base_dir="."):
    """Display the created project structure in current directory"""
    print(f"\n📁 Project Structure:")
    print("=" * 50)
    
    # List only the project files and directories we created
    project_items = [
        "app.py", "requirements.txt", "secrets.toml", "README.md",
        "auth/", "database/", "services/", "utils/", "config/"
    ]
    
    for item in project_items:
        if os.path.exists(item):
            if os.path.isdir(item):
                print(f"├── {item}")
                # List files in directory
                try:
                    files = os.listdir(item)
                    for i, file in enumerate(files):
                        if i == len(files) - 1:
                            print(f"│   └── {file}")
                        else:
                            print(f"│   ├── {file}")
                except PermissionError:
                    print(f"│   └── [Permission Denied]")
            else:
                print(f"├── {item}")

if __name__ == "__main__":
    # Create the project structure
    create_project_structure()
    
    # Display the structure
    list_project_structure()
