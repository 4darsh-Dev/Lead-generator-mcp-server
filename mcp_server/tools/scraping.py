"""
Scraping Tools for MCP Server.

Implements Google Maps scraping functionality as MCP tools.
"""

import json
import sys
import os

# Ensure project root is in path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_server.config import DEFAULT_CONFIG

# Set up logging
import logging
logger = logging.getLogger(__name__)


def register_scraping_tools(mcp) -> None:
    """
    Register all scraping-related tools with the MCP server.
    
    Args:
        mcp: FastMCP server instance to register tools with
    """
    
    @mcp.tool()
    async def scrape_google_maps(query: str, max_results: int = None) -> str:
        """
        Scrape business leads from Google Maps.
        
        Extracts comprehensive business information including name, address, phone,
        website, rating, and review count. Results are automatically validated and
        scored for lead quality.
        
        Args:
            query: Search query (e.g., 'coffee shops in Seattle', 'plumbers in NYC')
            max_results: Maximum number of results to scrape (default: 100, max: 500)
            
        Returns:
            str: JSON string containing:
                - success: Boolean indicating if operation succeeded
                - query: The search query used
                - results_count: Number of results returned
                - results: List of business data with lead scores
                - error: Error message if operation failed
        
        Example:
            >>> scrape_google_maps("coffee shops in Seattle", 50)
            '{"success": true, "results_count": 50, "results": [...]}'
        """
        # Lazy import to avoid circular dependencies and import issues
        # This imports the scraper only when the tool is actually called
        import sys
        import os
       
        # Make sure we can import from src
        src_path = os.path.join(project_root, 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        try:
            # Import the scraper class
            from core.scraper import GoogleMapsScraper
        except ImportError as e:
            error_msg = f"Failed to import scraper: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "query": query,
                "results": []
            })
        
        # Use default if not specified
        if max_results is None:
            max_results = DEFAULT_CONFIG.default_scrape_results
        
        logger.info(f"Scraping tool called: query='{query}', max_results={max_results}")
        
        # Validate input
        if not query or not query.strip():
            error_msg = "Error: Query parameter cannot be empty"
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "query": query,
                "results": []
            })
        
        if max_results < DEFAULT_CONFIG.min_scrape_results or max_results > DEFAULT_CONFIG.max_scrape_results:
            error_msg = f"Error: max_results must be between {DEFAULT_CONFIG.min_scrape_results} and {DEFAULT_CONFIG.max_scrape_results}, got {max_results}"
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "query": query,
                "results": []
            })
        
        try:
            # Initialize scraper with config settings
            scraper = GoogleMapsScraper(
                headless=DEFAULT_CONFIG.headless_browser,
                slow_mo=DEFAULT_CONFIG.browser_slow_mo
            )
            
            # Execute scraping
            validated_data = scraper.scrape(
                query=query,
                max_results=max_results
            )
            
            logger.info(f"Successfully scraped {len(validated_data)} businesses")
            
            # Return structured JSON response
            return json.dumps({
                "success": True,
                "query": query,
                "results_count": len(validated_data),
                "results": validated_data
            }, indent=2)
            
        except Exception as e:
            error_msg = f"Error scraping Google Maps: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "query": query,
                "results": []
            })
    
    logger.info("Registered scraping tools: scrape_google_maps")
