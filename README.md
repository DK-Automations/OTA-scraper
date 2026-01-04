# Airbnb & Booking.com Competitive Intelligence Scraper

A Python-based scraper to collect pricing and cleaning fee data from Airbnb and Booking.com competitors for the Darling Street Residence in South Melbourne, Australia.

## Overview

This tool helps answer critical business questions:
- What are competitors charging for cleaning fees?
- What are typical nightly rates for similar 1BR apartments?
- Should we increase our cleaning fee from $90 to $125?
- Are our nightly rates competitive?

## Project Structure

```
competitive-intelligence-scraper/
├── src/
│   ├── __init__.py
│   ├── airbnb_scraper.py      # Airbnb scraping logic
│   ├── booking_scraper.py     # Booking.com scraping logic
│   ├── data_processor.py      # Data cleaning & analysis
│   └── config.py              # Configuration settings
├── data/
│   ├── raw/                   # Raw JSON responses
│   ├── processed/             # Cleaned CSV files
│   └── archive/               # Historical data
├── output/
│   ├── competitors_YYYYMMDD.csv
│   ├── summary_YYYYMMDD.json
│   └── full_data_YYYYMMDD.json
├── requirements.txt
├── config.yaml
├── run_scraper.py             # Main execution script
└── README.md
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure search parameters (optional):
   - Edit `config.yaml` to customize search area, dates, or filters
   - Default configuration is set for South Melbourne, 1BR apartments

## Usage

### Basic Usage

Run the scraper with default settings:
```bash
python run_scraper.py
```

This will:
- Search Airbnb for competitors
- Search Booking.com for competitors
- Generate CSV and JSON reports in the `output/` directory

### Advanced Usage

#### Scrape only Airbnb:
```bash
python run_scraper.py --platform airbnb
```

#### Scrape only Booking.com:
```bash
python run_scraper.py --platform booking
```

#### Limit results:
```bash
python run_scraper.py --max-results 5
```

#### Custom config file:
```bash
python run_scraper.py --config custom_config.yaml
```

#### Verbose logging:
```bash
python run_scraper.py --verbose
```

#### Custom output directory:
```bash
python run_scraper.py --output-dir /path/to/output
```

### Command Line Options

```
Options:
  --config PATH          Path to config.yaml file
  --platform {airbnb,booking,both}
                        Platform to scrape (default: both)
  --output-dir PATH     Output directory for results
  --max-results N       Maximum number of results per platform
  --verbose             Enable verbose logging
  -h, --help            Show help message
```

## Configuration

The `config.yaml` file contains all search parameters and settings:

### Key Sections:

**Our Location:**
```yaml
our_location:
  latitude: -37.8283
  longitude: 144.9550
  name: "Darling Street Residence"
  current_rates:
    weekday_rate: 145
    cleaning_fee: 90
```

**Search Parameters:**
```yaml
search:
  max_distance_km: 2.0
  max_properties: 15

  airbnb:
    ne_lat: -37.820
    ne_long: 144.965
    sw_lat: -37.835
    sw_long: 144.950
```

**Date Ranges:**
```yaml
dates:
  weekday_checkin: "2026-02-15"
  weekday_checkout: "2026-02-17"
  weekend_checkin: "2026-02-21"
  weekend_checkout: "2026-02-23"
