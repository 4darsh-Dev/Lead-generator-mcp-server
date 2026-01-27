"""
Google Maps Lead Generator
A modular web scraper for extracting business leads from Google Maps.
"""

__version__ = '1.0.0'
__author__ = 'ADARSH MAURYA'

from .core.scraper import GoogleMapsScraper
from .models.business import Business
from .services import (
    BrowserManager,
    DataExtractor,
    ValidationService,
    LeadScoringService,
    ExportService
)
from .utils.logger import get_logger, configure_logging

__all__ = [
    'GoogleMapsScraper',
    'Business',
    'BrowserManager',
    'DataExtractor',
    'ValidationService',
    'LeadScoringService',
    'ExportService',
    'get_logger',
    'configure_logging',
]
