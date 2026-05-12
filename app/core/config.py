import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Payment Reconciliation Platform")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    
    # Database Settings
    # Default to SQLite if DATABASE_URL is not provided
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    
    # File Upload Settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads/")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", 10485760)) # Default 10MB
    
    # Matching Logic Settings
    AMOUNT_TOLERANCE: float = float(os.getenv("AMOUNT_TOLERANCE", 0.01))
    TIME_TOLERANCE_MINUTES: int = int(os.getenv("TIME_TOLERANCE_MINUTES", 5))

# Create a global settings object
settings = Settings()

# Ensure the upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
