from mcp.server.fastmcp import FastMCP
from scraper import GoogleMapsScraper

mcp = FastMCP("LeadGen MCP Server", dependencies=["playwright"])

@mcp.tool()
def scrape_google_maps(query: str, max_results: int = 100) -> list:
    scraper = GoogleMapsScraper(headless=True)
    scraper.start_browser()
    success = scraper.search_query(query)
    if not success:
        scraper.close_browser()
        return []
    scraper.scroll_results(max_results)
    raw_data = scraper.extract_business_data(max_results)
    validated_data = scraper.validate_data(raw_data)
    scraper.close_browser()
    return validated_data

if __name__ == "__main__":
    mcp.run(transport="http", port=8080, reload=True)
