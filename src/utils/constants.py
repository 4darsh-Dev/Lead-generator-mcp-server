"""
Constants and configuration values for the scraper.
"""

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
]

GOOGLE_MAPS_BASE_URL = "https://www.google.co.in/maps/search/"

SELECTORS = {
    'business_link': 'a.hfpxzc',
    'results_feed': 'div[role="feed"]',
    'business_name': 'h1.DUwDvf',
    'category': 'button[jsaction="pane.wfvdle17.category"], button[jsaction*="category"]',
    'rating': 'span[aria-label*="stars"][role="img"], span[aria-label*="stars"]',
    'reviews': 'button[jsaction="pane.wfvdle13.reviewChart.moreReviews"], button[jsaction*="moreReviews"]',
    'address': 'button[aria-label^="Address:"]',
    'phone': 'button[aria-label^="Phone:"]',
    'website': 'a[aria-label^="Website:"]'
}

DEFAULT_VIEWPORT = {"width": 1366, "height": 768}

HTTP_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

SCROLL_CONFIG = {
    'max_attempts': 50,  # Increased for loading more results
    'pause_time': 2.0,  # Increased pause to let results load
    'random_delay_min': 0.8,
    'random_delay_max': 2.0,
    'consecutive_same_count_limit': 8  # Stop if count doesn't change after 8 attempts
}

EXTRACTION_CONFIG = {
    'detail_timeout': 10000,
    'back_timeout': 10000,
    'min_delay': 1.0,
    'max_delay': 3.0,
    'scroll_delay_min': 0.5,
    'scroll_delay_max': 1.0
}

VALIDATION_CONFIG = {
    'website_timeout': 5,
    'default_country_code': 'US'
}

LEAD_SCORING = {
    'base_score': 50,
    'no_website': 20,
    'invalid_website': 15,
    'high_rating_threshold': 4.5,
    'high_rating_bonus': 10,
    'low_rating_threshold': 3.5,
    'low_rating_bonus': 5,
    'high_reviews_threshold': 100,
    'high_reviews_bonus': 5,
    'low_reviews_threshold': 10,
    'low_reviews_bonus': 10,
    'max_score': 100
}
