"""
Data validation service for business information.
"""

import random
from typing import Dict, List

import phonenumbers
import requests
from tqdm import tqdm

from src.utils.constants import VALIDATION_CONFIG, USER_AGENTS
from src.utils.helpers import extract_digits, normalize_url


class ValidationService:
    """Validates and enhances scraped business data."""
    
    def validate_phone_number(self, phone: str) -> tuple[str, bool]:
        """
        Validate and format phone number.
        
        Args:
            phone: Raw phone number string
            
        Returns:
            tuple: (formatted_phone, is_valid)
        """
        if phone == "N/A":
            return phone, False
        
        try:
            digits = extract_digits(phone)
            parsed_number = phonenumbers.parse(
                digits,
                VALIDATION_CONFIG['default_country_code']
            )
            
            if phonenumbers.is_valid_number(parsed_number):
                formatted = phonenumbers.format_number(
                    parsed_number,
                    phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                return formatted, True
            else:
                return phone, False
        except Exception:
            return phone, False
    
    def validate_website(self, url: str) -> bool:
        """
        Check if website URL is valid and accessible.
        
        Args:
            url: Website URL
            
        Returns:
            bool: True if website is accessible, False otherwise
        """
        if url == "N/A":
            return False
        
        normalized_url = normalize_url(url)
        
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            response = requests.head(
                normalized_url,
                timeout=VALIDATION_CONFIG['website_timeout'],
                headers=headers,
                allow_redirects=True
            )
            return response.status_code < 400
        except Exception:
            return False
    
    def validate_business(self, business_data: Dict) -> Dict:
        """
        Validate all fields of a business.
        
        Args:
            business_data: Raw business data dictionary
            
        Returns:
            dict: Validated business data with validation flags
        """
        validated = business_data.copy()
        
        validated['phone'], validated['phone_valid'] = self.validate_phone_number(
            business_data.get('phone', 'N/A')
        )
        
        validated['website_valid'] = self.validate_website(
            business_data.get('website', 'N/A')
        )
        
        return validated
    
    def validate_batch(self, businesses: List[Dict]) -> List[Dict]:
        """
        Validate a batch of businesses.
        
        Args:
            businesses: List of business data dictionaries
            
        Returns:
            list: List of validated business dictionaries
        """
        validated_businesses = []
        
        for business in tqdm(businesses, desc="Validating data"):
            validated = self.validate_business(business)
            validated_businesses.append(validated)
        
        return validated_businesses
