"""
MCP Server Implementation.

Main server module that initializes and runs the MCP server with all registered tools.
Follows MCP 2025-11-25 specification standards.
"""

import sys
import os

# When run as script or imported, adjust path
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from mcp_server.config import DEFAULT_CONFIG, MCPServerConfig
from mcp_server.tools import register_scraping_tools
from mcp_server.logger import get_logger

logger = get_logger(__name__)


def create_server(config: MCPServerConfig = None) -> FastMCP:
    """
    Create and configure the MCP server instance.
    
    Args:
        config: Optional configuration object. Uses DEFAULT_CONFIG if not provided.
        
    Returns:
        FastMCP: Configured MCP server instance
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    logger.info(f"Creating MCP server: {config.name} v{config.version}")
    
    # Initialize FastMCP server with configuration
    mcp = FastMCP(
        config.name,
        dependencies=config.dependencies
    )
    
    # Register all tools
    logger.info("Registering tools...")
    register_scraping_tools(mcp)
    
    logger.info("MCP server created successfully")
    return mcp


def run_server(config: MCPServerConfig = None) -> None:
    """
    Create and run the MCP server.
    
    This function:
    1. Creates the MCP server with the given configuration
    2. Starts the server with the configured transport (default: STDIO)
    3. Handles the server lifecycle
    
    Args:
        config: Optional configuration object. Uses DEFAULT_CONFIG if not provided.
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    logger.info("=" * 60)
    logger.info(f"Starting {config.name} v{config.version}")
    logger.info(f"Transport: {config.transport.upper()}")
    logger.info(f"Dependencies: {', '.join(config.dependencies)}")
    logger.info("=" * 60)
    
    # Create server instance
    mcp = create_server(config)
    
    # Log startup information
    if config.transport == "stdio":
        logger.info("Using STDIO transport (MCP standard)")
        logger.info("Ready to accept connections from MCP clients")
        logger.info("Note: All logs go to stderr to prevent JSON-RPC corruption")
    
    logger.info("Server is running. Press Ctrl+C to stop.")
    logger.info("=" * 60)
    
    try:
        # Run the server with configured transport
        mcp.run(transport=config.transport)
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point for the MCP server."""
    run_server()


if __name__ == "__main__":
    main()
