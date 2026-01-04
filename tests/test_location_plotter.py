"""
Tests for location plotting functionality.
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from location_plotter import LocationPlotter, create_location_from_address

# Check if folium is available
try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False


class TestLocationPlotter:
    """Tests for LocationPlotter class."""

    def test_get_price_category_budget(self, mock_config):
        """Test budget price category."""
        plotter = LocationPlotter(mock_config)

        assert plotter.get_price_category(50) == 'budget'
        assert plotter.get_price_category(100) == 'budget'
        assert plotter.get_price_category(119) == 'budget'

    def test_get_price_category_moderate(self, mock_config):
        """Test moderate price category."""
        plotter = LocationPlotter(mock_config)

        assert plotter.get_price_category(120) == 'moderate'
        assert plotter.get_price_category(150) == 'moderate'
        assert plotter.get_price_category(179) == 'moderate'

    def test_get_price_category_premium(self, mock_config):
        """Test premium price category."""
        plotter = LocationPlotter(mock_config)

        assert plotter.get_price_category(180) == 'premium'
        assert plotter.get_price_category(220) == 'premium'
        assert plotter.get_price_category(249) == 'premium'

    def test_get_price_category_luxury(self, mock_config):
        """Test luxury price category."""
        plotter = LocationPlotter(mock_config)

        assert plotter.get_price_category(250) == 'luxury'
        assert plotter.get_price_category(500) == 'luxury'

    def test_get_marker_color_returns_hex(self, mock_config):
        """Test that marker colors are valid hex codes."""
        plotter = LocationPlotter(mock_config)

        for rate in [50, 150, 200, 300]:
            color = plotter.get_marker_color(rate)
            assert color.startswith('#')
            assert len(color) == 7

    def test_price_colors_defined(self, mock_config):
        """Test that all price colors are defined."""
        plotter = LocationPlotter(mock_config)

        expected_categories = ['budget', 'moderate', 'premium', 'luxury']
        for category in expected_categories:
            assert category in plotter.PRICE_COLORS

    @pytest.mark.skipif(not FOLIUM_AVAILABLE, reason="folium not installed")
    def test_create_interactive_map(self, mock_config, sample_properties, tmp_path):
        """Test interactive map creation."""
        # Update mock_config output_dir
        mock_config._output_dir = tmp_path

        plotter = LocationPlotter(mock_config)

        # Add coordinates to properties
        for prop in sample_properties:
            prop['weekday_rate'] = prop.get('nightly_rate', 100)
            prop['weekend_rate'] = prop.get('nightly_rate', 100)

        map_path = plotter.create_interactive_map(
            properties=sample_properties,
            output_path=str(tmp_path / 'test_map.html')
        )

        assert map_path is not None
        assert Path(map_path).exists()
        assert map_path.endswith('.html')

        # Verify HTML content
        with open(map_path, 'r') as f:
            content = f.read()
            assert 'folium' in content.lower() or 'leaflet' in content.lower()

    @pytest.mark.skipif(not FOLIUM_AVAILABLE, reason="folium not installed")
    def test_create_interactive_map_empty_properties(self, mock_config, tmp_path):
        """Test map creation with no properties."""
        mock_config._output_dir = tmp_path
        plotter = LocationPlotter(mock_config)

        map_path = plotter.create_interactive_map(
            properties=[],
            output_path=str(tmp_path / 'empty_map.html')
        )

        assert map_path is not None
        assert Path(map_path).exists()

    @pytest.mark.skipif(not FOLIUM_AVAILABLE, reason="folium not installed")
    def test_plot_any_location(self, mock_config, tmp_path):
        """Test plotting arbitrary location."""
        mock_config._output_dir = tmp_path
        plotter = LocationPlotter(mock_config)

        map_path = plotter.plot_any_location(
            latitude=-37.8136,
            longitude=144.9631,
            location_name='Melbourne CBD',
            properties=[],
            radius_km=1.5
        )

        assert map_path is not None
        assert Path(map_path).exists()
        assert 'Melbourne_CBD' in map_path

    @pytest.mark.skipif(not FOLIUM_AVAILABLE, reason="folium not installed")
    def test_create_price_heatmap(self, mock_config, sample_properties, tmp_path):
        """Test price heatmap creation."""
        mock_config._output_dir = tmp_path
        plotter = LocationPlotter(mock_config)

        for prop in sample_properties:
            prop['weekday_rate'] = prop.get('nightly_rate', 100)
            prop['weekend_rate'] = prop.get('nightly_rate', 100)

        heatmap_path = plotter.create_price_heatmap(
            properties=sample_properties,
            output_path=str(tmp_path / 'heatmap.html')
        )

        assert heatmap_path is not None
        assert Path(heatmap_path).exists()

    def test_create_property_popup(self, mock_config):
        """Test popup HTML generation."""
        plotter = LocationPlotter(mock_config)

        prop = {
            'name': 'Test Property',
            'platform': 'Airbnb',
            'distance_km': 1.5,
            'weekday_rate': 150,
            'weekend_rate': 180,
            'cleaning_fee': 50,
            'rating': 4.8,
            'review_count': 100,
            'url': 'https://example.com'
        }

        popup_html = plotter._create_property_popup(prop, 165, 'moderate')

        assert 'Test Property' in popup_html
        assert 'Airbnb' in popup_html
        assert '1.50' in popup_html or '1.5' in popup_html
        assert '$150' in popup_html
        assert '$180' in popup_html


class TestCreateLocationFromAddress:
    """Tests for address geocoding helper."""

    def test_known_suburb_south_yarra(self):
        """Test lookup of South Yarra."""
        coords = create_location_from_address('South Yarra')

        assert coords is not None
        lat, lng = coords
        assert -37.85 < lat < -37.83
        assert 144.98 < lng < 145.00

    def test_known_suburb_st_kilda(self):
        """Test lookup of St Kilda."""
        coords = create_location_from_address('st kilda')

        assert coords is not None
        lat, lng = coords
        assert -37.88 < lat < -37.86
        assert 144.97 < lng < 144.99

    def test_known_suburb_melbourne_cbd(self):
        """Test lookup of Melbourne CBD."""
        coords = create_location_from_address('Melbourne CBD')

        assert coords is not None
        lat, lng = coords
        assert -37.82 < lat < -37.80
        assert 144.95 < lng < 144.97

    def test_known_suburb_case_insensitive(self):
        """Test that lookup is case insensitive."""
        coords_lower = create_location_from_address('richmond')
        coords_upper = create_location_from_address('RICHMOND')
        coords_mixed = create_location_from_address('Richmond')

        assert coords_lower == coords_upper == coords_mixed

    def test_unknown_address_returns_none(self):
        """Test that unknown address returns None."""
        coords = create_location_from_address('Unknown Place XYZ123')

        assert coords is None

    def test_partial_match(self):
        """Test partial suburb name matching."""
        coords = create_location_from_address('123 Something St, South Yarra VIC')

        assert coords is not None

    def test_all_known_locations(self):
        """Test all predefined Melbourne locations."""
        known_suburbs = [
            'south yarra', 'south melbourne', 'prahran', 'st kilda',
            'richmond', 'fitzroy', 'carlton', 'collingwood',
            'windsor', 'albert park', 'melbourne cbd', 'docklands', 'toorak'
        ]

        for suburb in known_suburbs:
            coords = create_location_from_address(suburb)
            assert coords is not None, f"Failed for suburb: {suburb}"
            lat, lng = coords
            # All Melbourne suburbs should be in this approximate range
            assert -38.0 < lat < -37.7, f"Latitude out of range for {suburb}"
            assert 144.8 < lng < 145.2, f"Longitude out of range for {suburb}"
