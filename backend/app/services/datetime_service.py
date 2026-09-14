import datetime
import zoneinfo
import re
from typing import Any, Optional, Tuple

class DateTimeService:
    """
    Central, reliable date/time service for Nexus AI.
    Never lets models guess today's date or time.
    Injects current date and user timezone into context and handles
    natural language date range resolution.
    """
    
    DEFAULT_TIMEZONE = "Asia/Kolkata"
    
    @classmethod
    def get_user_timezone_str(cls) -> str:
        # Default to Asia/Kolkata as per session environment, fallback to system
        return cls.DEFAULT_TIMEZONE

    @classmethod
    def get_user_tz(cls) -> datetime.tzinfo:
        try:
            return zoneinfo.ZoneInfo(cls.get_user_timezone_str())
        except Exception:
            # Fallback to local offset (e.g. +05:30)
            return datetime.timezone(datetime.timedelta(hours=5, minutes=30))

    @classmethod
    def get_current_datetime(cls) -> datetime.datetime:
        tz = cls.get_user_tz()
        return datetime.datetime.now(tz)

    @classmethod
    def get_current_date_str(cls) -> str:
        """Returns YYYY-MM-DD, e.g. '2026-09-14'"""
        return cls.get_current_datetime().strftime("%Y-%m-%d")

    @classmethod
    def get_current_time_str(cls) -> str:
        """Returns HH:MM:SS or 12-hour format with AM/PM"""
        return cls.get_current_datetime().strftime("%I:%M %p")

    @classmethod
    def get_current_context(cls) -> dict[str, str]:
        now = cls.get_current_datetime()
        return {
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%I:%M:%S %p"),
            "day_of_week": now.strftime("%A"),
            "timezone": cls.get_user_timezone_str(),
            "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p %Z")
        }

    @classmethod
    def parse_natural_date_range(cls, text: str) -> Tuple[str, str]:
        """
        Parses natural language date mentions into exact (start_datetime, end_datetime)
        strings formatted as 'YYYY-MM-DD HH:MM:SS'.
        Supports:
          - 'today'
          - 'tomorrow'
          - 'yesterday'
          - '15 september', '15 september 2026', 'september 15'
          - 'next monday', 'this week', 'next week'
        Defaults to today's full day range if nothing detected.
        """
        now = cls.get_current_datetime()
        today = now.date()
        lower = text.lower().strip()

        # Check for explicit date like "15 september" or "september 15" or "2026-09-15"
        # 1. YYYY-MM-DD
        iso_match = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", lower)
        if iso_match:
            y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
            target_date = datetime.date(y, m, d)
            return (f"{target_date} 00:00:00", f"{target_date} 23:59:59")

        # 2. Month name and day, e.g. "15 september", "september 15", "15th sept", "sep 15"
        months = {
            "january": 1, "jan": 1,
            "february": 2, "feb": 2,
            "march": 3, "mar": 3,
            "april": 4, "apr": 4,
            "may": 5,
            "june": 6, "jun": 6,
            "july": 7, "jul": 7,
            "august": 8, "aug": 8,
            "september": 9, "sept": 9, "sep": 9,
            "october": 10, "oct": 10,
            "november": 11, "nov": 11,
            "december": 12, "dec": 12
        }
        month_names_pattern = "|".join(months.keys())
        
        # pattern: 15 september (optional year) or 15th september
        pattern_d_m = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({month_names_pattern})(?:\s+(\d{{4}}))?\b", lower)
        if pattern_d_m:
            day = int(pattern_d_m.group(1))
            month_str = pattern_d_m.group(2)
            month = months[month_str]
            year = int(pattern_d_m.group(3)) if pattern_d_m.group(3) else today.year
            try:
                target_date = datetime.date(year, month, day)
                return (f"{target_date} 00:00:00", f"{target_date} 23:59:59")
            except ValueError:
                pass

        # pattern: september 15 (optional year) or september 15th
        pattern_m_d = re.search(rf"\b({month_names_pattern})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s+(\d{{4}}))?\b", lower)
        if pattern_m_d:
            month_str = pattern_m_d.group(1)
            month = months[month_str]
            day = int(pattern_m_d.group(2))
            year = int(pattern_m_d.group(3)) if pattern_m_d.group(3) else today.year
            try:
                target_date = datetime.date(year, month, day)
                return (f"{target_date} 00:00:00", f"{target_date} 23:59:59")
            except ValueError:
                pass

        # 3. 'tomorrow'
        if "tomorrow" in lower:
            target_date = today + datetime.timedelta(days=1)
            return (f"{target_date} 00:00:00", f"{target_date} 23:59:59")

        # 4. 'yesterday'
        if "yesterday" in lower:
            target_date = today - datetime.timedelta(days=1)
            return (f"{target_date} 00:00:00", f"{target_date} 23:59:59")

        # 5. 'this week'
        if "this week" in lower:
            start_week = today - datetime.timedelta(days=today.weekday())
            end_week = start_week + datetime.timedelta(days=6)
            return (f"{start_week} 00:00:00", f"{end_week} 23:59:59")

        # 6. 'next week'
        if "next week" in lower:
            start_next = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(days=7)
            end_next = start_next + datetime.timedelta(days=6)
            return (f"{start_next} 00:00:00", f"{end_next} 23:59:59")

        # 7. 'next monday', 'next tuesday', etc.
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for idx, wname in enumerate(weekdays):
            if f"next {wname}" in lower or f"on {wname}" in lower:
                days_ahead = (idx - today.weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                target_date = today + datetime.timedelta(days=days_ahead)
                return (f"{target_date} 00:00:00", f"{target_date} 23:59:59")

        # 8. 'today' or default
        return (f"{today} 00:00:00", f"{today} 23:59:59")
