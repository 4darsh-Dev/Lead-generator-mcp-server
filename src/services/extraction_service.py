"""
Data extraction service for scraping business information.

NOTE: This module now uses the V3 URL-based extraction approach.
For backward compatibility, DataExtractor is an alias to DataExtractorV3.

If you need the legacy implementation, it's available in the git history.
"""

# Import the new V3 extractor and expose it as DataExtractor for backward compatibility
from src.services.extraction_service_v3 import DataExtractorV3 as DataExtractor

# Re-export for backward compatibility
__all__ = ['DataExtractor']

# For users who want to explicitly use V3
DataExtractorV3 = DataExtractor
