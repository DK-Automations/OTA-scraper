"""
Pytest fixtures for OTA Scraper tests.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture
def sample_config_dict():
    """Sample configuration dictionary for testing."""
    return {
        'our_location': {
            'latitude': -37.8388,
            'longitude': 144.9924,
            'name': 'Test Property',
            'address': 'Darling St, South Yarra VIC 3141',
            'suburb': 'South Yarra',
            'current_rates': {
                'weekday_rate': 145,
                'weekend_rate': 145,
                'cleaning_fee': 90,
                'actual_cleaning_cost': 125
            }
        },
        'search': {
            'max_distance_km': 2.0,
            'max_properties': 20,
            'airbnb': {
                'ne_lat': -37.825,
                'ne_long': 145.010,
                'sw_lat': -37.855,
                'sw_long': 144.975,
                'zoom': 14
            },
            'booking': {
                'city': 'South Yarra',
                'country': 'Australia'
            }
        },
        'plotting': {
            'enabled': True,
            'create_interactive_map': True,
            'create_heatmap': False,
            'show_search_radius': True,
            'price_thresholds': {
                'budget': 120,
                'moderate': 180,
                'premium': 250
            }
        },
        'dates': {
            'weekday_checkin': '2026-02-15',
            'weekday_checkout': '2026-02-17',
            'weekend_checkin': '2026-02-21',
            'weekend_checkout': '2026-02-23'
        },
        'filters': {
            'property_type': 'Entire place',
            'bedrooms': 1,
            'min_price': 80,
            'max_price': 300,
            'currency': 'AUD',
            'min_rating': 7.0
        },
        'rate_limit': {
            'requests_per_minute': 10,
            'delay_between_requests': 3,
            'min_delay': 2,
            'max_delay': 5
        },
        'output': {
            'save_raw_json': True,
            'save_processed_csv': True,
            'save_summary': True,
            'archive_old_data': True,
            'date_format': '%Y%m%d'
        }
    }


@pytest.fixture
def sample_properties():
    """Sample property data for testing."""
    return [
        {
            'property_id': 'airbnb_001',
            'platform': 'Airbnb',
            'name': 'Cozy Studio in South Yarra',
            'url': 'https://airbnb.com/rooms/001',
            'latitude': -37.8400,
            'longitude': 144.9930,
            'nightly_rate': 120,
            'cleaning_fee': 50,
            'service_fee': 30,
            'bedrooms': 1,
            'bathrooms': 1,
            'max_guests': 2,
            'rating': 4.8,
            'review_count': 45,
            'amenities': ['WiFi', 'Kitchen', 'Air conditioning'],
            'date_scraped': '2026-01-04'
        },
        {
            'property_id': 'airbnb_002',
            'platform': 'Airbnb',
            'name': 'Modern Apartment near Chapel St',
            'url': 'https://airbnb.com/rooms/002',
            'latitude': -37.8450,
            'longitude': 144.9950,
            'nightly_rate': 180,
            'cleaning_fee': 80,
            'service_fee': 45,
            'bedrooms': 2,
            'bathrooms': 1,
            'max_guests': 4,
            'rating': 4.5,
            'review_count': 120,
            'amenities': ['WiFi', 'Kitchen', 'Pool'],
            'date_scraped': '2026-01-04'
        },
        {
            'property_id': 'booking_001',
            'platform': 'Booking.com',
            'name': 'South Yarra Luxury Suite',
            'url': 'https://booking.com/hotel/001',
            'latitude': -37.8380,
            'longitude': 144.9900,
            'nightly_rate': 250,
            'cleaning_fee': 0,
            'service_fee': 0,
            'bedrooms': 1,
            'bathrooms': 1,
            'max_guests': 2,
            'rating': 9.2,
            'review_count': 89,
            'amenities': ['WiFi', 'Breakfast'],
            'date_scraped': '2026-01-04'
        }
    ]


@pytest.fixture
def mock_config(sample_config_dict, tmp_path):
    """Create a mock config object for testing."""
    class MockConfig:
        def __init__(self, config_dict, output_dir):
            self._config = config_dict
            self._output_dir = output_dir

        @property
        def our_location(self):
            return self._config['our_location']

        @property
        def search_params(self):
            return self._config['search']

        @property
        def dates(self):
            return self._config['dates']

        @property
        def filters(self):
            return self._config['filters']

        @property
        def rate_limit(self):
            return self._config['rate_limit']

        @property
        def output_settings(self):
            return self._config['output']

        @property
        def plotting_settings(self):
            return self._config.get('plotting', {})

        @property
        def output_dir(self):
            return self._output_dir

        @property
        def data_dir(self):
            return self._output_dir / 'data'

        def get(self, key, default=None):
            return self._config.get(key, default)

    return MockConfig(sample_config_dict, tmp_path)
