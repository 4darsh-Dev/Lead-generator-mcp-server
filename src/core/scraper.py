"""
Main scraper orchestrator that coordinates all services.
"""

from typing import Optional, List, Dict

from src.services.browser_service import BrowserManager
from src.services.extraction_service_v3 import DataExtractorV3
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
        self.data_extractor = DataExtractorV3(self.browser_manager)
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
        results = []
        
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
            
            # Collect data with callback
            def collect_business(business_data: Dict):
                # Validate
                validated = self.validator.validate_business(business_data)
                # Score
                scored = self.scorer.calculate_score(validated)
                validated['lead_score'] = scored
                # Add to results
                results.append(validated)
            
            self.data_extractor.extract_from_listings_incremental(
                max_results, 
                callback=collect_business
            )
            
            logger.info(f"Extracted and processed {len(results)} businesses")
            return results
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}", exc_info=True)
            return results  # Return partial results if any
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
        Scrape data and export to file with incremental saving.
        Each business is saved immediately after extraction and validation.
        
        Args:
            query: Search query for Google Maps
            max_results: Maximum number of results to scrape
            output_file: Output filename (auto-generated if None)
            export_format: Export format ('csv' or 'json')
            
        Returns:
            str: Path to exported file, or None if failed
        """
        if export_format.lower() == 'json':
            # JSON doesn't support incremental writing well, fall back to batch mode
            data = self.scrape(query, max_results)
            if not data:
                logger.error("No data to export")
                return None
            try:
                output_path = self.exporter.export_to_json(data, output_file)
                logger.info(f"Data exported to {output_path}")
                return output_path
            except Exception as e:
                logger.error(f"Export failed: {e}", exc_info=True)
                return None
        
        # CSV incremental mode
        logger.info(f"Starting scrape for query: {query}")
        extracted_count = 0
        
        try:
            # Initialize incremental CSV
            output_path = self.exporter.init_incremental_csv(output_file)
            logger.info(f"Saving results incrementally to: {output_path}")
            
            self.browser_manager.start()
            
            if not self.browser_manager.navigate_to_search(query):
                logger.error("Failed to navigate to search results")
                self.exporter.close_csv()
                return None
            
            result_count = self.browser_manager.scroll_results_container(max_results)
            logger.info(f"Loaded {result_count} business listings")
            
            if result_count == 0:
                logger.warning("No results found")
                self.exporter.close_csv()
                return None
            
            # Extract with callback for incremental saving
            def save_business(business_data: Dict):
                nonlocal extracted_count
                # Validate
                validated = self.validator.validate_business(business_data)
                # Score
                scored = self.scorer.calculate_score(validated)
                validated['lead_score'] = scored
                # Save immediately
                self.exporter.append_to_csv(validated)
                extracted_count += 1
                logger.info(f"Saved business {extracted_count}: {validated.get('name', 'Unknown')}")
            
            self.data_extractor.extract_from_listings_incremental(
                max_results, 
                callback=save_business
            )
            
            logger.info(f"Extraction complete. Total businesses saved: {extracted_count}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}", exc_info=True)
            if extracted_count > 0:
                logger.info(f"Partial data saved: {extracted_count} businesses before error")
                return output_path
            return None
        finally:
            self.exporter.close_csv()
            self.browser_manager.close()
