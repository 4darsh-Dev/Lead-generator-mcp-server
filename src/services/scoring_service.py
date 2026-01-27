"""
Lead scoring service to rank business quality.
"""

from typing import Dict

from utils.constants import LEAD_SCORING


class LeadScoringService:
    """Calculates lead quality scores for businesses."""
    
    def calculate_score(self, business: Dict) -> int:
        """
        Calculate a lead score (0-100) based on business attributes.
        
        Args:
            business: Business data dictionary
            
        Returns:
            int: Lead quality score (0-100)
        """
        score = LEAD_SCORING['base_score']
        
        score += self._score_website(business)
        score += self._score_rating(business)
        score += self._score_reviews(business)
        
        return min(score, LEAD_SCORING['max_score'])
    
    def _score_website(self, business: Dict) -> int:
        """Calculate score based on website presence."""
        if business.get('website') == "N/A":
            return LEAD_SCORING['no_website']
        elif not business.get('website_valid', False):
            return LEAD_SCORING['invalid_website']
        return 0
    
    def _score_rating(self, business: Dict) -> int:
        """Calculate score based on business rating."""
        rating_str = business.get('rating', 'N/A')
        if rating_str == "N/A":
            return 0
        
        try:
            rating = float(rating_str)
            if rating >= LEAD_SCORING['high_rating_threshold']:
                return LEAD_SCORING['high_rating_bonus']
            elif rating < LEAD_SCORING['low_rating_threshold']:
                return LEAD_SCORING['low_rating_bonus']
        except ValueError:
            pass
        
        return 0
    
    def _score_reviews(self, business: Dict) -> int:
        """Calculate score based on review count."""
        reviews_str = business.get('reviews', 'N/A')
        if reviews_str == "N/A":
            return 0
        
        try:
            reviews = int(reviews_str)
            if reviews > LEAD_SCORING['high_reviews_threshold']:
                return LEAD_SCORING['high_reviews_bonus']
            elif reviews < LEAD_SCORING['low_reviews_threshold']:
                return LEAD_SCORING['low_reviews_bonus']
        except ValueError:
            pass
        
        return 0
    
    def score_batch(self, businesses: list[Dict]) -> list[Dict]:
        """
        Calculate lead scores for a batch of businesses.
        
        Args:
            businesses: List of business dictionaries
            
        Returns:
            list: Businesses with lead_score field added
        """
        for business in businesses:
            business['lead_score'] = self.calculate_score(business)
        
        return businesses
