"""
Browser automation module for web scraping.
Handles browser initialization, navigation, and interaction.
"""

import random
import time
from typing import Optional

from playwright.sync_api import sync_playwright, Page, Browser

from .config import (
    USER_AGENTS, HTTP_HEADERS, BROWSER_CONFIG, SCRAPING_CONFIG, 
    SELECTORS, GOOGLE_MAPS_CONFIG
)
from .logger import get_logger

logger = get_logger(__name__)


class BrowserManager:
    """Manages browser lifecycle and navigation."""
    
    def __init__(self, headless: bool = True, slow_mo: int = 50):
        """
        Initialize the browser manager.
        
        Args:
            headless: Whether to run browser in headless mode
            slow_mo: Delay in milliseconds between browser actions
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.last_query: Optional[str] = None
        
    def start(self) -> None:
        """Initialize and start the Playwright browser."""
        logger.info("Starting browser...")
        self.playwright = sync_playwright().start()
        
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        
        viewport = BROWSER_CONFIG['viewport']
        self.page = self.browser.new_page(
            user_agent=random.choice(USER_AGENTS),
            viewport=viewport
        )
        
        self.page.set_extra_http_headers(HTTP_HEADERS)
        logger.info("Browser started successfully")
        
    def close(self) -> None:
        """Close the browser and clean up resources."""
        logger.info("Closing browser...")
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed")
        
    def navigate_to_search(self, query: str) -> bool:
        """
        Navigate to Google Maps and enter the search query.
        
        Args:
            query: Search query string
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        encoded_query = query.replace(' ', '+') if GOOGLE_MAPS_CONFIG['url_encoding'] else query
        url = GOOGLE_MAPS_CONFIG['base_url'].format(query=encoded_query)
        
        logger.info(f"Navigating to: {query}")
        self.page.goto(url)
        self.last_query = query
        
        try:
            timeout = SCRAPING_CONFIG['search_timeout']
            self.page.wait_for_selector(SELECTORS['business_link'], timeout=timeout)
            logger.info("Search results loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading search results: {e}")
            return False
            
    def scroll_results_container(self, max_results: int = 100) -> int:
        """
        Scroll through results to load more businesses.
        
        Args:
            max_results: Maximum number of results to load
            
        Returns:
            int: Number of results loaded
        """
        logger.info(f"Scrolling to load up to {max_results} results")
        
        results_selector = SELECTORS['results_container']
        
        if not self.page.query_selector(results_selector):
            logger.error("No results container found")
            return 0
        
        previous_count = 0
        attempt = 0
        max_attempts = SCRAPING_CONFIG['max_scroll_attempts']
        scroll_pause = SCRAPING_CONFIG['scroll_pause_base']
        scroll_variation = SCRAPING_CONFIG['scroll_pause_variation']
        
        while attempt < max_attempts:
            results = self.page.query_selector_all(SELECTORS['business_link'])
            current_count = len(results)
            
            if current_count >= max_results:
                logger.info(f"Loaded {current_count} results (reached target)")
                break
            
            self.page.evaluate(f'''
                document.querySelector('{results_selector}').scrollTop = 
                document.querySelector('{results_selector}').scrollHeight
            ''')
            
            delay = scroll_pause + random.uniform(*scroll_variation)
            time.sleep(delay)
            
            if current_count == previous_count:
                attempt += 1
            else:
                attempt = 0
                previous_count = current_count
        
        if attempt == max_attempts:
            logger.info(f"Scrolling stopped: No new results after {max_attempts} attempts")
        
        return current_count
        
    def click_business_listing(self, element) -> bool:
        """
        Click on a business listing element.
        
        Args:
            element: Playwright element to click
            
        Returns:
            bool: True if click successful, False otherwise
        """
        try:
            self.page.evaluate(
                '(element) => element.scrollIntoView({ behavior: "smooth", block: "center" })', 
                element
            )
            delay = random.uniform(*SCRAPING_CONFIG['click_delay'])
            time.sleep(delay)
            
            element.click()
            
            timeout = SCRAPING_CONFIG['page_load_timeout']
            self.page.wait_for_selector(SELECTORS['phone_button'], timeout=timeout)
            
            delay = random.uniform(*SCRAPING_CONFIG['page_load_delay'])
            time.sleep(delay)
            return True
            
        except Exception as e:
            logger.warning(f"Error clicking business listing: {e}")
            return False
            
    def go_back_to_results(self) -> bool:
        """
        Navigate back to the results page.
        
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            self.page.evaluate('window.history.back()')
            
            timeout = SCRAPING_CONFIG['page_load_timeout']
            self.page.wait_for_selector(SELECTORS['business_link'], timeout=timeout)
            
            delay = random.uniform(*SCRAPING_CONFIG['action_delay'])
            time.sleep(delay)
            return True
            
        except Exception as e:
            logger.error(f"Error navigating back to results: {e}")
            return False
            
    def retry_search(self) -> bool:
        """
        Retry the last search query.
        
        Returns:
            bool: True if retry successful, False otherwise
        """
        if self.last_query:
            logger.info(f"Retrying search: {self.last_query}")
            return self.navigate_to_search(self.last_query)
        return False
        
    def get_page(self) -> Page:
        """
        Get the current page object.
        
        Returns:
            Page: Playwright page object
        """
        return self.page
