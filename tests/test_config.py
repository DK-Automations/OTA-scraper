"""
Tests for configuration management.
"""
import pytest
import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import Config


class TestConfig:
    """Tests for Config class."""

    def test_config_loads_from_file(self, tmp_path):
        """Test that config loads correctly from YAML file."""
        config_content = {
            'our_location': {
                'latitude': -37.8388,
                'longitude': 144.9924,
                'name': 'Test Property',
                'current_rates': {
                    'weekday_rate': 100,
                    'weekend_rate': 120,
                    'cleaning_fee': 50,
                    'actual_cleaning_cost': 75
                }
            },
            'search': {
                'max_distance_km': 2.0,
                'max_properties': 15,
                'airbnb': {'ne_lat': -37.82, 'ne_long': 145.0, 'sw_lat': -37.85, 'sw_long': 144.97, 'zoom': 14},
                'booking': {'city': 'Test City', 'country': 'Australia'}
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

        config_file = tmp_path / 'config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        config = Config(config_file)

        assert config.our_location['latitude'] == -37.8388
        assert config.our_location['longitude'] == 144.9924
        assert config.search_params['max_distance_km'] == 2.0

    def test_config_missing_file_raises_error(self, tmp_path):
        """Test that missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Config(tmp_path / 'nonexistent.yaml')

    def test_config_get_method(self, tmp_path):
        """Test the get method with default values."""
        config_content = {
            'our_location': {'latitude': -37.8, 'longitude': 144.9, 'name': 'Test', 'current_rates': {'weekday_rate': 100, 'weekend_rate': 100, 'cleaning_fee': 50, 'actual_cleaning_cost': 75}},
            'search': {'max_distance_km': 2.0, 'max_properties': 15, 'airbnb': {'ne_lat': -37.82, 'ne_long': 145.0, 'sw_lat': -37.85, 'sw_long': 144.97, 'zoom': 14}, 'booking': {'city': 'Test', 'country': 'Australia'}},
            'dates': {'weekday_checkin': '2026-02-15', 'weekday_checkout': '2026-02-17', 'weekend_checkin': '2026-02-21', 'weekend_checkout': '2026-02-23'},
            'filters': {'property_type': 'Entire place', 'bedrooms': 1, 'min_price': 80, 'max_price': 300, 'currency': 'AUD', 'min_rating': 7.0},
            'rate_limit': {'requests_per_minute': 10, 'delay_between_requests': 3, 'min_delay': 2, 'max_delay': 5},
            'output': {'save_raw_json': True, 'save_processed_csv': True, 'save_summary': True, 'archive_old_data': True, 'date_format': '%Y%m%d'}
        }

        config_file = tmp_path / 'config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        config = Config(config_file)

        assert config.get('nonexistent', 'default') == 'default'
        assert config.get('our_location') is not None

    def test_plotting_settings_defaults(self, tmp_path):
        """Test that plotting settings have sensible defaults."""
        config_content = {
            'our_location': {'latitude': -37.8, 'longitude': 144.9, 'name': 'Test', 'current_rates': {'weekday_rate': 100, 'weekend_rate': 100, 'cleaning_fee': 50, 'actual_cleaning_cost': 75}},
            'search': {'max_distance_km': 2.0, 'max_properties': 15, 'airbnb': {'ne_lat': -37.82, 'ne_long': 145.0, 'sw_lat': -37.85, 'sw_long': 144.97, 'zoom': 14}, 'booking': {'city': 'Test', 'country': 'Australia'}},
            'dates': {'weekday_checkin': '2026-02-15', 'weekday_checkout': '2026-02-17', 'weekend_checkin': '2026-02-21', 'weekend_checkout': '2026-02-23'},
            'filters': {'property_type': 'Entire place', 'bedrooms': 1, 'min_price': 80, 'max_price': 300, 'currency': 'AUD', 'min_rating': 7.0},
            'rate_limit': {'requests_per_minute': 10, 'delay_between_requests': 3, 'min_delay': 2, 'max_delay': 5},
            'output': {'save_raw_json': True, 'save_processed_csv': True, 'save_summary': True, 'archive_old_data': True, 'date_format': '%Y%m%d'}
        }

        config_file = tmp_path / 'config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)

        config = Config(config_file)
        plotting = config.plotting_settings

        assert plotting['enabled'] is True
        assert plotting['create_interactive_map'] is True
        assert 'price_thresholds' in plotting
