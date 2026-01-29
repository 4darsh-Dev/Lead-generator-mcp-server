"""
Test script to compare extraction solutions and identify the best approach.
Run this to validate which solution works best for your use case.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.browser_service import BrowserManager
from src.services.extraction_service import DataExtractor  # Original
from src.services.extraction_service_v2 import DataExtractorV2  # Locators
from src.services.extraction_service_v3 import DataExtractorV3  # URL-based
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_extractor(extractor_class, solution_name: str, max_results: int = 30):
    """
    Test an extraction solution.
    
    Args:
        extractor_class: The extractor class to test
        solution_name: Name of the solution being tested
        max_results: Number of results to extract
        
    Returns:
        dict: Test results and metrics
    """
    print(f"\n{'='*80}")
    print(f"🧪 Testing: {solution_name}")
    print('='*80)
    
    browser = BrowserManager(headless=False, slow_mo=50)
    
    try:
        # Start browser
        print("🚀 Starting browser...")
        browser.start()
        
        # Navigate to search
        search_query = "interior designers in Delhi"
        print(f"🔍 Searching for: {search_query}")
        
        if not browser.navigate_to_search(search_query):
            print("❌ Failed to navigate to search results")
            return None
        
        # Scroll to load results
        print(f"📜 Loading {max_results} results...")
        loaded_count = browser.scroll_results_container(max_results)
        print(f"✅ Loaded {loaded_count} results")
        
        # Initialize extractor
        extractor = extractor_class(browser)
        
        # Track results
        results = []
        start_time = time.time()
        
        def callback(data):
            results.append(data)
            print(f"  ✅ [{len(results)}] {data.get('name', 'N/A')[:50]}")
        
        # Run extraction
        print(f"\n🔧 Extracting data from {max_results} listings...")
        print("-" * 80)
        
        extracted_count = extractor.extract_from_listings_incremental(
            max_results=max_results,
            callback=callback
        )
        
        elapsed_time = time.time() - start_time
        
        # Calculate metrics
        success_rate = (extracted_count / max_results * 100) if max_results > 0 else 0
        avg_time_per_listing = elapsed_time / extracted_count if extracted_count > 0 else 0
        
        metrics = {
            'solution': solution_name,
            'attempted': max_results,
            'successful': extracted_count,
            'failed': max_results - extracted_count,
            'success_rate': success_rate,
            'total_time': elapsed_time,
            'avg_time_per_listing': avg_time_per_listing
        }
        
        # Print summary
        print("\n" + "="*80)
        print("📊 Test Results")
        print("="*80)
        print(f"✅ Successful extractions: {extracted_count}/{max_results}")
        print(f"❌ Failed extractions: {max_results - extracted_count}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        print(f"⏱️  Total time: {elapsed_time:.1f}s")
        print(f"⚡ Avg time per listing: {avg_time_per_listing:.2f}s")
        print("="*80)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Test failed for {solution_name}: {e}", exc_info=True)
        return None
        
    finally:
        print("\n🔒 Closing browser...")
        browser.close()


def compare_solutions():
    """Run comparison tests on all solutions."""
    print("\n" + "="*80)
    print("🔬 EXTRACTION SOLUTIONS COMPARISON TEST")
    print("="*80)
    print("\nThis test will compare three different extraction approaches:")
    print("  1. Original (Current implementation with enhancements)")
    print("  2. Playwright Locators (Modern auto-retrying approach)")
    print("  3. URL-Based Navigation (Most reliable)")
    print("\nEach solution will extract 30 business listings.")
    print("="*80)
    
    input("\nPress Enter to start testing...")
    
    test_cases = [
        # (DataExtractor, "Original Implementation"),  # Uncomment to test original
        (DataExtractorV2, "Solution 1: Playwright Locators (Recommended)"),
        (DataExtractorV3, "Solution 2: URL-Based Navigation (Most Reliable)"),
    ]
    
    all_metrics = []
    
    for extractor_class, name in test_cases:
        metrics = test_extractor(extractor_class, name, max_results=30)
        if metrics:
            all_metrics.append(metrics)
        
        # Wait between tests
        if extractor_class != test_cases[-1][0]:
            print("\n⏸️  Waiting 5 seconds before next test...")
            time.sleep(5)
    
    # Print comparison
    if len(all_metrics) > 1:
        print("\n" + "="*80)
        print("📊 FINAL COMPARISON")
        print("="*80)
        print(f"{'Solution':<50} {'Success Rate':<15} {'Avg Time':<10}")
        print("-"*80)
        
        for metrics in all_metrics:
            print(f"{metrics['solution']:<50} "
                  f"{metrics['success_rate']:>6.1f}% "
                  f"({metrics['successful']}/{metrics['attempted']})   "
                  f"{metrics['avg_time_per_listing']:>6.2f}s")
        
        print("="*80)
        
        # Recommend best solution
        best_solution = max(all_metrics, key=lambda x: (x['success_rate'], -x['avg_time_per_listing']))
        print(f"\n🏆 Best Solution: {best_solution['solution']}")
        print(f"   ✅ Success Rate: {best_solution['success_rate']:.1f}%")
        print(f"   ⚡ Speed: {best_solution['avg_time_per_listing']:.2f}s per listing")
        print("="*80)


def quick_test():
    """Quick test with just 10 results for rapid validation."""
    print("\n" + "="*80)
    print("⚡ QUICK VALIDATION TEST (10 listings)")
    print("="*80)
    
    # Test URL-based solution (most reliable)
    metrics = test_extractor(
        DataExtractorV3, 
        "URL-Based Navigation (Quick Test)", 
        max_results=10
    )
    
    if metrics and metrics['success_rate'] >= 80:
        print("\n✅ Quick test PASSED! Solution is working well.")
    else:
        print("\n⚠️  Quick test shows issues. Check logs for details.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test extraction solutions')
    parser.add_argument(
        '--mode',
        choices=['quick', 'full', 'compare'],
        default='quick',
        help='Test mode: quick (10 results), full (30 results), compare (all solutions)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'quick':
            quick_test()
        elif args.mode == 'full':
            test_extractor(DataExtractorV3, "URL-Based Navigation", max_results=30)
        elif args.mode == 'compare':
            compare_solutions()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
