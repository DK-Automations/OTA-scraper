"""
Booking.com scraper using custom implementation.
"""
import logging
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential


logger = logging.getLogger(__name__)


class BookingScraper:
    """Scraper for Booking.com listings."""

    def __init__(self, config):
        """
        Initialize Booking.com scraper.

        Args:
            config: Configuration object
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

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
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search Booking.com for competitor listings.

        Args:
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            max_results: Maximum number of results to return

        Returns:
            List of property dictionaries
        """
        logger.info(f"Searching Booking.com: {check_in} to {check_out}")

        booking_params = self.config.search_params['booking']
        filters_config = self.config.filters

        properties = []

        try:
            # Build search URL
            # Note: This is a basic implementation. Booking.com has complex anti-bot measures.
            # In production, you might need to use Selenium or a service like ScraperAPI.

            search_url = self._build_search_url(
                city=booking_params['city'],
                country=booking_params['country'],
                check_in=check_in,
                check_out=check_out
            )

            logger.info(f"Search URL: {search_url}")

            # Make request
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()

            # Parse results
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find property listings
            # Note: These selectors may need to be updated as Booking.com changes their HTML
            listings = self._parse_search_results(soup)

            logger.info(f"Found {len(listings)} Booking.com listings")

            for idx, listing in enumerate(listings[:max_results]):
                try:
                    property_data = self._extract_property_data(
                        listing,
                        check_in,
                        check_out
                    )

                    if property_data and self._meets_criteria(property_data):
                        properties.append(property_data)
                        logger.info(f"Added property: {property_data.get('name', 'Unknown')}")

                    # Be respectful with delays
                    if idx < len(listings) - 1:
                        self.respectful_delay()

                except Exception as e:
                    logger.error(f"Error processing Booking.com listing {idx}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error searching Booking.com: {e}")
            logger.warning("Booking.com scraping failed. This is expected due to anti-bot measures.")
            logger.warning("Consider using alternative methods or manual data collection.")

        logger.info(f"Collected {len(properties)} qualifying Booking.com properties")
        return properties

    def _build_search_url(
        self,
        city: str,
        country: str,
        check_in: str,
        check_out: str
    ) -> str:
        """
        Build Booking.com search URL.

        Args:
            city: City name
            country: Country name
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)

        Returns:
            Search URL
        """
        # Convert dates to Booking.com format
        checkin_parts = check_in.split('-')
        checkout_parts = check_out.split('-')

        # Basic search URL structure
        base_url = "https://www.booking.com/searchresults.html"
        params = {
            'ss': f"{city}, {country}",
            'checkin_year': checkin_parts[0],
            'checkin_month': checkin_parts[1],
            'checkin_monthday': checkin_parts[2],
            'checkout_year': checkout_parts[0],
            'checkout_month': checkout_parts[1],
            'checkout_monthday': checkout_parts[2],
            'group_adults': '2',
            'no_rooms': '1',
            'group_children': '0',
            'nflt': 'ht_id%3D201',  # Apartments filter
        }

        # Build query string
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"

    def _parse_search_results(self, soup: BeautifulSoup) -> List:
        """
        Parse search results from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of listing elements
        """
        # Common selectors for Booking.com property cards
        # These may need to be updated as the site changes
        selectors = [
            '[data-testid="property-card"]',
            '.sr_property_block',
            '[data-testid="property-list-item"]',
        ]

        listings = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                listings = found
                logger.info(f"Found listings using selector: {selector}")
                break

        return listings

    def _extract_property_data(
        self,
        listing_element,
        check_in: str,
        check_out: str
    ) -> Optional[Dict]:
        """
        Extract property data from listing element.

        Args:
            listing_element: BeautifulSoup element
            check_in: Check-in date
            check_out: Check-out date

        Returns:
            Property data dictionary
        """
        try:
            # Extract property name
            name_selectors = [
                '[data-testid="title"]',
                '.sr-hotel__name',
                'h3',
            ]
            name = self._find_text(listing_element, name_selectors, 'Unknown Property')

            # Extract price
            price_selectors = [
                '[data-testid="price-and-discounted-price"]',
                '.bui-price-display__value',
                '.prco-valign-middle-helper',
            ]
            price_text = self._find_text(listing_element, price_selectors, '0')
            nightly_rate = self._parse_price(price_text)

            # Extract rating
            rating_selectors = [
                '[data-testid="review-score"]',
                '.bui-review-score__badge',
            ]
            rating_text = self._find_text(listing_element, rating_selectors, '0')
            rating = self._parse_rating(rating_text)

            # Extract review count
            review_selectors = [
                '[data-testid="review-score-total"]',
                '.bui-review-score__text',
            ]
            review_text = self._find_text(listing_element, review_selectors, '0')
            review_count = self._parse_review_count(review_text)

            # Extract URL
            url_selectors = ['a[href*="/hotel/"]', 'a']
            url = self._find_attr(listing_element, url_selectors, 'href', '')
            if url and not url.startswith('http'):
                url = f"https://www.booking.com{url}"

            # Build property data
            property_data = {
                'platform': 'Booking.com',
                'property_id': self._extract_id_from_url(url),
                'name': name,
                'url': url,
                'latitude': 0,  # Would need geocoding or detailed page scraping
                'longitude': 0,
                'bedrooms': 1,  # Assumed from our filter
                'bathrooms': 1,  # Often not shown on search results
                'max_guests': 2,  # Assumed
                'nightly_rate': nightly_rate,
                'cleaning_fee': 0,  # Usually included in Booking.com price
                'service_fee': 0,
                'property_type': 'Apartment',
                'rating': rating,
                'review_count': review_count,
                'amenities': [],
                'check_in': check_in,
                'check_out': check_out,
                'date_scraped': datetime.now().isoformat(),
                'raw_data': str(listing_element)[:500]  # Truncated for storage
            }

            return property_data

        except Exception as e:
            logger.error(f"Error extracting Booking.com property data: {e}")
            return None

    def _find_text(self, element, selectors: List[str], default: str = '') -> str:
        """Find text using multiple selectors."""
        for selector in selectors:
            found = element.select_one(selector)
            if found:
                return found.get_text(strip=True)
        return default

    def _find_attr(self, element, selectors: List[str], attr: str, default: str = '') -> str:
        """Find attribute value using multiple selectors."""
        for selector in selectors:
            found = element.select_one(selector)
            if found and found.get(attr):
                return found.get(attr)
        return default

    def _parse_price(self, price_text: str) -> float:
        """Parse price from text."""
        try:
            # Remove currency symbols and extract number
            import re
            numbers = re.findall(r'[\d,]+\.?\d*', price_text.replace(',', ''))
            if numbers:
                return float(numbers[0])
        except:
            pass
        return 0.0

    def _parse_rating(self, rating_text: str) -> float:
        """Parse rating from text."""
        try:
            import re
            numbers = re.findall(r'\d+\.?\d*', rating_text)
            if numbers:
                rating = float(numbers[0])
                # Booking.com uses 10-point scale, convert if needed
                return rating
        except:
            pass
        return 0.0

    def _parse_review_count(self, review_text: str) -> int:
        """Parse review count from text."""
        try:
            import re
            numbers = re.findall(r'\d+', review_text.replace(',', ''))
            if numbers:
                return int(numbers[0])
        except:
            pass
        return 0

    def _extract_id_from_url(self, url: str) -> str:
        """Extract property ID from URL."""
        try:
            import re
            match = re.search(r'/hotel/[a-z]{2}/([^/]+)', url)
            if match:
                return match.group(1)
        except:
            pass
        return ''

    def _meets_criteria(self, property_data: Dict) -> bool:
        """
        Check if property meets our filter criteria.

        Args:
            property_data: Property data dictionary

        Returns:
            True if property meets criteria
        """
        filters = self.config.filters

        # Check price range
        nightly_rate = property_data.get('nightly_rate', 0)
        if nightly_rate < filters['min_price'] or nightly_rate > filters['max_price']:
            return False

        # Check rating (Booking.com uses 10-point scale)
        rating = property_data.get('rating', 0)
        if rating > 0 and rating < filters['min_rating']:
            return False

        return True

    def search_weekday_and_weekend(self, max_results: int = 10) -> Dict[str, List[Dict]]:
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
