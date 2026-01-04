"""
Airbnb scraper using pyairbnb library.
"""
import logging
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from pyairbnb import Api
except ImportError:
    Api = None
    logging.warning("pyairbnb not installed. Airbnb scraping will not work.")


logger = logging.getLogger(__name__)


class AirbnbScraper:
    """Scraper for Airbnb listings."""

    def __init__(self, config):
        """
        Initialize Airbnb scraper.

        Args:
            config: Configuration object
        """
        self.config = config
        self.api = None
        if Api is not None:
            self.api = Api(currency=config.filters['currency'])

    def respectful_delay(self):
        """Add respectful delay between requests."""
        delay = random.uniform(
            self.config.rate_limit['min_delay'],
            self.config.rate_limit['max_delay']
        )
        logger.debug(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def search_competitors(
        self,
        check_in: str,
        check_out: str,
        max_results: int = 15
    ) -> List[Dict]:
        """
        Search Airbnb for competitor listings.

        Args:
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            max_results: Maximum number of results to return

        Returns:
            List of property dictionaries
        """
        if self.api is None:
            logger.error("pyairbnb not available. Cannot search Airbnb.")
            return []

        logger.info(f"Searching Airbnb: {check_in} to {check_out}")

        airbnb_params = self.config.search_params['airbnb']
        filters_config = self.config.filters

        properties = []

        try:
            # Search using bounding box
            results = self.api.search(
                checkin=check_in,
                checkout=check_out,
                ne_lat=airbnb_params['ne_lat'],
                ne_long=airbnb_params['ne_long'],
                sw_lat=airbnb_params['sw_lat'],
                sw_long=airbnb_params['sw_long'],
                zoom_value=airbnb_params.get('zoom', 14),
                currency=filters_config['currency']
            )

            logger.info(f"Found {len(results)} Airbnb listings")

            # Process each result
            for idx, listing in enumerate(results):
                if idx >= max_results:
                    break

                try:
                    # Extract basic information
                    property_data = self._extract_listing_data(listing, check_in, check_out)

                    if property_data and self._meets_criteria(property_data):
                        properties.append(property_data)
                        logger.info(f"Added property: {property_data.get('name', 'Unknown')}")

                    # Be respectful with delays
                    if idx < len(results) - 1:
                        self.respectful_delay()

                except Exception as e:
                    logger.error(f"Error processing listing {idx}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error searching Airbnb: {e}")
            raise

        logger.info(f"Collected {len(properties)} qualifying Airbnb properties")
        return properties

    def _extract_listing_data(
        self,
        listing: Dict,
        check_in: str,
        check_out: str
    ) -> Optional[Dict]:
        """
        Extract relevant data from a listing.

        Args:
            listing: Raw listing data from API
            check_in: Check-in date
            check_out: Check-out date

        Returns:
            Dictionary with extracted property data
        """
        try:
            # Extract pricing information
            pricing = listing.get('pricing', {})
            price_info = pricing.get('rate', {})

            # Get nightly rate
            nightly_rate = None
            if 'amount' in price_info:
                nightly_rate = float(price_info['amount'])
            elif 'price' in listing:
                nightly_rate = float(listing['price'])

            # Extract cleaning fee
            cleaning_fee = 0
            if 'cleaningFee' in pricing:
                cleaning_fee = float(pricing['cleaningFee'].get('amount', 0))
            elif 'cleaning_fee' in listing:
                cleaning_fee = float(listing.get('cleaning_fee', 0))

            # Extract location
            lat = listing.get('lat', 0)
            lng = listing.get('lng', 0)

            # Build property data dictionary
            property_data = {
                'platform': 'Airbnb',
                'property_id': listing.get('id', ''),
                'name': listing.get('name', ''),
                'url': f"https://www.airbnb.com/rooms/{listing.get('id', '')}",
                'latitude': lat,
                'longitude': lng,
                'bedrooms': listing.get('bedrooms', 0),
                'bathrooms': listing.get('bathrooms', 0),
                'max_guests': listing.get('person_capacity', 0),
                'nightly_rate': nightly_rate,
                'cleaning_fee': cleaning_fee,
                'service_fee': 0,  # Will be calculated
                'property_type': listing.get('room_type', ''),
                'rating': listing.get('star_rating', 0),
                'review_count': listing.get('reviews_count', 0),
                'amenities': listing.get('amenities', []),
                'check_in': check_in,
                'check_out': check_out,
                'date_scraped': datetime.now().isoformat(),
                'raw_data': listing
            }

            return property_data

        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return None

    def _meets_criteria(self, property_data: Dict) -> bool:
        """
        Check if property meets our filter criteria.

        Args:
            property_data: Property data dictionary

        Returns:
            True if property meets criteria, False otherwise
        """
        filters = self.config.filters

        # Check bedrooms
        if property_data.get('bedrooms', 0) != filters['bedrooms']:
            return False

        # Check price range
        nightly_rate = property_data.get('nightly_rate', 0)
        if nightly_rate < filters['min_price'] or nightly_rate > filters['max_price']:
            return False

        # Check property type (if we want "Entire place")
        property_type = property_data.get('property_type', '').lower()
        if 'entire' not in property_type and property_data.get('bedrooms', 0) == 1:
            # Sometimes 1BR apartments are classified differently
            # We'll be lenient here
            pass

        return True

    def get_listing_details(
        self,
        room_id: str,
        check_in: str,
        check_out: str
    ) -> Optional[Dict]:
        """
        Get detailed information for a specific listing.

        Args:
            room_id: Airbnb room/listing ID
            check_in: Check-in date
            check_out: Check-out date

        Returns:
            Detailed property data dictionary
        """
        if self.api is None:
            logger.error("pyairbnb not available.")
            return None

        try:
            logger.info(f"Fetching details for listing {room_id}")

            # Get listing details
            details = self.api.get_room_details(room_id)

            self.respectful_delay()

            return details

        except Exception as e:
            logger.error(f"Error fetching listing details for {room_id}: {e}")
            return None

    def search_weekday_and_weekend(self, max_results: int = 15) -> Dict[str, List[Dict]]:
        """
        Search for both weekday and weekend pricing.

        Args:
            max_results: Maximum results per search

        Returns:
            Dictionary with 'weekday' and 'weekend' property lists
        """
        dates = self.config.dates

        logger.info("Starting weekday search...")
        weekday_properties = self.search_competitors(
            check_in=dates['weekday_checkin'],
            check_out=dates['weekday_checkout'],
            max_results=max_results
        )

        logger.info("Starting weekend search...")
        weekend_properties = self.search_competitors(
            check_in=dates['weekend_checkin'],
            check_out=dates['weekend_checkout'],
            max_results=max_results
        )

        return {
            'weekday': weekday_properties,
            'weekend': weekend_properties
        }
