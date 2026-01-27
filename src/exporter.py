"""
Data export module.
Handles exporting scraped data to various formats.
"""

from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd

from .config import EXPORT_CONFIG
from .logger import get_logger

logger = get_logger(__name__)


class CSVExporter:
    """Exports business data to CSV format."""
    
    @staticmethod
    def export(data: List[Dict], filename: Optional[str] = None) -> str:
        """
        Export business data to a CSV file.
        
        Args:
            data: List of business data dictionaries
            filename: Output filename (optional, auto-generated if not provided)
            
        Returns:
            str: Path to the exported CSV file
        """
        if not data:
            logger.warning("No data to export")
            return None
            
        if not filename:
            filename = CSVExporter._generate_filename()
        
        logger.info(f"Exporting {len(data)} records to {filename}")
        
        df = pd.DataFrame(data)
        df = CSVExporter._prepare_dataframe(df)
        
        df.to_csv(filename, index=False)
        logger.info(f"Data successfully exported to {filename}")
        
        return filename
        
    @staticmethod
    def _generate_filename() -> str:
        """Generate a timestamped filename."""
        timestamp = datetime.now().strftime(EXPORT_CONFIG['timestamp_format'])
        pattern = EXPORT_CONFIG['default_filename_pattern']
        return pattern.format(timestamp=timestamp)
        
    @staticmethod
    def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare dataframe for export (reorder columns, sort).
        
        Args:
            df: Input dataframe
            
        Returns:
            pd.DataFrame: Prepared dataframe
        """
        column_order = EXPORT_CONFIG['column_order'].copy()
        
        column_order = [col for col in column_order if col in df.columns]
        
        for col in df.columns:
            if col not in column_order:
                column_order.append(col)
        
        df = df[column_order]
        
        sort_by = EXPORT_CONFIG['sort_by']
        if sort_by in df.columns:
            ascending = EXPORT_CONFIG['sort_ascending']
            df = df.sort_values(by=sort_by, ascending=ascending)
        
        return df


class DataExporter:
    """Main exporter class supporting multiple formats."""
    
    def __init__(self):
        """Initialize data exporter."""
        self.csv_exporter = CSVExporter()
        
    def export_csv(self, data: List[Dict], filename: Optional[str] = None) -> str:
        """
        Export data to CSV format.
        
        Args:
            data: Business data to export
            filename: Output filename (optional)
            
        Returns:
            str: Path to exported file
        """
        return self.csv_exporter.export(data, filename)
        
    def export(self, data: List[Dict], filename: Optional[str] = None, 
               format: str = 'csv') -> str:
        """
        Export data to specified format.
        
        Args:
            data: Business data to export
            filename: Output filename (optional)
            format: Export format ('csv' currently supported)
            
        Returns:
            str: Path to exported file
        """
        if format.lower() == 'csv':
            return self.export_csv(data, filename)
        else:
            raise ValueError(f"Unsupported export format: {format}")
