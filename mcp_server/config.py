"""
MCP Server Configuration.

Centralizes all configuration for the MCP server including
server metadata, transport settings, and tool configurations.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class MCPServerConfig:
    """Configuration for the MCP server."""
    
    # Server metadata
    name: str = "LeadGen MCP Server"
    version: str = "1.0.0"
    
    # Transport configuration
    transport: str = "stdio"  # "stdio" is the MCP standard
    
    # System dependencies required by tools
    dependencies: list = None
    
    # Tool configurations
    max_scrape_results: int = 500
    default_scrape_results: int = 100
    min_scrape_results: int = 1
    
    # Browser settings
    headless_browser: bool = True
    browser_slow_mo: int = 50
    
    def __post_init__(self):
        """Initialize default dependencies if not provided."""
        if self.dependencies is None:
            self.dependencies = ["playwright"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "transport": self.transport,
            "dependencies": self.dependencies,
            "max_scrape_results": self.max_scrape_results,
            "default_scrape_results": self.default_scrape_results,
            "min_scrape_results": self.min_scrape_results,
            "headless_browser": self.headless_browser,
            "browser_slow_mo": self.browser_slow_mo,
        }


# Default configuration instance
DEFAULT_CONFIG = MCPServerConfig()
