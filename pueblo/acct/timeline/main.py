#!/usr/bin/env python3
"""
On-call Compensation Calculator based on OpsGenie API data

This script calculates compensation for on-call duty periods according to specified rules,
handling different time zones, working hours, and special cases for weekends and holidays.
It can fetch data directly from OpsGenie API or read from a CSV file.
"""

import csv
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import sys

import click
import holidays
import icalendar
import matplotlib.pyplot as plt
import pandas as pd
import pytz
import requests
from dateutil import parser
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, Field, field_validator

# Load environment variables from .env file
load_dotenv()

# Constants for compensation calculation
STANDARD_RATE = 5.56  # Euro per hour outside working hours
WEEKEND_SHORT_SHIFT_THRESHOLD = 5  # hours
WEEKEND_SHORT_SHIFT_RATE = 27.80  # Euro fixed rate
NIGHT_SHORT_SHIFT_THRESHOLD = 2  # hours
NIGHT_SHORT_SHIFT_RATE = 11.12  # Euro fixed rate
NIGHT_START_HOUR = 22  # 10 PM
NIGHT_END_HOUR = 6    # 6 AM

# OpsGenie API constants
OPSGENIE_API_URL = "https://api.opsgenie.com/v2/schedules/{schedule_id}/timeline"
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

# Holiday calendar URLs - public holiday iCal feeds
HOLIDAY_CALENDAR_URLS = {
    'AT': 'https://www.officeholidays.com/ics/austria',
    'FR': 'https://www.officeholidays.com/ics/france',
    'ES': 'https://www.officeholidays.com/ics/spain',
    'BG': 'https://www.officeholidays.com/ics/bulgaria',
    'DE': 'https://www.officeholidays.com/ics/germany'
}

# Default country code for new profiles
DEFAULT_COUNTRY_CODE = 'AT'  # Austria as default


class CompensationType(str, Enum):
    """Types of compensation that can be applied"""
    STANDARD = "Standard"
    WEEKEND_SHORT_SHIFT = "Wochenend-Sonderfall"
    NIGHT_SHORT_SHIFT = "Nacht-Sonderfall"


class UserProfile(BaseModel):
    """Model for user profile data"""
    email: EmailStr
    timezone: str
    working_days: List[int] = Field(default=[0, 1, 2, 3, 4])  # 0=Monday, 6=Sunday
    working_hours_start: time = Field(default=time(9, 0))
    working_hours_end: time = Field(default=time(17, 0))
    country_code: str = Field(default=DEFAULT_COUNTRY_CODE)
    region: Optional[str] = None
    custom_holidays: List[str] = Field(default_factory=list)
    # Removed calendar_file field since we'll handle calendars dynamically

    @field_validator('timezone')
    def validate_timezone(cls, v):
        if v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {v}")
        return v


@dataclass
class CompensationPeriod:
    """A period with calculated compensation"""
    user: str
    start: datetime
    end: datetime
    hours: float
    compensated_hours: float
    amount: float
    compensation_type: CompensationType
    holiday_info: Optional[Dict[str, str]] = None  # Store holiday name and source if applicable


class OnCallShift(BaseModel):
    """Model for on-call shift data from CSV"""
    start: datetime
    end: datetime
    hours: float
    user: EmailStr

    @field_validator('start', 'end', mode='before')
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return parser.parse(v)
        return v


