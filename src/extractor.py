"""
Data extraction module for business information.
Handles extraction of business details from Google Maps.
"""

import re
from typing import Dict, List

import requests
from tqdm import tqdm

from .config import SELECTORS
from .logger import get_logger

logger = get_logger(__name__)


class DataExtractor:
    """Extracts business data from Google Maps pages."""
    
    def __init__(self, page):
        """
        Initialize the data extractor.
        
        Args:
            page: Playwright page object
        """
        self.page = page
        
    def extract_name(self) -> str:
        """
        Extract business name from the page.
        
        Returns:
            str: Business name or 'N/A'
        """
        try:
            name_element = self.page.query_selector(SELECTORS['business_name'])
            if name_element:
                name_text = name_element.inner_text()
                name_text = re.sub(r'\s{2,}', ' ', name_text).strip()
                return name_text
        except Exception as e:
            logger.warning(f"Error extracting business name: {e}")
        return "N/A"
        
    def extract_category(self) -> str:
        """
        Extract business category from the page.
        
        Returns:
            str: Business category or 'N/A'
        """
        try:
            category_element = self.page.query_selector(SELECTORS['category'])
            if category_element:
                return category_element.inner_text()
        except Exception as e:
            logger.warning(f"Error extracting category: {e}")
        return "N/A"
        
    def extract_rating(self) -> str:
        """
        Extract business rating from the page.
        
        Returns:
            str: Rating value or 'N/A'
        """
        try:
            rating_element = self.page.query_selector(SELECTORS['rating'])
            if rating_element:
                rating_text = rating_element.get_attribute('aria-label')
                if rating_text:
                    rating_match = re.search(r'(\d+\.\d+)', rating_text)
                    if rating_match:
                        return rating_match.group(1)
        except Exception as e:
            logger.warning(f"Error extracting rating: {e}")
        return "N/A"
        
    def extract_reviews(self) -> str:
        """
        Extract number of reviews from the page.
        
        Returns:
            str: Number of reviews or 'N/A'
        """
        try:
            reviews_element = self.page.query_selector(SELECTORS['reviews'])
            if reviews_element:
                span_element = reviews_element.query_selector('span')
                reviews_text = span_element.inner_text() if span_element else reviews_element.inner_text()
                
                reviews_match = re.search(r'(\d+(?:,\d+)*)', reviews_text)
                if reviews_match:
                    return reviews_match.group(1).replace(',', '')
        except Exception as e:
            logger.warning(f"Error extracting reviews: {e}")
        return "N/A"
        
    def extract_address(self) -> str:
        """
        Extract business address from the page.
        
        Returns:
            str: Address or 'N/A'
        """
        try:
            address_element = self.page.query_selector(SELECTORS['address_button'])
            if address_element:
                address = address_element.get_attribute('aria-label')
                if address:
                    return address.replace('Address: ', '')
        except Exception as e:
            logger.warning(f"Error extracting address: {e}")
        return "N/A"
        
    def extract_phone(self) -> str:
        """
        Extract business phone number from the page.
        
        Returns:
            str: Phone number or 'N/A'
        """
        try:
            phone_element = self.page.query_selector(SELECTORS['phone_button'])
            if phone_element:
                phone = phone_element.get_attribute('aria-label')
                if phone:
                    return phone.replace('Phone: ', '')
        except Exception as e:
            logger.warning(f"Error extracting phone: {e}")
        return "N/A"
        
    def extract_website(self) -> str:
        """
        Extract business website from the page.
        
        Returns:
            str: Website URL or 'N/A'
        """
        try:
            website_element = self.page.query_selector(SELECTORS['website_link'])
            if website_element:
                website = website_element.get_attribute('aria-label')
                if website:
                    website = website.replace('Website: ', '')
                
                href = website_element.get_attribute('href')
                if href and "google.com/url" in href:
                    website_match = re.search(r'q=([^&]+)', href)
                    if website_match:
                        website = requests.utils.unquote(website_match.group(1))
                
                return website
        except Exception as e:
            logger.warning(f"Error extracting website: {e}")
        return "N/A"
        
    def extract_all(self) -> Dict[str, str]:
        """
        Extract all business information from the page.
        
        Returns:
            dict: Dictionary containing all extracted business data
        """
        return {
            'name': self.extract_name(),
            'category': self.extract_category(),
            'address': self.extract_address(),
            'phone': self.extract_phone(),
            'website': self.extract_website(),
            'rating': self.extract_rating(),
            'reviews': self.extract_reviews()
        }


class BusinessDataCollector:
    """Collects data from multiple business listings."""
    
    def __init__(self, browser_manager):
        """
        Initialize the data collector.
        
        Args:
            browser_manager: BrowserManager instance
        """
        self.browser_manager = browser_manager
        self.page = browser_manager.get_page()
        
    def collect_from_listings(self, max_results: int = 100) -> List[Dict]:
        """
        Collect data from all business listings.
        
        Args:
            max_results: Maximum number of businesses to process
            
        Returns:
            list: List of dictionaries containing business data
        """
        logger.info("Collecting business data from listings...")
        
        business_links = self.page.query_selector_all(SELECTORS['business_link'])
        business_links = business_links[:max_results]
        
        results = []
        
        for i, link in enumerate(tqdm(business_links, desc="Extracting data")):
            try:
                if not self.browser_manager.click_business_listing(link):
                    self._handle_click_failure(i)
                    continue
                
                extractor = DataExtractor(self.page)
                business_data = extractor.extract_all()
                results.append(business_data)
                
                if not self.browser_manager.go_back_to_results():
                    self._handle_navigation_failure()
                    
            except Exception as e:
                logger.warning(f"Error collecting data from business {i+1}: {e}")
                self._attempt_recovery()
        
        logger.info(f"Successfully collected data from {len(results)} businesses")
        return results
        
    def _handle_click_failure(self, index: int) -> None:
        """Handle failure to click business listing."""
        logger.warning(f"Failed to click business {index+1}, attempting recovery...")
        try:
            self.browser_manager.go_back_to_results()
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            
    def _handle_navigation_failure(self) -> None:
        """Handle failure to navigate back to results."""
        logger.error("Failed to return to results page")
        self.browser_manager.retry_search()
        
    def _attempt_recovery(self) -> None:
        """Attempt to recover from extraction error."""
        try:
            self.browser_manager.go_back_to_results()
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            self.browser_manager.retry_search()
