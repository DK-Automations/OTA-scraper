"""
Location plotter for visualizing competitor properties on interactive maps.
Supports any location with customizable markers and price-based color coding.
"""
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from datetime import datetime

try:
    import folium
    from folium import plugins
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


logger = logging.getLogger(__name__)


class LocationPlotter:
    """Interactive map plotter for property locations."""

    # Price range color coding
    PRICE_COLORS = {
        'budget': '#2ecc71',      # Green - under $120/night
        'moderate': '#3498db',     # Blue - $120-180/night
        'premium': '#f39c12',      # Orange - $180-250/night
        'luxury': '#e74c3c',       # Red - over $250/night
    }

    def __init__(self, config):
        """
        Initialize the location plotter.

        Args:
            config: Configuration object with location settings
        """
        self.config = config
        self.our_location = config.our_location
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required plotting libraries are available."""
        if not FOLIUM_AVAILABLE:
            logger.warning(
                "folium not installed. Install with: pip install folium"
            )
        if not MATPLOTLIB_AVAILABLE:
            logger.warning(
                "matplotlib not installed. Install with: pip install matplotlib"
            )

    def get_price_category(self, nightly_rate: float) -> str:
        """
        Determine price category based on nightly rate.

        Args:
            nightly_rate: Average nightly rate

        Returns:
            Price category string
        """
        if nightly_rate < 120:
            return 'budget'
        elif nightly_rate < 180:
            return 'moderate'
        elif nightly_rate < 250:
            return 'premium'
        else:
            return 'luxury'

    def get_marker_color(self, nightly_rate: float) -> str:
        """
        Get marker color based on nightly rate.

        Args:
            nightly_rate: Average nightly rate

        Returns:
            Hex color string
        """
        category = self.get_price_category(nightly_rate)
        return self.PRICE_COLORS.get(category, '#95a5a6')

    def create_interactive_map(
        self,
        properties: List[Dict],
        output_path: str = None,
        center_location: Tuple[float, float] = None,
        zoom_start: int = 15,
        show_radius: bool = True,
        radius_km: float = None
    ) -> Optional[str]:
        """
        Create an interactive Folium map with all properties plotted.

        Args:
            properties: List of property dictionaries with coordinates
            output_path: Path to save HTML map file
            center_location: (lat, lng) tuple for map center (defaults to our property)
            zoom_start: Initial zoom level
            show_radius: Whether to show search radius circle
            radius_km: Search radius in km (defaults to config max_distance_km)

        Returns:
            Path to saved HTML file, or None if folium not available
        """
        if not FOLIUM_AVAILABLE:
            logger.error("Cannot create interactive map: folium not installed")
            return None

        # Default center to our property location
        if center_location is None:
            center_location = (
                self.our_location['latitude'],
                self.our_location['longitude']
            )

        if radius_km is None:
            radius_km = self.config.search_params.get('max_distance_km', 2.0)

        logger.info(f"Creating interactive map centered at {center_location}")

        # Create base map
        m = folium.Map(
            location=center_location,
            zoom_start=zoom_start,
            tiles='cartodbpositron'
        )

        # Add search radius circle if requested
        if show_radius:
            folium.Circle(
                location=center_location,
                radius=radius_km * 1000,  # Convert to meters
                color='#9b59b6',
                fill=True,
                fillOpacity=0.1,
                popup=f'Search radius: {radius_km}km'
            ).add_to(m)

        # Add our property marker (special star icon)
        our_name = self.our_location.get('name', 'Our Property')
        our_rates = self.our_location.get('current_rates', {})
        our_popup = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="color: #9b59b6; margin: 0 0 10px 0;">{our_name}</h4>
            <p style="margin: 5px 0;"><strong>Your Property</strong></p>
            <p style="margin: 5px 0;">Weekday: ${our_rates.get('weekday_rate', 'N/A')}/night</p>
            <p style="margin: 5px 0;">Weekend: ${our_rates.get('weekend_rate', 'N/A')}/night</p>
            <p style="margin: 5px 0;">Cleaning Fee: ${our_rates.get('cleaning_fee', 'N/A')}</p>
        </div>
        """

        folium.Marker(
            location=center_location,
            popup=folium.Popup(our_popup, max_width=300),
            tooltip=our_name,
            icon=folium.Icon(
                color='purple',
                icon='star',
                prefix='fa'
            )
        ).add_to(m)

        # Create feature groups for filtering
        platform_groups = {}

        # Add competitor property markers
        for prop in properties:
            lat = prop.get('latitude')
            lng = prop.get('longitude')

            if not lat or not lng:
                continue

            # Calculate average rate for color coding
            weekday = prop.get('weekday_rate', 0)
            weekend = prop.get('weekend_rate', 0)
            avg_rate = (weekday + weekend) / 2 if (weekday and weekend) else weekday or weekend

            # Get marker color based on price
            color = self.get_marker_color(avg_rate)
            price_category = self.get_price_category(avg_rate)

            # Create popup content
            popup_html = self._create_property_popup(prop, avg_rate, price_category)

            # Get or create platform feature group
            platform = prop.get('platform', 'Unknown')
            if platform not in platform_groups:
                platform_groups[platform] = folium.FeatureGroup(name=platform)
                platform_groups[platform].add_to(m)

            # Add marker
            folium.CircleMarker(
                location=[lat, lng],
                radius=8,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=f"{prop.get('name', 'Property')[:30]} - ${avg_rate:.0f}/night"
            ).add_to(platform_groups[platform])

        # Add layer control
        folium.LayerControl().add_to(m)

        # Add legend
        legend_html = self._create_legend_html()
        m.get_root().html.add_child(folium.Element(legend_html))

        # Add minimap
        plugins.MiniMap(toggle_display=True).add_to(m)

        # Add fullscreen option
        plugins.Fullscreen().add_to(m)

        # Save map
        if output_path is None:
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = str(self.config.output_dir / f'property_map_{date_str}.html')

        m.save(output_path)
        logger.info(f"Interactive map saved to: {output_path}")

        return output_path

    def _create_property_popup(
        self,
        prop: Dict,
        avg_rate: float,
        price_category: str
    ) -> str:
        """Create HTML popup content for a property marker."""
        name = prop.get('name', 'Unknown Property')[:50]
        platform = prop.get('platform', 'Unknown')
        distance = prop.get('distance_km', 0)
        weekday = prop.get('weekday_rate', 0)
        weekend = prop.get('weekend_rate', 0)
        cleaning = prop.get('cleaning_fee', 0)
        rating = prop.get('rating', 'N/A')
        reviews = prop.get('review_count', 0)
        url = prop.get('url', '#')

        color = self.PRICE_COLORS[price_category]

        return f"""
        <div style="font-family: Arial, sans-serif; min-width: 250px;">
            <h4 style="color: {color}; margin: 0 0 10px 0;">{name}</h4>
            <p style="margin: 3px 0;"><strong>Platform:</strong> {platform}</p>
            <p style="margin: 3px 0;"><strong>Distance:</strong> {distance:.2f} km</p>
            <hr style="margin: 8px 0;">
            <p style="margin: 3px 0;"><strong>Weekday Rate:</strong> ${weekday}/night</p>
            <p style="margin: 3px 0;"><strong>Weekend Rate:</strong> ${weekend}/night</p>
            <p style="margin: 3px 0;"><strong>Avg Rate:</strong> ${avg_rate:.0f}/night</p>
            <p style="margin: 3px 0;"><strong>Cleaning Fee:</strong> ${cleaning}</p>
            <hr style="margin: 8px 0;">
            <p style="margin: 3px 0;"><strong>Rating:</strong> {rating} ({reviews} reviews)</p>
            <p style="margin: 8px 0 0 0;">
                <a href="{url}" target="_blank" style="color: #3498db;">View Listing</a>
            </p>
        </div>
        """

    def _create_legend_html(self) -> str:
        """Create HTML legend for the map."""
        return """
        <div style="
            position: fixed;
            bottom: 50px;
            left: 50px;
            z-index: 1000;
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            font-family: Arial, sans-serif;
            font-size: 12px;
        ">
            <h4 style="margin: 0 0 10px 0;">Price Categories</h4>
            <div style="margin: 5px 0;">
                <span style="background: #2ecc71; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 8px;"></span>
                Budget (&lt; $120/night)
            </div>
            <div style="margin: 5px 0;">
                <span style="background: #3498db; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 8px;"></span>
                Moderate ($120-180/night)
            </div>
            <div style="margin: 5px 0;">
                <span style="background: #f39c12; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 8px;"></span>
                Premium ($180-250/night)
            </div>
            <div style="margin: 5px 0;">
                <span style="background: #e74c3c; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 8px;"></span>
                Luxury (&gt; $250/night)
            </div>
            <hr style="margin: 10px 0;">
            <div style="margin: 5px 0;">
                <span style="color: #9b59b6; font-size: 14px; margin-right: 8px;">&#9733;</span>
                Your Property
            </div>
        </div>
        """

    def create_static_map(
        self,
        properties: List[Dict],
        output_path: str = None,
        figsize: Tuple[int, int] = (12, 10)
    ) -> Optional[str]:
        """
        Create a static matplotlib map (fallback when folium unavailable).

        Args:
            properties: List of property dictionaries
            output_path: Path to save image file
            figsize: Figure size tuple

        Returns:
            Path to saved image, or None if matplotlib not available
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("Cannot create static map: matplotlib not installed")
            return None

        logger.info("Creating static map visualization")

        fig, ax = plt.subplots(figsize=figsize)

        # Plot our property
        our_lat = self.our_location['latitude']
        our_lng = self.our_location['longitude']
        ax.scatter(
            our_lng, our_lat,
            c='purple', s=200, marker='*',
            label='Your Property', zorder=5
        )

        # Separate properties by platform and price category
        for prop in properties:
            lat = prop.get('latitude')
            lng = prop.get('longitude')

            if not lat or not lng:
                continue

            weekday = prop.get('weekday_rate', 0)
            weekend = prop.get('weekend_rate', 0)
            avg_rate = (weekday + weekend) / 2 if (weekday and weekend) else weekday or weekend

            color = self.get_marker_color(avg_rate)
            platform = prop.get('platform', 'Unknown')
            marker = 'o' if platform == 'Airbnb' else 's'

            ax.scatter(lng, lat, c=color, s=80, marker=marker, alpha=0.7, zorder=3)

        # Add search radius circle
        radius_km = self.config.search_params.get('max_distance_km', 2.0)
        # Approximate: 1 degree latitude ~ 111km
        radius_deg = radius_km / 111
        circle = plt.Circle(
            (our_lng, our_lat), radius_deg,
            fill=False, color='purple', linestyle='--', alpha=0.5
        )
        ax.add_patch(circle)

        # Create legend
        legend_elements = [
            mpatches.Patch(color='purple', label='Your Property'),
            mpatches.Patch(color='#2ecc71', label='Budget (<$120)'),
            mpatches.Patch(color='#3498db', label='Moderate ($120-180)'),
            mpatches.Patch(color='#f39c12', label='Premium ($180-250)'),
            mpatches.Patch(color='#e74c3c', label='Luxury (>$250)'),
        ]
        ax.legend(handles=legend_elements, loc='upper right')

        # Labels and title
        property_name = self.our_location.get('name', 'Your Property')
        ax.set_title(f'Competitor Properties Near {property_name}', fontsize=14)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.grid(True, alpha=0.3)

        # Equal aspect ratio
        ax.set_aspect('equal')

        # Save figure
        if output_path is None:
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = str(self.config.output_dir / f'property_map_{date_str}.png')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Static map saved to: {output_path}")
        return output_path

    def create_price_heatmap(
        self,
        properties: List[Dict],
        output_path: str = None
    ) -> Optional[str]:
        """
        Create a price heatmap overlay on the map.

        Args:
            properties: List of property dictionaries
            output_path: Path to save HTML file

        Returns:
            Path to saved file, or None if folium not available
        """
        if not FOLIUM_AVAILABLE:
            logger.error("Cannot create heatmap: folium not installed")
            return None

        logger.info("Creating price heatmap")

        center = (self.our_location['latitude'], self.our_location['longitude'])

        m = folium.Map(location=center, zoom_start=15, tiles='cartodbpositron')

        # Prepare heatmap data: [lat, lng, intensity]
        heat_data = []
        for prop in properties:
            lat = prop.get('latitude')
            lng = prop.get('longitude')
            if not lat or not lng:
                continue

            weekday = prop.get('weekday_rate', 0)
            weekend = prop.get('weekend_rate', 0)
            avg_rate = (weekday + weekend) / 2 if (weekday and weekend) else weekday or weekend

            # Normalize rate to intensity (higher price = more intensity)
            intensity = min(avg_rate / 200, 1.0)  # Cap at 200 for normalization
            heat_data.append([lat, lng, intensity])

        if heat_data:
            plugins.HeatMap(
                heat_data,
                min_opacity=0.3,
                radius=25,
                blur=15,
                gradient={
                    0.2: 'blue',
                    0.4: 'green',
                    0.6: 'yellow',
                    0.8: 'orange',
                    1.0: 'red'
                }
            ).add_to(m)

        # Add our property marker
        our_name = self.our_location.get('name', 'Our Property')
        folium.Marker(
            location=center,
            tooltip=our_name,
            icon=folium.Icon(color='purple', icon='star', prefix='fa')
        ).add_to(m)

        # Save
        if output_path is None:
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = str(self.config.output_dir / f'price_heatmap_{date_str}.html')

        m.save(output_path)
        logger.info(f"Price heatmap saved to: {output_path}")

        return output_path

    def plot_any_location(
        self,
        latitude: float,
        longitude: float,
        location_name: str = "Custom Location",
        properties: List[Dict] = None,
        radius_km: float = 2.0,
        output_path: str = None
    ) -> Optional[str]:
        """
        Plot any custom location with optional property data.

        This is the main entry point for plotting arbitrary locations.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            location_name: Name to display for the location
            properties: Optional list of nearby properties to plot
            radius_km: Search/display radius in km
            output_path: Path to save the map

        Returns:
            Path to saved HTML file
        """
        if not FOLIUM_AVAILABLE:
            logger.error("Cannot plot location: folium not installed")
            return None

        logger.info(f"Plotting location: {location_name} at ({latitude}, {longitude})")

        # Create map centered on the location
        m = folium.Map(
            location=[latitude, longitude],
            zoom_start=15,
            tiles='cartodbpositron'
        )

        # Add search radius circle
        folium.Circle(
            location=[latitude, longitude],
            radius=radius_km * 1000,
            color='#9b59b6',
            fill=True,
            fillOpacity=0.1,
            popup=f'Search radius: {radius_km}km'
        ).add_to(m)

        # Add the main location marker
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="color: #9b59b6; margin: 0 0 10px 0;">{location_name}</h4>
            <p style="margin: 5px 0;"><strong>Coordinates:</strong></p>
            <p style="margin: 5px 0;">Lat: {latitude:.6f}</p>
            <p style="margin: 5px 0;">Lng: {longitude:.6f}</p>
        </div>
        """

        folium.Marker(
            location=[latitude, longitude],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=location_name,
            icon=folium.Icon(color='purple', icon='star', prefix='fa')
        ).add_to(m)

        # Add property markers if provided
        if properties:
            for prop in properties:
                lat = prop.get('latitude')
                lng = prop.get('longitude')
                if not lat or not lng:
                    continue

                weekday = prop.get('weekday_rate', 0)
                weekend = prop.get('weekend_rate', 0)
                avg_rate = (weekday + weekend) / 2 if (weekday and weekend) else weekday or weekend

                color = self.get_marker_color(avg_rate)
                price_category = self.get_price_category(avg_rate)
                popup = self._create_property_popup(prop, avg_rate, price_category)

                folium.CircleMarker(
                    location=[lat, lng],
                    radius=8,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.7,
                    popup=folium.Popup(popup, max_width=350),
                    tooltip=f"{prop.get('name', 'Property')[:30]} - ${avg_rate:.0f}/night"
                ).add_to(m)

        # Add controls
        plugins.MiniMap(toggle_display=True).add_to(m)
        plugins.Fullscreen().add_to(m)

        # Add legend
        legend_html = self._create_legend_html()
        m.get_root().html.add_child(folium.Element(legend_html))

        # Save
        if output_path is None:
            date_str = datetime.now().strftime('%Y%m%d')
            safe_name = "".join(c if c.isalnum() else "_" for c in location_name)
            output_path = str(self.config.output_dir / f'map_{safe_name}_{date_str}.html')

        m.save(output_path)
        logger.info(f"Location map saved to: {output_path}")

        return output_path


