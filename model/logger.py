import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_file: str = 'model.log', level=logging.INFO, log_to_file: bool = False):
    """
    Set up a logger with both file and console handlers
    
    Args:
        name: Name of the logger
        log_file: Path to the log file
        level: Logging level
    
    Returns:
        Logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    

    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(log_format)

    if log_to_file:
        file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    else:
        file_handler = None
        

    # Add handlers to the logger
    logger.addHandler(console_handler)

    return logger

# Create a default logger instance
logger = setup_logger('model_logger')