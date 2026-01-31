#!/usr/bin/env python3
"""
Test script for resume functionality.
Tests state management, resume capability, and duplicate prevention.
"""

import os
import sys
import csv
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.state_service import StateManager, ScrapingState
from src.services.export_service import ExportService
from src.utils.logger import configure_logging, get_logger

configure_logging('INFO')
logger = get_logger(__name__)


def test_state_manager():
    """Test StateManager functionality."""
    print("\n" + "="*80)
    print("TEST 1: State Manager")
    print("="*80)
    
    state_manager = StateManager()
    
    # Create test state
    test_urls = [f"https://maps.google.com/place/{i}" for i in range(10)]
    query = "Test Query"
    max_results = 10
    
    print(f"✓ Creating new state for: {query}")
    state = state_manager.create_new_state(
        query=query,
        max_results=max_results,
        output_file="test_output.csv",
        business_urls=test_urls
    )
    
    assert len(state.business_urls) == 10
    assert state.query == query
    print(f"  State created with {len(state.business_urls)} URLs")
    
    # Mark some as processed
    print("✓ Marking URLs 0, 1, 2 as processed")
    state.mark_processed(0)
    state.mark_processed(1)
    state.mark_processed(2)
    state_manager.save_state(state)
    
    assert len(state.processed_indices) == 3
    print(f"  Progress: {state.progress_percentage:.1f}%")
    
    # Load state
    print("✓ Loading state from disk")
    loaded_state = state_manager.load_state(query, max_results)
    
    assert loaded_state is not None
    assert len(loaded_state.processed_indices) == 3
    assert loaded_state.query == query
    print(f"  Loaded state with {len(loaded_state.processed_indices)} processed URLs")
    
    # Get pending URLs
    pending = loaded_state.get_pending_urls()
    print(f"✓ Pending URLs: {len(pending)}")
    assert len(pending) == 7
    
    # Mark completed
    print("✓ Marking session as completed")
    state_manager.mark_completed(loaded_state)
    
    # Try to load completed state (should return None)
    completed_state = state_manager.load_state(query, max_results)
    assert completed_state is None
    print("  Completed state correctly returns None")
    
    # Cleanup
    state_manager.delete_state(query, max_results)
    print("✓ Cleanup completed")
    
    print("\n✅ State Manager Test PASSED\n")