def create_location_from_address(
    address: str,
    geocoding_api: str = None
) -> Optional[Tuple[float, float]]:
    """
    Convert an address to coordinates (requires geocoding API).

    This is a placeholder for geocoding functionality.
    In production, you would integrate with a geocoding service like:
    - Google Maps Geocoding API
    - OpenStreetMap Nominatim
    - Mapbox Geocoding

    Args:
        address: Street address string
        geocoding_api: Optional API key for geocoding service

    Returns:
        (latitude, longitude) tuple or None
    """
    # Known Melbourne locations for convenience
    KNOWN_LOCATIONS = {
        'south yarra': (-37.8388, 144.9924),
        'south melbourne': (-37.8283, 144.9550),
        'prahran': (-37.8499, 144.9926),
        'st kilda': (-37.8676, 144.9814),
        'richmond': (-37.8183, 144.9981),
        'fitzroy': (-37.7982, 144.9787),
        'carlton': (-37.7948, 144.9673),
        'collingwood': (-37.8028, 144.9876),
        'windsor': (-37.8563, 144.9913),
        'albert park': (-37.8419, 144.9540),
        'melbourne cbd': (-37.8136, 144.9631),
        'docklands': (-37.8145, 144.9442),
        'toorak': (-37.8407, 145.0137),
    }

    address_lower = address.lower()

    for location, coords in KNOWN_LOCATIONS.items():
        if location in address_lower:
            logger.info(f"Found known location '{location}' in address")
            return coords

    logger.warning(
        f"Could not geocode address: {address}. "
        "Consider integrating a geocoding API for full address support."
    )
    return None
