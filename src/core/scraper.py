"""
Main scraper orchestrator that coordinates all services.
"""

from typing import Optional, List, Dict

from src.services.browser_service import BrowserManager
from src.services.extraction_service import DataExtractor
from src.services.validation_service import ValidationService
from src.services.scoring_service import LeadScoringService
from src.services.export_service import ExportService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleMapsScraper:
    """Main scraper class that orchestrates the scraping workflow."""
    
    def __init__(self, headless: bool = True, slow_mo: int = 50):
        """
        Initialize the scraper with all required services.
        
        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down operations by specified milliseconds
        """
        self.browser_manager = BrowserManager(headless, slow_mo)
        self.data_extractor = DataExtractor(self.browser_manager)
        self.validator = ValidationService()
        self.scorer = LeadScoringService()
        self.exporter = ExportService()
    
    def scrape(
        self, 
        query: str, 
        max_results: int = 100
    ) -> List[Dict]:
        """
        Execute the complete scraping workflow.
        
        Args:
            query: Search query for Google Maps
            max_results: Maximum number of results to scrape
            
        Returns:
            list: List of validated and scored business dictionaries
        """
        logger.info(f"Starting scrape for query: {query}")
        
        try:
            self.browser_manager.start()
            
            if not self.browser_manager.navigate_to_search(query):
                logger.error("Failed to navigate to search results")
                return []
            
            result_count = self.browser_manager.scroll_results_container(max_results)
            logger.info(f"Loaded {result_count} business listings")
            
            if result_count == 0:
                logger.warning("No results found")
                return []
            
            raw_data = self.data_extractor.extract_from_listings(max_results)
            logger.info(f"Extracted data from {len(raw_data)} businesses")
            
            validated_data = self.validator.validate_batch(raw_data)
            logger.info("Data validation complete")
            
            scored_data = self.scorer.score_batch(validated_data)
            logger.info("Lead scoring complete")
            
            return scored_data
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}", exc_info=True)
            return []
        finally:
            self.browser_manager.close()
    
    def scrape_and_export(
        self,
        query: str,
        max_results: int = 100,
        output_file: Optional[str] = None,
        export_format: str = 'csv'
    ) -> Optional[str]:
        """
        Scrape data and export to file.
        
        Args:
            query: Search query for Google Maps
            max_results: Maximum number of results to scrape
            output_file: Output filename (auto-generated if None)
            export_format: Export format ('csv' or 'json')
            
        Returns:
            str: Path to exported file, or None if failed
        """
        data = self.scrape(query, max_results)
        
        if not data:
            logger.error("No data to export")
            return None
        
        try:
            if export_format.lower() == 'json':
                output_path = self.exporter.export_to_json(data, output_file)
            else:
                output_path = self.exporter.export_to_csv(data, output_file)
            
            logger.info(f"Data exported to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            return None
