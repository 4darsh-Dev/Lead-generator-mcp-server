"""
Configuration module for the Lead Generator scraper.
Contains all configuration constants and settings.
"""

# Browser Configuration
BROWSER_CONFIG = {
    'headless': True,
    'slow_mo': 50,
    'viewport': {'width': 1366, 'height': 768}
}

# User agents for rotation to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
]

# HTTP Headers for anti-detection
HTTP_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

# Scraping Configuration
SCRAPING_CONFIG = {
    'max_scroll_attempts': 20,
    'scroll_pause_base': 1.5,
    'scroll_pause_variation': (0.5, 1.5),
    'click_delay': (0.5, 1.0),
    'page_load_delay': (1.0, 2.0),
    'action_delay': (1.0, 3.0),
    'page_load_timeout': 10000,
    'search_timeout': 20000
}

# Google Maps Selectors
SELECTORS = {
    'results_container': 'div[role="feed"]',
    'business_link': 'a.hfpxzc',
    'phone_button': 'button[aria-label^="Phone:"]',
    'address_button': 'button[aria-label^="Address:"]',
    'website_link': 'a[aria-label^="Website:"]',
    'business_name': 'h1.DUwDvf',
    'category': 'button[jsaction="pane.wfvdle17.category"], button[jsaction*="category"]',
    'rating': 'span[aria-label*="stars"][role="img"], span[aria-label*="stars"]',
    'reviews': 'button[jsaction="pane.wfvdle13.reviewChart.moreReviews"], button[jsaction*="moreReviews"]'
}

# Lead Scoring Configuration
LEAD_SCORING = {
    'base_score': 50,
    'no_website_bonus': 20,
    'invalid_website_bonus': 15,
    'high_rating_bonus': 10,  # For rating >= 4.5
    'low_rating_bonus': 5,    # For rating < 3.5
    'high_reviews_bonus': 5,  # For reviews > 100
    'low_reviews_bonus': 10,  # For reviews < 10
    'high_rating_threshold': 4.5,
    'low_rating_threshold': 3.5,
    'high_reviews_threshold': 100,
    'low_reviews_threshold': 10,
    'max_score': 100
}

# Data Validation Configuration
VALIDATION_CONFIG = {
    'default_country_code': 'US',
    'website_timeout': 5,
    'website_max_redirects': True
}

# Export Configuration
EXPORT_CONFIG = {
    'default_filename_pattern': 'business_leads_{timestamp}.csv',
    'timestamp_format': '%Y%m%d_%H%M%S',
    'column_order': [
        'name', 'category', 'address', 'phone', 'phone_valid',
        'website', 'website_valid', 'rating', 'reviews', 'lead_score'
    ],
    'sort_by': 'lead_score',
    'sort_ascending': False
}

# Google Maps Configuration
GOOGLE_MAPS_CONFIG = {
    'base_url': 'https://www.google.co.in/maps/search/{query}',
    'url_encoding': True
}
