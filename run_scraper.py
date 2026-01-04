#!/usr/bin/env python3
"""
Main script to run the competitive intelligence scraper.
"""
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import Config
from airbnb_scraper import AirbnbScraper
from booking_scraper import BookingScraper
from data_processor import DataProcessor


def setup_logging(verbose=False):
    """
    Set up logging configuration.

    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler('scraper.log'),
            logging.StreamHandler()
        ]
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Competitive Intelligence Scraper for Airbnb & Booking.com'
    )

    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to config.yaml file'
    )

    parser.add_argument(
        '--platform',
        type=str,
        choices=['airbnb', 'booking', 'both'],
        default='both',
        help='Platform to scrape (default: both)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for results'
    )

    parser.add_argument(
        '--max-results',
        type=int,
        default=None,
        help='Maximum number of results per platform'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()


def main():
    """Main execution function."""
    # Parse arguments
    args = parse_arguments()

    # Set up logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("Competitive Intelligence Scraper")
    logger.info("=" * 80)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = Config(args.config)

        # Override output directory if specified
        if args.output_dir:
            config._config['output']['directory'] = args.output_dir

        # Ensure directories exist
        config.ensure_directories()

        # Determine max results
        max_results_airbnb = args.max_results or config.search_params.get('max_properties', 15)
        max_results_booking = args.max_results or 10

        # Initialize scrapers
        airbnb_data = {'weekday': [], 'weekend': []}
        booking_data = {'weekday': [], 'weekend': []}

        # Scrape Airbnb
        if args.platform in ['airbnb', 'both']:
            logger.info("\n" + "=" * 80)
            logger.info("AIRBNB SCRAPING")
            logger.info("=" * 80)

            airbnb_scraper = AirbnbScraper(config)
            airbnb_data = airbnb_scraper.search_weekday_and_weekend(
                max_results=max_results_airbnb
            )

            logger.info(f"Airbnb Results: {len(airbnb_data['weekday'])} weekday, {len(airbnb_data['weekend'])} weekend")

        # Scrape Booking.com
        if args.platform in ['booking', 'both']:
            logger.info("\n" + "=" * 80)
            logger.info("BOOKING.COM SCRAPING")
            logger.info("=" * 80)

            booking_scraper = BookingScraper(config)
            booking_data = booking_scraper.search_weekday_and_weekend(
                max_results=max_results_booking
            )

            logger.info(f"Booking.com Results: {len(booking_data['weekday'])} weekday, {len(booking_data['weekend'])} weekend")

        # Process and export data
        logger.info("\n" + "=" * 80)
        logger.info("DATA PROCESSING & EXPORT")
        logger.info("=" * 80)

        processor = DataProcessor(config)
        date_str = datetime.now().strftime(config.output_settings['date_format'])

        summary = processor.process_and_export(
            airbnb_data=airbnb_data,
            booking_data=booking_data,
            date_str=date_str
        )

        # Display results
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY RESULTS")
        logger.info("=" * 80)

        if summary and 'market_analysis' in summary:
            market = summary['market_analysis']
            our_perf = summary['our_performance']

            logger.info(f"\nTotal Properties Found: {market['total_properties']}")
            logger.info(f"  - Airbnb: {market['airbnb_count']}")
            logger.info(f"  - Booking.com: {market['booking_count']}")

            logger.info(f"\nMarket Averages:")
            logger.info(f"  - Weekday Rate: ${market['avg_weekday_rate']:.2f}")
            logger.info(f"  - Weekend Rate: ${market['avg_weekend_rate']:.2f}")
            logger.info(f"  - Cleaning Fee: ${market['avg_cleaning_fee']:.2f}")

            logger.info(f"\nYour Position:")
            logger.info(f"  - Your Weekday Rate: ${our_perf['our_weekday_rate']}")
            logger.info(f"  - Position vs Market: {our_perf['position_vs_market']}")
            logger.info(f"  - Your Cleaning Fee: ${our_perf['our_cleaning_fee']}")
            logger.info(f"  - Cleaning Fee vs Market: {our_perf['cleaning_fee_vs_market']}")

            logger.info(f"\nRecommendation:")
            logger.info(f"  {our_perf['recommendation']}")

        # Output file locations
        logger.info("\n" + "=" * 80)
        logger.info("OUTPUT FILES")
        logger.info("=" * 80)
        logger.info(f"CSV: {config.output_dir}/competitors_{date_str}.csv")
        logger.info(f"Summary: {config.output_dir}/summary_{date_str}.json")
        logger.info(f"Full Data: {config.output_dir}/full_data_{date_str}.json")

        logger.info("\n" + "=" * 80)
        logger.info("SCRAPING COMPLETE!")
        logger.info("=" * 80)

    except KeyboardInterrupt:
        logger.warning("\nScraping interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"\nError: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
