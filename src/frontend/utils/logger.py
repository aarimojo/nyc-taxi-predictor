import logging
import sys
from pathlib import Path
from datetime import datetime

class Logger:
    _instance = None

    @staticmethod
    def setup(
        name: str = "nyc-taxi-frontend",
        log_level: str = "INFO",
        log_to_file: bool = False
    ) -> logging.Logger:
        """
        Setup logging configuration
        """
        if Logger._instance is None:
            # Create logger instance
            logger = logging.getLogger(name)
            logger.setLevel(log_level)
            
            # Create formatters
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
            )
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler
            if log_to_file:
                log_dir = Path("logs")
                log_dir.mkdir(exist_ok=True)
                
                log_file = log_dir / f"frontend_{datetime.now().strftime('%Y%m%d')}.log"
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
            
            Logger._instance = logger
        
        return Logger._instance

    @staticmethod
    def get_logger(module_name: str = None) -> logging.Logger:
        """
        Get logger instance
        """
        if Logger._instance is None:
            Logger.setup()
            
        if module_name:
            return logging.getLogger(f"{Logger._instance.name}.{module_name}")
        return Logger._instance