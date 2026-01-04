#!/usr/bin/env python3
"""
Demo script to showcase pricing around Darling St, South Yarra.
Generates an interactive map with sample competitor data.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import Config
from data_processor import DataProcessor
from location_plotter import LocationPlotter

# Sample competitor properties around South Yarra (realistic Melbourne data)
SAMPLE_COMPETITORS = [
    {
        'property_id': 'airbnb_sy_001',
        'platform': 'Airbnb',
        'name': 'Stylish Studio on Chapel Street',
        'url': 'https://airbnb.com/rooms/sy001',
        'latitude': -37.8410,
        'longitude': 144.9945,
        'weekday_rate': 135,
        'weekend_rate': 155,
        'cleaning_fee': 65,
        'service_fee': 35,
        'bedrooms': 1,
        'bathrooms': 1,
        'max_guests': 2,
        'rating': 4.85,
        'review_count': 127,
        'amenities': ['WiFi', 'Kitchen', 'Air conditioning', 'Washer'],
        'date_scraped': '2026-01-04'
    },
    {
        'property_id': 'airbnb_sy_002',
        'platform': 'Airbnb',
        'name': 'Modern 1BR near Toorak Rd',
        'url': 'https://airbnb.com/rooms/sy002',
        'latitude': -37.8365,
        'longitude': 144.9880,
        'weekday_rate': 165,
        'weekend_rate': 185,
        'cleaning_fee': 80,
        'service_fee': 42,
        'bedrooms': 1,
        'bathrooms': 1,
        'max_guests': 2,
        'rating': 4.72,
        'review_count': 89,
        'amenities': ['WiFi', 'Kitchen', 'Parking', 'Pool'],
        'date_scraped': '2026-01-04'
    },
    {
        'property_id': 'airbnb_sy_003',
        'platform': 'Airbnb',
        'name': 'Luxury Apartment with City Views',
        'url': 'https://airbnb.com/rooms/sy003',
        'latitude': -37.8352,
        'longitude': 144.9958,
        'weekday_rate': 220,
        'weekend_rate': 265,
        'cleaning_fee': 100,
        'service_fee': 55,
        'bedrooms': 2,
        'bathrooms': 1,
        'max_guests': 4,
        'rating': 4.92,
        'review_count': 203,
        'amenities': ['WiFi', 'Kitchen', 'Gym', 'Concierge'],
        'date_scraped': '2026-01-04'
    },
    {
        'property_id': 'airbnb_sy_004',
        'platform': 'Airbnb',
        'name': 'Cozy Retreat in Prahran',
        'url': 'https://airbnb.com/rooms/sy004',
        'latitude': -37.8485,
        'longitude': 144.9920,
        'weekday_rate': 110,
        'weekend_rate': 130,
        'cleaning_fee': 55,
        'service_fee': 28,
        'bedrooms': 1,
        'bathrooms': 1,
        'max_guests': 2,
        'rating': 4.65,
        'review_count': 56,
        'amenities': ['WiFi', 'Kitchen'],
        'date_scraped': '2026-01-04'
    },
    {
        'property_id': 'airbnb_sy_005',
        'platform': 'Airbnb',
        'name': 'Designer Loft South Yarra',
        'url': 'https://airbnb.com/rooms/sy005',
        'latitude': -37.8395,
        'longitude': 144.9905,
        'weekday_rate': 175,
        'weekend_rate': 195,
        'cleaning_fee': 85,
        'service_fee': 45,
        'bedrooms': 1,
        'bathrooms': 1,
        'max_guests': 3,
        'rating': 4.88,
        'review_count': 142,
        'amenities': ['WiFi', 'Kitchen', 'Balcony', 'Smart TV'],
        'date_scraped': '2026-01-04'
    },
    {
        'property_id': 'booking_sy_001',
        'platform': 'Booking.com',
        'name': 'The Como Melbourne - MGallery',
        'url': 'https://booking.com/hotel/sy001',
        'latitude': -37.8420,
        'longitude': 144.9935,
        'weekday_rate': 280,
        'weekend_rate': 320,
        'cleaning_fee': 0,
        'service_fee': 0,
        'bedrooms': 1,
        'bathrooms': 1,
        'max_guests': 2,
        'rating': 9.1,
        'review_count': 1250,
        'amenities': ['WiFi', 'Pool', 'Spa', 'Restaurant'],
        'date_scraped': '2026-01-04'
    },
    {
        'property_id': 'booking_sy_002',
        'platform': 'Booking.com',
        'name': 'Quest South Yarra',
        'url': 'https://booking.com/hotel/sy002',
        'latitude': -37.8378,
        'longitude': 144.9912,
        'weekday_rate': 155,
        'weekend_rate': 175,
        'cleaning_fee': 0,
        'service_fee': 0,
        'bedrooms': 1,
        'bathrooms': 1,
        'max_guests': 2,
        'rating': 8.5,
        'review_count': 890,
        'amenities': ['WiFi', 'Kitchen', 'Parking'],
        'date_scraped': '2026-01-04'
    },
    {
        'property_id': 'airbnb_sy_006',
        'platform': 'Airbnb',
        'name': 'Budget-Friendly Studio',
        'url': 'https://airbnb.com/rooms/sy006',
        'latitude': -37.8445,
        'longitude': 144.9895,
        'weekday_rate': 95,
        'weekend_rate': 115,
        'cleaning_fee': 45,
        'service_fee': 25,
        'bedrooms': 0,
        'bathrooms': 1,
        'max_guests': 2,
        'rating': 4.52,
        'review_count': 34,
        'amenities': ['WiFi', 'Kitchenette'],
        'date_scraped': '2026-01-04'
    },
    {
        'property_id': 'airbnb_sy_007',
        'platform': 'Airbnb',
        'name': 'Charming Victorian Terrace',
        'url': 'https://airbnb.com/rooms/sy007',
        'latitude': -37.8372,
        'longitude': 144.9962,
        'weekday_rate': 195,
        'weekend_rate': 225,
        'cleaning_fee': 90,
        'service_fee': 50,
        'bedrooms': 2,
        'bathrooms': 2,
        'max_guests': 4,
        'rating': 4.95,
        'review_count': 178,
        'amenities': ['WiFi', 'Kitchen', 'Garden', 'Parking'],
        'date_scraped': '2026-01-04'
    },
    {
        'property_id': 'airbnb_sy_008',
        'platform': 'Airbnb',
        'name': 'Trendy Pad near Botanical Gardens',
        'url': 'https://airbnb.com/rooms/sy008',
        'latitude': -37.8330,
        'longitude': 144.9890,
        'weekday_rate': 145,
        'weekend_rate': 165,
        'cleaning_fee': 70,
        'service_fee': 38,
        'bedrooms': 1,
        'bathrooms': 1,
        'max_guests': 2,
        'rating': 4.78,
        'review_count': 95,
        'amenities': ['WiFi', 'Kitchen', 'Bike'],
        'date_scraped': '2026-01-04'
    },
]


def main():
    print("=" * 70)
    print("DARLING ST, SOUTH YARRA - COMPETITOR PRICE ANALYSIS")
    print("=" * 70)

    # Load config
    config = Config()
    config.ensure_directories()

    print(f"\n📍 Your Property: {config.our_location['name']}")
    print(f"   Location: ({config.our_location['latitude']}, {config.our_location['longitude']})")
    print(f"   Your Weekday Rate: ${config.our_location['current_rates']['weekday_rate']}")
    print(f"   Your Weekend Rate: ${config.our_location['current_rates']['weekend_rate']}")
    print(f"   Your Cleaning Fee: ${config.our_location['current_rates']['cleaning_fee']}")

    # Process sample data
    processor = DataProcessor(config)

    # Add distance calculations
    for prop in SAMPLE_COMPETITORS:
        prop['distance_km'] = processor.calculate_distance(
            (prop['latitude'], prop['longitude'])
        )
        # Calculate totals
        prop['total_2night_weekday'] = (
            prop['weekday_rate'] * 2 +
            prop.get('cleaning_fee', 0) +
            prop.get('service_fee', 0)
        )
        prop['total_2night_weekend'] = (
            prop['weekend_rate'] * 2 +
            prop.get('cleaning_fee', 0) +
            prop.get('service_fee', 0)
        )

    # Filter by distance
    filtered = processor.filter_by_distance(SAMPLE_COMPETITORS, max_distance_km=2.0)

    print(f"\n📊 MARKET ANALYSIS ({len(filtered)} competitors within 2km)")
    print("-" * 50)

    # Calculate statistics
    weekday_rates = [p['weekday_rate'] for p in filtered]
    weekend_rates = [p['weekend_rate'] for p in filtered]
    cleaning_fees = [p['cleaning_fee'] for p in filtered if p['cleaning_fee'] > 0]

    avg_weekday = sum(weekday_rates) / len(weekday_rates)
    avg_weekend = sum(weekend_rates) / len(weekend_rates)
    avg_cleaning = sum(cleaning_fees) / len(cleaning_fees) if cleaning_fees else 0

    print(f"\n   Market Averages:")
    print(f"   • Weekday Rate: ${avg_weekday:.2f}/night")
    print(f"   • Weekend Rate: ${avg_weekend:.2f}/night")
    print(f"   • Cleaning Fee: ${avg_cleaning:.2f} (Airbnb only)")

    print(f"\n   Rate Range:")
    print(f"   • Weekday: ${min(weekday_rates)} - ${max(weekday_rates)}/night")
    print(f"   • Weekend: ${min(weekend_rates)} - ${max(weekend_rates)}/night")

    # Your position
    your_weekday = config.our_location['current_rates']['weekday_rate']
    your_cleaning = config.our_location['current_rates']['cleaning_fee']

    weekday_diff = ((your_weekday - avg_weekday) / avg_weekday) * 100
    cleaning_diff = ((your_cleaning - avg_cleaning) / avg_cleaning) * 100 if avg_cleaning else 0

    print(f"\n   Your Position vs Market:")
    print(f"   • Weekday Rate: {weekday_diff:+.1f}% vs average")
    print(f"   • Cleaning Fee: {cleaning_diff:+.1f}% vs average")

    # Price distribution
    print(f"\n   Price Category Distribution:")
    budget = sum(1 for p in filtered if p['weekday_rate'] < 120)
    moderate = sum(1 for p in filtered if 120 <= p['weekday_rate'] < 180)
    premium = sum(1 for p in filtered if 180 <= p['weekday_rate'] < 250)
    luxury = sum(1 for p in filtered if p['weekday_rate'] >= 250)

    print(f"   • Budget (<$120):     {budget} properties")
    print(f"   • Moderate ($120-180): {moderate} properties")
    print(f"   • Premium ($180-250):  {premium} properties")
    print(f"   • Luxury (>$250):      {luxury} properties")

    # Generate interactive map
    print(f"\n🗺️  GENERATING INTERACTIVE MAP")
    print("-" * 50)

    plotter = LocationPlotter(config)

    # Create main interactive map
    map_path = plotter.create_interactive_map(
        properties=filtered,
        show_radius=True,
        radius_km=2.0
    )
    print(f"   ✓ Interactive map: {map_path}")

    # Create price heatmap
    heatmap_path = plotter.create_price_heatmap(properties=filtered)
    print(f"   ✓ Price heatmap: {heatmap_path}")

    # List competitors sorted by distance
    print(f"\n📋 COMPETITOR LISTINGS (sorted by distance)")
    print("-" * 70)

    sorted_props = sorted(filtered, key=lambda x: x['distance_km'])

    for i, prop in enumerate(sorted_props, 1):
        avg_rate = (prop['weekday_rate'] + prop['weekend_rate']) / 2
        print(f"\n   {i}. {prop['name'][:40]}")
        print(f"      Platform: {prop['platform']} | Distance: {prop['distance_km']:.2f}km")
        print(f"      Rates: ${prop['weekday_rate']}/weekday, ${prop['weekend_rate']}/weekend")
        print(f"      Cleaning: ${prop['cleaning_fee']} | Rating: {prop['rating']} ({prop['review_count']} reviews)")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"\nOpen the interactive map in your browser:")
    print(f"  file://{map_path}")
    print()


if __name__ == '__main__':
    main()
