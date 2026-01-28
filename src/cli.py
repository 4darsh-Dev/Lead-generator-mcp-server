"""
Command-line interface for the Google Maps scraper.
"""

import argparse
import sys

from src.core.scraper import GoogleMapsScraper
from src.utils.logger import configure_logging, get_logger

logger = get_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Google Maps Business Lead Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --query "coffee shops in Seattle" --max-results 50
  %(prog)s --query "beauty salons in London" --max-results 100 --visible
  %(prog)s --query "restaurants in NYC" --output nyc_restaurants.csv
        """
    )
    
    parser.add_argument(
        '--query',
        type=str,
        required=True,
        help='Search query (e.g., "beauty salons in London")'
    )
    
    parser.add_argument(
        '--max-results',
        type=int,
        default=100,
        help='Maximum number of results to scrape (default: 100)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output CSV filename (optional, auto-generated if not provided)'
    )
    
    parser.add_argument(
        '--visible',
        action='store_true',
        help='Run browser in visible mode (default: headless)'
    )
    
    parser.add_argument(
        '--slow-mo',
        type=int,
        default=50,
        help='Delay in milliseconds between browser actions (default: 50)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> bool:
    """
    Validate parsed arguments.
    
    Args:
        args: Parsed arguments
        
    Returns:
        bool: True if arguments are valid
    """
    if args.max_results < 1:
        logger.error("max-results must be at least 1")
        return False
        
    if args.slow_mo < 0:
        logger.error("slow-mo must be non-negative")
        return False
        
    if not args.query.strip():
        logger.error("query cannot be empty")
        return False
        
    return True


def run_cli() -> int:
    """
    Run the command-line interface.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    args = parse_arguments()
    
    configure_logging(args.log_level)
    
    if not validate_arguments(args):
        return 1
    
    logger.info("Starting Google Maps Lead Generator")
    logger.info(f"Query: {args.query}")
    logger.info(f"Max results: {args.max_results}")
    logger.info(f"Mode: {'Visible' if args.visible else 'Headless'}")
    
    try:
        scraper = GoogleMapsScraper(
            headless=not args.visible,
            slow_mo=args.slow_mo
        )
        
        output_file = scraper.scrape_and_export(
            query=args.query,
            max_results=args.max_results,
            output_file=args.output
        )
        
        if output_file:
            print(f"\nSuccess! Data saved to: {output_file}")
            return 0
        else:
            print("\nScraping failed. Check logs for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user.")
        logger.info("User interrupted scraping")
        return 1
        
    except Exception as e:
        print(f"\nError: {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


def main():
    """Entry point for the CLI."""
    sys.exit(run_cli())


if __name__ == "__main__":
    main()