class CompensationCalculator:
    """Calculates compensation for on-call shifts"""

    def __init__(self, user_profiles_path: Optional[Path] = None):
        self.user_profiles: Dict[str, UserProfile] = {}
        self.user_holidays: Dict[str, Dict[str, Union[holidays.HolidayBase, List[str]]]] = {}

        if user_profiles_path:
            self.load_user_profiles(user_profiles_path)

    def load_user_profiles(self, path: Path):
        """Load user profiles from a JSON file"""
        with open(path, 'r') as f:
            profiles_data = json.load(f)

        for profile_data in profiles_data:
            profile = UserProfile(**profile_data)
            self.user_profiles[profile.email] = profile

            # Initialize holidays for each user
            self._load_holidays_for_user(profile)

    def _load_holidays_for_user(self, profile: UserProfile):
        """Initialize holidays for a user based on their country/region"""
        user_holiday_dict = {}
        holiday_sources = []

        try:
            # First try to load holidays from the country code using the holidays package
            if profile.region:
                country_holidays = holidays.country_holidays(
                    profile.country_code,
                    subdiv=profile.region
                )
                user_holiday_dict.update({date: name for date, name in country_holidays.items()})
                holiday_sources.append(f"{profile.country_code}/{profile.region}")
            else:
                country_holidays = holidays.country_holidays(profile.country_code)
                user_holiday_dict.update({date: name for date, name in country_holidays.items()})
                holiday_sources.append(profile.country_code)

            # Add custom holidays from the profile
            for holiday_str in profile.custom_holidays:
                holiday_date = parser.parse(holiday_str).date()
                user_holiday_dict[holiday_date] = "Custom Holiday"

            if profile.custom_holidays:
                holiday_sources.append(f"{profile.email}")

            # Create a HolidayBase object to store the holidays
            user_holidays = holidays.HolidayBase()
            for date, name in user_holiday_dict.items():
                user_holidays[date] = name

            # Note: We don't load calendar files here anymore, as they will be loaded dynamically
            # when calculating compensation based on the shift date

            # Store both the holidays object and the sources of holidays
            self.user_holidays[profile.email] = {
                'holidays': user_holidays,
                'sources': holiday_sources,
                'country_code': profile.country_code  # Store country code for later calendar lookup
            }

        except (KeyError, AttributeError) as e:
            logging.warning(f"Could not load holidays for {profile.email}: {str(e)}")
            # Create an empty holidays object if we can't load the country
            self.user_holidays[profile.email] = {
                'holidays': holidays.HolidayBase(),
                'sources': [],
                'country_code': profile.country_code
            }

    def add_user_profile(self, profile: UserProfile):
        """Add or update a user profile"""
        self.user_profiles[profile.email] = profile
        self._load_holidays_for_user(profile)

    def get_holiday_from_calendar(self, date: datetime, user_email: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if a given date is a holiday in the user's calendar file(s).

        Args:
            date: The date to check
            user_email: The user's email address

        Returns:
            Tuple of (is_holiday, holiday_name, source)
        """
        if user_email not in self.user_holidays:
            return False, None, None

        # Get the user's country code
        country_code = self.user_holidays[user_email].get('country_code')
        if not country_code:
            return False, None, None

        # Determine which year's calendar we need to check
        year = date.year

        # Check if we've already loaded this calendar
        calendar_key = f"{country_code}_{year}"
        if calendar_key not in getattr(self, 'calendar_cache', {}):
            # Initialize calendar cache if it doesn't exist
            if not hasattr(self, 'calendar_cache'):
                self.calendar_cache = {}

            # Try to load the calendar file for this country and year
            calendar_path = Path(f"calendars/{country_code}_holidays_{year}.ics")
            if calendar_path.exists():
                # Parse the calendar file
                holidays_dict = parse_ical_holidays(calendar_path)
                self.calendar_cache[calendar_key] = {
                    'holidays': holidays_dict,
                    'source': f"{country_code} Calendar {year}"
                }
            else:
                # Calendar file doesn't exist for this year
                self.calendar_cache[calendar_key] = {
                    'holidays': {},
                    'source': None
                }

        # Check if the date is a holiday in the loaded calendar
        calendar_data = self.calendar_cache.get(calendar_key, {})
        holidays_dict = calendar_data.get('holidays', {})

        if date.date() in holidays_dict:
            holiday_name = holidays_dict[date.date()]
            source = calendar_data.get('source')
            return True, holiday_name, source

        return False, None, None

    def is_holiday(self, date: datetime, user: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a given date is a holiday for the specified user.
        Now checks both built-in holidays and calendar files.

        Returns:
            Tuple containing (is_holiday, holiday_name)
        """
        if user not in self.user_holidays:
            return False, None

        # First check the built-in holidays
        holiday_info = self.user_holidays[user]
        holiday_obj = holiday_info['holidays']

        date_obj = date.date()
        if date_obj in holiday_obj:
            return True, holiday_obj[date_obj]

        # If not found, check calendar files based on date
        is_cal_holiday, holiday_name, source = self.get_holiday_from_calendar(date, user)
        if is_cal_holiday:
            # Add the holiday to the user's holiday object for future reference
            holiday_obj[date_obj] = holiday_name
            if source and source not in holiday_info['sources']:
                holiday_info['sources'].append(source)
            return True, holiday_name

        return False, None

    def is_weekend(self, date: datetime, user: str) -> bool:
        """Check if a given date is a weekend for the specified user"""
        if user not in self.user_profiles:
            # Default to standard weekend (Saturday and Sunday)
            return date.weekday() >= 5

        return date.weekday() not in self.user_profiles[user].working_days

    def is_working_hours(self, dt: datetime, user: str) -> bool:
        """Check if a given datetime falls within the user's working hours"""
        if user not in self.user_profiles:
            # Default working hours: Monday-Friday, 9 AM - 5 PM
            if dt.weekday() >= 5:  # Saturday and Sunday
                return False
            return time(9, 0) <= dt.time() < time(17, 0)

        profile = self.user_profiles[user]

        # Check if it's a work day
        if dt.weekday() not in profile.working_days:
            return False

        # Check if it's a holiday
        is_holiday, _ = self.is_holiday(dt, user)
        if is_holiday:
            return False

        # Special handling for December 24th and December 31st (shorter working hours)
        if dt.month == 12 and (dt.day == 24 or dt.day == 31):
            # Work hours on these days are only 09:00-12:30
            return profile.working_hours_start <= dt.time() < time(12, 30)

        # Regular working hours for normal days
        return profile.working_hours_start <= dt.time() < profile.working_hours_end

    def get_user_local_time(self, utc_time: datetime, user: str) -> datetime:
        """Convert UTC time to the user's local timezone"""
        if user in self.user_profiles:
            user_tz = pytz.timezone(self.user_profiles[user].timezone)
        else:
            # Default to UTC if user not found
            user_tz = pytz.UTC

        # Ensure the datetime is UTC
        if utc_time.tzinfo is None:
            utc_time = pytz.UTC.localize(utc_time)
        elif utc_time.tzinfo != pytz.UTC:
            utc_time = utc_time.astimezone(pytz.UTC)

        return utc_time.astimezone(user_tz)

    def calculate_compensation(self, shift: OnCallShift) -> List[CompensationPeriod]:
        """
        Calculate compensation for an on-call shift based on the defined rules.
        May return multiple CompensationPeriod objects if the shift spans different day types.
        """

        # Convert shift times to user's local timezone
        local_start = self.get_user_local_time(shift.start, shift.user)
        local_end = self.get_user_local_time(shift.end, shift.user)

        # Calculate duration in hours (already provided in the shift data)
        duration_hours = shift.hours

        # First, check for special cases that apply fixed rates

        # Weekend short shift - only apply if the entire shift is on a weekend
        is_weekend_shift = all(
            self.is_weekend(local_start + timedelta(hours=h), shift.user)
            for h in range(int(duration_hours) + 1)
        )

        if is_weekend_shift and duration_hours < WEEKEND_SHORT_SHIFT_THRESHOLD:
            return [CompensationPeriod(
                user=shift.user,
                start=local_start,
                end=local_end,
                hours=duration_hours,
                compensated_hours=duration_hours,
                amount=WEEKEND_SHORT_SHIFT_RATE,
                compensation_type=CompensationType.WEEKEND_SHORT_SHIFT
            )]

        # Night short shift on weekdays
        is_night_shift = False
        if duration_hours < NIGHT_SHORT_SHIFT_THRESHOLD:
            # Check if shift is entirely during night hours
            is_night_time = (
                (local_start.hour >= NIGHT_START_HOUR or local_start.hour < NIGHT_END_HOUR) and
                (local_end.hour >= NIGHT_START_HOUR or local_end.hour < NIGHT_END_HOUR)
            )

            # Check if it's a weekday
            is_weekday = not any(
                self.is_weekend(local_start + timedelta(hours=h), shift.user) or
                self.is_holiday(local_start + timedelta(hours=h), shift.user)[0]
                for h in range(int(duration_hours) + 1)
            )

            is_night_shift = is_night_time and is_weekday

            if is_night_shift:
                return [CompensationPeriod(
                    user=shift.user,
                    start=local_start,
                    end=local_end,
                    hours=duration_hours,
                    compensated_hours=duration_hours,
                    amount=NIGHT_SHORT_SHIFT_RATE,
                    compensation_type=CompensationType.NIGHT_SHORT_SHIFT
                )]

        all_periods = []
        processed_ranges = []

        # First, identify and process holiday segments
        current_day = local_start.replace(hour=0, minute=0, second=0, microsecond=0)
        end_day = local_end.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

        # Process holidays first
        while current_day < end_day:
            # Check if this day is a holiday
            is_holiday, holiday_name = self.is_holiday(current_day, shift.user)

            if is_holiday:
                # For a holiday, calculate the intersection of this day with the shift
                day_start = max(local_start, current_day)
                day_end = min(local_end, current_day + timedelta(days=1))

                if day_start < day_end:  # If there's any overlap
                    holiday_hours = (day_end - day_start).total_seconds() / 3600

                    # Get holiday source information
                    holiday_sources = []
                    if shift.user in self.user_holidays:
                        holiday_sources = self.user_holidays[shift.user].get('sources', [])

                    holiday_source = "Unknown"
                    if holiday_sources:
                        holiday_source = ", ".join(holiday_sources)

                    # Check for calendar-specific source
                    is_cal_holiday, cal_name, cal_source = self.get_holiday_from_calendar(current_day, shift.user)
                    if is_cal_holiday and cal_source:
                        holiday_source = cal_source

                    # Create a holiday-specific period
                    holiday_period = CompensationPeriod(
                        user=shift.user,
                        start=day_start,
                        end=day_end,
                        hours=holiday_hours,
                        compensated_hours=holiday_hours,  # All holiday hours are compensated
                        amount=holiday_hours * STANDARD_RATE,
                        compensation_type=CompensationType.STANDARD,
                        holiday_info={
                            'name': holiday_name,
                            'source': holiday_source
                        }
                    )
                    all_periods.append(holiday_period)
                    processed_ranges.append((day_start, day_end))

            # Move to the next day
            current_day += timedelta(days=1)

        # Now, handle weekend that aren't holidays
        current_day = local_start.replace(hour=0, minute=0, second=0, microsecond=0)
        while current_day < end_day:
            # Skip if it's a holiday (already processed)
            is_holiday, _ = self.is_holiday(current_day, shift.user)
            if is_holiday:
                current_day += timedelta(days=1)
                continue

            # Check if this day is a weekend
            if self.is_weekend(current_day, shift.user):
                # Calculate the intersection of this day with the shift
                day_start = max(local_start, current_day)
                day_end = min(local_end, current_day + timedelta(days=1))

                if day_start < day_end:  # If there's any overlap
                    # Check if this period overlaps with any already processed periods
                    overlap = False
                    for start, end in processed_ranges:
                        if max(start, day_start) < min(end, day_end):
                            overlap = True
                            break

                    if not overlap:
                        weekend_hours = (day_end - day_start).total_seconds() / 3600

                        weekend_period = CompensationPeriod(
                            user=shift.user,
                            start=day_start,
                            end=day_end,
                            hours=weekend_hours,
                            compensated_hours=weekend_hours,  # All weekend hours are compensated
                            amount=weekend_hours * STANDARD_RATE,
                            compensation_type=CompensationType.STANDARD
                        )
                        all_periods.append(weekend_period)
                        processed_ranges.append((day_start, day_end))

            current_day += timedelta(days=1)

        # Finally, process remaining weekday segments
        # Create a list of all unprocessed time segments
        if not processed_ranges:
            unprocessed = [(local_start, local_end)]
        else:
            processed_ranges.sort()
            unprocessed = []
            current = local_start

            for start, end in processed_ranges:
                if current < start:
                    unprocessed.append((current, start))
                current = max(current, end)

            if current < local_end:
                unprocessed.append((current, local_end))

        # Process each unprocessed weekday segment
        for segment_start, segment_end in unprocessed:
            segment_hours = (segment_end - segment_start).total_seconds() / 3600

            # Calculate compensated hours (only outside working hours)
            compensated_hours = 0
            current_time = segment_start

            while current_time < segment_end:
                chunk_end = min(current_time + timedelta(hours=1), segment_end)
                chunk_hours = (chunk_end - current_time).total_seconds() / 3600

                # Compensate outside working hours
                if not self.is_working_hours(current_time, shift.user):
                    compensated_hours += chunk_hours

                current_time = chunk_end

            if segment_hours > 0:
                weekday_period = CompensationPeriod(
                    user=shift.user,
                    start=segment_start,
                    end=segment_end,
                    hours=segment_hours,
                    compensated_hours=compensated_hours,
                    amount=compensated_hours * STANDARD_RATE,
                    compensation_type=CompensationType.STANDARD
                )
                all_periods.append(weekday_period)

        # If no periods were created (unlikely), fallback to the original approach
        if not all_periods:
            compensated_hours = 0
            current_time = local_start

            while current_time < local_end:
                chunk_end = min(current_time + timedelta(hours=1), local_end)
                chunk_hours = (chunk_end - current_time).total_seconds() / 3600

                is_compensated = False

                # Weekend or holiday - always compensated
                if (self.is_weekend(current_time, shift.user) or
                    self.is_holiday(current_time, shift.user)[0]):
                    is_compensated = True
                # Weekday - compensate only outside working hours
                elif not self.is_working_hours(current_time, shift.user):
                    is_compensated = True

                if is_compensated:
                    compensated_hours += chunk_hours

                current_time = chunk_end

            amount = compensated_hours * STANDARD_RATE

            all_periods = [CompensationPeriod(
                user=shift.user,
                start=local_start,
                end=local_end,
                hours=duration_hours,
                compensated_hours=compensated_hours,
                amount=amount,
                compensation_type=CompensationType.STANDARD
            )]

        # Sort periods by start time for better reporting
        all_periods.sort(key=lambda p: p.start)

        return all_periods


class CompensationReport:
    """Generates reports for on-call compensation"""

    def __init__(self, compensation_periods: List[CompensationPeriod]):
        self.periods = compensation_periods
        self.df = self._prepare_dataframe()

    def _prepare_dataframe(self) -> pd.DataFrame:
        """Convert compensation periods to a DataFrame for easier analysis"""
        data = []

        for period in self.periods:
            date = period.start.date()

            # Check if this is a holiday period
            is_holiday = period.holiday_info is not None
            holiday_name = period.holiday_info['name'] if is_holiday else None
            holiday_source = period.holiday_info['source'] if is_holiday else None

            data.append({
                'User': period.user,
                'Date': date,
                'Start': period.start,
                'End': period.end,
                'Hours': period.hours,
                'Compensated Hours': period.compensated_hours,
                'Amount': period.amount,
                'Compensation Type': period.compensation_type,
                'Is Holiday': is_holiday,
                'Holiday Name': holiday_name,
                'Holiday Source': holiday_source
            })

        return pd.DataFrame(data)

    def get_daily_summary(self) -> pd.DataFrame:
        """Generate a daily summary of compensation per user"""
        if self.df.empty:
            return pd.DataFrame()

        # Group by user and date, and sum the amounts
        daily_summary = self.df.groupby(['User', 'Date']).agg({
            'Compensated Hours': 'sum',
            'Amount': 'sum',
            'Compensation Type': lambda x: ', '.join(set(x))
        }).reset_index()

        # Add day of week
        daily_summary['Day'] = daily_summary['Date'].apply(
            lambda x: x.strftime('%A')
        )

        return daily_summary

    def get_user_totals(self) -> pd.DataFrame:
        """Generate total compensation per user"""
        if self.df.empty:
            return pd.DataFrame()

        return self.df.groupby('User').agg({
            'Compensated Hours': 'sum',
            'Amount': 'sum'
        }).reset_index()

    def get_user_month_totals(self) -> pd.DataFrame:
        """Generate total compensation per user per month"""
        if self.df.empty:
            return pd.DataFrame()

        # Add year-month column to the dataframe
        self.df['Year-Month'] = self.df['Date'].apply(lambda x: f"{x.year}-{x.month:02d}")

        # Group by user and year-month
        return self.df.groupby(['User', 'Year-Month']).agg({
            'Compensated Hours': 'sum',
            'Amount': 'sum'
        }).reset_index()

    def get_grand_total(self) -> float:
        """Get the grand total compensation amount"""
        if self.df.empty:
            return 0.0

        return self.df['Amount'].sum()

    def get_hours_breakdown(self) -> Dict[str, float]:
        """Get a breakdown of compensated hours by category (workday, weekend, holiday)"""
        if self.df.empty:
            return {
                'workday_hours': 0.0,
                'weekend_hours': 0.0,
                'holiday_hours': 0.0,
                'total_hours': 0.0
            }

        # Initialize counters
        workday_hours = 0.0
        weekend_hours = 0.0
        holiday_hours = 0.0

        # Group by date to avoid double-counting the same hours
        for _, row in self.df.iterrows():
            if row['Is Holiday']:
                holiday_hours += row['Compensated Hours']
            elif row['Start'].strftime('%A') in ['Saturday', 'Sunday']:
                weekend_hours += row['Compensated Hours']
            else:
                workday_hours += row['Compensated Hours']

        return {
            'workday_hours': workday_hours,
            'weekend_hours': weekend_hours,
            'holiday_hours': holiday_hours,
            'total_hours': workday_hours + weekend_hours + holiday_hours
        }

    def print_report(self):
        """Print a comprehensive report to stdout"""
        if self.df.empty:
            print("No compensation data available")
            return

        # Sort the dataframe by date and start time
        sorted_df = self.df.sort_values(['Date', 'Start'])

        print("\n=== DAILY COMPENSATION SUMMARY ===")
        print(f"{'User':<30} {'StartDay':<10} {'StartDate':<10} {'Start':<6} {'EndDate':<10} {'End':<6} {'Hours':<8} {'Amount (€)':<12} {'Pauschale'}")
        print("-" * 120)

        # Keep track of consecutive shifts for gap detection and correction
        previous_end = None
        previous_user = None
        previous_end_time_str = None

        for _, row in sorted_df.iterrows():
            start_date_str = row['Start'].strftime('%Y-%m-%d')
            end_date_str = row['End'].strftime('%Y-%m-%d')
            start_time_str = row['Start'].strftime('%H:%M')
            end_time_str = row['End'].strftime('%H:%M')
            day_str = row['Start'].strftime('%A')

            compensation_type = str(row['Compensation Type']).split('.')[-1]  # Extract just the name part after the dot

            # Check if this is a holiday entry
            if row['Is Holiday']:
                compensation_type = f"Holiday: {row['Holiday Name']} ({row['Holiday Source']})"

            # Check if this is December 24th or December 31st (special working hours days)
            start_month_day = (row['Start'].month, row['Start'].day)
            # //FIXME: This is a workaround for the special case of December 24th and 31st
            if start_month_day in [(12, 24), (12, 31)]:
                special_day = "Christmas Eve" if start_month_day == (12, 24) else "New Year's Eve"
                compensation_type = f"{compensation_type} ({special_day}: working hours 09:00-12:30)"

            # Check for time gaps with previous shift due to timezone differences
            if previous_end is not None:
                # Calculate the time difference between this shift's start and the previous shift's end
                time_diff = (row['Start'] - previous_end).total_seconds() / 60  # in minutes

                # If there's a small gap or overlap (less than 30 minutes), it's likely due to timezone differences
                if abs(time_diff) < 30:
                    # If this is a different user than the previous one (handover), adjust display times
                    if previous_user != row['User']:
                        if time_diff > 0:  # There's a gap
                            # Make previous shift end at the same time as this shift starts
                            previous_end_time_str = start_time_str
                        else:  # There's an overlap
                            # Make this shift start at the same time as previous shift ends
                            start_time_str = previous_end_time_str

            # Print the row
            print(
                f"{row['User']:<30} "
                f"{day_str:<10} "
                f"{start_date_str:<10} "
                f"{start_time_str:<6} "
                f"{end_date_str:<10} "
                f"{end_time_str:<6} "
                f"{row['Compensated Hours']:<8.1f} "
                f"{row['Amount']:<12.2f} "
                f"{compensation_type}"
            )

            # Update tracking variables for the next iteration
            previous_end = row['End']
            previous_user = row['User']
            previous_end_time_str = end_time_str

        # User-Month totals
        user_month_totals = self.get_user_month_totals()
        print("\n=== USER TOTALS PER MONTH (INCLUDING PRE-PAID COMPENSATION) ===")
        print(f"{'User':<30} {'Month':<10} {'Total Hours':<12} {'Raw Amount (€)':<15} {'Pre-Paid (€)':<15} {'Final Amount (€)':<15}")
        print("-" * 100)

        # Sort by user and year-month
        user_month_totals = user_month_totals.sort_values(['User', 'Year-Month'])

        current_user = None
        user_total_hours = 0
        user_total_raw_amount = 0

        # Variables to track unique months per user
        user_unique_months = {}

        for _, row in user_month_totals.iterrows():
            # If we're processing a new user, print a separator for readability
            if current_user is not None and current_user != row['User']:
                # Calculate the fixed monthly pre-paid amount (€510 per unique month)
                unique_months_count = len(user_unique_months.get(current_user, []))
                fixed_monthly_prepaid = 510.0 * unique_months_count

                # Calculate final amount after deducting the fixed monthly pre-paid
                final_amount = max(0, user_total_raw_amount - fixed_monthly_prepaid)

                # Print user subtotal with fixed monthly pre-paid
                print(f"{'':<30} {'SUBTOTAL':<10} {user_total_hours:<12.1f} {user_total_raw_amount:<15.2f} {fixed_monthly_prepaid:<15.2f} {final_amount:<15.2f}")
                if final_amount > 0:
                    print(f"{'':<30} {'ADDITIONAL COMPENSATION':<25} {final_amount:<15.2f}")
                print(f"{'':<30} {'':-<10} {'':-<12} {'':-<15} {'':-<15} {'':-<15}")

                # Reset variables for the next user
                user_total_hours = 0
                user_total_raw_amount = 0

            # Keep track of unique months for this user
            if current_user != row['User']:
                current_user = row['User']
                if current_user not in user_unique_months:
                    user_unique_months[current_user] = set()

            user_unique_months[current_user].add(row['Year-Month'])
            user_total_hours += row['Compensated Hours']
            user_total_raw_amount += row['Amount']

            # Calculate pre-paid amount for this month (for display purposes only)
            year, month = map(int, row['Year-Month'].split('-'))

            # For display purposes, show the full monthly pre-paid amount
            month_prepaid = 510.0

            # Calculate the adjusted amount for this month (for display purposes only)
            month_adjusted = max(0, row['Amount'] - month_prepaid)

            month_name = datetime(year, month, 1).strftime('%Y %b')

            print(
                f"{row['User']:<30} "
                f"{month_name:<10} "
                f"{row['Compensated Hours']:<12.1f} "
                f"{row['Amount']:<15.2f} "
                f"{month_prepaid:<15.2f} "
                f"{month_adjusted:<15.2f}"
            )

        # Print final user subtotal if we had any data
        if current_user is not None:
            # Calculate the fixed monthly pre-paid amount (€510 per unique month)
            unique_months_count = len(user_unique_months.get(current_user, []))
            fixed_monthly_prepaid = 510.0 * unique_months_count

            # Calculate final amount after deducting the fixed monthly pre-paid
            final_amount = max(0, user_total_raw_amount - fixed_monthly_prepaid)

            # Print user subtotal with fixed monthly pre-paid
            print(f"{'':<30} {'SUBTOTAL':<10} {user_total_hours:<12.1f} {user_total_raw_amount:<15.2f} {fixed_monthly_prepaid:<15.2f} {final_amount:<15.2f}")
            if final_amount > 0:
                print(f"{'':<30} {'ADDITIONAL COMPENSATION':<25} {final_amount:<15.2f}")

        # Calculate the grand totals
        total_compensated_hours = user_month_totals['Compensated Hours'].sum()
        total_raw_amount = user_month_totals['Amount'].sum()

        # Calculate total fixed pre-paid amount based on unique user-months
        total_unique_user_months = sum(len(months) for months in user_unique_months.values())
        total_fixed_prepaid = 510.0 * total_unique_user_months

        # Calculate total additional compensation
        total_additional_compensation = max(0, total_raw_amount - total_fixed_prepaid)

        # Print grand totals with pre-paid information
        print("\n=== GRAND TOTAL (WITH FIXED MONTHLY PRE-PAID COMPENSATION) ===")
        print(f"Total compensated hours: {total_compensated_hours:.1f} hours")
        print(f"Total raw compensation amount: {total_raw_amount:.2f} €")
        print(f"Total fixed pre-paid compensation ({total_unique_user_months} user-months @ 510 €): {total_fixed_prepaid:.2f} €")
        print(f"Total additional compensation: {total_additional_compensation:.2f} €")

        # Hours breakdown for validation
        hours_breakdown = self.get_hours_breakdown()

        print("\n=== HOURS BREAKDOWN (VALIDATION) ===")
        print(f"Workday hours (outside working hours): {hours_breakdown['workday_hours']:.1f} hours")
        print(f"Weekend hours: {hours_breakdown['weekend_hours']:.1f} hours")
        print(f"Holiday hours (based on AT calendar): {hours_breakdown['holiday_hours']:.1f} hours")
        print(f"TOTAL COMPENSATED HOURS: {hours_breakdown['total_hours']:.1f} hours")

        # Validate that total hours match the sum of individual categories
        calculated_total = hours_breakdown['workday_hours'] + hours_breakdown['weekend_hours'] + hours_breakdown['holiday_hours']
        difference = abs(calculated_total - hours_breakdown['total_hours'])

        if difference > 0.1:  # Allow for small floating-point differences
            print("\n⚠️ VALIDATION WARNING: Hours breakdown doesn't match total compensated hours.")
            print(f"   Difference: {difference:.2f} hours")
        else:
            print("\n✓ VALIDATION OK: Hours breakdown matches total compensated hours.")

    def plot_daily_amounts(self, output_path: Optional[Path] = None):
        """Generate a bar chart of daily compensation amounts"""
        if self.df.empty:
            print("No data to plot")
            return

        daily = self.get_daily_summary()

        # Pivot for plotting
        pivot_df = daily.pivot_table(
            index='Date',
            columns='User',
            values='Amount',
            aggfunc='sum'
        ).fillna(0)

        # Plot
        fig, ax = plt.subplots(figsize=(12, 8))
        pivot_df.plot(kind='bar', stacked=True, ax=ax)

        plt.title('Daily Compensation Amounts')
        plt.ylabel('Amount (€)')
        plt.xlabel('Date')
        plt.xticks(rotation=45)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"Plot saved to {output_path}")
        else:
            plt.show()

    def plot_hours_distribution(self, output_path: Optional[Path] = None):
        """
        Generate a stacked bar chart showing the distribution of on-call hours per user
        across different categories (working hours, outside work hours, weekends, holidays)
        """
        if self.df.empty:
            print("No data to plot")
            return

        # Create a new DataFrame to hold the categorized hours
        user_hours = {}
        # Track the earliest start and latest end date for each user
        user_periods = {}

        for user in self.df['User'].unique():
            user_df = self.df[self.df['User'] == user]

            # Initialize counters for this user
            work_hours = 0.0
            outside_work_hours = 0.0
            weekend_hours = 0.0
            holiday_hours = 0.0

            # Track start and end times
            start_dates = []
            end_dates = []

            for _, row in user_df.iterrows():
                # Track start/end times
                start_dates.append(row['Start'])
                end_dates.append(row['End'])

                # Check if it's a holiday
                if row['Is Holiday']:
                    holiday_hours += row['Hours']
                    continue

                # Check if it's a weekend
                if row['Start'].strftime('%A') in ['Saturday', 'Sunday']:
                    weekend_hours += row['Hours']
                    continue

                # For weekdays, calculate working hours vs outside working hours
                # Compensated hours are outside working hours, so:
                outside_work_hours += row['Compensated Hours']
                # And the remainder are within working hours
                work_hours += (row['Hours'] - row['Compensated Hours'])

            # Store the results
            user_hours[user] = {
                'Regular Work Hours': work_hours,
                'Outside Work Hours': outside_work_hours,
                'Weekend Hours': weekend_hours,
                'Holiday Hours': holiday_hours
            }

            # Store period info if we have any shifts
            if start_dates and end_dates:
                earliest_start = min(start_dates)
                latest_end = max(end_dates)
                user_periods[user] = {
                    'start': earliest_start,
                    'end': latest_end
                }

        # Convert to DataFrame for plotting
        hours_df = pd.DataFrame(user_hours).T

        # Plot
        fig, ax = plt.subplots(figsize=(14, 10))  # Make the figure larger to accommodate the additional text
        hours_df.plot(kind='bar', stacked=True, ax=ax,
                     colormap='viridis')

        plt.title('Distribution of On-Call Hours per User')
        plt.ylabel('Hours')
        plt.xlabel('User')
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Hour Category')

        # Add annotations showing total hours for each user
        for i, user in enumerate(hours_df.index):
            total_hours = sum(hours_df.loc[user])

            # Get period info
            period_info = ""
            if user in user_periods:
                start = user_periods[user]['start']
                end = user_periods[user]['end']
                period_info = f"\n{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"

            # Annotate with both total hours and period
            plt.annotate(f'{total_hours:.1f}h{period_info}',
                         xy=(i, total_hours + 0.5),
                         ha='center',
                         va='bottom',
                         fontweight='bold',
                         fontsize=8,
                         wrap=True)

        # Add a global date range in the footer
        if self.df.empty is False:
            min_date = self.df['Start'].min().strftime('%Y-%m-%d')
            max_date = self.df['End'].max().strftime('%Y-%m-%d')
            plt.figtext(0.5, 0.01, f"Date Range: {min_date} to {max_date}",
                       ha='center', fontsize=10, fontweight='bold')

        plt.tight_layout(rect=[0, 0.03, 1, 0.97])  # Make room for the footer

        if output_path:
            plt.savefig(output_path, dpi=300)  # Higher DPI for better quality
            print(f"Hours distribution plot saved to {output_path}")
        else:
            plt.show()

    def export_to_excel(self, output_path: Path):
        """Export the compensation report to an Excel file"""
        if self.df.empty:
            print("No data to export")
            return

        # Force pandas to convert all datetime objects to strings to avoid timezone issues
        def ensure_no_datetimes(df):
            """Convert all datetime columns to strings to avoid timezone issues with Excel"""
            df_copy = df.copy()
            for col in df_copy.columns:

                # Convert all datetime columns to string format
                if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                    # Full datetime columns: convert to string in a readable format
                    if col in ['Start', 'End']:
                        df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M')
                    # Just date columns: convert to string in YYYY-MM-DD format
                    elif col == 'Date':
                        df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d')
                    # Any other datetime column: convert to string in a standard format
                    else:
                        df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                # Handle potential Series with datetime objects
                elif pd.api.types.is_object_dtype(df_copy[col]):
                    if df_copy[col].apply(lambda x: isinstance(x, datetime)).any():
                        df_copy[col] = df_copy[col].apply(lambda x:
                            x.strftime('%Y-%m-%d %H:%M') if isinstance(x, datetime) else x)
            return df_copy

        # Create a new Excel writer
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Get the workbook and add formats
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })

            money_format = workbook.add_format({'num_format': '€#,##0.00'})

            # Create detailed shifts sheet
            detailed_df = ensure_no_datetimes(self.df)
            detailed_df.to_excel(writer, sheet_name='Detailed Shifts', index=False)

            # Apply formats to the sheet
            worksheet = writer.sheets['Detailed Shifts']
            for col_num, value in enumerate(detailed_df.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Auto-adjust columns width
            for i, col in enumerate(detailed_df.columns):
                column_length = detailed_df[col].astype(str).map(len)
                # Handle empty dataframes or columns
                max_length = column_length.max() if not column_length.empty else 0
                column_width = max(max_length, len(str(col))) + 2
                worksheet.set_column(i, i, column_width)

            # Add daily summary sheet
            daily_summary = ensure_no_datetimes(self.get_daily_summary())
            if not daily_summary.empty:
                daily_summary.to_excel(writer, sheet_name='Daily Summary', index=False)

                # Apply formats
                worksheet = writer.sheets['Daily Summary']
                for col_num, value in enumerate(daily_summary.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Format the Amount column as money
                amount_col = daily_summary.columns.get_loc('Amount')
                worksheet.set_column(amount_col, amount_col, None, money_format)

                # Auto-adjust columns width
                for i, col in enumerate(daily_summary.columns):
                    column_length = daily_summary[col].astype(str).map(len)
                    max_length = column_length.max() if not column_length.empty else 0
                    column_width = max(max_length, len(str(col))) + 2
                    worksheet.set_column(i, i, column_width)

            # Add user-month totals sheet with prepaid calculation
            user_month_totals = ensure_no_datetimes(self.get_user_month_totals())
            if not user_month_totals.empty:
                # Add columns for pre-paid and final amount calculation
                user_month_df = user_month_totals.copy()
                user_month_df['Pre-Paid Amount'] = 510.0  # Fixed pre-paid amount per month
                user_month_df['Final Amount'] = user_month_df.apply(
                    lambda row: max(0, row['Amount'] - row['Pre-Paid Amount']), axis=1
                )

                # Add Month Name column for better readability
                user_month_df['Month Name'] = user_month_df['Year-Month'].apply(
                    lambda ym: datetime(int(ym.split('-')[0]), int(ym.split('-')[1]), 1).strftime('%B %Y')
                )

                # Reorder columns
                user_month_df = user_month_df[['User', 'Year-Month', 'Month Name', 'Compensated Hours',
                                              'Amount', 'Pre-Paid Amount', 'Final Amount']]

                user_month_df.to_excel(writer, sheet_name='User Month Totals', index=False)

                # Apply formats
                worksheet = writer.sheets['User Month Totals']
                for col_num, value in enumerate(user_month_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Format money columns
                for col in ['Amount', 'Pre-Paid Amount', 'Final Amount']:
                    col_idx = user_month_df.columns.get_loc(col)
                    worksheet.set_column(col_idx, col_idx, None, money_format)

                # Auto-adjust columns width
                for i, col in enumerate(user_month_df.columns):
                    column_length = user_month_df[col].astype(str).map(len)
                    max_length = column_length.max() if not column_length.empty else 0
                    column_width = max(max_length, len(str(col))) + 2
                    worksheet.set_column(i, i, column_width)

                # Add user totals
                user_totals = ensure_no_datetimes(self.get_user_totals())
                if not user_totals.empty:
                    # Calculate rows in user_month sheet to know where to place the totals
                    start_row = len(user_month_df) + 3
                    worksheet.write(start_row - 1, 0, "USER TOTALS", header_format)

                    # Write user totals with proper formatting
                    for i, (idx, row) in enumerate(user_totals.iterrows()):
                        worksheet.write(start_row + i, 0, row['User'])
                        worksheet.write(start_row + i, 3, row['Compensated Hours'])
                        worksheet.write(start_row + i, 4, row['Amount'], money_format)

            # Add a summary sheet
            summary_data = []
            # Get grand total
            grand_total = self.get_grand_total()
            summary_data.append(["Grand Total Amount", grand_total])

            # Get hours breakdown
            hours_breakdown = self.get_hours_breakdown()
            summary_data.append(["Total Compensated Hours", hours_breakdown['total_hours']])
            summary_data.append(["Workday Hours (outside working hours)", hours_breakdown['workday_hours']])
            summary_data.append(["Weekend Hours", hours_breakdown['weekend_hours']])
            summary_data.append(["Holiday Hours", hours_breakdown['holiday_hours']])

            # Calculate total pre-paid amount
            if not user_month_totals.empty:
                unique_user_months = len(user_month_totals.groupby(['User', 'Year-Month']))
                total_prepaid = 510.0 * unique_user_months
                summary_data.append(["Total Pre-Paid Amount", total_prepaid])
                summary_data.append(["Additional Compensation", max(0, grand_total - total_prepaid)])

            # Create the summary sheet
            summary_df = pd.DataFrame(summary_data, columns=['Description', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Apply formats to summary sheet
            worksheet = writer.sheets['Summary']
            for col_num, value in enumerate(summary_df.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Format the Value column based on type
            for i, row in summary_df.iterrows():
                if "Hours" in row['Description']:
                    worksheet.write(i + 1, 1, row['Value'])
                else:
                    worksheet.write(i + 1, 1, row['Value'], money_format)

            # Auto-adjust columns width
            for i, col in enumerate(summary_df.columns):
                column_length = summary_df[col].astype(str).map(len)
                max_length = column_length.max() if not column_length.empty else 0
                column_width = max(max_length, len(str(col))) + 2
                worksheet.set_column(i, i, column_width)

        print(f"Compensation report exported to: {output_path}")


def load_shifts_from_csv(csv_path: Path) -> List[OnCallShift]:
    """Load on-call shifts from a CSV file"""
    shifts = []

    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)

        for row in reader:
            shift = OnCallShift(
                start=row['start'],
                end=row['end'],
                hours=float(row['hours']),
                user=row['user']
            )
            shifts.append(shift)

    return shifts


def fetch_shifts_from_opsgenie(
    api_token: str,
    schedule_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[OnCallShift]:
    """Fetch on-call shifts from OpsGenie API for a given schedule and date range"""

    # Ensure start_date and end_date have timezone info (make them timezone-aware)
    if start_date.tzinfo is None:
        start_date = pytz.UTC.localize(start_date)
    if end_date.tzinfo is None:
        end_date = pytz.UTC.localize(end_date)

    # Calculate the interval in months between start and end date
    months_diff = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1

    # Construct the API URL
    url = OPSGENIE_API_URL.format(schedule_id=schedule_id)
    params = {
        "intervalUnit": "months",
        "interval": months_diff,
        "date": start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    headers = {
        "Authorization": f"GenieKey {api_token}"
    }

    # Make the API request
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        error_message = f"Error from OpsGenie API: {response.status_code}"
        try:
            error_message += f" - {response.json()}"
        except:
            pass
        raise RuntimeError(error_message)

    # Parse the response
    data = response.json()
    shifts = []

    try:
        # Extract rotation periods from the response
        periods = data['data']['finalTimeline']['rotations'][0]['periods']

        for item in periods:
            # Parse the dates and ensure they're timezone-aware
            shift_start = parser.parse(item['startDate'])
            if shift_start.tzinfo is None:
                shift_start = pytz.UTC.localize(shift_start)

            shift_end = parser.parse(item['endDate'])
            if shift_end.tzinfo is None:
                shift_end = pytz.UTC.localize(shift_end)

            # Skip shifts outside our requested date range
            if shift_end < start_date or shift_start > end_date:
                continue

            # Calculate hours
            hours = round((shift_end - shift_start).total_seconds() / 3600, 2)

            # Get user email from the recipient
            user_email = item['recipient'].get('name', "unknown@example.com")

            # Create OnCallShift object
            shift = OnCallShift(
                start=shift_start,
                end=shift_end,
                hours=hours,
                user=user_email
            )
            shifts.append(shift)
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Failed to parse OpsGenie response: {str(e)}")

    return shifts


def save_shifts_to_csv(shifts: List[OnCallShift], output_path: Path):
    """Save shifts to a CSV file for future use"""
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["start", "end", "hours", "user"])
        writer.writeheader()

        for shift in shifts:
            writer.writerow({
                "start": shift.start.strftime(TIME_FORMAT),
                "end": shift.end.strftime(TIME_FORMAT),
                "hours": shift.hours,
                "user": shift.user
            })

    print(f"Saved {len(shifts)} shifts to {output_path}")


def create_default_user_profiles(users: List[str], output_path: Path):
    """Create a default user profiles JSON file for the given users"""
    profiles = []

    # Check if calendars directory exists and has AT calendar
    calendar_year = datetime.now().year
    calendar_dir = Path('calendars')
    at_calendar_path = calendar_dir / f"AT_holidays_{calendar_year}.ics"

    # If Austria calendar doesn't exist, try to download it
    if not at_calendar_path.exists() and calendar_dir.exists():
        click.echo("Austria calendar not found. Attempting to download it...")
        at_calendar_path = download_holiday_calendar('AT', calendar_year, calendar_dir)

    # Determine calendar path to use in profiles
    calendar_file = None
    if at_calendar_path and at_calendar_path.exists():
        calendar_file = str(at_calendar_path)
        click.echo(f"Using Austria holiday calendar: {calendar_file}")

    for user in users:
        profile = {
            "email": user,
            "timezone": "Europe/Berlin",  # Default timezone for German users
            "working_days": [0, 1, 2, 3, 4],  # Monday to Friday
            "working_hours_start": "09:00:00",
            "working_hours_end": "17:00:00",
            "country_code": DEFAULT_COUNTRY_CODE  # Austria as default
        }
        profiles.append(profile)

    with open(output_path, 'w') as f:
        json.dump(profiles, f, indent=2)

    print(f"Created default user profiles at {output_path}")
    print("Please customize the profiles with correct timezones and working hours.")
    if calendar_file:
        print(f"All profiles include the Austria holiday calendar: {calendar_file}")
    else:
        print("No calendar file was found. You may want to run:")
        print("  uv run main.py calendars --country AT")
        print("and then update the user profiles with the calendar file path.")


def process_shifts(shifts, user_profiles, create_profiles, output_plot, export_excel):
    """Process shifts and generate compensation report."""
    # Create default user profiles if requested
    if create_profiles:
        users = list(set(shift.user for shift in shifts))
        output_path = user_profiles or Path('user_profiles.json')
        create_default_user_profiles(users, output_path)
        if not user_profiles:  # if we just created default profiles, exit
            return

    # Initialize the calculator
    calculator = CompensationCalculator(
        user_profiles_path=user_profiles if user_profiles and Path(user_profiles).exists() else None
    )

    # Calculate compensation for each shift
    compensation_periods = []
    for shift in shifts:
        periods = calculator.calculate_compensation(shift)
        compensation_periods.extend(periods)  # Extend with all periods (including holiday periods)

    # Generate and print report
    report = CompensationReport(compensation_periods)
    report.print_report()

    # Generate plot if requested
    if output_plot:
        report.plot_hours_distribution(output_plot)

    # Export to Excel if requested
    if export_excel:
        report.export_to_excel(export_excel)


def download_holiday_calendar(country_code: str, year: int = None, output_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Download holiday calendar for the specified country code and save it to a file.

    Args:
        country_code: Two-letter country code (e.g., 'AT', 'DE')
        year: Optional year to include in the filename
        output_dir: Directory to save the calendar file

    Returns:
        Path to the downloaded calendar file, or None if download failed
    """
    if country_code not in HOLIDAY_CALENDAR_URLS:
        logging.warning(f"No holiday calendar URL defined for country code: {country_code}")
        return None

    # Create output directory if it doesn't exist
    if output_dir is None:
        output_dir = Path('calendars')
    output_dir.mkdir(exist_ok=True, parents=True)

    # Determine filename
    filename = f"{country_code}_holidays"
    if year:
        filename += f"_{year}"
    filename += ".ics"

    output_path = output_dir / filename

    # For older years or if we need to ensure we have holidays for a specific year,
    # create a calendar using the holidays package
    if year and year <= datetime.now().year:
        try:
            # Create an iCalendar file using the holidays package
            cal = icalendar.Calendar()
            cal.add('prodid', f'-//Holidays in {country_code}//{year}//EN')
            cal.add('version', '2.0')

            # Get holidays for the specific country and year
            try:
                country_holidays = holidays.country_holidays(country_code, years=year)

                # If we got holidays, create and save the calendar file
                if country_holidays:
                    # Add each holiday as an event
                    for date, name in country_holidays.items():
                        event = icalendar.Event()
                        event.add('summary', f"{country_code}: {name}")
                        event.add('dtstart', date)
                        event.add('dtend', date)
                        event.add('dtstamp', datetime.now())
                        cal.add_component(event)

                    # Write the iCalendar file
                    with open(output_path, 'wb') as f:
                        f.write(cal.to_ical())

                    logging.info(f"Created holiday calendar for {country_code} {year} using holidays package")
                    return output_path
                else:
                    logging.warning(f"No holidays found for {country_code} {year} using holidays package")
            except (KeyError, AttributeError, ValueError) as e:
                logging.error(f"Failed to get holidays for {country_code} {year}: {str(e)}")
        except Exception as e:
            logging.error(f"Failed to create holiday calendar for {country_code} {year}: {str(e)}")

    # If we couldn't create a calendar with the holidays package or we need future years,
    # try to download from the website
    url = HOLIDAY_CALENDAR_URLS[country_code]
    try:
        logging.info(f"Downloading calendar from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Check if the content looks like an iCal file
        if not response.content.strip().startswith(b'BEGIN:VCALENDAR'):
            logging.error(f"Downloaded content is not a valid iCal file for {country_code}")
            return None

        # If we have a specific year, check if the calendar contains holidays for that year
        if year:
            try:
                cal = icalendar.Calendar.from_ical(response.content)
                year_str = str(year)

                # Look for at least one event for the requested year
                found_year = False
                for component in cal.walk():
                    if component.name == "VEVENT":
                        dt = component.get('dtstart').dt
                        if isinstance(dt, datetime):
                            dt = dt.date()
                        if str(dt.year) == year_str:
                            found_year = True
                            break

                if not found_year:
                    logging.warning(f"Downloaded calendar doesn't contain holidays for {year}")
                    # If the existing calendar creation with holidays package failed and this too,
                    # we'll still save this calendar as a fallback
            except Exception as e:
                logging.warning(f"Error parsing downloaded calendar: {str(e)}")

        # Save the calendar file
        with open(output_path, 'wb') as f:
            f.write(response.content)

        logging.info(f"Downloaded holiday calendar for {country_code} to {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"Failed to download holiday calendar for {country_code}: {str(e)}")
        return None


def parse_ical_holidays(calendar_path: Path) -> Dict[datetime.date, str]:
    """
    Parse an iCalendar file and extract holidays

    Args:
        calendar_path: Path to the .ics calendar file

    Returns:
        Dictionary mapping dates to holiday names
    """
    holidays_dict = {}

    try:
        with open(calendar_path, 'rb') as f:
            cal = icalendar.Calendar.from_ical(f.read())

            for component in cal.walk():
                if component.name == "VEVENT":
                    # Get the event date
                    dt = component.get('dtstart').dt

                    # Make sure it's a date (not a datetime)
                    if isinstance(dt, datetime):
                        dt = dt.date()

                    # Get the summary (holiday name)
                    summary = str(component.get('summary', "Holiday"))

                    # Store in our dictionary
                    holidays_dict[dt] = summary

        return holidays_dict

    except Exception as e:
        logging.error(f"Failed to parse calendar file {calendar_path}: {str(e)}")
        return {}


# Define a Click command group for organizing sub-commands
@click.group()
def cli():
    """Calculate on-call compensation based on OpsGenie API data or CSV files."""
    pass


@cli.command('csv')
@click.argument('csv_file', type=click.Path(exists=True, path_type=Path),
                envvar='OPSGENIE_CSV_FILE')
@click.option('--user-profiles', type=click.Path(path_type=Path),
              help='Path to user profiles JSON file',
              envvar='OPSGENIE_USER_PROFILES')
@click.option('--create-profiles', is_flag=True,
              help='Create default user profiles file')
@click.option('--output-plot', type=click.Path(path_type=Path),
              help='Path to save the daily compensation plot',
              envvar='OPSGENIE_OUTPUT_PLOT')
@click.option('--export-excel', type=click.Path(path_type=Path),
              help='Export the report to an Excel file',
              envvar='OPSGENIE_EXPORT_EXCEL')
def calculate_from_csv(csv_file, user_profiles, create_profiles, output_plot, export_excel):
    """Calculate compensation from a CSV file with on-call shifts data."""
    try:
        shifts = load_shifts_from_csv(csv_file)
        print(f"Loaded {len(shifts)} shifts from {csv_file}")
    except Exception as e:
        click.echo(f"Error loading CSV file: {str(e)}", err=True)
        sys.exit(1)

    process_shifts(shifts, user_profiles, create_profiles, output_plot, export_excel)


@cli.command('opsgenie')
@click.option('--api-token', required=True,
              help='OpsGenie API token',
              envvar='OPSGENIE_API_TOKEN')
@click.option('--schedule-id', required=True,
              help='OpsGenie schedule ID',
              envvar='OPSGENIE_SCHEDULE_ID')
@click.option('--start-date', required=True,
              help='Start date for fetching on-call data (YYYY-MM-DD format)',
              envvar='OPSGENIE_START_DATE')
@click.option('--end-date', required=True,
              help='End date for fetching on-call data (YYYY-MM-DD format)',
              envvar='OPSGENIE_END_DATE')
@click.option('--save-csv', type=click.Path(path_type=Path),
              help='Save OpsGenie data to CSV file for future use',
              envvar='OPSGENIE_SAVE_CSV')
@click.option('--user-profiles', type=click.Path(path_type=Path),
              help='Path to user profiles JSON file',
              envvar='OPSGENIE_USER_PROFILES')
@click.option('--create-profiles', is_flag=True,
              help='Create default user profiles file')
@click.option('--output-plot', type=click.Path(path_type=Path),
              help='Path to save the daily compensation plot',
              envvar='OPSGENIE_OUTPUT_PLOT')
@click.option('--export-excel', type=click.Path(path_type=Path),
              help='Export the report to an Excel file',
              envvar='OPSGENIE_EXPORT_EXCEL')
def calculate_from_opsgenie(api_token, schedule_id, start_date, end_date, save_csv,
                            user_profiles, create_profiles, output_plot, export_excel):
    """Fetch on-call data from OpsGenie API and calculate compensation."""
    # Parse dates
    try:
        start_date_obj = parser.parse(start_date)
        end_date_obj = parser.parse(end_date)
    except Exception as e:
        click.echo(f"Error parsing dates: {str(e)}", err=True)
        click.echo("Please use YYYY-MM-DD format for dates", err=True)
        sys.exit(1)

    # Fetch shifts from OpsGenie API
    try:
        shifts = fetch_shifts_from_opsgenie(
            api_token,
            schedule_id,
            start_date_obj,
            end_date_obj
        )
        click.echo(f"Fetched {len(shifts)} shifts from OpsGenie API")

        # Save to CSV if requested
        if save_csv:
            save_shifts_to_csv(shifts, save_csv)
    except Exception as e:
        click.echo(f"Error fetching data from OpsGenie API: {str(e)}", err=True)
        sys.exit(1)

    process_shifts(shifts, user_profiles, create_profiles, output_plot, export_excel)


@cli.command('profiles')
@click.argument('csv_file', type=click.Path(exists=True, path_type=Path),
                envvar='OPSGENIE_CSV_FILE')
@click.option('--output', '-o', type=click.Path(path_type=Path),
              default='user_profiles.json',
              help='Output path for the user profiles JSON file',
              envvar='OPSGENIE_PROFILES_OUTPUT')
def create_profiles(csv_file, output):
    """Create default user profiles from a CSV file with on-call shifts."""
    try:
        shifts = load_shifts_from_csv(csv_file)
        users = list(set(shift.user for shift in shifts))
        create_default_user_profiles(users, output)
        click.echo(f"Created profiles for {len(users)} users at {output}")
    except Exception as e:
        click.echo(f"Error creating profiles: {str(e)}", err=True)
        sys.exit(1)


@cli.command('calendars')
@click.option('--country', '-c',
              type=click.Choice(['AT', 'DE', 'FR', 'ES', 'BG'], case_sensitive=False),
              multiple=True,
              help='Country codes to download calendars for')
@click.option('--year', '-y', type=int,
              multiple=True,
              help='Years to include in calendar filenames (can specify multiple years)')
@click.option('--year-range', type=str,
              help='Year range in format YYYY-YYYY (e.g., 2024-2026)')
@click.option('--output-dir', '-o',
              type=click.Path(path_type=Path),
              default='calendars',
              help='Directory to save calendar files')
@click.option('--all-countries', '--all', is_flag=True,
              help='Download calendars for all supported countries')
@click.option('--list', is_flag=True,
              help='List all holidays for the specified countries and years')
def download_calendars(country, year, year_range, output_dir, all_countries, list):
    """Download holiday calendar files for the specified countries and years."""
    countries_to_download = []
    years_to_download = []

    # Process country options
    if all_countries:
        # Use hardcoded list of countries instead of calling .keys()
        countries_to_download = ['AT', 'FR', 'ES', 'BG', 'DE']
    elif country:
        # Convert the country tuple to a list without calling list()
        countries_to_download = [c for c in country]
    else:
        click.echo("Please specify at least one country code or use --all-countries")
        sys.exit(1)

    # Process year options
    if year:
        years_to_download = list(year)
    elif year_range:
        try:
            start_year, end_year = map(int, year_range.split('-'))
            years_to_download = list(range(start_year, end_year + 1))
        except ValueError:
            click.echo("Invalid year range format. Please use YYYY-YYYY", err=True)
            sys.exit(1)
    else:
        # Default to current year and previous year
        current_year = datetime.now().year
        years_to_download = [current_year - 1, current_year]
        if current_year - 1 != current_year:  # Just a safety check in case datetime is wrong
            click.echo(f"Using default years: {current_year-1} and {current_year}")
        else:
            click.echo(f"Using default year: {current_year}")

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    # Show summary of what will be downloaded
    click.echo(f"Will download calendars for: {', '.join(countries_to_download)}")
    click.echo(f"For years: {', '.join(map(str, years_to_download))}")

    # Download calendars for each country and year combination
    for country_code in countries_to_download:
        for year_val in years_to_download:
            click.echo(f"Downloading {country_code} calendar for {year_val}...")
            calendar_path = download_holiday_calendar(country_code, year_val, output_dir)

            if calendar_path:
                click.echo(f"✓ Downloaded to {calendar_path}")

                # Parse and display some holidays as a preview
                holidays_dict = parse_ical_holidays(calendar_path)
                if holidays_dict:
                    click.echo(f"  Found {len(holidays_dict)} holidays")
                    if len(holidays_dict) > 0 and isinstance(holidays_dict, dict):
                        # Show up to 3 example holidays
                        click.echo("  Examples:")
                        try:
                            example_holidays = sorted(list(holidays_dict.items()))[:3]
                            for date, name in example_holidays:
                                click.echo(f"    {date.strftime('%Y-%m-%d')}: {name}")
                        except (TypeError, AttributeError) as e:
                            click.echo(f"    Error displaying examples: {str(e)}")
            else:
                click.echo(f"✗ Failed to download calendar for {country_code} {year_val}")

    # List all holidays if requested
    if list:
        click.echo("\n=== LISTING HOLIDAYS ===")
        for country_code in countries_to_download:
            for year_val in years_to_download:
                calendar_path = output_dir / f"{country_code}_holidays_{year_val}.ics"
                if calendar_path.exists():
                    holidays_dict = parse_ical_holidays(calendar_path)
                    click.echo(f"\n{country_code} HOLIDAYS FOR {year_val} ({len(holidays_dict)} holidays):")
                    click.echo("-" * 50)
                    for date, name in sorted(holidays_dict.items()):
                        weekday = date.strftime("%a")  # Get abbreviated weekday name (Mon, Tue, etc.)
                        click.echo(f"  {date.strftime('%Y-%m-%d')} ({weekday}) - {name}")
                else:
                    click.echo(f"\nNo calendar file found for {country_code} {year_val}")

    # Provide updated instructions for using the calendars
    click.echo("\nCalendars are now ready to use with your user profiles.")
    click.echo("The system will automatically use the appropriate calendar based on each shift's date.")
    click.echo("Just ensure your user profiles have the correct country_code set.")


if __name__ == "__main__":
    cli()
