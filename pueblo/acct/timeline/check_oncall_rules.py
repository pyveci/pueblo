#!/usr/bin/env python3
"""
On-call Shift Rules Compliance Checker

This standalone script analyzes on-call shifts data from a CSV file
and verifies compliance with the following rules:

1. Maximum 10 on-call shifts per month (max 168 hours per month)
2. Maximum 30 on-call days in any three-month period

The script generates a report that highlights any violations and
provides a summary of compliance status for each user.
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, List, Set, Tuple, Any

import click
import pandas as pd
import pytz


def load_shifts_from_csv(csv_path: str) -> pd.DataFrame:
    """
    Load on-call shifts from a CSV file into a pandas DataFrame

    Args:
        csv_path: Path to the CSV file

    Returns:
        DataFrame with shifts data
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)

        # Check if required columns exist
        required_cols = ['start', 'end', 'hours', 'user']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            click.echo(f"Error: CSV file is missing required columns: {', '.join(missing_cols)}", err=True)
            sys.exit(1)

        # Convert start and end strings to datetime objects
        df['start'] = pd.to_datetime(df['start'])
        df['end'] = pd.to_datetime(df['end'])

        # Sort by start time
        df = df.sort_values('start')

        return df

    except Exception as e:
        click.echo(f"Error loading CSV file: {str(e)}", err=True)
        sys.exit(1)


def get_date_coverage(row, timezone: str) -> Set[datetime.date]:
    """
    Get all dates covered by a shift in the specified timezone

    Args:
        row: DataFrame row with start and end times
        timezone: Timezone string

    Returns:
        Set of dates covered by the shift
    """
    # Localize to specified timezone
    tz = pytz.timezone(timezone)
    start = row['start'].replace(tzinfo=pytz.UTC).astimezone(tz)
    end = row['end'].replace(tzinfo=pytz.UTC).astimezone(tz)

    # Generate all dates from start to end
    dates = set()
    current = start.date()
    end_date = end.date()

    while current <= end_date:
        dates.add(current)
        current += timedelta(days=1)

    return dates


def analyze_shifts(df: pd.DataFrame, timezone: str) -> Dict[str, Dict[str, Any]]:
    """
    Analyze on-call shifts to check compliance with rules

    Args:
        df: DataFrame with shifts data
        timezone: Timezone to use for date calculations

    Returns:
        Dictionary with compliance analysis results for each user
    """
    if df.empty:
        click.echo("No shifts data to analyze")
        return {}

    # Initialize results dictionary
    results = {}

    # Group data by user
    users = df['user'].unique()

    for user in users:
        user_df = df[df['user'] == user].copy()

        # Get all dates covered by each shift
        user_df['dates'] = user_df.apply(lambda row: get_date_coverage(row, timezone), axis=1)

        # Extract year and month from start dates
        user_df['year'] = user_df['start'].dt.year
        user_df['month'] = user_df['start'].dt.month
        user_df['year_month'] = user_df['start'].dt.strftime('%Y-%m')

        # Initialize user results
        results[user] = {
            'monthly_violations': [],
            'quarterly_violations': [],
            'summary': {},
            'all_shifts': len(user_df),
            'all_days': sum(len(dates) for dates in user_df['dates']),
            'all_hours': user_df['hours'].sum()
        }

        # Check monthly limits (max 10 shifts per month, max 168 hours per month)
        monthly_data = {}

        for _, row in user_df.iterrows():
            year_month = row['year_month']
            if year_month not in monthly_data:
                monthly_data[year_month] = {
                    'shifts': 0,
                    'hours': 0,
                    'days': set(),
                    'year': row['year'],
                    'month': row['month']
                }

            monthly_data[year_month]['shifts'] += 1
            monthly_data[year_month]['hours'] += row['hours']
            monthly_data[year_month]['days'].update(row['dates'])

        # Check for monthly violations
        for ym, data in monthly_data.items():
            month_days = len(data['days'])
            month_name = datetime(data['year'], data['month'], 1).strftime('%Y %B')

            if data['shifts'] > 10 or data['hours'] > 168 or month_days > 10:
                results[user]['monthly_violations'].append({
                    'year': data['year'],
                    'month': data['month'],
                    'month_name': month_name,
                    'shifts': data['shifts'],
                    'days': month_days,
                    'hours': data['hours'],
                    'max_shifts': 10,
                    'max_days': 10,
                    'max_hours': 168
                })

        # Check quarterly limits (max 30 days in any 3-month period)
        if len(monthly_data) >= 3:
            sorted_months = sorted(monthly_data.keys())

            for i in range(len(sorted_months) - 2):
                # Get 3-month window
                months_window = sorted_months[i:i+3]

                # Collect all days in this period
                quarter_days = set()
                for m in months_window:
                    quarter_days.update(monthly_data[m]['days'])

                if len(quarter_days) > 30:
                    # Convert months to readable format
                    month_names = [
                        datetime(monthly_data[m]['year'], monthly_data[m]['month'], 1).strftime('%Y %B')
                        for m in months_window
                    ]

                    results[user]['quarterly_violations'].append({
                        'period': ' → '.join(month_names),
                        'days': len(quarter_days),
                        'max_days': 30
                    })

        # Build summary
        total_months = len(monthly_data)
        months_with_violations = len(results[user]['monthly_violations'])
        total_quarters = max(0, len(sorted_months) - 2) if len(monthly_data) >= 3 else 0
        quarters_with_violations = len(results[user]['quarterly_violations'])

        results[user]['summary'] = {
            'total_months': total_months,
            'months_with_violations': months_with_violations,
            'total_quarters': total_quarters,
            'quarters_with_violations': quarters_with_violations,
            'compliant': (months_with_violations == 0 and quarters_with_violations == 0)
        }

    return results


