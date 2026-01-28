"""
Logger utility for MCP Server.

Simple logging configuration that writes to stderr for MCP STDIO compatibility.
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance for MCP server.
    
    Logs to stderr to avoid corrupting JSON-RPC messages on stdout.
    
    Args:
        name: Name of the logger (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Use stderr for MCP STDIO compatibility
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
