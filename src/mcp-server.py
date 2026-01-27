"""
Model Context Protocol (MCP) Server for Lead Generation.
Exposes scraping functionality through MCP interface.
"""

from mcp.server.fastmcp import FastMCP

from scraper_core import create_scraper
from logger import get_logger

logger = get_logger(__name__)

mcp = FastMCP("LeadGen MCP Server", dependencies=["playwright"])


@mcp.tool()
def scrape_google_maps(query: str, max_results: int = 100) -> list:
    """
    Scrape business leads from Google Maps.
    
    Args:
        query: Search query (e.g., 'coffee shops in Seattle')
        max_results: Maximum number of results to scrape (default: 100)
        
    Returns:
        list: List of validated business data dictionaries
    """
    logger.info(f"MCP tool called: query='{query}', max_results={max_results}")
    
    try:
        scraper = create_scraper(headless=True)
        
        scraper.browser_manager.start()
        
        if not scraper.browser_manager.navigate_to_search(query):
            logger.error("Search navigation failed")
            return []
        
        scraper.browser_manager.scroll_results_container(max_results)
        
        from extractor import BusinessDataCollector
        collector = BusinessDataCollector(scraper.browser_manager)
        raw_data = collector.collect_from_listings(max_results)
        
        validated_data = scraper.validator.validate_batch(raw_data)
        
        scraper.browser_manager.close()
        
        logger.info(f"Successfully scraped {len(validated_data)} businesses")
        return validated_data
        
    except Exception as e:
        logger.error(f"Error in MCP tool: {e}", exc_info=True)
        return []


if __name__ == "__main__":
    logger.info("Starting MCP server...")
    mcp.run(transport="http", port=8080, reload=True)

