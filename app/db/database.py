from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.logger import logger

# Get the database URL from settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

logger.info(f"Connecting to database at {SQLALCHEMY_DATABASE_URL}")

try:
    # If using SQLite, we need to add connect_args={"check_same_thread": False}
    # For PostgreSQL, we don't need connect_args
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)

    # Create a configured "Session" class
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create a Base class for our declarative models
    Base = declarative_base()
    
    logger.info("Database connection setup completed successfully.")
except Exception as e:
    logger.error(f"Failed to setup database connection: {str(e)}")
    raise

def get_db():
    """
    Dependency that yields a database session.
    Ensures that the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
