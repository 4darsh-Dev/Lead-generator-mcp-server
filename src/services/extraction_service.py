"""
Data extraction service for scraping business information.
"""

import re
import time
import random
from typing import Dict, List, Optional

import requests
from tqdm import tqdm

from utils.constants import SELECTORS, EXTRACTION_CONFIG
from utils.helpers import clean_text, extract_number_from_text, extract_rating_from_label
from services.browser_service import BrowserManager


class DataExtractor:
    """Extracts business data from Google Maps pages."""
    
    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize data extractor.
        
        Args:
            browser_manager: Browser manager instance
        """
        self.browser = browser_manager
        self.page = browser_manager.page
    
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
        except Exception:
            return None
    
    def _extract_name(self) -> str:
        """Extract business name."""
        name_element = self.page.query_selector(SELECTORS['business_name'])
        if name_element:
            name_text = name_element.inner_text()
            return clean_text(name_text)
        return "N/A"
    
    def _extract_category(self) -> str:
        """Extract business category."""
        category_element = self.page.query_selector(SELECTORS['category'])
        return category_element.inner_text() if category_element else "N/A"
    
    def _extract_rating(self) -> str:
        """Extract business rating."""
        rating_element = self.page.query_selector(SELECTORS['rating'])
        if rating_element:
            rating_text = rating_element.get_attribute('aria-label')
            rating = extract_rating_from_label(rating_text)
            if rating:
                return rating
        return "N/A"
    
    def _extract_reviews(self) -> str:
        """Extract number of reviews."""
        reviews_element = self.page.query_selector(SELECTORS['reviews'])
        if reviews_element:
            span_element = reviews_element.query_selector('span')
            reviews_text = span_element.inner_text() if span_element else reviews_element.inner_text()
            reviews = extract_number_from_text(reviews_text)
            if reviews:
                return reviews
        return "N/A"
    
    def _extract_address(self) -> str:
        """Extract business address."""
        address_element = self.page.query_selector(SELECTORS['address'])
        if address_element:
            return address_element.get_attribute('aria-label').replace('Address: ', '')
        return "N/A"
    
    def _extract_phone(self) -> str:
        """Extract business phone number."""
        phone_element = self.page.query_selector(SELECTORS['phone'])
        if phone_element:
            return phone_element.get_attribute('aria-label').replace('Phone: ', '')
        return "N/A"
    
    def _extract_website(self) -> str:
        """Extract business website URL."""
        website_element = self.page.query_selector(SELECTORS['website'])
        if website_element:
            website = website_element.get_attribute('aria-label').replace('Website: ', '')
            href = website_element.get_attribute('href')
            
            if href and "google.com/url" in href:
                website_match = re.search(r'q=([^&]+)', href)
                if website_match:
                    website = requests.utils.unquote(website_match.group(1))
            
            return website
        return "N/A"
    
    def extract_from_listings(self, max_results: int = 100) -> List[Dict]:
        """
        Extract data from multiple business listings.
        
        Args:
            max_results: Maximum number of businesses to extract
            
        Returns:
            list: List of business data dictionaries
        """
        business_links = self.browser.get_business_links(max_results)
        results = []
        
        for i, link in enumerate(tqdm(business_links, desc="Extracting data")):
            try:
                self.page.evaluate(
                    '(element) => element.scrollIntoView({ behavior: "smooth", block: "center" })', 
                    link
                )
                time.sleep(random.uniform(
                    EXTRACTION_CONFIG['scroll_delay_min'],
                    EXTRACTION_CONFIG['scroll_delay_max']
                ))
                
                link.click()
                
                try:
                    self.page.wait_for_selector(
                        SELECTORS['phone'],
                        timeout=EXTRACTION_CONFIG['detail_timeout']
                    )
                    time.sleep(random.uniform(1.0, 2.0))
                except Exception:
                    self.browser.navigate_back()
                    time.sleep(random.uniform(1.0, 2.0))
                    continue
                
                business_data = self.extract_business_details()
                if business_data:
                    results.append(business_data)
                
                self.browser.navigate_back()
                time.sleep(random.uniform(
                    EXTRACTION_CONFIG['min_delay'],
                    EXTRACTION_CONFIG['max_delay']
                ))
                
            except Exception:
                try:
                    self.page.go_back()
                    self.page.wait_for_selector(
                        SELECTORS['business_link'],
                        timeout=EXTRACTION_CONFIG['back_timeout']
                    )
                    time.sleep(random.uniform(1.0, 2.0))
                except Exception:
                    if self.browser.last_query:
                        self.browser.navigate_to_search(self.browser.last_query)
        
        return results
