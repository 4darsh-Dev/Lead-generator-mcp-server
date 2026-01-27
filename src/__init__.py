"""
Lead Generator MCP Server Package.
Scrapes business data from Google Maps for lead generation.
"""

from .scraper_core import GoogleMapsScraper, create_scraper
from .browser import BrowserManager
from .extractor import DataExtractor, BusinessDataCollector
from .validator import DataValidator, PhoneValidator, WebsiteValidator, LeadScorer
from .exporter import DataExporter, CSVExporter
from .logger import get_logger, configure_logging

__version__ = '1.0.0'

__all__ = [
    'GoogleMapsScraper',
    'create_scraper',
    'BrowserManager',
    'DataExtractor',
    'BusinessDataCollector',
    'DataValidator',
    'PhoneValidator',
    'WebsiteValidator',
    'LeadScorer',
    'DataExporter',
    'CSVExporter',
    'get_logger',
    'configure_logging',
]
