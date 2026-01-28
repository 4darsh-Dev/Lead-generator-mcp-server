"""
MCP (Model Context Protocol) Server Package for Lead Generation.

This package provides a modular MCP server implementation that exposes
lead generation and scraping capabilities through the MCP interface.
"""

__version__ = "1.0.0"
__author__ = "Lead Generator MCP Server"

from mcp_server.server import create_server, run_server

__all__ = ["create_server", "run_server"]