```

## Output Files

### 1. CSV Report (`competitors_YYYYMMDD.csv`)

Spreadsheet with all competitor properties:
- Platform (Airbnb/Booking.com)
- Property name and URL
- Distance from your property
- Weekday and weekend rates
- Cleaning fees
- Review count and ratings
- Key amenities

### 2. Summary Statistics (`summary_YYYYMMDD.json`)

Market analysis including:
- Total properties found
- Average rates (weekday/weekend)
- Average cleaning fees
- Your position vs market
- Pricing recommendations

Example:
```json
{
  "market_analysis": {
    "total_properties": 15,
    "avg_weekday_rate": 155.50,
    "avg_cleaning_fee": 115.00
  },
  "our_performance": {
    "position_vs_market": "-6.8%",
    "cleaning_fee_vs_market": "-21.7%",
    "recommendation": "Consider increasing cleaning fee to $115-125 to match market"
  }
}
```

### 3. Full Data (`full_data_YYYYMMDD.json`)

Complete dataset with all scraped information for further analysis.

## Technical Details

### Rate Limiting

The scraper includes respectful delays:
- 2-5 seconds between requests
- Exponential backoff on failures
- Maximum 3 retry attempts

### Error Handling

- Network errors are automatically retried
- Failed listings are logged but don't stop execution
- Detailed logs saved to `scraper.log`

### Data Processing

The scraper:
1. Searches both weekday and weekend dates
2. Merges pricing data by property
3. Calculates distance from your property using Haversine formula
4. Filters properties by distance and criteria
5. Generates comparative statistics

## Troubleshooting

### Common Issues

**1. "pyairbnb not installed" error:**
```bash
pip install --upgrade pyairbnb
```

**2. Booking.com returns no results:**
- This is expected due to anti-bot measures
- Booking.com has sophisticated bot detection
- Consider manual data collection or use residential proxies

**3. SSL Certificate errors:**
```bash
pip install --upgrade certifi
```

**4. Empty results:**
- Check date ranges (must be in future)
- Verify search coordinates in `config.yaml`
- Review `scraper.log` for detailed errors

### Logs

All activity is logged to `scraper.log` with timestamps and details. Check this file for debugging.

## Important Warnings

### Legal & Ethical Considerations

- **Terms of Service:** Both Airbnb and Booking.com prohibit automated scraping
- **Use Case:** This tool is for personal competitive analysis only
- **Do NOT:** Republish, resell, or commercially use this data
- **Rate Limiting:** The scraper includes respectful delays to avoid banning

### Technical Limitations

- **Anti-bot measures:** Sites may detect and block scrapers
- **Dynamic content:** Heavy JavaScript usage may cause issues
- **Structure changes:** Sites update frequently; scraper may break
- **IP bans:** Excessive requests will result in blocking
- **CAPTCHAs:** May appear during scraping

### Booking.com Challenges

Booking.com has particularly strong anti-bot protections. The scraper includes a basic implementation, but expect:
- Limited success rate
- Potential blocking
- Need for proxies or manual collection

For reliable Booking.com data, consider:
- Manual research
- Residential proxy services
- Browser automation tools (Selenium/Playwright)

## Best Practices

1. **Run Monthly:** Update your competitive data once per month
2. **Archive Results:** Keep historical data to track trends
3. **Verify Data:** Spot-check a few properties manually
4. **Adjust Gradually:** Make incremental pricing changes
5. **Monitor Performance:** Track occupancy after price changes

## Monthly Usage Workflow

```bash
# 1. Run the scraper
python run_scraper.py

# 2. Review the summary
cat output/summary_YYYYMMDD.json

# 3. Open CSV in Excel/Sheets
# output/competitors_YYYYMMDD.csv

# 4. Archive previous month's data
# Move old files to data/archive/

# 5. Make pricing decisions based on data
```

## Data Analysis Tips

### Using the CSV Output:

1. **Sort by Distance:** Find closest competitors
2. **Filter by Rating:** Focus on highly-rated properties (4.5+)
3. **Compare Amenities:** See what competitors offer
4. **Calculate Averages:** Use spreadsheet formulas

### Key Metrics to Track:

- **Cleaning Fee Range:** Min, max, average
- **Rate Distribution:** Are you above/below median?
- **Value Proposition:** Price vs. rating vs. amenities
- **Seasonal Patterns:** Weekend vs. weekday differences

## Future Enhancements

Potential improvements:
- Email notifications on completion
- Historical trend analysis
- Price optimization recommendations
- Occupancy correlation
- Automated monthly reports
- Dashboard visualization

## Support

For issues or questions:
1. Check `scraper.log` for error details
2. Review Troubleshooting section
3. Verify configuration in `config.yaml`
4. Test with `--verbose` flag for detailed output

## License

This tool is for personal use only. Respect the Terms of Service of Airbnb and Booking.com.

---

**Last Updated:** January 2026
**Version:** 1.0.0
