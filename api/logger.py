import logging
import sys
from typing import Optional

class Logger:
    _instance: Optional[logging.Logger] = None

    @staticmethod
    def setup(name: str = 'taxi-predictor-api') -> logging.Logger:
        """Set up and return a logger instance."""
        if Logger._instance is None:
            # Configure root logger
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
            
            # Create logger instance
            Logger._instance = logging.getLogger(name)
            
        return Logger._instance

    @staticmethod
    def get_logger(module_name: str = '') -> logging.Logger:
        """Get a logger instance with the given module name."""
        if Logger._instance is None:
            Logger.setup()
            
        if module_name:
            return logging.getLogger(f"{Logger._instance.name}.{module_name}")
        return Logger._instance