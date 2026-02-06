"""
Data validation service for business information.
"""

import random
from typing import Dict, List
import urllib3

import phonenumbers
import requests
from tqdm import tqdm

from src.utils.constants import VALIDATION_CONFIG, USER_AGENTS
from src.utils.helpers import extract_digits, normalize_url

# Suppress only the single InsecureRequestWarning from urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
        if url == "N/A" or not url.strip():
            return False
        
        normalized_url = normalize_url(url)
        
        # Try HEAD request first (faster)
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            response = requests.head(
                normalized_url,
                timeout=VALIDATION_CONFIG['website_timeout'],
                headers=headers,
                allow_redirects=True,
                verify=True  # Verify SSL certificates
            )
            
            # Success codes: 200-399 (including redirects)
            if response.status_code < 400:
                return True
            
            # If HEAD returns 405 (Method Not Allowed) or 404, try GET
            if response.status_code in [404, 405, 501]:
                raise requests.exceptions.RequestException("HEAD not supported, trying GET")
                
        except Exception:
            # Fallback to GET request if HEAD fails
            try:
                response = requests.get(
                    normalized_url,
                    timeout=VALIDATION_CONFIG['website_timeout'] + 5,  # Extra time for GET
                    headers=headers,
                    allow_redirects=True,
                    verify=True,
                    stream=True  # Don't download full content
                )
                
                # Close connection immediately after getting headers
                response.close()
                
                return response.status_code < 400
                
            except Exception:
                # Last resort: try without SSL verification (some sites have cert issues)
                try:
                    response = requests.get(
                        normalized_url,
                        timeout=VALIDATION_CONFIG['website_timeout'] + 5,
                        headers=headers,
                        allow_redirects=True,
                        verify=False,  # Ignore SSL errors
                        stream=True
                    )
                    response.close()
                    return response.status_code < 400
                except Exception:
                    return False
        
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
