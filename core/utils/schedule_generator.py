"""
Schedule Generator Utility

Utility untuk generate multiple schedule dates berdasarkan date range dan days.
Bisa dipake untuk Lab Schedule, Duty Schedule, dan model scheduling lainnya.

Features:
- Generate dates based on start_date, end_date, dan selected days
- Support multiple days (e.g., ['MONDAY', 'WEDNESDAY', 'FRIDAY'])
- Handle holidays dan exclusions
- Validate generated dates
- Support untuk different time slots

Usage:
    from core.utils.schedule_generator import ScheduleGenerator
    
    generator = ScheduleGenerator()
    dates = generator.generate_dates(
        start_date=date(2025, 6, 1),
        end_date=date(2025, 6, 30),
        days=['MONDAY', 'WEDNESDAY', 'FRIDAY'],
        exclude_holidays=True
    )
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.enums import ActivityType


class ScheduleGenerator:
    """Generator untuk create multiple schedule dates."""

    # Mapping hari dalam bahasa Indonesia/English
    DAYS_MAPPING = {
        "MONDAY": 0,
        "SENIN": 0,
        "TUESDAY": 1,
        "SELASA": 1,
        "WEDNESDAY": 2,
        "RABU": 2,
        "THURSDAY": 3,
        "KAMIS": 3,
        "FRIDAY": 4,
        "JUMAT": 4,
        "SATURDAY": 5,
        "SABTU": 5,
        "SUNDAY": 6,
        "MINGGU": 6,
    }

    def __init__(self):
        self.generated_dates = []
        self.excluded_dates = []

    def generate_dates(
        self,
        start_date: date,
        end_date: date,
        days: List[str],
        exclude_holidays: bool = True,
        exclude_dates: Optional[List[date]] = None,
    ) -> List[date]:
        """
        Generate list tanggal berdasarkan criteria yang diberikan.

        Args:
            start_date: Tanggal mulai
            end_date: Tanggal berakhir
            days: List hari yang dipilih ['MONDAY', 'FRIDAY', etc]
            exclude_holidays: Exclude hari libur nasional
            exclude_dates: List tanggal yang mau di-exclude manual

        Returns:
            List[date]: List tanggal yang di-generate
        """
        self._validate_inputs(start_date, end_date, days)

        # Convert days ke weekday numbers
        weekdays = [self.DAYS_MAPPING[day.upper()] for day in days]
        exclude_dates = exclude_dates or []

        generated_dates = []
        current_date = start_date

        while current_date <= end_date:
            # Check apakah hari ini sesuai dengan days yang dipilih
            if current_date.weekday() in weekdays:
                # Check exclude conditions
                if not self._should_exclude_date(
                    current_date, exclude_holidays, exclude_dates
                ):
                    generated_dates.append(current_date)

            current_date += timedelta(days=1)

        self.generated_dates = generated_dates
        return generated_dates

    def generate_schedule_data(
        self,
        start_date: date,
        end_date: date,
        days: List[str],
        time_slots: List[Dict[str, Any]],
        type: str = ActivityType.PRACTICUM.value,
        details: Optional[str] = None,
        created_by=None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generate complete schedule data untuk bulk creation.

        Args:
            start_date: Tanggal mulai
            end_date: Tanggal berakhir
            days: List hari yang dipilih
            time_slots: List time slots [{'start_time': time(9,0), 'end_time': time(11,0)}]
            type: Jenis aktivitas
            details: Detail aktivitas
            created_by: User yang create
            **kwargs: Additional fields

        Returns:
            List[Dict]: List data schedule siap untuk bulk create
        """
        dates = self.generate_dates(start_date, end_date, days)
        schedule_data = []

        for date in dates:
            for time_slot in time_slots:
                schedule_item = {
                    "scheduled_date": date,
                    "activity_start_time": time_slot["start_time"],
                    "activity_end_time": time_slot["end_time"],
                    "lab_type": type,
                    "lab_details": details,
                    "created_by": created_by,
                    **kwargs,  # Additional fields
                }
                schedule_data.append(schedule_item)

        return schedule_data

    def _validate_inputs(self, start_date: date, end_date: date, days: List[str]):
        """Validate input parameters."""
        if start_date >= end_date:
            raise ValidationError(_("Start date must be before end date"))

        if not days:
            raise ValidationError(_("At least one day must be selected"))

        # Validate days
        invalid_days = [day for day in days if day.upper() not in self.DAYS_MAPPING]
        if invalid_days:
            raise ValidationError(
                _("Invalid days: %(days)s") % {"days": ", ".join(invalid_days)}
            )

        # Check if start_date is not in the past
        if start_date < timezone.localdate():
            raise ValidationError(_("Start date cannot be in the past"))

    def _should_exclude_date(
        self, current_date: date, exclude_holidays: bool, exclude_dates: List[date]
    ) -> bool:
        """Check apakah tanggal harus di-exclude."""
        # Manual exclusions
        if current_date in exclude_dates:
            return True

        # Holiday exclusions (bisa extend dengan holiday library)
        if exclude_holidays:
            # TODO: Integrate dengan holiday library atau custom holiday list
            # Contoh: Indonesian holidays
            indonesia_holidays_2025 = [
                date(2025, 1, 1),  # New Year
                date(2025, 8, 17),  # Independence Day
                date(2025, 12, 25),  # Christmas
                # Add more holidays as needed
            ]
            if current_date in indonesia_holidays_2025:
                return True

        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics dari generated dates."""
        if not self.generated_dates:
            return {}

        return {
            "total_dates": len(self.generated_dates),
            "start_date": min(self.generated_dates),
            "end_date": max(self.generated_dates),
            "weekdays_distribution": self._get_weekday_distribution(),
            "excluded_count": len(self.excluded_dates),
        }

    def _get_weekday_distribution(self) -> Dict[str, int]:
        """Get distribusi hari dari generated dates."""
        weekday_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        distribution = {day: 0 for day in weekday_names}

        for date_item in self.generated_dates:
            weekday_name = weekday_names[date_item.weekday()]
            distribution[weekday_name] += 1

        return distribution


# Convenience functions
def generate_lab_dates(
    start_date: date, end_date: date, days: List[str], **kwargs
) -> List[date]:
    """Convenience function untuk generate lab schedule dates."""
    generator = ScheduleGenerator()
    return generator.generate_dates(start_date, end_date, days, **kwargs)


def generate_duty_dates(
    start_date: date, end_date: date, days: List[str], **kwargs
) -> List[date]:
    """Convenience function untuk generate duty schedule dates."""
    generator = ScheduleGenerator()
    return generator.generate_dates(start_date, end_date, days, **kwargs)
