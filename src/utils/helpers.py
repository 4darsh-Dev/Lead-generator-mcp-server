"""
Helper utility functions.
"""

import random
import re
import time
from typing import Optional


def add_random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """Add a random delay to simulate human behavior."""
    time.sleep(random.uniform(min_seconds, max_seconds))


def clean_text(text: str) -> str:
    """Clean and normalize text by removing extra whitespace."""
    return re.sub(r'\s{2,}', ' ', text).strip()


def extract_number_from_text(text: str) -> Optional[str]:
    """Extract numeric value from text string."""
    match = re.search(r'(\d+(?:,\d+)*)', text)
    if match:
        return match.group(1).replace(',', '')
    return None


def extract_rating_from_label(aria_label: str) -> Optional[str]:
    """Extract rating value from aria-label text."""
    if not aria_label:
        return None
    match = re.search(r'(\d+\.\d+)', aria_label)
    if match:
        return match.group(1)
    return None


def encode_search_query(query: str) -> str:
    """Encode search query for URL."""
    return query.replace(' ', '+')


def extract_digits(text: str) -> str:
    """Extract only digits from text."""
    return re.sub(r'\D', '', text)


def is_valid_url(url: str) -> bool:
    """Check if URL has valid format."""
    return url.startswith(('http://', 'https://'))


def normalize_url(url: str) -> str:
    """Normalize URL by adding https:// if missing."""
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    return url
