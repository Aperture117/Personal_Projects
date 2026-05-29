import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """Creates and returns a pre-configured logger."""
    logger = logging.getLogger(name)
    
    # Only configure if it doesn't have handlers already
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # StreamHandler logs to console
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
    return logger
