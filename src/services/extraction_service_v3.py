"""
Data extraction service with URL tracking and state management.
Hybrid approach combining URL-based navigation with data attributes.
"""

import re
import time
import random
from typing import Dict, List, Optional, Callable
from urllib.parse import urlparse, parse_qs

import requests
from tqdm import tqdm

from src.utils.constants import SELECTORS, EXTRACTION_CONFIG
from src.utils.helpers import clean_text, extract_number_from_text, extract_rating_from_label
from src.services.browser_service import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataExtractorV3:
    """
    Extracts business data using URL tracking and data attributes.
    
    Key improvements:
    - Extracts and stores business URLs from links
    - Navigates directly to business URLs instead of clicking
    - Maintains URL-based state management
    - Better error recovery
    """
    
    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize data extractor.
        
        Args:
            browser_manager: Browser manager instance
        """
        self.browser = browser_manager
        self.search_url = None
        self.business_urls = []
    
    @property
    def page(self):
        """Get the current page from browser manager."""
        return self.browser.page
    
    def extract_business_details(self) -> Optional[Dict]:
        """
        Extract detailed information from a business listing page.
        
        Returns:
            dict: Business data or None if extraction fails
        """
        try:
            business_data = {
                'name': self._extract_name(),
                'category': self._extract_category(),
                'rating': self._extract_rating(),
                'reviews': self._extract_reviews(),
                'address': self._extract_address(),
                'phone': self._extract_phone(),
                'website': self._extract_website()
            }
            return business_data
        except Exception as e:
            logger.error(f"Failed to extract business details: {e}", exc_info=True)
            return None
    
    def _extract_name(self) -> str:
        """Extract business name."""
        try:
            name_element = self.page.query_selector(SELECTORS['business_name'])
            if name_element:
                name_text = name_element.inner_text()
                return clean_text(name_text)
        except Exception as e:
            logger.debug(f"Failed to extract name: {e}")
        return "N/A"
    
    def _extract_category(self) -> str:
        """Extract business category."""
        try:
            category_element = self.page.query_selector(SELECTORS['category'])
            return category_element.inner_text() if category_element else "N/A"
        except Exception as e:
            logger.debug(f"Failed to extract category: {e}")
            return "N/A"
    
    def _extract_rating(self) -> str:
        """Extract business rating."""
        try:
            rating_element = self.page.query_selector(SELECTORS['rating'])
            if rating_element:
                rating_text = rating_element.get_attribute('aria-label')
                rating = extract_rating_from_label(rating_text)
                if rating:
                    return rating
        except Exception as e:
            logger.debug(f"Failed to extract rating: {e}")
        return "N/A"
    
    def _extract_reviews(self) -> str:
        """Extract number of reviews."""
        try:
            reviews_element = self.page.query_selector(SELECTORS['reviews'])
            if reviews_element:
                span_element = reviews_element.query_selector('span')
                reviews_text = span_element.inner_text() if span_element else reviews_element.inner_text()
                reviews = extract_number_from_text(reviews_text)
                if reviews:
                    return reviews
        except Exception as e:
            logger.debug(f"Failed to extract reviews: {e}")
        return "N/A"
    
    def _extract_address(self) -> str:
        """Extract business address."""
        try:
            address_element = self.page.query_selector(SELECTORS['address'])
            if address_element:
                return address_element.get_attribute('aria-label').replace('Address: ', '')
        except Exception as e:
            logger.debug(f"Failed to extract address: {e}")
        return "N/A"
    
    def _extract_phone(self) -> str:
        """Extract business phone number."""
        try:
            phone_element = self.page.query_selector(SELECTORS['phone'])
            if phone_element:
                return phone_element.get_attribute('aria-label').replace('Phone: ', '')
        except Exception as e:
            logger.debug(f"Failed to extract phone: {e}")
        return "N/A"
    
    def _extract_website(self) -> str:
        """Extract business website URL."""
        try:
            website_element = self.page.query_selector(SELECTORS['website'])
            if website_element:
                website = website_element.get_attribute('aria-label').replace('Website: ', '')
                href = website_element.get_attribute('href')
                
                if href and "google.com/url" in href:
                    website_match = re.search(r'q=([^&]+)', href)
                    if website_match:
                        website = requests.utils.unquote(website_match.group(1))
                
                return website
        except Exception as e:
            logger.debug(f"Failed to extract website: {e}")
        return "N/A"
    
    def _collect_business_urls(self, max_results: int) -> List[str]:
        """
        Collect all business URLs from the current search results page.
        
        Args:
            max_results: Maximum number of URLs to collect
            
        Returns:
            list: List of business URLs
        """
        urls = []
        try:
            # Get all business link elements
            business_links = self.page.query_selector_all(SELECTORS['business_link'])
            
            for link in business_links[:max_results]:
                try:
                    href = link.get_attribute('href')
                    if href and '/maps/place/' in href:
                        urls.append(href)
                except Exception as e:
                    logger.debug(f"Failed to extract URL from link: {e}")
                    continue
            
            logger.info(f"Collected {len(urls)} business URLs")
            
        except Exception as e:
            logger.error(f"Failed to collect business URLs: {e}")
        
        return urls
    
    def extract_from_listings_incremental(
        self,
        max_results: int = 100,
        callback: Optional[Callable[[Dict, int], None]] = None,
        start_index: int = 0,
        processed_indices: Optional[set] = None
    ) -> int:
        """
        Extract data using URL-based navigation with resume support.
        
        Args:
            max_results: Maximum number of businesses to extract
            callback: Function to call with each extracted business (receives Dict and index)
            start_index: Index to start extraction from (for resume)
            processed_indices: Set of already processed indices (for resume)
            
        Returns:
            int: Number of successfully extracted businesses
        """
        # Store search URL for recovery
        self.search_url = self.page.url
        logger.info(f"Search URL: {self.search_url}")
        
        # Collect all business URLs upfront if not already collected
        if not self.business_urls:
            logger.info("Collecting business URLs from search results...")
            self.business_urls = self._collect_business_urls(max_results)
        
        if not self.business_urls:
            logger.error("No business URLs collected")
            return 0
        
        extracted_count = 0
        failed_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        # Initialize processed indices set if not provided
        if processed_indices is None:
            processed_indices = set()
        
        # Calculate URLs to process
        urls_to_process = [
            (i, url) for i, url in enumerate(self.business_urls)
            if i not in processed_indices
        ]
        
        logger.info(
            f"Starting extraction: {len(urls_to_process)} pending, "
            f"{len(processed_indices)} already processed, "
            f"{len(self.business_urls)} total"
        )
        
        for i, business_url in tqdm(urls_to_process, desc="Extracting & saving"):
            try:
                # Navigate directly to business URL
                logger.debug(f"[{i+1}/{len(self.business_urls)}] Navigating to: {business_url}")
                
                self.page.goto(business_url, wait_until='domcontentloaded', timeout=30000)
                
                # Wait for phone element (indicates page loaded)
                try:
                    self.page.wait_for_selector(
                        SELECTORS['phone'],
                        timeout=EXTRACTION_CONFIG['detail_timeout']
                    )
                    time.sleep(random.uniform(1.0, 2.0))
                except Exception as wait_error:
                    logger.debug(f"Timeout waiting for details on listing {i+1}: {wait_error}")
                    consecutive_failures += 1
                    failed_count += 1
                    
                    # Call callback with failure info
                    if callback:
                        try:
                            callback(None, i)
                        except Exception as callback_error:
                            logger.error(f"Callback error for failed listing {i+1}: {callback_error}")
                    
                    continue
                
                # Extract business data
                business_data = self.extract_business_details()
                if business_data:
                    extracted_count += 1
                    consecutive_failures = 0  # Reset on success
                    logger.debug(f"[{i+1}/{len(self.business_urls)}] Extracted: {business_data.get('name', 'Unknown')}")
                    
                    # Call callback immediately with data and index
                    if callback:
                        try:
                            callback(business_data, i)
                        except Exception as callback_error:
                            logger.error(f"Callback error for business {i+1}: {callback_error}")
                else:
                    logger.warning(f"Failed to extract data for listing {i+1}")
                    failed_count += 1
                    consecutive_failures += 1
                    
                    # Call callback with failure info
                    if callback:
                        try:
                            callback(None, i)
                        except Exception as callback_error:
                            logger.error(f"Callback error for failed listing {i+1}: {callback_error}")
                
                # Check if too many consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"Too many consecutive failures ({consecutive_failures}). Stopping.")
                    break
                
                # Random delay between extractions
                time.sleep(random.uniform(
                    EXTRACTION_CONFIG['min_delay'],
                    EXTRACTION_CONFIG['max_delay']
                ))
                
            except Exception as e:
                logger.error(f"Error extracting listing {i+1}: {e}")
                consecutive_failures += 1
                failed_count += 1
                
                # Call callback with failure info
                if callback:
                    try:
                        callback(None, i)
                    except Exception as callback_error:
                        logger.error(f"Callback error for exception at {i+1}: {callback_error}")
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"Too many consecutive failures ({consecutive_failures}). Stopping extraction.")
                    break
                
                # Longer delay after errors
                time.sleep(random.uniform(2.0, 4.0))
        
        logger.info(f"Extraction complete: {extracted_count} successful, {failed_count} failed")
        return extracted_count
