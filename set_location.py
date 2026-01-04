#!/usr/bin/env python3
"""
Interactive script to set your property location for competitive scraping.
"""
import sys
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from geocoder import get_location_from_address, calculate_bounding_box


def set_location_from_address():
    """Interactive address-based location setting."""
    print("=" * 60)
    print("SET PROPERTY LOCATION")
    print("=" * 60)
    print()

    # Get address
    address = input("Enter street address (e.g., 'Darling Street'): ").strip()
    if not address:
        print("Error: Address is required")
        return

    city = input("Enter city/suburb (e.g., 'South Yarra'): ").strip()
    if not city:
        print("Error: City is required")
        return

    # Get radius
    radius_input = input("Search radius in km [default: 2.0]: ").strip()
    radius_km = 2.0
    if radius_input:
        try:
            radius_km = float(radius_input)
        except ValueError:
            print("Invalid radius, using default 2.0 km")

    # Geocode
    print(f"\nGeocoding '{address}, {city}, Australia'...")
    location_data = get_location_from_address(address, city, radius_km)

    if not location_data:
        print("❌ Could not find location. Please check the address and try again.")
        return

    print(f"✓ Found: {location_data['display_name']}")
    print(f"  Latitude: {location_data['latitude']}")
    print(f"  Longitude: {location_data['longitude']}")
    print(f"  Search radius: {radius_km} km")

    # Get property details
    print("\nProperty Details:")
    property_name = input("Property name [default: 'My Property']: ").strip() or "My Property"

    # Get current rates
    weekday_rate = input("Current weekday rate (AUD) [default: 145]: ").strip()
    weekday_rate = int(weekday_rate) if weekday_rate else 145

    cleaning_fee = input("Current cleaning fee (AUD) [default: 90]: ").strip()
    cleaning_fee = int(cleaning_fee) if cleaning_fee else 90

    actual_cleaning = input("Actual cleaning cost (AUD) [default: 125]: ").strip()
    actual_cleaning = int(actual_cleaning) if actual_cleaning else 125

    # Update config
    update_config(location_data, property_name, weekday_rate, cleaning_fee, actual_cleaning)

    print("\n✅ Location updated successfully!")
    print(f"\nYou can now run the scraper:")
    print(f"  python run_scraper.py")


def set_location_from_coordinates():
    """Manual coordinate-based location setting."""
    print("=" * 60)
    print("SET PROPERTY LOCATION (Manual Coordinates)")
    print("=" * 60)
    print()

    try:
        lat = float(input("Enter latitude (e.g., -37.8439): ").strip())
        lng = float(input("Enter longitude (e.g., 144.9944): ").strip())
        radius_km = float(input("Search radius in km [default: 2.0]: ").strip() or "2.0")
        property_name = input("Property name: ").strip() or "My Property"

        # Get current rates
        weekday_rate = int(input("Current weekday rate (AUD) [145]: ").strip() or "145")
        cleaning_fee = int(input("Current cleaning fee (AUD) [90]: ").strip() or "90")
        actual_cleaning = int(input("Actual cleaning cost (AUD) [125]: ").strip() or "125")

        # Calculate bounding box
        bbox = calculate_bounding_box(lat, lng, radius_km)

        location_data = {
            'name': property_name,
            'latitude': lat,
            'longitude': lng,
            'display_name': f"{property_name} ({lat}, {lng})",
            'bounding_box': bbox,
            'radius_km': radius_km
        }

        update_config(location_data, property_name, weekday_rate, cleaning_fee, actual_cleaning)

        print("\n✅ Location updated successfully!")

    except ValueError:
        print("❌ Invalid input. Please enter valid numbers.")


def update_config(location_data, property_name, weekday_rate, cleaning_fee, actual_cleaning):
    """Update config.yaml with new location."""
    config_path = Path(__file__).parent / "config.yaml"

    # Load existing config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Update location
    bbox = location_data['bounding_box']

    config['our_location'] = {
        'latitude': location_data['latitude'],
        'longitude': location_data['longitude'],
        'name': property_name,
        'display_name': location_data['display_name'],
        'current_rates': {
            'weekday_rate': weekday_rate,
            'weekend_rate': weekday_rate,  # Same as weekday for now
            'cleaning_fee': cleaning_fee,
            'actual_cleaning_cost': actual_cleaning
        }
    }

    # Update search parameters with bounding box
    config['search']['max_distance_km'] = location_data['radius_km']
    config['search']['airbnb']['ne_lat'] = bbox['ne_lat']
    config['search']['airbnb']['ne_long'] = bbox['ne_long']
    config['search']['airbnb']['sw_lat'] = bbox['sw_lat']
    config['search']['airbnb']['sw_long'] = bbox['sw_long']

    # Update Booking.com city if possible
    if 'display_name' in location_data:
        # Try to extract city from display name
        parts = location_data['display_name'].split(',')
        if len(parts) >= 2:
            city = parts[1].strip()
            config['search']['booking']['city'] = city

    # Save updated config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"\n📝 Updated config.yaml:")
    print(f"   Location: {location_data['display_name']}")
    print(f"   Coordinates: ({location_data['latitude']}, {location_data['longitude']})")
    print(f"   Bounding box: ({bbox['sw_lat']}, {bbox['sw_long']}) to ({bbox['ne_lat']}, {bbox['ne_long']})")
    print(f"   Search radius: {location_data['radius_km']} km")


def main():
    """Main entry point."""
    print()
    print("🏠 OTA Scraper - Location Setup")
    print()
    print("Choose how you want to set your location:")
    print()
    print("1. Enter address (automatic geocoding)")
    print("2. Enter coordinates manually")
    print("3. Exit")
    print()

    choice = input("Enter choice [1]: ").strip() or "1"

    if choice == "1":
        set_location_from_address()
    elif choice == "2":
        set_location_from_coordinates()
    elif choice == "3":
        print("Exiting...")
        return
    else:
        print("Invalid choice")


if __name__ == '__main__':
    main()
