# On-Call Compensation Calculator

This tool calculates compensation for on-call shifts based on data from OpsGenie API or CSV files, following specific compensation rules for different time periods and special cases.

## Features

- Calculate on-call compensation with standard rates (5.56 € per hour outside working hours)
- Apply special rates for weekend short shifts (< 5 hours: 27.80 €) and night shifts (< 2 hours: 11.12 €)
- Consider individual working hours, time zones, and holidays
- Handle daylight saving time transitions
- Generate detailed reports and compensation summaries
- Create visualizations of daily compensation amounts
- 24.12. + 31.12 are considered 1/2 a workday, unless the downloaded Calendar data suggest a holiday.
- Creates an XSLX File if requested `--export-excel`
- Has a separate module for check for 24x7 compliance: `uv run ./check_oncall_rules.py shifts.csv`
- Custom Holidays per user (in user_profiles.json) are supported:
```json
    "country_code": "AT",
    "custom_holidays": [
      "2024-06-16",
      "2024-10-31",
      "2024-12-13"
    ]
```

## Installation

1. Make sure you have Python 3.12 or later installed
2. Clone this repository
3. Install dependencies:

```bash
uv pip install -e .
```

## Configuration

### Environment Variables

You can configure the tool using environment variables in a `.env` file:

```
# OpsGenie API configuration
OPSGENIE_API_TOKEN=your-api-token-here
OPSGENIE_SCHEDULE_ID=your-schedule-id-here
OPSGENIE_START_DATE=2025-01-01
OPSGENIE_END_DATE=2025-05-09

# File paths
OPSGENIE_CSV_FILE=shifts.csv
OPSGENIE_USER_PROFILES=user_profiles.json
OPSGENIE_OUTPUT_PLOT=compensation_chart.png
OPSGENIE_SAVE_CSV=shifts.csv
```

### User Profiles

User profiles are stored in a JSON file and contain information about:
- User's email
- Time zone
- Working days (0-6, where 0 is Monday)
- Working hours
- Country and region for holiday calculation
- Custom holidays

## Usage

The tool provides these main commands:

### 1. Fetch Data from OpsGenie API

Retrieve on-call shift data directly from the OpsGenie API:

```bash
uv run main.py opsgenie --api-token YOUR_TOKEN --schedule-id YOUR_SCHEDULE_ID \
    --start-date 2025-01-01 --end-date 2025-05-09 \
    --save-csv shifts.csv --user-profiles profiles.json
```

Or using environment variables:

```bash
# After setting up your .env file
uv run main.py opsgenie
```

### 2. Process Data from CSV File

If you already have on-call data in a CSV file:

```bash
uv run main.py csv shifts.csv --user-profiles profiles.json --output-plot compensation_chart.png
```

### 3. Create User Profiles

Generate default user profiles from existing on-call data:

```bash
uv run main.py profiles shifts.csv --output user_profiles.json
```

### 4. Download Holiday Calendars

Download holiday calendars for specific countries:

```bash
uv run main.py calendars --country AT --country FR --country ES --country BG
```

You can also download all supported calendars at once:

```bash
uv run main.py calendars --all
```

## Workflow Examples

### Full Workflow with OpsGenie API

1. Fetch data from OpsGenie and save to CSV:

```bash
uv run main.py opsgenie \
    --api-token YOUR_TOKEN \
    --schedule-id YOUR_SCHEDULE_ID \
    --start-date 2025-01-01 \
    --end-date 2025-05-09 \
    --save-csv shifts.csv
```

2. Generate user profiles:

```bash
uv run main.py profiles shifts.csv --output user_profiles.json
```

3. Edit the user profiles to adjust timezones, working hours, etc.

4. Calculate compensation with the updated profiles:

```bash
uv run main.py csv shifts.csv --user-profiles user_profiles.json --output-plot chart.png
```

### Using Environment Variables

1. Create a `.env` file with your configuration:

```
OPSGENIE_API_TOKEN=your-token
OPSGENIE_SCHEDULE_ID=your-schedule-id
OPSGENIE_START_DATE=2025-01-01
OPSGENIE_END_DATE=2025-05-09
OPSGENIE_SAVE_CSV=shifts.csv
```

2. Fetch data and save to CSV:

```bash
uv run main.py opsgenie
```

3. Create and adjust user profiles:

```bash
uv run main.py profiles shifts.csv
# Edit user_profiles.json to adjust settings
```

4. Run the compensation calculation:

```bash
uv run main.py csv shifts.csv
```

## Report Format

The tool generates a detailed compensation report showing:

```
=== DAILY COMPENSATION SUMMARY ===
User                           StartDay   StartDate  Start  EndDate  End      Hours    Amount (€)   Pauschale
...

=== USER TOTALS ===
User                           Total Hours     Total Amount (€)
...

=== GRAND TOTAL ===
Total compensation amount: XXX.XX €
```

## CSV Format

The CSV file should have the following columns:
- `start`: Start time of the shift (ISO 8601 format)
- `end`: End time of the shift (ISO 8601 format)
- `hours`: Duration of the shift in hours
- `user`: Email of the user who was on call
