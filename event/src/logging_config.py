import os
import sys
from pathlib import Path
from loguru import logger

def setup_logging():
    """Configure loguru with both file and console handlers."""
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_file = os.environ.get('LOG_FILE', '/var/log/foxrose/app.log')
    
    # Remove default handler
    logger.remove()
    
    # Add console handler (always works)
    logger.add(
        sys.stdout,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} [{level}] {name}: {message}"
    )
    
    # Try to add file handler, fall back gracefully if we can't create the directory
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} [{level}] {name}: {message}",
            rotation="10 MB",
            retention="5 days",
            compression="zip"
        )
    except (PermissionError, OSError):
        # If we can't create the log directory, just use console logging
        # This is expected when running outside Docker
        pass
    
    return logger

# Initialize logger on import
setup_logging()
