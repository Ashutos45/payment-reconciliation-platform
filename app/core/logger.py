import sys
from loguru import logger

# Remove default logger configuration
logger.remove()

# Add standard output configuration with formatting
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Add file logging configuration for persistent logs
logger.add(
    "logs/app.log",
    rotation="10 MB",  # Rotate log file when it reaches 10MB
    retention="10 days", # Keep logs for 10 days
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

# Export the logger object
__all__ = ["logger"]
