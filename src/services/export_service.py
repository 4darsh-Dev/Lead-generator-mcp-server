"""
Export service for saving data to various formats.
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd


class ExportService:
    """Handles exporting business data to various formats."""
    
    def __init__(self):
        """Initialize export service."""
        self.csv_writer = None
        self.csv_file = None
        self.csv_filename = None
        self.headers_written = False
    
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
    
    def init_incremental_csv(self, filename: Optional[str] = None) -> str:
        """
        Initialize incremental CSV writing mode.
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            str: Path to the CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"business_leads_{timestamp}.csv"
        
        self.csv_filename = filename
        self.csv_file = open(filename, 'w', newline='', encoding='utf-8')
        self.headers_written = False
        
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
            
            self.csv_writer = csv.DictWriter(
                self.csv_file, 
                fieldnames=columns_order,
                extrasaction='ignore'
            )
            self.csv_writer.writeheader()
            self.csv_file.flush()
            self.headers_written = True
        
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
