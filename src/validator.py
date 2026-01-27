"""
Data validation module.
Validates and enriches scraped business data.
"""

import random
import re
from typing import Dict, List

import phonenumbers
import requests
from tqdm import tqdm

from .config import USER_AGENTS, VALIDATION_CONFIG, LEAD_SCORING
from .logger import get_logger

logger = get_logger(__name__)


class PhoneValidator:
    """Validates and formats phone numbers."""
    
    def __init__(self, default_country: str = None):
        """
        Initialize phone validator.
        
        Args:
            default_country: Default country code for parsing (e.g., 'US')
        """
        self.default_country = default_country or VALIDATION_CONFIG['default_country_code']
        
    def validate(self, phone: str) -> tuple[str, bool]:
        """
        Validate and format a phone number.
        
        Args:
            phone: Phone number string to validate
            
        Returns:
            tuple: (formatted_phone, is_valid)
        """
        if phone == "N/A":
            return phone, False
            
        try:
            digits = re.sub(r'\D', '', phone)
            parsed_number = phonenumbers.parse(digits, self.default_country)
            
            if phonenumbers.is_valid_number(parsed_number):
                formatted = phonenumbers.format_number(
                    parsed_number, 
                    phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                return formatted, True
            else:
                return phone, False
        except Exception as e:
            logger.debug(f"Phone validation error: {e}")
            return phone, False


class WebsiteValidator:
    """Validates website URLs."""
    
    @staticmethod
    def validate(url: str) -> bool:
        """
        Check if a website URL is valid and accessible.
        
        Args:
            url: Website URL to validate
            
        Returns:
            bool: True if valid and accessible, False otherwise
        """
        if url == "N/A":
            return False
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            timeout = VALIDATION_CONFIG['website_timeout']
            allow_redirects = VALIDATION_CONFIG['website_max_redirects']
            
            response = requests.head(
                url, 
                timeout=timeout, 
                headers=headers, 
                allow_redirects=allow_redirects
            )
            return response.status_code < 400
        except Exception as e:
            logger.debug(f"Website validation error for {url}: {e}")
            return False


class LeadScorer:
    """Calculates lead quality scores."""
    
    @staticmethod
    def calculate_score(business: Dict) -> int:
        """
        Calculate a lead score (0-100) based on business attributes.
        
        Args:
            business: Dictionary containing business data
            
        Returns:
            int: Lead score between 0 and 100
        """
        score = LEAD_SCORING['base_score']
        
        score += LeadScorer._score_website(business)
        score += LeadScorer._score_rating(business)
        score += LeadScorer._score_reviews(business)
        
        return min(score, LEAD_SCORING['max_score'])
        
    @staticmethod
    def _score_website(business: Dict) -> int:
        """Score based on website presence and validity."""
        if business.get('website') == "N/A":
            return LEAD_SCORING['no_website_bonus']
        elif not business.get('website_valid', False):
            return LEAD_SCORING['invalid_website_bonus']
        return 0
        
    @staticmethod
    def _score_rating(business: Dict) -> int:
        """Score based on business rating."""
        rating_str = business.get('rating', 'N/A')
        if rating_str == 'N/A':
            return 0
            
        try:
            rating = float(rating_str)
            if rating >= LEAD_SCORING['high_rating_threshold']:
                return LEAD_SCORING['high_rating_bonus']
            elif rating < LEAD_SCORING['low_rating_threshold']:
                return LEAD_SCORING['low_rating_bonus']
        except (ValueError, TypeError):
            pass
        return 0
        
    @staticmethod
    def _score_reviews(business: Dict) -> int:
        """Score based on number of reviews."""
        reviews_str = business.get('reviews', 'N/A')
        if reviews_str == 'N/A':
            return 0
            
        try:
            reviews = int(reviews_str)
            if reviews > LEAD_SCORING['high_reviews_threshold']:
                return LEAD_SCORING['high_reviews_bonus']
            elif reviews < LEAD_SCORING['low_reviews_threshold']:
                return LEAD_SCORING['low_reviews_bonus']
        except (ValueError, TypeError):
            pass
        return 0


class DataValidator:
    """Validates and enriches scraped business data."""
    
    def __init__(self):
        """Initialize data validator with component validators."""
        self.phone_validator = PhoneValidator()
        self.website_validator = WebsiteValidator()
        self.lead_scorer = LeadScorer()
        
    def validate_batch(self, data: List[Dict]) -> List[Dict]:
        """
        Validate and enhance a batch of business data.
        
        Args:
            data: List of business data dictionaries
            
        Returns:
            list: Validated and enhanced business data
        """
        logger.info(f"Validating {len(data)} business records...")
        validated_data = []
        
        for business in tqdm(data, desc="Validating data"):
            validated_business = self.validate_single(business)
            validated_data.append(validated_business)
        
        logger.info(f"Validation complete: {len(validated_data)} records processed")
        return validated_data
        
    def validate_single(self, business: Dict) -> Dict:
        """
        Validate and enhance a single business record.
        
        Args:
            business: Business data dictionary
            
        Returns:
            dict: Validated and enhanced business data
        """
        phone = business.get('phone', 'N/A')
        business['phone'], business['phone_valid'] = self.phone_validator.validate(phone)
        
        website = business.get('website', 'N/A')
        business['website_valid'] = self.website_validator.validate(website)
        
        business['lead_score'] = self.lead_scorer.calculate_score(business)
        
        return business
