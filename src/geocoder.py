"""
Geocoding utilities for converting addresses to coordinates.
"""
import logging
import requests
from typing import Dict, Optional, Tuple


logger = logging.getLogger(__name__)


class Geocoder:
    """Geocoder using Nominatim (OpenStreetMap) API."""

    def __init__(self):
        """Initialize geocoder."""
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'OTA-Scraper/1.0 (Competitive Intelligence Tool)'
        }

    def geocode_address(self, address: str, city: str = None, country: str = "Australia") -> Optional[Dict]:
        """
        Convert address to coordinates using Nominatim.

        Args:
            address: Street address
            city: City name
            country: Country name (default: Australia)

        Returns:
            Dictionary with lat, lng, and display_name, or None if not found
        """
        # Build search query
        query_parts = [address]
        if city:
            query_parts.append(city)
        query_parts.append(country)

        query = ", ".join(query_parts)

        logger.info(f"Geocoding address: {query}")

        try:
            params = {
                'q': query,
                'format': 'json',
                'limit': 1
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            results = response.json()

            if not results:
                logger.warning(f"No results found for address: {query}")
                return None

            result = results[0]

            return {
                'latitude': float(result['lat']),
                'longitude': float(result['lon']),
                'display_name': result['display_name']
            }

        except Exception as e:
            logger.error(f"Error geocoding address: {e}")
            return None


def calculate_bounding_box(
    center_lat: float,
    center_lng: float,
    radius_km: float
) -> Dict[str, float]:
    """
    Calculate bounding box coordinates from center point and radius.

    Args:
        center_lat: Center latitude
        center_lng: Center longitude
        radius_km: Radius in kilometers

    Returns:
        Dictionary with ne_lat, ne_long, sw_lat, sw_long
    """
    # Approximate conversion (good enough for small areas)
    # 1 degree latitude ≈ 111 km
    # 1 degree longitude varies by latitude

    import math

    lat_offset = radius_km / 111.0
    lng_offset = radius_km / (111.0 * math.cos(math.radians(center_lat)))

    return {
        'ne_lat': center_lat + lat_offset,
        'ne_long': center_lng + lng_offset,
        'sw_lat': center_lat - lat_offset,
        'sw_long': center_lng - lng_offset,
        'center_lat': center_lat,
        'center_lng': center_lng
    }


def get_location_from_address(
    address: str,
    city: str = None,
    radius_km: float = 2.0
) -> Optional[Dict]:
    """
    Get location data from address including bounding box.

    Args:
        address: Street address
        city: City name
        radius_km: Search radius in kilometers

    Returns:
        Dictionary with location data or None if geocoding fails
    """
    geocoder = Geocoder()
    result = geocoder.geocode_address(address, city)

    if not result:
        return None

    # Calculate bounding box
    bbox = calculate_bounding_box(
        result['latitude'],
        result['longitude'],
        radius_km
    )

    return {
        'name': address,
        'latitude': result['latitude'],
        'longitude': result['longitude'],
        'display_name': result['display_name'],
        'bounding_box': bbox,
        'radius_km': radius_km
    }
