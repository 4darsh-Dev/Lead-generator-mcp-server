"""
Data extraction service with Playwright Locators (Best Practice Implementation).
Uses modern Playwright locators API for robust, auto-retrying element interactions.
"""

import re
import time
import random
from typing import Dict, List, Optional

import requests
from tqdm import tqdm

from src.utils.constants import SELECTORS, EXTRACTION_CONFIG
from src.utils.helpers import clean_text, extract_number_from_text, extract_rating_from_label
from src.services.browser_service import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataExtractorV2:
    """
    Extracts business data using Playwright Locators for robustness.
    
    Key improvements:
    - Uses locators instead of stored element references
    - URL-based navigation instead of browser back
    - Better error recovery with state validation
    - Exponential backoff on failures
    """
    
    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize data extractor.
        
        Args:
            browser_manager: Browser manager instance
        """
        self.browser = browser_manager
        self.search_url = None  # Store the search results URL
    
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
            name_locator = self.page.locator(SELECTORS['business_name']).first
            if name_locator.is_visible(timeout=3000):
                name_text = name_locator.inner_text()
                return clean_text(name_text)
        except Exception as e:
            logger.debug(f"Failed to extract name: {e}")
        return "N/A"
    
    def _extract_category(self) -> str:
        """Extract business category."""
        try:
            category_locator = self.page.locator(SELECTORS['category']).first
            if category_locator.is_visible(timeout=3000):
                return category_locator.inner_text()
        except Exception as e:
            logger.debug(f"Failed to extract category: {e}")
        return "N/A"
    
    def _extract_rating(self) -> str:
        """Extract business rating."""
        try:
            rating_locator = self.page.locator(SELECTORS['rating']).first
            if rating_locator.is_visible(timeout=3000):
                rating_text = rating_locator.get_attribute('aria-label')
                rating = extract_rating_from_label(rating_text)
                if rating:
                    return rating
        except Exception as e:
            logger.debug(f"Failed to extract rating: {e}")
        return "N/A"
    
    def _extract_reviews(self) -> str:
        """Extract number of reviews."""
        try:
            reviews_locator = self.page.locator(SELECTORS['reviews']).first
            if reviews_locator.is_visible(timeout=3000):
                span_locator = reviews_locator.locator('span').first
                reviews_text = span_locator.inner_text() if span_locator.count() > 0 else reviews_locator.inner_text()
                reviews = extract_number_from_text(reviews_text)
                if reviews:
                    return reviews
        except Exception as e:
            logger.debug(f"Failed to extract reviews: {e}")
        return "N/A"
    
    def _extract_address(self) -> str:
        """Extract business address."""
        try:
            address_locator = self.page.locator(SELECTORS['address']).first
            if address_locator.is_visible(timeout=3000):
                return address_locator.get_attribute('aria-label').replace('Address: ', '')
        except Exception as e:
            logger.debug(f"Failed to extract address: {e}")
        return "N/A"
    
    def _extract_phone(self) -> str:
        """Extract business phone number."""
        try:
            phone_locator = self.page.locator(SELECTORS['phone']).first
            if phone_locator.is_visible(timeout=3000):
                return phone_locator.get_attribute('aria-label').replace('Phone: ', '')
        except Exception as e:
            logger.debug(f"Failed to extract phone: {e}")
        return "N/A"
    
    def _extract_website(self) -> str:
        """Extract business website URL."""
        try:
            website_locator = self.page.locator(SELECTORS['website']).first
            if website_locator.is_visible(timeout=3000):
                website = website_locator.get_attribute('aria-label').replace('Website: ', '')
                href = website_locator.get_attribute('href')
                
                if href and "google.com/url" in href:
                    website_match = re.search(r'q=([^&]+)', href)
                    if website_match:
                        website = requests.utils.unquote(website_match.group(1))
                
                return website
        except Exception as e:
            logger.debug(f"Failed to extract website: {e}")
        return "N/A"
    
    def _validate_page_state(self) -> bool:
        """
        Validate that we're on a valid search results page.
        
        Returns:
            bool: True if on valid search results page
        """
        try:
            # Check if business links are visible
            business_links_locator = self.page.locator(SELECTORS['business_link'])
            return business_links_locator.count() > 0
        except Exception as e:
            logger.debug(f"Page state validation failed: {e}")
            return False
    
    def _navigate_to_search_results(self) -> bool:
        """
        Navigate back to search results using stored URL.
        
        Returns:
            bool: True if navigation successful
        """
        if not self.search_url:
            logger.error("No search URL stored for navigation")
            return False
        
        try:
            logger.debug(f"Navigating to search results: {self.search_url}")
            self.page.goto(self.search_url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for business links to be visible
            self.page.locator(SELECTORS['business_link']).first.wait_for(
                state='visible',
                timeout=10000
            )
            
            time.sleep(random.uniform(1.0, 2.0))
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to search results: {e}")
            return False
    
    def extract_from_listings_incremental(self, max_results: int = 100, callback=None) -> int:
        """
        Extract data from multiple business listings with incremental callback.
        Uses locators and URL-based navigation for robustness.
        
        Args:
            max_results: Maximum number of businesses to extract
            callback: Function to call with each extracted business (receives Dict)
            
        Returns:
            int: Number of successfully extracted businesses
        """
        # Store the search results URL for recovery
        self.search_url = self.page.url
        logger.info(f"Stored search URL: {self.search_url}")
        
        extracted_count = 0
        failed_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        logger.info(f"Starting extraction for up to {max_results} businesses")
        
        for i in range(max_results):
            try:
                # Validate we're on search results page
                if not self._validate_page_state():
                    logger.warning(f"Invalid page state at iteration {i+1}, attempting recovery")
                    if not self._navigate_to_search_results():
                        logger.error("Failed to recover page state")
                        break
                
                # Get fresh locator for business links (auto-retrying)
                business_links_locator = self.page.locator(SELECTORS['business_link'])
                
                # Check if we've reached the end
                total_links = business_links_locator.count()
                if i >= total_links:
                    logger.info(f"Reached end of results at {i}/{total_links} listings")
                    break
                
                # Get the specific link using nth()
                current_link = business_links_locator.nth(i)
                
                # Scroll into view using locator
                try:
                    current_link.scroll_into_view_if_needed(timeout=5000)
                    time.sleep(random.uniform(
                        EXTRACTION_CONFIG['scroll_delay_min'],
                        EXTRACTION_CONFIG['scroll_delay_max']
                    ))
                except Exception as scroll_error:
                    logger.debug(f"Scroll failed for listing {i+1}: {scroll_error}")
                    consecutive_failures += 1
                    failed_count += 1
                    continue
                
                # Click using locator (auto-waits for actionability)
                try:
                    current_link.click(timeout=5000)
                except Exception as click_error:
                    logger.warning(f"Click failed for listing {i+1}: {click_error}")
                    consecutive_failures += 1
                    failed_count += 1
                    continue
                
                # Wait for details page to load
                try:
                    phone_locator = self.page.locator(SELECTORS['phone']).first
                    phone_locator.wait_for(
                        state='visible',
                        timeout=EXTRACTION_CONFIG['detail_timeout']
                    )
                    time.sleep(random.uniform(1.0, 2.0))
                except Exception as wait_error:
                    logger.debug(f"Timeout waiting for details on listing {i+1}: {wait_error}")
                    self._navigate_to_search_results()
                    consecutive_failures += 1
                    failed_count += 1
                    continue
                
                # Extract business data
                business_data = self.extract_business_details()
                if business_data:
                    extracted_count += 1
                    consecutive_failures = 0  # Reset on success
                    logger.debug(f"[{i+1}/{max_results}] Extracted: {business_data.get('name', 'Unknown')}")
                    
                    # Call callback immediately
                    if callback:
                        try:
                            callback(business_data)
                        except Exception as callback_error:
                            logger.error(f"Callback error for business {i+1}: {callback_error}")
                else:
                    logger.warning(f"Failed to extract data for listing {i+1}")
                    failed_count += 1
                    consecutive_failures += 1
                
                # Navigate back to search results using URL
                if not self._navigate_to_search_results():
                    logger.error(f"Failed to return to search results after listing {i+1}")
                    consecutive_failures += 1
                    
                    # Try to recover
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
                
                # Try to recover
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"Too many consecutive failures ({consecutive_failures}). Stopping extraction.")
                    break
                
                # Attempt recovery
                if not self._navigate_to_search_results():
                    logger.error("Recovery failed - cannot continue")
                    break
                
                time.sleep(random.uniform(2.0, 4.0))  # Longer delay after errors
        
        logger.info(f"Extraction complete: {extracted_count} successful, {failed_count} failed")
        return extracted_count
