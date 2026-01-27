"""
Main scraper orchestrator.
Coordinates the scraping workflow across all modules.
"""

from typing import Optional

from .browser import BrowserManager
from .extractor import BusinessDataCollector
from .validator import DataValidator
from .exporter import DataExporter
from .logger import get_logger

logger = get_logger(__name__)


class GoogleMapsScraper:
    """
    Main scraper class coordinating the complete workflow.
    Orchestrates browser management, data extraction, validation, and export.
    """
    
    def __init__(self, headless: bool = True, slow_mo: int = 50):
        """
        Initialize the scraper with configuration.
        
        Args:
            headless: Run browser in headless mode
            slow_mo: Delay in milliseconds between browser actions
        """
        self.browser_manager = BrowserManager(headless, slow_mo)
        self.validator = DataValidator()
        self.exporter = DataExporter()
        
    def scrape(self, query: str, max_results: int = 100, 
               output_file: Optional[str] = None) -> Optional[str]:
        """
        Execute the complete scraping workflow.
        
        Args:
            query: Search query for Google Maps
            max_results: Maximum number of businesses to scrape
            output_file: Output CSV filename (optional)
            
        Returns:
            str: Path to output file, or None if failed
        """
        try:
            self._start_scraping()
            
            if not self._search(query):
                return None
            
            result_count = self._load_results(max_results)
            if result_count == 0:
                logger.warning("No results found")
                return None
            
            raw_data = self._extract_data(max_results)
            if not raw_data:
                logger.warning("No data extracted")
                return None
            
            validated_data = self._validate_data(raw_data)
            
            output_path = self._export_data(validated_data, output_file)
            
            logger.info("Scraping workflow completed successfully")
            return output_path
            
        except Exception as e:
            logger.error(f"Error during scraping workflow: {e}", exc_info=True)
            return None
        finally:
            self._cleanup()
            
    def _start_scraping(self) -> None:
        """Initialize browser for scraping."""
        logger.info("Initializing scraper...")
        self.browser_manager.start()
        
    def _search(self, query: str) -> bool:
        """
        Execute search query on Google Maps.
        
        Args:
            query: Search query string
            
        Returns:
            bool: True if search successful
        """
        logger.info(f"Searching for: {query}")
        success = self.browser_manager.navigate_to_search(query)
        
        if not success:
            logger.error("Search failed")
        return success
        
    def _load_results(self, max_results: int) -> int:
        """
        Load search results by scrolling.
        
        Args:
            max_results: Maximum results to load
            
        Returns:
            int: Number of results loaded
        """
        result_count = self.browser_manager.scroll_results_container(max_results)
        logger.info(f"Loaded {result_count} business listings")
        return result_count
        
    def _extract_data(self, max_results: int) -> list:
        """
        Extract data from business listings.
        
        Args:
            max_results: Maximum businesses to extract
            
        Returns:
            list: Extracted business data
        """
        collector = BusinessDataCollector(self.browser_manager)
        raw_data = collector.collect_from_listings(max_results)
        logger.info(f"Extracted data from {len(raw_data)} businesses")
        return raw_data
        
    def _validate_data(self, raw_data: list) -> list:
        """
        Validate and enhance extracted data.
        
        Args:
            raw_data: Raw extracted data
            
        Returns:
            list: Validated and enhanced data
        """
        return self.validator.validate_batch(raw_data)
        
    def _export_data(self, data: list, output_file: Optional[str]) -> Optional[str]:
        """
        Export data to file.
        
        Args:
            data: Data to export
            output_file: Output filename (optional)
            
        Returns:
            str: Path to exported file
        """
        return self.exporter.export_csv(data, output_file)
        
    def _cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up resources...")
        self.browser_manager.close()


def create_scraper(headless: bool = True, slow_mo: int = 50) -> GoogleMapsScraper:
    """
    Factory function to create a configured scraper instance.
    
    Args:
        headless: Run browser in headless mode
        slow_mo: Delay in milliseconds between browser actions
        
    Returns:
        GoogleMapsScraper: Configured scraper instance
    """
    return GoogleMapsScraper(headless=headless, slow_mo=slow_mo)
