"""Constants for Startup India scraping pipeline."""

from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

BASE_DOMAIN = "https://www.startupindia.gov.in"
DEFAULT_SEARCH_PATH = "/content/sih/en/search.html"
DEFAULT_SEARCH_URL = (
    "https://www.startupindia.gov.in/content/sih/en/search.html"
    "?stages=scaling&roles=Startup&page=1"
)

RESULT_CARD_SELECTOR = ".search-card.new-eco-card"
RESULT_TILE_SELECTOR = ".search-card.new-eco-card"
RESULT_LINK_SELECTOR = "a.img-wrap"
LOAD_MORE_SELECTOR = "#loadmoreicon"
NO_MORE_SELECTOR = "#nomore"

PROFILE_NAME_SELECTOR = ".company-name .pStartupName"
PROFILE_PHONE_SELECTOR = ".company-name .telephone"
PROFILE_EMAIL_SELECTOR = ".company-name .mail"
PROFILE_WEBSITE_SELECTOR = ".company-name a.website"
PROFILE_DESCRIPTION_SELECTOR = "div.read.margin-t20"
PROFILE_STAGE_SELECTOR = ".events-details .highlighted-text"
PROFILE_LOCATION_SELECTOR = ".events-details li.location span"
PROFILE_INDUSTRY_SELECTOR = ".down-dept .dept"
PROFILE_ENGAGEMENT_SELECTOR = ".company-name .orglevel strong"
PROFILE_ACTIVE_SINCE_SELECTOR = ".company-name .active-since strong"

LISTING_PAGE_TIMEOUT_MS = 60000
PROFILE_PAGE_TIMEOUT_MS = 45000
DISCOVERY_IDLE_ROUNDS = 5
DEFAULT_CONCURRENCY = 5
DEFAULT_CHECKPOINT_INTERVAL = 20
DEFAULT_MAX_RETRIES = 3


def enforce_startup_scaling_filters(search_url: str) -> str:
    """Ensure search URL always keeps roles=Startup and stages=scaling."""
    parsed = urlparse(search_url)
    query = parse_qs(parsed.query)
    query["roles"] = ["Startup"]
    query["stages"] = ["scaling"]
    if "page" not in query:
        query["page"] = ["1"]
    encoded_query = urlencode(query, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, encoded_query, parsed.fragment))
