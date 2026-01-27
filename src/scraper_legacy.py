"""
Google Maps Business Scraper
----------------------------
Scrapes business data from Google Maps based on search queries
and exports the data to CSV for lead generation.
"""

import argparse
import csv
import json
import logging
import os
import random
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import phonenumbers
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Browser
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
]

class GoogleMapsScraper:
    """Main scraper class to extract business data from Google Maps."""
    
    def __init__(self, headless: bool = True, slow_mo: int = 50):
        """Initialize the scraper with browser settings."""
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser = None
        self.page = None
        self.data = []
        self.playwright = None
        
        # Load NLP classifier for lead scoring
        try:
            # self.classifier = pipeline("text-classification", model="distilbert-base-uncased")
            logger.info("NLP classifier loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load NLP classifier: {e}")
            self.classifier = None

    def start_browser(self) -> None:
        """Initialize and start the Playwright browser."""
        self.playwright = sync_playwright().start()
        
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        
        self.page = self.browser.new_page(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1366, "height": 768}
        )
        
        # Set extra HTTP headers to avoid detection
        self.page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })

    def close_browser(self) -> None:
        """Close the browser and clean up resources."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def search_query(self, query: str) -> bool:
        """Navigate to Google Maps and enter the search query."""
        encoded_query = query.replace(' ', '+')
        url = f"https://www.google.co.in/maps/search/{encoded_query}"
        
        logger.info(f"Searching for: {query}")
        self.page.goto(url)
        
        # Store the last query for potential use later
        self.last_query = query
        
        # Wait for search results to load - using the hfpxzc class that's used in the working Selenium code
        try:
            self.page.wait_for_selector('a.hfpxzc', timeout=20000)
            logger.info("Search results loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading search results: {e}")
            return False

    def scroll_results(self, max_results: int = 100) -> int:
        """Scroll through results to load more businesses."""
        logger.info(f"Scrolling to load up to {max_results} results")
        
        # Find the results container - adjusted to match Google Maps current structure
        results_selector = 'div[role="feed"]'
        
        # Check if results exist
        if not self.page.query_selector(results_selector):
            logger.error("No results found")
            return 0
        
        # Get initial number of results
        previous_count = 0
        
        # Scroll until we have enough results or can't load more
        attempt = 0
        max_attempts = 20
        scroll_pause = 1.5
        
        with tqdm(total=max_results, desc="Loading results") as pbar:
            while attempt < max_attempts:
                # Get current results count - using the hfpxzc class as in Selenium code
                results = self.page.query_selector_all('a.hfpxzc')
                current_count = len(results)
                
                # Update progress bar
                if current_count > previous_count:
                    pbar.update(current_count - previous_count)
                    previous_count = current_count
                
                # Check if we have enough results
                if current_count >= max_results:
                    logger.info(f"Loaded {current_count} results (reached target)")
                    break
                
                # Scroll to the bottom of the results
                self.page.evaluate(f'''
                    document.querySelector('{results_selector}').scrollTop = 
                    document.querySelector('{results_selector}').scrollHeight
                ''')
                
                # Add random delay to avoid detection
                time.sleep(scroll_pause + random.uniform(0.5, 1.5))
                
                # Check if we've loaded more results
                if current_count == previous_count:
                    attempt += 1
                else:
                    attempt = 0
            
            if attempt == max_attempts:
                logger.info(f"Scrolling stopped: No new results after {max_attempts} attempts")
        
        return current_count

    def extract_business_data(self, max_results: int = 100) -> List[Dict]:
        """Extract data from business listings."""
        logger.info("Extracting business data...")
        
        # Get all business listings using the correct selector
        business_links = self.page.query_selector_all('a.hfpxzc')
        results = []
        
        # Limit to max_results
        business_links = business_links[:max_results]
        
        for i, link in enumerate(tqdm(business_links, desc="Extracting data")):
            try:
                # Scroll the element into view to make sure it's clickable
                self.page.evaluate('(element) => element.scrollIntoView({ behavior: "smooth", block: "center" })', link)
                time.sleep(random.uniform(0.5, 1.0))  # Brief pause for scrolling
                
                # Click on the listing to get detailed information
                link.click()
                
                # Wait for the details panel to load with phone button
                try:
                    self.page.wait_for_selector('button[aria-label^="Phone:"]', timeout=10000)
                    # Give it a moment to fully load
                    time.sleep(random.uniform(1.0, 2.0))
                except Exception as e:
                    logger.warning(f"Timeout waiting for phone button on business {i+1}: {e}")
                    # Try to go back and continue
                    self.page.go_back()
                    self.page.wait_for_selector('a.hfpxzc', timeout=10000)
                    time.sleep(random.uniform(1.0, 2.0))
                    continue
                
                # Extract business name
                # name_element = self.page.query_selector('h1')
                # name_text = name_element.inner_text() if name_element else "N/A"

                # Extract business name using the specific class you mentioned
                # Extract business name
                name_element = self.page.query_selector('h1.DUwDvf')
                name_text = "N/A"
                if name_element:
                    # Get the direct text content of the h1, ignoring the span children
                    name_text = name_element.inner_text()
                    
                    # Additional cleaning to remove any extra spans that might be included
                    name_text = re.sub(r'\s{2,}', ' ', name_text).strip()

                
                # Extract category - update selector to match new structure
                # Extract category using the updated selector
                category_element = self.page.query_selector('button[jsaction="pane.wfvdle17.category"], button[jsaction*="category"]')
                category = category_element.inner_text() if category_element else "N/A"
                # Extract rating using the aria-label approach from Selenium code
                # rating_element = self.page.query_selector('span[aria-label*="stars"]')
                # rating = "N/A"
                # if rating_element:
                #     rating_text = rating_element.get_attribute('aria-label')
                #     rating_match = re.search(r'(\d+\.\d+)', rating_text)
                #     if rating_match:
                #         rating = rating_match.group(1)

                # Extract rating with enhanced selector including role="img"
                rating_element = self.page.query_selector('span[aria-label*="stars"][role="img"], span[aria-label*="stars"]')
                rating = "N/A"
                if rating_element:
                    rating_text = rating_element.get_attribute('aria-label')
                    if rating_text:
                        rating_match = re.search(r'(\d+\.\d+)', rating_text)
                        if rating_match:
                            rating = rating_match.group(1)
                
               # Extract reviews count - updated selector for the reviews button
                reviews_element = self.page.query_selector('button[jsaction="pane.wfvdle13.reviewChart.moreReviews"], button[jsaction*="moreReviews"]')
                reviews = "N/A"
                if reviews_element:
                    # Find the span inside the button that contains the reviews text
                    span_element = reviews_element.query_selector('span')
                    if span_element:
                        reviews_text = span_element.inner_text()
                    else:
                        reviews_text = reviews_element.inner_text()
                    
                    # Extract just the numbers
                    reviews_match = re.search(r'(\d+(?:,\d+)*)', reviews_text)
                    if reviews_match:
                        reviews = reviews_match.group(1).replace(',', '')
                
                # Extract address using aria-label like in the Selenium code
                address_element = self.page.query_selector('button[aria-label^="Address:"]')
                address = "N/A"
                if address_element:
                    address = address_element.get_attribute('aria-label').replace('Address: ', '')
                
                # Extract phone using aria-label like in the Selenium code
                phone_element = self.page.query_selector('button[aria-label^="Phone:"]')
                phone = "N/A"
                if phone_element:
                    phone = phone_element.get_attribute('aria-label').replace('Phone: ', '')
                
                # Extract website using aria-label like in the Selenium code
                website_element = self.page.query_selector('a[aria-label^="Website:"]')
                website = "N/A"
                if website_element:
                    website = website_element.get_attribute('aria-label').replace('Website: ', '')
                    # Also get the href attribute
                    href = website_element.get_attribute('href')
                    if href and "google.com/url" in href:
                        # Extract the real URL from Google's redirect
                        website_match = re.search(r'q=([^&]+)', href)
                        if website_match:
                            website = requests.utils.unquote(website_match.group(1))
                
                # Add to results
                business_data = {
                    'name': name_text,
                    'category': category,
                    'address': address,
                    'phone': phone,
                    'website': website,
                    'rating': rating,
                    'reviews': reviews
                }
                
                results.append(business_data)
                
                # Go back to results list - using JS history for better reliability
                self.page.evaluate('window.history.back()')
                
                # Wait for results page to reload
                self.page.wait_for_selector('a.hfpxzc', timeout=10000)
                
                # Add random delay between 1-3 seconds
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                logger.warning(f"Error extracting data from business {i+1}: {e}")
                # Try to return to results page if we're stuck
                try:
                    self.page.go_back()
                    self.page.wait_for_selector('a.hfpxzc', timeout=10000)
                    time.sleep(random.uniform(1.0, 2.0))
                except:
                    logger.error("Failed to return to results page")
                    # If we can't recover, try searching again
                    self.search_query(self.last_query)
        
        return results

    def validate_data(self, data: List[Dict]) -> List[Dict]:
        """Validate and enhance the scraped data."""
        validated_data = []
        
        for business in tqdm(data, desc="Validating data"):
            # Validate phone numbers
            if business['phone'] != "N/A":
                try:
                    # Extract digits only
                    digits = re.sub(r'\D', '', business['phone'])
                    # Parse as international number (assuming US for simplicity)
                    parsed_number = phonenumbers.parse(digits, "US")
                    if phonenumbers.is_valid_number(parsed_number):
                        # Format consistently
                        business['phone'] = phonenumbers.format_number(
                            parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                        )
                        business['phone_valid'] = True
                    else:
                        business['phone_valid'] = False
                except:
                    business['phone_valid'] = False
            else:
                business['phone_valid'] = False
            
            # Validate websites
            if business['website'] != "N/A":
                business['website_valid'] = self.is_website_valid(business['website'])
            else:
                business['website_valid'] = False
            
            # Add lead score based on business attributes
            business['lead_score'] = self.calculate_lead_score(business)
            
            validated_data.append(business)
        
        return validated_data

    def is_website_valid(self, url: str) -> bool:
        """Check if a website URL is valid and accessible."""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            response = requests.head(url, timeout=5, headers=headers, allow_redirects=True)
            return response.status_code < 400
        except:
            return False

    def calculate_lead_score(self, business: Dict) -> int:
        """Calculate a lead score (0-100) based on business attributes."""
        score = 50  # Base score
        
        # Adjust score based on website presence
        if business['website'] == "N/A":
            score += 20  # No website = good lead for web services
        elif not business.get('website_valid', False):
            score += 15  # Invalid website = good lead
        
        # Adjust for ratings
        if business['rating'] != "N/A":
            try:
                rating = float(business['rating'])
                if rating >= 4.5:
                    score += 10  # High-rated businesses may have budget for services
                elif rating < 3.5:
                    score += 5  # Low-rated may need marketing help
            except:
                pass
        
        # Adjust for review count (popularity)
        if business['reviews'] != "N/A":
            try:
                reviews = int(business['reviews'])
                if reviews > 100:
                    score += 5  # Established business
                elif reviews < 10:
                    score += 10  # New business likely needs help
            except:
                pass
        
        # Use NLP to analyze business name/category if available
        # if self.classifier and business['category'] != "N/A":
        #     try:
        #         result = self.classifier(business['category'])[0]
        #         if result['label'] == 'POSITIVE' and result['score'] > 0.7:
        #             score += 5
        #     except:
        #         pass
        
        # Cap score at 100
        return min(score, 100)

    def export_to_csv(self, data: List[Dict], filename: Optional[str] = None) -> str:
        """Export the data to a CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"business_leads_{timestamp}.csv"
        
        df = pd.DataFrame(data)
        
        # Reorder columns for better readability
        columns_order = [
            'name', 'category', 'address', 'phone', 'phone_valid',
            'website', 'website_valid', 'rating', 'reviews', 'lead_score'
        ]
        
        # Only include columns that exist in the dataframe
        columns_order = [col for col in columns_order if col in df.columns]
        
        # Add any additional columns not in our ordered list
        for col in df.columns:
            if col not in columns_order:
                columns_order.append(col)
        
        # Sort by lead score (highest first)
        df = df.sort_values(by='lead_score', ascending=False)
        
        # Export to CSV
        df.to_csv(filename, index=False, columns=columns_order)
        logger.info(f"Data exported to {filename}")
        
        return filename

    def run(self, query: str, max_results: int = 100, output_file: Optional[str] = None) -> str:
        """Run the complete scraping workflow."""
        try:
            self.start_browser()
            
            # Search for the query
            search_success = self.search_query(query)
            if not search_success:
                logger.error("Search failed. Exiting.")
                return None
            
            # Load results by scrolling
            result_count = self.scroll_results(max_results)
            logger.info(f"Found {result_count} businesses")
            
            if result_count == 0:
                logger.warning("No results found. Exiting.")
                return None
            
            # Extract business data
            raw_data = self.extract_business_data(max_results)
            logger.info(f"Extracted data from {len(raw_data)} businesses")
            
            # Validate and enhance data
            validated_data = self.validate_data(raw_data)
            
            # Export to CSV
            output_path = self.export_to_csv(validated_data, output_file)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return None
        finally:
            self.close_browser()


def main():
    """Main function to run the scraper from command line."""
    parser = argparse.ArgumentParser(description="Google Maps Business Scraper")
    parser.add_argument("--query", type=str, required=True, help="Search query (e.g., 'beauty salons in London')")
    parser.add_argument("--max-results", type=int, default=100, help="Maximum number of results to scrape")
    parser.add_argument("--output", type=str, help="Output CSV filename")
    parser.add_argument("--visible", action="store_true", help="Run in visible browser mode")
    args = parser.parse_args()
    
    scraper = GoogleMapsScraper(headless=not args.visible)
    
    try:
        output_file = scraper.run(args.query, args.max_results, args.output)
        if output_file:
            print(f"Scraping completed successfully. Data saved to: {output_file}")
        else:
            print("Scraping failed.")
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()