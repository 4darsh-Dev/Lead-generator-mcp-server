"""Data models for Startup India scraping pipeline."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass
class StartupListingItem:
    """Represents one startup tile from search results."""

    name: str
    stage: str
    city: str
    state: str
    industry: str
    profile_url: str
    listing_url: str


@dataclass
class StartupProfileData:
    """Represents extracted profile data for one startup."""

    name: str = ""
    stage: str = ""
    city: str = ""
    state: str = ""
    industry: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    description: str = ""
    engagement_level: str = ""
    active_since: str = ""
    profile_url: str = ""
    listing_url: str = ""
    run_id: str = ""
    scraped_at: str = ""

    def to_row(self) -> Dict[str, str]:
        """Convert model to CSV row dictionary."""
        if not self.scraped_at:
            self.scraped_at = datetime.utcnow().isoformat()
        return {
            "name": self.name,
            "stage": self.stage,
            "city": self.city,
            "state": self.state,
            "industry": self.industry,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "description": self.description,
            "engagement_level": self.engagement_level,
            "active_since": self.active_since,
            "profile_url": self.profile_url,
            "listing_url": self.listing_url,
            "run_id": self.run_id,
            "scraped_at": self.scraped_at,
        }
