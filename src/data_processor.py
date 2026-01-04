"""
Data processor for cleaning, analyzing, and exporting scraped data.
"""
import logging
import json
import csv
from datetime import datetime
from typing import List, Dict, Tuple
from math import radians, cos, sin, asin, sqrt
import pandas as pd


logger = logging.getLogger(__name__)


class DataProcessor:
    """Processor for scraped property data."""

    def __init__(self, config):
        """
        Initialize data processor.

        Args:
            config: Configuration object
        """
        self.config = config
        self.our_location = config.our_location

    def calculate_distance(
        self,
        property_coords: Tuple[float, float],
        our_coords: Tuple[float, float] = None
    ) -> float:
        """
        Calculate distance in km using Haversine formula.

        Args:
            property_coords: (latitude, longitude) of property
            our_coords: (latitude, longitude) of our property

        Returns:
            Distance in kilometers
        """
        if our_coords is None:
            our_coords = (
                self.our_location['latitude'],
                self.our_location['longitude']
            )

        lat1, lon1 = our_coords
        lat2, lon2 = property_coords

        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))

        # Radius of Earth in kilometers
        r = 6371

        return c * r

    def merge_weekday_weekend_data(
        self,
        weekday_properties: List[Dict],
        weekend_properties: List[Dict]
    ) -> List[Dict]:
        """
        Merge weekday and weekend pricing data.

        Args:
            weekday_properties: List of properties from weekday search
            weekend_properties: List of properties from weekend search

        Returns:
            List of merged property data
        """
        logger.info("Merging weekday and weekend data...")

        # Create lookup by property ID
        weekday_map = {p['property_id']: p for p in weekday_properties}
        weekend_map = {p['property_id']: p for p in weekend_properties}

        merged = []

        # Get all unique property IDs
        all_ids = set(weekday_map.keys()) | set(weekend_map.keys())

        for prop_id in all_ids:
            weekday = weekday_map.get(prop_id, {})
            weekend = weekend_map.get(prop_id, {})

            # Use weekday as base, supplement with weekend
            if weekday:
                base = weekday.copy()
            else:
                base = weekend.copy()

            # Add both rates
            base['weekday_rate'] = weekday.get('nightly_rate', 0)
            base['weekend_rate'] = weekend.get('nightly_rate', 0)

            # Calculate distance
            if base.get('latitude') and base.get('longitude'):
                base['distance_km'] = self.calculate_distance(
                    (base['latitude'], base['longitude'])
                )
            else:
                base['distance_km'] = 0

            # Calculate totals
            base['total_2night_weekday'] = (
                base['weekday_rate'] * 2 +
                base.get('cleaning_fee', 0) +
                base.get('service_fee', 0)
            )
            base['total_2night_weekend'] = (
                base['weekend_rate'] * 2 +
                base.get('cleaning_fee', 0) +
                base.get('service_fee', 0)
            )

            merged.append(base)

        logger.info(f"Merged {len(merged)} unique properties")
        return merged

    def filter_by_distance(
        self,
        properties: List[Dict],
        max_distance_km: float = None
    ) -> List[Dict]:
        """
        Filter properties by distance.

        Args:
            properties: List of properties
            max_distance_km: Maximum distance in km

        Returns:
            Filtered list of properties
        """
        if max_distance_km is None:
            max_distance_km = self.config.search_params['max_distance_km']

        filtered = [
            p for p in properties
            if p.get('distance_km', 0) <= max_distance_km
        ]

        logger.info(f"Filtered to {len(filtered)} properties within {max_distance_km}km")
        return filtered

    def generate_summary_stats(
        self,
        properties: List[Dict]
    ) -> Dict:
        """
        Calculate market averages and our position.

        Args:
            properties: List of properties

        Returns:
            Summary statistics dictionary
        """
        logger.info("Generating summary statistics...")

        if not properties:
            logger.warning("No properties to analyze")
            return {}

        # Separate by platform
        airbnb_props = [p for p in properties if p['platform'] == 'Airbnb']
        booking_props = [p for p in properties if p['platform'] == 'Booking.com']

        # Calculate averages
        weekday_rates = [p['weekday_rate'] for p in properties if p.get('weekday_rate', 0) > 0]
        weekend_rates = [p['weekend_rate'] for p in properties if p.get('weekend_rate', 0) > 0]
        cleaning_fees = [p['cleaning_fee'] for p in properties if p.get('cleaning_fee', 0) > 0]

        avg_weekday = sum(weekday_rates) / len(weekday_rates) if weekday_rates else 0
        avg_weekend = sum(weekend_rates) / len(weekend_rates) if weekend_rates else 0
        avg_cleaning = sum(cleaning_fees) / len(cleaning_fees) if cleaning_fees else 0

        # Calculate ranges
        cleaning_fee_range = {
            'min': min(cleaning_fees) if cleaning_fees else 0,
            'max': max(cleaning_fees) if cleaning_fees else 0
        }

        rate_range = {
            'min': min(weekday_rates + weekend_rates) if (weekday_rates or weekend_rates) else 0,
            'max': max(weekday_rates + weekend_rates) if (weekday_rates or weekend_rates) else 0
        }

        # Our performance vs market
        our_weekday = self.our_location['current_rates']['weekday_rate']
        our_cleaning = self.our_location['current_rates']['cleaning_fee']

        weekday_vs_market = ((our_weekday - avg_weekday) / avg_weekday * 100) if avg_weekday else 0
        cleaning_vs_market = ((our_cleaning - avg_cleaning) / avg_cleaning * 100) if avg_cleaning else 0

        # Generate recommendation
        recommendation = self._generate_recommendation(
            avg_cleaning,
            avg_weekday,
            avg_weekend,
            our_weekday,
            our_cleaning
        )

        summary = {
            'date_collected': datetime.now().isoformat(),
            'search_parameters': {
                'weekday_dates': f"{self.config.dates['weekday_checkin']} to {self.config.dates['weekday_checkout']}",
                'weekend_dates': f"{self.config.dates['weekend_checkin']} to {self.config.dates['weekend_checkout']}",
                'max_distance_km': self.config.search_params['max_distance_km']
            },
            'market_analysis': {
                'total_properties': len(properties),
                'airbnb_count': len(airbnb_props),
                'booking_count': len(booking_props),
                'avg_weekday_rate': round(avg_weekday, 2),
                'avg_weekend_rate': round(avg_weekend, 2),
                'avg_cleaning_fee': round(avg_cleaning, 2),
                'cleaning_fee_range': cleaning_fee_range,
                'rate_range': rate_range
            },
            'our_performance': {
                'our_weekday_rate': our_weekday,
                'position_vs_market': f"{weekday_vs_market:+.1f}%",
                'our_cleaning_fee': our_cleaning,
                'cleaning_fee_vs_market': f"{cleaning_vs_market:+.1f}%",
                'recommendation': recommendation
            }
        }

        return summary

    def _generate_recommendation(
        self,
        avg_cleaning: float,
        avg_weekday: float,
        avg_weekend: float,
        our_weekday: float,
        our_cleaning: float
    ) -> str:
        """Generate pricing recommendation."""
        recommendations = []

        # Cleaning fee recommendation
        if avg_cleaning > 0:
            if our_cleaning < avg_cleaning * 0.85:
                target = round(avg_cleaning, -1)  # Round to nearest 10
                recommendations.append(
                    f"Consider increasing cleaning fee to ${target:.0f}-${target+10:.0f} to match market"
                )
            elif our_cleaning > avg_cleaning * 1.15:
                recommendations.append(
                    "Your cleaning fee is above market average. Monitor competitor bookings."
                )
            else:
                recommendations.append("Your cleaning fee is competitive with the market.")

        # Rate recommendation
        if avg_weekday > 0:
            if our_weekday < avg_weekday * 0.90:
                recommendations.append(
                    f"Your nightly rate (${our_weekday}) is below market average (${avg_weekday:.0f}). Consider gradual increase."
                )
            elif our_weekday > avg_weekday * 1.10:
                recommendations.append(
                    "Your nightly rate is above market. Ensure value justifies premium."
                )
            else:
                recommendations.append("Your nightly rate is well-positioned.")

        return " ".join(recommendations) if recommendations else "Insufficient data for recommendations."

    def export_to_csv(
        self,
        properties: List[Dict],
        filename: str
    ) -> None:
        """
        Export cleaned data to CSV.

        Args:
            properties: List of properties
            filename: Output filename
        """
        logger.info(f"Exporting to CSV: {filename}")

        if not properties:
            logger.warning("No properties to export")
            return

        # Define CSV columns
        columns = [
            'Platform', 'Property_Name', 'URL', 'Distance_km',
            'Bedrooms', 'Bathrooms', 'Max_Guests',
            'Weekday_Rate', 'Weekend_Rate', 'Cleaning_Fee', 'Service_Fee',
            'Total_2Night_Weekday', 'Total_2Night_Weekend',
            'Cancellation_Policy', 'Review_Count', 'Rating',
            'Key_Amenities', 'Date_Scraped'
        ]

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            for prop in properties:
                # Format amenities
                amenities = prop.get('amenities', [])
                if isinstance(amenities, list):
                    amenities_str = ', '.join(amenities[:5])  # Top 5 amenities
                else:
                    amenities_str = str(amenities)

                row = {
                    'Platform': prop.get('platform', ''),
                    'Property_Name': prop.get('name', ''),
                    'URL': prop.get('url', ''),
                    'Distance_km': round(prop.get('distance_km', 0), 2),
                    'Bedrooms': prop.get('bedrooms', 0),
                    'Bathrooms': prop.get('bathrooms', 0),
                    'Max_Guests': prop.get('max_guests', 0),
                    'Weekday_Rate': prop.get('weekday_rate', 0),
                    'Weekend_Rate': prop.get('weekend_rate', 0),
                    'Cleaning_Fee': prop.get('cleaning_fee', 0),
                    'Service_Fee': prop.get('service_fee', 0),
                    'Total_2Night_Weekday': prop.get('total_2night_weekday', 0),
                    'Total_2Night_Weekend': prop.get('total_2night_weekend', 0),
                    'Cancellation_Policy': prop.get('cancellation_policy', ''),
                    'Review_Count': prop.get('review_count', 0),
                    'Rating': prop.get('rating', 0),
                    'Key_Amenities': amenities_str,
                    'Date_Scraped': prop.get('date_scraped', '')
                }

                writer.writerow(row)

        logger.info(f"Exported {len(properties)} properties to CSV")

    def export_to_json(
        self,
        data: Dict,
        filename: str
    ) -> None:
        """
        Export data to JSON.

        Args:
            data: Data dictionary
            filename: Output filename
        """
        logger.info(f"Exporting to JSON: {filename}")

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info("JSON export complete")

    def save_raw_data(
        self,
        data: Dict,
        platform: str,
        date_str: str
    ) -> None:
        """
        Save raw data to JSON file.

        Args:
            data: Raw data
            platform: Platform name (airbnb or booking)
            date_str: Date string for filename
        """
        raw_dir = self.config.data_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)

        filename = raw_dir / f"{platform}_raw_{date_str}.json"
        self.export_to_json(data, str(filename))

    def process_and_export(
        self,
        airbnb_data: Dict,
        booking_data: Dict,
        date_str: str = None
    ) -> Dict:
        """
        Process all data and export to files.

        Args:
            airbnb_data: Airbnb weekday/weekend data
            booking_data: Booking.com weekday/weekend data
            date_str: Date string for filenames

        Returns:
            Summary statistics
        """
        if date_str is None:
            date_str = datetime.now().strftime(self.config.output_settings['date_format'])

        logger.info("Processing and exporting data...")

        # Save raw data if configured
        if self.config.output_settings['save_raw_json']:
            self.save_raw_data(airbnb_data, 'airbnb', date_str)
            self.save_raw_data(booking_data, 'booking', date_str)

        # Merge weekday/weekend for each platform
        airbnb_merged = self.merge_weekday_weekend_data(
            airbnb_data.get('weekday', []),
            airbnb_data.get('weekend', [])
        )

        booking_merged = self.merge_weekday_weekend_data(
            booking_data.get('weekday', []),
            booking_data.get('weekend', [])
        )

        # Combine all properties
        all_properties = airbnb_merged + booking_merged

        # Filter by distance
        filtered_properties = self.filter_by_distance(all_properties)

        # Generate summary statistics
        summary = self.generate_summary_stats(filtered_properties)

        # Export to CSV
        if self.config.output_settings['save_processed_csv']:
            csv_filename = self.config.output_dir / f"competitors_{date_str}.csv"
            self.export_to_csv(filtered_properties, str(csv_filename))

        # Export summary
        if self.config.output_settings['save_summary']:
            summary_filename = self.config.output_dir / f"summary_{date_str}.json"
            self.export_to_json(summary, str(summary_filename))

        # Export full data
        full_data = {
            'summary': summary,
            'properties': filtered_properties
        }
        full_filename = self.config.output_dir / f"full_data_{date_str}.json"
        self.export_to_json(full_data, str(full_filename))

        logger.info("Data processing and export complete!")

        return summary

    def create_location_maps(
        self,
        properties: List[Dict],
        date_str: str = None
    ) -> Dict[str, str]:
        """
        Create location maps for the scraped properties.

        Args:
            properties: List of property dictionaries with coordinates
            date_str: Date string for filenames

        Returns:
            Dictionary with paths to created map files
        """
        try:
            from location_plotter import LocationPlotter
        except ImportError:
            logger.warning("LocationPlotter not available - skipping map generation")
            return {}

        if date_str is None:
            date_str = datetime.now().strftime(self.config.output_settings['date_format'])

        plotter = LocationPlotter(self.config)
        plotting_settings = self.config.plotting_settings
        created_maps = {}

        # Create interactive map
        if plotting_settings.get('create_interactive_map', True):
            map_path = plotter.create_interactive_map(
                properties=properties,
                show_radius=plotting_settings.get('show_search_radius', True),
                radius_km=self.config.search_params.get('max_distance_km', 2.0)
            )
            if map_path:
                created_maps['interactive_map'] = map_path
                logger.info(f"Interactive map created: {map_path}")

        # Create heatmap
        if plotting_settings.get('create_heatmap', False):
            heatmap_path = plotter.create_price_heatmap(properties=properties)
            if heatmap_path:
                created_maps['price_heatmap'] = heatmap_path
                logger.info(f"Price heatmap created: {heatmap_path}")

        return created_maps
