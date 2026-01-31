"""
Main scraper orchestrator that coordinates all services.
"""

from typing import Optional, List, Dict

from src.services.browser_service import BrowserManager
from src.services.extraction_service_v3 import DataExtractorV3
from src.services.validation_service import ValidationService
from src.services.scoring_service import LeadScoringService
from src.services.export_service import ExportService
from src.services.state_service import get_state_manager, ScrapingState
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
        export_format: str = 'csv',
        resume: bool = True
    ) -> Optional[str]:
        """
        Scrape data and export to file with incremental saving and resume support.
        Each business is saved immediately after extraction and validation.
        
        Args:
            query: Search query for Google Maps
            max_results: Maximum number of results to scrape
            output_file: Output filename (auto-generated if None)
            export_format: Export format ('csv' or 'json')
            resume: Enable resume functionality (default: True)
            
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
        
        # CSV incremental mode with state management
        state_manager = get_state_manager()
        state: Optional[ScrapingState] = None
        
        try:
            # Check for existing state if resume is enabled
            if resume:
                state = state_manager.load_state(query, max_results)
            
            resuming = state is not None
            
            if resuming:
                logger.info(f"🔄 Resuming previous session")
                logger.info(f"   Already processed: {len(state.processed_indices)}/{len(state.business_urls)}")
                logger.info(f"   Output file: {state.output_file}")
                output_file = state.output_file
            else:
                logger.info(f"🆕 Starting new scraping session for: {query}")
            
            # Initialize or resume CSV
            if resuming:
                output_path = self.exporter.init_incremental_csv(output_file, resume=True)
                # Load existing business names to avoid duplicates
                existing_names = self.exporter.load_existing_business_names(output_file)
            else:
                output_path = self.exporter.init_incremental_csv(output_file, resume=False)
                existing_names = set()
            
            logger.info(f"Output file: {output_path}")
            
            self.browser_manager.start()
            
            if not self.browser_manager.navigate_to_search(query):
                logger.error("Failed to navigate to search results")
                self.exporter.close_csv()
                return None
            
            # Collect business URLs if this is a new session
            if not resuming:
                result_count = self.browser_manager.scroll_results_container(max_results)
                logger.info(f"Loaded {result_count} business listings")
                
                if result_count == 0:
                    logger.warning("No results found")
                    self.exporter.close_csv()
                    return None
                
                # Collect URLs and create state
                business_urls = self.data_extractor._collect_business_urls(max_results)
                state = state_manager.create_new_state(
                    query=query,
                    max_results=max_results,
                    output_file=output_path,
                    business_urls=business_urls
                )
                
                # Store URLs in extractor
                self.data_extractor.business_urls = business_urls
            else:
                # Restore URLs to extractor
                self.data_extractor.business_urls = state.business_urls
                logger.info(f"Restored {len(state.business_urls)} business URLs from state")
            
            extracted_count = 0
            
            # Extract with callback for incremental saving and state updates
            def save_and_track_business(business_data: Optional[Dict], index: int):
                nonlocal extracted_count
                
                if business_data is None:
                    # Failed extraction
                    state.mark_failed(index)
                    state_manager.update_state(state)
                    return
                
                # Check for duplicates
                business_name = business_data.get('name', '').strip().lower()
                if business_name in existing_names:
                    logger.debug(f"Skipping duplicate: {business_data.get('name', 'Unknown')}")
                    state.mark_processed(index)
                    state_manager.update_state(state)
                    return
                
                # Validate
                validated = self.validator.validate_business(business_data)
                # Score
                scored = self.scorer.calculate_score(validated)
                validated['lead_score'] = scored
                
                # Save immediately
                self.exporter.append_to_csv(validated)
                extracted_count += 1
                
                # Update state
                state.mark_processed(index)
                state_manager.update_state(state)
                
                # Add to existing names
                if business_name:
                    existing_names.add(business_name)
                
                logger.info(
                    f"Saved business {len(state.processed_indices)}/{len(state.business_urls)}: "
                    f"{validated.get('name', 'Unknown')}"
                )
            
            # Extract with resume support
            self.data_extractor.extract_from_listings_incremental(
                max_results=max_results,
                callback=save_and_track_business,
                processed_indices=state.processed_indices if resuming else None
            )
            
            logger.info(f"Extraction complete. Total businesses saved in this session: {extracted_count}")
            logger.info(f"Total businesses in file: {len(state.processed_indices)}")
            
            # Mark state as completed
            state_manager.mark_completed(state)
            
            return output_path
            
        except KeyboardInterrupt:
            logger.warning("⚠️  Scraping interrupted by user")
            if state:
                logger.info(f"✅ Progress saved! Run the same command to resume.")
                logger.info(f"   Processed: {len(state.processed_indices)}/{len(state.business_urls)}")
                state_manager.save_state(state)
            raise
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}", exc_info=True)
            if state and extracted_count > 0:
                logger.info(f"Partial data saved: {extracted_count} businesses before error")
                logger.info(f"Run the same command to resume from where it stopped.")
                state_manager.save_state(state)
                return output_path
            return None
        finally:
            self.exporter.close_csv()
            self.browser_manager.close()
