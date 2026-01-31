"""
Export service for saving data to various formats.
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExportService:
    """Handles exporting business data to various formats with resume support."""
    
    def __init__(self):
        """Initialize export service."""
        self.csv_writer = None
        self.csv_file = None
        self.csv_filename = None
        self.headers_written = False
        self.fieldnames = None
    
    @staticmethod
    def export_to_csv(data: List[Dict], filename: Optional[str] = None) -> str:
        """
        Export business data to CSV file.
        
        Args:
            data: List of business dictionaries
            filename: Output filename (auto-generated if None)
            
        Returns:
            str: Path to the created CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"business_leads_{timestamp}.csv"
        
        df = pd.DataFrame(data)
        
        columns_order = [
            'name', 'category', 'address', 'phone', 'phone_valid',
            'website', 'website_valid', 'rating', 'reviews', 'lead_score'
        ]
        
        columns_order = [col for col in columns_order if col in df.columns]
        
        for col in df.columns:
            if col not in columns_order:
                columns_order.append(col)
        
        df = df.sort_values(by='lead_score', ascending=False)
        
        df.to_csv(filename, index=False, columns=columns_order)
        
        return filename
    
    @staticmethod
    def export_to_json(data: List[Dict], filename: Optional[str] = None) -> str:
        """
        Export business data to JSON file.
        
        Args:
            data: List of business dictionaries
            filename: Output filename (auto-generated if None)
            
        Returns:
            str: Path to the created JSON file
        """
        import json
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"business_leads_{timestamp}.json"
        
        sorted_data = sorted(data, key=lambda x: x.get('lead_score', 0), reverse=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def init_incremental_csv(self, filename: Optional[str] = None, resume: bool = False) -> str:
        """
        Initialize incremental CSV writing mode with resume support.
        
        Args:
            filename: Output filename (auto-generated if None)
            resume: If True, append to existing file; if False, create new
            
        Returns:
            str: Path to the CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"business_leads_{timestamp}.csv"
        
        self.csv_filename = filename
        
        # Check if file exists and we're resuming
        file_exists = Path(filename).exists()
        
        if resume and file_exists:
            logger.info(f"Resuming: appending to existing file {filename}")
            # Open in append mode
            self.csv_file = open(filename, 'a', newline='', encoding='utf-8')
            self.headers_written = True  # Headers already exist
            
            # Read existing file to get fieldnames
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.fieldnames = reader.fieldnames
                    logger.debug(f"Loaded existing fieldnames: {self.fieldnames}")
            except Exception as e:
                logger.error(f"Failed to read existing CSV headers: {e}")
                raise
        else:
            if file_exists:
                logger.warning(f"File {filename} exists but not resuming. It will be overwritten.")
            logger.info(f"Creating new file: {filename}")
            # Open in write mode
            self.csv_file = open(filename, 'w', newline='', encoding='utf-8')
            self.headers_written = False
            self.fieldnames = None
        
        return filename
    
    def load_existing_business_names(self, filename: str) -> Set[str]:
        """
        Load business names from existing CSV file to avoid duplicates.
        
        Args:
            filename: CSV filename to read
            
        Returns:
            Set of business names already in the file
        """
        existing_names = set()
        
        if not Path(filename).exists():
            return existing_names
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get('name', '').strip()
                    if name and name != 'N/A':
                        existing_names.add(name.lower())
            
            logger.info(f"Loaded {len(existing_names)} existing business names from {filename}")
        except Exception as e:
            logger.warning(f"Failed to load existing businesses: {e}")
        
        return existing_names
        
        return filename
    
    def append_to_csv(self, business: Dict) -> None:
        """
        Append a single business record to the CSV file.
        
        Args:
            business: Business data dictionary
        """
        if not self.csv_file:
            raise ValueError("CSV file not initialized. Call init_incremental_csv() first.")
        
        if not self.headers_written:
            # Define column order
            columns_order = [
                'name', 'category', 'address', 'phone', 'phone_valid',
                'website', 'website_valid', 'rating', 'reviews', 'lead_score'
            ]
            
            # Add any additional columns from business data
            for key in business.keys():
                if key not in columns_order:
                    columns_order.append(key)
            
            self.fieldnames = columns_order
            self.csv_writer = csv.DictWriter(
                self.csv_file, 
                fieldnames=self.fieldnames,
                extrasaction='ignore'
            )
            self.csv_writer.writeheader()
            self.csv_file.flush()
            self.headers_written = True
        else:
            # Resuming mode - create writer with existing fieldnames
            if self.csv_writer is None and self.fieldnames:
                self.csv_writer = csv.DictWriter(
                    self.csv_file,
                    fieldnames=self.fieldnames,
                    extrasaction='ignore'
                )
        
        # Write the business data
        self.csv_writer.writerow(business)
        self.csv_file.flush()  # Flush to disk immediately
        os.fsync(self.csv_file.fileno())  # Force write to disk
    
    def close_csv(self) -> None:
        """Close the CSV file."""
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
            self.headers_written = False
