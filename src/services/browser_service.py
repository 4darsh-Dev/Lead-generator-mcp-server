"""
Browser automation service using Playwright.
"""

import random
import time
from typing import Optional

from playwright.sync_api import sync_playwright, Page, Browser, Playwright
from tqdm import tqdm

from src.utils.constants import (
    USER_AGENTS, 
    GOOGLE_MAPS_BASE_URL, 
    SELECTORS, 
    DEFAULT_VIEWPORT,
    HTTP_HEADERS,
    SCROLL_CONFIG
)
from src.utils.helpers import add_random_delay, encode_search_query


class BrowserManager:
    """Manages browser lifecycle and navigation."""
    
    def __init__(self, headless: bool = True, slow_mo: int = 50):
        """
        Initialize browser manager.
        
        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down operations by specified milliseconds
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.last_query: Optional[str] = None
        
    def start(self) -> None:
        """Initialize and start the Playwright browser."""
        self.playwright = sync_playwright().start()
        
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        
        self.page = self.browser.new_page(
            user_agent=random.choice(USER_AGENTS),
            viewport=DEFAULT_VIEWPORT
        )
        
        self.page.set_extra_http_headers(HTTP_HEADERS)
    
    def close(self) -> None:
        """Close the browser and clean up resources."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def navigate_to_search(self, query: str, max_retries: int = 3) -> bool:
        """
        Navigate to Google Maps and enter the search query with retry logic.
        
        Args:
            query: Search query string
            max_retries: Maximum number of retry attempts
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        from src.utils.logger import get_logger
        logger = get_logger(__name__)
        
        encoded_query = encode_search_query(query)
        url = f"{GOOGLE_MAPS_BASE_URL}{encoded_query}"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigating to Google Maps (attempt {attempt + 1}/{max_retries})")
                self.page.goto(url, timeout=60000, wait_until='domcontentloaded')
                self.last_query = query
                
                # Wait for business links to appear
                self.page.wait_for_selector(SELECTORS['business_link'], timeout=30000)
                logger.info("Successfully navigated to search results")
                return True
                
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Increasing wait time
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to navigate after {max_retries} attempts")
                    return False
        
        return False
    
    def scroll_results_container(self, max_results: int = 100) -> int:
        """
        Scroll through results to load more businesses with improved strategy.
        
        Args:
            max_results: Maximum number of results to load
            
        Returns:
            int: Number of results loaded
        """
        from src.utils.logger import get_logger
        logger = get_logger(__name__)
        
        results_selector = SELECTORS['results_feed']
        
        if not self.page.query_selector(results_selector):
            return 0
        
        previous_count = 0
        consecutive_same_count = 0
        scroll_iteration = 0
        
        with tqdm(total=max_results, desc="Loading results") as pbar:
            while scroll_iteration < SCROLL_CONFIG['max_attempts']:
                results = self.page.query_selector_all(SELECTORS['business_link'])
                current_count = len(results)
                
                # Update progress bar
                if current_count > previous_count:
                    pbar.update(current_count - previous_count)
                    logger.debug(f"Loaded {current_count} results so far")
                    previous_count = current_count
                    consecutive_same_count = 0
                else:
                    consecutive_same_count += 1
                
                # Stop if we've reached target or no more results loading
                if current_count >= max_results:
                    logger.info(f"Reached target of {max_results} results")
                    break
                
                if consecutive_same_count >= SCROLL_CONFIG['consecutive_same_count_limit']:
                    logger.info(f"No new results after {consecutive_same_count} attempts. Stopping at {current_count} results.")
                    break
                
                # Scroll to bottom with multiple scroll actions for better loading
                try:
                    # Multiple small scrolls can trigger better loading
                    for _ in range(3):
                        self.page.evaluate(f'''
                            const container = document.querySelector('{results_selector}');
                            if (container) {{
                                container.scrollTop = container.scrollHeight;
                            }}
                        ''')
                        time.sleep(0.3)
                except Exception as e:
                    logger.debug(f"Scroll error: {e}")
                
                # Wait for new results to load
                time.sleep(
                    SCROLL_CONFIG['pause_time'] + 
                    random.uniform(
                        SCROLL_CONFIG['random_delay_min'],
                        SCROLL_CONFIG['random_delay_max']
                    )
                )
                
                scroll_iteration += 1
        
        return previous_count
    
    def get_business_links(self, max_results: int) -> list:
        """
        Get list of business links from search results.
        
        Args:
            max_results: Maximum number of links to retrieve
            
        Returns:
            list: List of business link elements
        """
        business_links = self.page.query_selector_all(SELECTORS['business_link'])
        return business_links[:max_results]
    
    def navigate_back(self) -> None:
        """Navigate back to the previous page."""
        self.page.evaluate('window.history.back()')
        self.page.wait_for_selector(SELECTORS['business_link'], timeout=10000)
