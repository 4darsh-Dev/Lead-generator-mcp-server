"""
Command-line interface for the Google Maps scraper.
"""

import argparse
import asyncio
import sys

from src.core.scraper import GoogleMapsScraper
from src.services.state_service import get_state_manager
from src.startup_india.constants import DEFAULT_SEARCH_URL
from src.startup_india.scraper import StartupIndiaScraper
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
        required=False,
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
    
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Disable resume functionality and start fresh'
    )
    
    parser.add_argument(
        '--show-sessions',
        action='store_true',
        help='Show active scraping sessions and exit'
    )

    parser.add_argument(
        '--startup-india',
        action='store_true',
        help='Run Startup India scaling startup scraper workflow'
    )

    parser.add_argument(
        '--search-url',
        type=str,
        default=DEFAULT_SEARCH_URL,
        help='Startup India search URL (roles=Startup and stages=scaling are enforced)'
    )

    parser.add_argument(
        '--concurrency',
        type=int,
        default=5,
        help='Concurrent profile extraction tasks for Startup India mode (default: 5)'
    )

    parser.add_argument(
        '--checkpoint-interval',
        type=int,
        default=20,
        help='Save state every N processed profiles in Startup India mode (default: 20)'
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Max retries per Startup India profile page (default: 3)'
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
    # Query not required for --show-sessions
    if args.show_sessions:
        return True
    
    if not args.startup_india and not args.query:
        logger.error("--query is required for scraping")
        return False
    
    if args.max_results < 1:
        logger.error("max-results must be at least 1")
        return False

    if args.concurrency < 1:
        logger.error("concurrency must be at least 1")
        return False

    if args.checkpoint_interval < 1:
        logger.error("checkpoint-interval must be at least 1")
        return False

    if args.max_retries < 1:
        logger.error("max-retries must be at least 1")
        return False
        
    if args.slow_mo < 0:
        logger.error("slow-mo must be non-negative")
        return False
        
    if not args.startup_india and not args.query.strip():
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
    
    # Handle show sessions command
    if args.show_sessions:
        return show_active_sessions()
    
    if not validate_arguments(args):
        return 1
    
    if args.startup_india:
        logger.info("Starting Startup India Lead Generator")
        logger.info(f"Search URL: {args.search_url}")
        logger.info(f"Max profiles: {args.max_results}")
        logger.info(f"Concurrency: {args.concurrency}")
        logger.info(f"Mode: {'Visible' if args.visible else 'Headless'}")
        logger.info(f"Resume: {'Disabled' if args.no_resume else 'Enabled'}")
    else:
        logger.info("Starting Google Maps Lead Generator")
        logger.info(f"Query: {args.query}")
        logger.info(f"Max results: {args.max_results}")
        logger.info(f"Mode: {'Visible' if args.visible else 'Headless'}")
        logger.info(f"Resume: {'Disabled' if args.no_resume else 'Enabled'}")
    
    try:
        if args.startup_india:
            scraper = StartupIndiaScraper(
                headless=not args.visible,
                slow_mo=args.slow_mo,
                concurrency=args.concurrency,
                checkpoint_interval=args.checkpoint_interval,
                max_retries=args.max_retries,
            )
            output_file = asyncio.run(
                scraper.run(
                    search_url=args.search_url,
                    output_file=args.output,
                    resume=not args.no_resume,
                    max_profiles=args.max_results,
                )
            )
        else:
            scraper = GoogleMapsScraper(
                headless=not args.visible,
                slow_mo=args.slow_mo
            )

            output_file = scraper.scrape_and_export(
                query=args.query,
                max_results=args.max_results,
                output_file=args.output,
                resume=not args.no_resume
            )
        
        if output_file:
            print(f"\n✅ Success! Data saved to: {output_file}")
            return 0
        else:
            print("\n❌ Scraping failed. Check logs for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user.")
        print("💾 Progress has been saved automatically.")
        print("🔄 Run the same command again to resume from where you left off.")
        logger.info("User interrupted scraping")
        return 1
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


def show_active_sessions() -> int:
    """
    Display active scraping sessions.
    
    Returns:
        int: Exit code (0 for success)
    """
    state_manager = get_state_manager()
    active_states = state_manager.list_active_states()
    
    if not active_states:
        print("\n📊 No active scraping sessions found.")
        return 0
    
    print(f"\n📊 Active Scraping Sessions ({len(active_states)}):")
    print("=" * 80)
    
    for i, state in enumerate(active_states, 1):
        progress = state.progress_percentage
        print(f"\n{i}. Query: {state.query}")
        print(f"   Max Results: {state.max_results}")
        print(f"   Output File: {state.output_file}")
        print(f"   Progress: {len(state.processed_indices)}/{len(state.business_urls)} ({progress:.1f}%)")
        print(f"   Successful: {state.successful_count} | Failed: {state.failed_count}")
        print(f"   Last Updated: {state.updated_at}")
    
    print("\n" + "=" * 80)
    print("\n💡 Tip: Run the same command to resume any session.")
    
    return 0


def main():
    """Entry point for the CLI."""
    sys.exit(run_cli())


if __name__ == "__main__":
    main()
