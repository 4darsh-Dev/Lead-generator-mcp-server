"""
MCP Tools Package.

This package contains all MCP tool implementations.
Each tool is a separate module for better maintainability.
"""

from mcp_server.tools.scraping import register_scraping_tools

__all__ = ["register_scraping_tools"]
