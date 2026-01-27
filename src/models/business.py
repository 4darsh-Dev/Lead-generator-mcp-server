"""
Business data model.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Business:
    """Represents a business entity with all scraped information."""
    
    name: str
    category: str = "N/A"
    address: str = "N/A"
    phone: str = "N/A"
    website: str = "N/A"
    rating: str = "N/A"
    reviews: str = "N/A"
    phone_valid: bool = False
    website_valid: bool = False
    lead_score: int = 0
    
    def to_dict(self) -> dict:
        """Convert business to dictionary."""
        return {
            'name': self.name,
            'category': self.category,
            'address': self.address,
            'phone': self.phone,
            'phone_valid': self.phone_valid,
            'website': self.website,
            'website_valid': self.website_valid,
            'rating': self.rating,
            'reviews': self.reviews,
            'lead_score': self.lead_score
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Business':
        """Create Business instance from dictionary."""
        return Business(
            name=data.get('name', 'N/A'),
            category=data.get('category', 'N/A'),
            address=data.get('address', 'N/A'),
            phone=data.get('phone', 'N/A'),
            website=data.get('website', 'N/A'),
            rating=data.get('rating', 'N/A'),
            reviews=data.get('reviews', 'N/A'),
            phone_valid=data.get('phone_valid', False),
            website_valid=data.get('website_valid', False),
            lead_score=data.get('lead_score', 0)
        )
