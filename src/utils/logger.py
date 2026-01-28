"""
Logging configuration module.
Provides consistent logging across all modules.

IMPORTANT: For MCP STDIO servers, logs MUST go to stderr, not stdout!
Writing to stdout corrupts JSON-RPC messages.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Get a configured logger instance.
    
    CRITICAL: Uses stderr for MCP STDIO compatibility.
    Never use stdout in MCP servers as it corrupts JSON-RPC messages.
    
    Args:
        name: Name of the logger (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # CRITICAL: Use stderr, not stdout for MCP STDIO compatibility
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
    
    return logger


def configure_logging(level: str = 'INFO') -> None:
    """
    Configure global logging settings.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
