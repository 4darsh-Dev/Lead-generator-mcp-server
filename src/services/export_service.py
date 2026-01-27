"""
Export service for saving data to various formats.
"""

from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd


class ExportService:
    """Handles exporting business data to various formats."""
    
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