def test_export_service():
    """Test ExportService resume functionality."""
    print("="*80)
    print("TEST 2: Export Service Resume")
    print("="*80)
    
    export_service = ExportService()
    test_file = "test_resume_export.csv"
    
    # Clean up if exists
    if Path(test_file).exists():
        Path(test_file).unlink()
    
    # Create initial file
    print(f"✓ Creating initial CSV: {test_file}")
    export_service.init_incremental_csv(test_file, resume=False)
    
    business1 = {
        'name': 'Business One',
        'category': 'Category A',
        'address': '123 Street',
        'phone': '1234567890',
        'phone_valid': 'Yes',
        'website': 'https://example.com',
        'website_valid': 'Yes',
        'rating': '4.5',
        'reviews': '100',
        'lead_score': 85
    }
    
    business2 = {
        'name': 'Business Two',
        'category': 'Category B',
        'address': '456 Avenue',
        'phone': '0987654321',
        'phone_valid': 'Yes',
        'website': 'https://example2.com',
        'website_valid': 'Yes',
        'rating': '4.0',
        'reviews': '50',
        'lead_score': 75
    }
    
    export_service.append_to_csv(business1)
    export_service.append_to_csv(business2)
    export_service.close_csv()
    
    print(f"  Added 2 businesses to CSV")
    
    # Verify file
    with open(test_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    print(f"  Verified: {len(rows)} rows in CSV")
    
    # Resume mode
    print("✓ Reopening in resume mode")
    export_service2 = ExportService()
    export_service2.init_incremental_csv(test_file, resume=True)
    
    # Load existing names
    existing_names = export_service2.load_existing_business_names(test_file)
    print(f"  Loaded {len(existing_names)} existing business names")
    assert 'business one' in existing_names
    assert 'business two' in existing_names
    
    business3 = {
        'name': 'Business Three',
        'category': 'Category C',
        'address': '789 Road',
        'phone': '5555555555',
        'phone_valid': 'No',
        'website': 'N/A',
        'website_valid': 'No',
        'rating': '3.5',
        'reviews': '25',
        'lead_score': 60
    }
    
    export_service2.append_to_csv(business3)
    export_service2.close_csv()
    
    print("  Appended 1 more business")
    
    # Verify total
    with open(test_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 3
    print(f"  Verified: {len(rows)} total rows in CSV")
    
    # Cleanup
    Path(test_file).unlink()
    print("✓ Cleanup completed")
    
    print("\n✅ Export Service Resume Test PASSED\n")


def test_integration():
    """Test integration of state management with export service."""
    print("="*80)
    print("TEST 3: Integration Test")
    print("="*80)
    
    state_manager = StateManager()
    export_service = ExportService()
    
    test_file = "test_integration.csv"
    query = "Integration Test Query"
    max_results = 5
    
    # Clean up
    if Path(test_file).exists():
        Path(test_file).unlink()
    state_manager.delete_state(query, max_results)
    
    # Simulate scraping session
    print(f"✓ Simulating scraping session for: {query}")
    
    business_urls = [f"https://maps.google.com/place/{i}" for i in range(5)]
    state = state_manager.create_new_state(
        query=query,
        max_results=max_results,
        output_file=test_file,
        business_urls=business_urls
    )
    
    export_service.init_incremental_csv(test_file, resume=False)
    
    # Process 3 businesses
    for i in range(3):
        business = {
            'name': f'Business {i+1}',
            'category': 'Test Category',
            'address': f'{i+1} Test St',
            'phone': f'123456789{i}',
            'phone_valid': 'Yes',
            'website': f'https://test{i+1}.com',
            'website_valid': 'Yes',
            'rating': '4.0',
            'reviews': '10',
            'lead_score': 70
        }
        export_service.append_to_csv(business)
        state.mark_processed(i)
        state_manager.save_state(state)
    
    export_service.close_csv()
    print(f"  Processed 3 businesses, saved to {test_file}")
    print(f"  Progress: {state.progress_percentage:.1f}%")
    
    # Simulate resume
    print("✓ Simulating resume...")
    
    loaded_state = state_manager.load_state(query, max_results)
    assert loaded_state is not None
    assert len(loaded_state.processed_indices) == 3
    print(f"  State loaded: {len(loaded_state.processed_indices)} already processed")
    
    export_service2 = ExportService()
    export_service2.init_incremental_csv(test_file, resume=True)
    existing_names = export_service2.load_existing_business_names(test_file)
    
    assert len(existing_names) == 3
    print(f"  Loaded {len(existing_names)} existing names")
    
    # Process remaining 2
    pending = loaded_state.get_pending_urls()
    for i, url in pending:
        # Check not already processed
        if f'business {i+1}'.lower() not in existing_names:
            business = {
                'name': f'Business {i+1}',
                'category': 'Test Category',
                'address': f'{i+1} Test St',
                'phone': f'123456789{i}',
                'phone_valid': 'Yes',
                'website': f'https://test{i+1}.com',
                'website_valid': 'Yes',
                'rating': '4.0',
                'reviews': '10',
                'lead_score': 70
            }
            export_service2.append_to_csv(business)
            loaded_state.mark_processed(i)
            state_manager.save_state(loaded_state)
    
    export_service2.close_csv()
    print("  Processed remaining 2 businesses")
    
    # Verify final count
    with open(test_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 5
    print(f"  Verified: {len(rows)} total businesses in file")
    
    # Mark completed
    state_manager.mark_completed(loaded_state)
    print("  Session marked as completed")
    
    # Cleanup
    Path(test_file).unlink()
    state_manager.delete_state(query, max_results)
    print("✓ Cleanup completed")
    
    print("\n✅ Integration Test PASSED\n")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("RESUME FUNCTIONALITY TEST SUITE")
    print("="*80)
    
    try:
        test_state_manager()
        test_export_service()
        test_integration()
        
        print("="*80)
        print("🎉 ALL TESTS PASSED!")
        print("="*80)
        print("\n✅ Resume functionality is working correctly")
        print("✅ State management is operational")
        print("✅ Duplicate prevention is functioning")
        print("✅ Integration between components is solid\n")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