def print_report(results: Dict[str, Dict[str, Any]], verbose: bool = False):
    """
    Print compliance report to stdout

    Args:
        results: Analysis results dictionary
        verbose: Whether to print detailed information
    """
    if not results:
        click.echo("No data to report")
        return

    click.echo("\n=== ON-CALL RULES COMPLIANCE REPORT ===")
    click.echo("Rules:")
    click.echo("1. Maximum 10 on-call shifts per month (max 168 hours per month)")
    click.echo("2. Maximum 30 on-call days in any 3-month period")
    click.echo("=" * 80)

    # Print summary table
    click.echo("\n--- COMPLIANCE SUMMARY ---")
    click.echo(f"{'User':<40} {'Status':<15} {'Months':<8} {'Violations':<12} {'Quarters':<8} {'Violations'}")
    click.echo("-" * 100)

    compliant_users = 0
    non_compliant_users = 0

    for user, data in sorted(results.items()):
        summary = data['summary']
        status = "✓ Compliant" if summary['compliant'] else "✗ Non-compliant"
        months = f"{summary['months_with_violations']}/{summary['total_months']}"
        quarters = f"{summary['quarters_with_violations']}/{summary['total_quarters']}"

        if summary['compliant']:
            compliant_users += 1
        else:
            non_compliant_users += 1

        click.echo(f"{user:<40} {status:<15} {months:<8} {'':<12} {quarters:<8}")

    click.echo(f"\nUsers in compliance: {compliant_users}")
    click.echo(f"Users with violations: {non_compliant_users}")

    # Print detailed violations if any
    any_violations = False
    for user, data in results.items():
        if data['monthly_violations'] or data['quarterly_violations']:
            any_violations = True
            break

    if any_violations:
        click.echo("\n--- DETAILED VIOLATIONS ---")

        for user, data in sorted(results.items()):
            monthly_violations = data['monthly_violations']
            quarterly_violations = data['quarterly_violations']

            if monthly_violations or quarterly_violations:
                click.echo(f"\nUser: {user}")
                click.echo(f"Total tracked: {data['all_shifts']} shifts, {data['all_days']} days, {data['all_hours']:.1f} hours")

                if monthly_violations:
                    click.echo("  Monthly limit violations:")
                    for v in monthly_violations:
                        click.echo(f"    {v['month_name']}: {v['shifts']} shifts, {v['days']} days, {v['hours']:.1f} hours")
                        click.echo(f"      (limits: 10 shifts, 10 days, 168 hours per month)")

                if quarterly_violations:
                    click.echo("  Three-month period limit violations:")
                    for v in quarterly_violations:
                        click.echo(f"    Period {v['period']}: {v['days']} days (limit: 30 days)")
    else:
        click.echo("\n✓ All users are compliant with on-call schedule rules.")

    # Print detailed shift information if verbose mode is enabled
    if verbose:
        click.echo("\n--- DETAILED SHIFT INFORMATION ---")
        for user, data in sorted(results.items()):
            click.echo(f"\nUser: {user}")
            # You would add more detailed information about each shift here


@click.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--timezone', default='UTC', help='Timezone to use for date calculations (default: UTC)')
@click.option('--verbose', is_flag=True, help='Print detailed information about each shift')
def main(csv_file, timezone, verbose):
    """
    Check on-call shift schedule compliance with rules.

    This tool analyzes on-call shifts from a CSV file and verifies compliance with:

    \b
    1. Maximum 10 on-call shifts per month (max 168 hours per month)
    2. Maximum 30 on-call days in any three-month period

    The CSV file must contain columns: start, end, hours, user
    """
    # Load shifts data
    click.echo(f"Loading shifts data from {csv_file}...")
    df = load_shifts_from_csv(csv_file)
    click.echo(f"Loaded {len(df)} shifts for {df['user'].nunique()} users")

    # Display time range of the shifts
    if not df.empty:
        start_date = df['start'].min().strftime('%Y-%m-%d %H:%M')
        end_date = df['end'].max().strftime('%Y-%m-%d %H:%M')
        click.echo(f"Time range: {start_date} to {end_date}")

    # Analyze shifts
    click.echo(f"Analyzing shifts using timezone: {timezone}...")
    results = analyze_shifts(df, timezone)

    # Print report
    print_report(results, verbose)


if __name__ == "__main__":
    main()
