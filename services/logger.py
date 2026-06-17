import logging
import os
from logging.handlers import RotatingFileHandler
from config.paths import LOGS_DIR

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Configuration
LOG_LEVEL = os.environ.get("WSMIS_LOG_LEVEL", "INFO").upper()
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

FORMATTER = logging.Formatter(
    fmt='%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def _setup_logger(name: str, log_file: str) -> logging.Logger:
    """Creates a logger with a rotating file handler."""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # Prevent duplicate handlers
    if not logger.handlers:
        file_path = os.path.join(LOGS_DIR, log_file)
        handler = RotatingFileHandler(
            file_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        handler.setFormatter(FORMATTER)
        logger.addHandler(handler)
        
        # Add console handler for active debugging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(FORMATTER)
        logger.addHandler(console_handler)
        
    return logger

# Dedicated loggers
app_logger = _setup_logger("wsmis.app", "application.log")
error_logger = _setup_logger("wsmis.error", "errors.log")
perf_logger = _setup_logger("wsmis.perf", "performance.log")
export_logger = _setup_logger("wsmis.export", "exports.log")

# Legacy compatibility
logger = app_logger
