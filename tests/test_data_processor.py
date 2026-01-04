"""
Tests for data processor functionality.
"""
import pytest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data_processor import DataProcessor


class TestDataProcessor:
    """Tests for DataProcessor class."""

    def test_calculate_distance_same_location(self, mock_config):
        """Test distance calculation for same location returns 0."""
        processor = DataProcessor(mock_config)

        # Same coordinates as our property
        distance = processor.calculate_distance((-37.8388, 144.9924))

        assert distance == pytest.approx(0, abs=0.001)

    def test_calculate_distance_nearby(self, mock_config):
        """Test distance calculation for nearby location."""
        processor = DataProcessor(mock_config)

        # Approximately 1km away
        distance = processor.calculate_distance((-37.8478, 144.9924))

        assert distance == pytest.approx(1.0, abs=0.1)

    def test_calculate_distance_custom_reference(self, mock_config):
        """Test distance calculation with custom reference point."""
        processor = DataProcessor(mock_config)

        # Melbourne CBD to St Kilda (~5km)
        distance = processor.calculate_distance(
            (-37.8676, 144.9814),  # St Kilda
            (-37.8136, 144.9631)   # Melbourne CBD
        )

        assert distance == pytest.approx(6.2, abs=0.5)

    def test_merge_weekday_weekend_data(self, mock_config):
        """Test merging weekday and weekend property data."""
        processor = DataProcessor(mock_config)

        weekday_props = [
            {
                'property_id': 'prop_001',
                'platform': 'Airbnb',
                'name': 'Test Property',
                'latitude': -37.84,
                'longitude': 144.99,
                'nightly_rate': 100,
                'cleaning_fee': 50
            }
        ]

        weekend_props = [
            {
                'property_id': 'prop_001',
                'platform': 'Airbnb',
                'name': 'Test Property',
                'latitude': -37.84,
                'longitude': 144.99,
                'nightly_rate': 120,
                'cleaning_fee': 50
            }
        ]

        merged = processor.merge_weekday_weekend_data(weekday_props, weekend_props)

        assert len(merged) == 1
        assert merged[0]['weekday_rate'] == 100
        assert merged[0]['weekend_rate'] == 120
        assert merged[0]['distance_km'] > 0

    def test_merge_handles_missing_weekend(self, mock_config):
        """Test merging when weekend data is missing for a property."""
        processor = DataProcessor(mock_config)

        weekday_props = [
            {
                'property_id': 'prop_001',
                'platform': 'Airbnb',
                'name': 'Test Property',
                'latitude': -37.84,
                'longitude': 144.99,
                'nightly_rate': 100,
                'cleaning_fee': 50
            }
        ]

        weekend_props = []

        merged = processor.merge_weekday_weekend_data(weekday_props, weekend_props)

        assert len(merged) == 1
        assert merged[0]['weekday_rate'] == 100
        assert merged[0]['weekend_rate'] == 0

    def test_filter_by_distance(self, mock_config, sample_properties):
        """Test filtering properties by distance."""
        processor = DataProcessor(mock_config)

        # Add distance to properties
        for prop in sample_properties:
            prop['distance_km'] = processor.calculate_distance(
                (prop['latitude'], prop['longitude'])
            )

        # All sample properties are within 2km
        filtered = processor.filter_by_distance(sample_properties, max_distance_km=2.0)
        assert len(filtered) == len(sample_properties)

        # Filter to 0.5km - should get fewer
        filtered_close = processor.filter_by_distance(sample_properties, max_distance_km=0.5)
        assert len(filtered_close) <= len(sample_properties)

    def test_generate_summary_stats(self, mock_config, sample_properties):
        """Test summary statistics generation."""
        processor = DataProcessor(mock_config)

        # Add required merged fields
        for prop in sample_properties:
            prop['weekday_rate'] = prop.get('nightly_rate', 0)
            prop['weekend_rate'] = prop.get('nightly_rate', 0)
            prop['distance_km'] = 1.0

        summary = processor.generate_summary_stats(sample_properties)

        assert 'date_collected' in summary
        assert 'market_analysis' in summary
        assert 'our_performance' in summary

        market = summary['market_analysis']
        assert market['total_properties'] == 3
        assert market['airbnb_count'] == 2
        assert market['booking_count'] == 1
        assert market['avg_weekday_rate'] > 0

    def test_generate_summary_stats_empty(self, mock_config):
        """Test summary stats with no properties."""
        processor = DataProcessor(mock_config)

        summary = processor.generate_summary_stats([])

        assert summary == {}

    def test_export_to_csv(self, mock_config, sample_properties, tmp_path):
        """Test CSV export functionality."""
        processor = DataProcessor(mock_config)

        # Add required fields
        for prop in sample_properties:
            prop['weekday_rate'] = prop.get('nightly_rate', 0)
            prop['weekend_rate'] = prop.get('nightly_rate', 0)
            prop['distance_km'] = 1.0
            prop['total_2night_weekday'] = prop['weekday_rate'] * 2 + prop.get('cleaning_fee', 0)
            prop['total_2night_weekend'] = prop['weekend_rate'] * 2 + prop.get('cleaning_fee', 0)

        csv_path = tmp_path / 'test_output.csv'
        processor.export_to_csv(sample_properties, str(csv_path))

        assert csv_path.exists()

        # Read and verify content
        with open(csv_path, 'r') as f:
            content = f.read()
            assert 'Platform' in content
            assert 'Airbnb' in content
            assert 'Booking.com' in content

    def test_export_to_json(self, mock_config, tmp_path):
        """Test JSON export functionality."""
        processor = DataProcessor(mock_config)

        test_data = {
            'summary': {'test': 'data'},
            'properties': [{'id': 1}, {'id': 2}]
        }

        json_path = tmp_path / 'test_output.json'
        processor.export_to_json(test_data, str(json_path))

        assert json_path.exists()

        with open(json_path, 'r') as f:
            loaded = json.load(f)
            assert loaded == test_data


class TestDistanceCalculation:
    """Focused tests for Haversine distance calculation."""

    def test_haversine_known_distances(self, mock_config):
        """Test against known distances between Melbourne landmarks."""
        processor = DataProcessor(mock_config)

        # Flinders Station to MCG (~1km)
        distance = processor.calculate_distance(
            (-37.8199, 144.9834),  # MCG
            (-37.8183, 144.9671)   # Flinders Station
        )
        assert 1.0 < distance < 2.0

    def test_haversine_zero_distance(self, mock_config):
        """Test that same coordinates give zero distance."""
        processor = DataProcessor(mock_config)

        distance = processor.calculate_distance(
            (-37.8388, 144.9924),
            (-37.8388, 144.9924)
        )
        assert distance == 0

    def test_haversine_symmetry(self, mock_config):
        """Test that distance is same in both directions."""
        processor = DataProcessor(mock_config)

        point_a = (-37.8388, 144.9924)
        point_b = (-37.8500, 145.0000)

        distance_ab = processor.calculate_distance(point_a, point_b)
        distance_ba = processor.calculate_distance(point_b, point_a)

        assert distance_ab == pytest.approx(distance_ba, abs=0.0001)
