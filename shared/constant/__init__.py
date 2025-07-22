"""
Shared Constants Module for Teaching Assistant Laboratory Management System

This module provides centralized constant definitions for the laboratory management
application. It ensures consistency across the system by providing standardized
values for business rules, time constraints, and operational parameters.

What: Centralized constant definitions for application-wide use
Why: Maintains consistency and provides single source of truth for business rules
How: Import constants from this module instead of hardcoding values throughout the application

Main Components:
- LabOperatingHoursConstant: Standard laboratory operating hours configuration

Key Features:
- Centralized constant management for maintainability
- Type-safe constant definitions with proper typing
- Comprehensive documentation for each constant
- Business rule enforcement through standardized values
- Easy configuration changes through single source of truth
- Integration with Django's time and datetime utilities

Constant Categories:
- Time-based constants: Operating hours, scheduling boundaries
- Business rule constants: Validation thresholds, limits
- Configuration constants: System-wide settings

Usage Examples:
    from shared.constant import LabOperatingHoursConstant
    from datetime import time
    
    # Validate booking time against lab operating hours
    booking_time = time(14, 30)  # 2:30 PM
    
    if (LabOperatingHoursConstant.START_TIME <= booking_time <= 
        LabOperatingHoursConstant.END_TIME):
        logger.info("Booking time is within lab operating hours")
    else:
        logger.warning("Booking time is outside lab operating hours")
    
    # Display operating hours in UI
    start_time = LabOperatingHoursConstant.START_TIME.strftime('%H:%M')
    end_time = LabOperatingHoursConstant.END_TIME.strftime('%H:%M')
    logger.info(f"Lab operates from {start_time} to {end_time}")

Integration with Business Logic:
    from shared.constant import LabOperatingHoursConstant
    from django.core.exceptions import ValidationError
    
    def validate_lab_booking_time(booking_time):
        \"\"\"Validate if booking time falls within lab operating hours.\"\"\"
        if not (LabOperatingHoursConstant.START_TIME <= booking_time <= 
                LabOperatingHoursConstant.END_TIME):
            raise ValidationError(
                f"Booking time must be between "
                f"{LabOperatingHoursConstant.START_TIME.strftime('%H:%M')} "
                f"and {LabOperatingHoursConstant.END_TIME.strftime('%H:%M')}"
            )
        return True

Form Validation Integration:
    from django import forms
    from shared.constant import LabOperatingHoursConstant
    
    class LabBookingForm(forms.Form):
        booking_time = forms.TimeField(
            help_text=f"Lab operates from "
                     f"{LabOperatingHoursConstant.START_TIME.strftime('%H:%M')} "
                     f"to {LabOperatingHoursConstant.END_TIME.strftime('%H:%M')}"
        )
        
        def clean_booking_time(self):
            booking_time = self.cleaned_data['booking_time']
            if not (LabOperatingHoursConstant.START_TIME <= booking_time <= 
                    LabOperatingHoursConstant.END_TIME):
                raise forms.ValidationError(
                    "Booking time must be within lab operating hours"
                )
            return booking_time

API Response Integration:
    from rest_framework.response import Response
    from shared.constant import LabOperatingHoursConstant
    from shared.presenter import ResponsePresenter
    
    def get_lab_operating_hours(request):
        \"\"\"API endpoint to get lab operating hours.\"\"\"
        data = {
            'start_time': LabOperatingHoursConstant.START_TIME.strftime('%H:%M'),
            'end_time': LabOperatingHoursConstant.END_TIME.strftime('%H:%M'),
            'duration_hours': (
                datetime.combine(date.today(), LabOperatingHoursConstant.END_TIME) -
                datetime.combine(date.today(), LabOperatingHoursConstant.START_TIME)
            ).total_seconds() / 3600
        }
        return ResponsePresenter.success_response(
            "Lab operating hours retrieved successfully", 
            data
        )

Template Usage:
    <!-- In Django templates -->
    {% load custom_tags %}
    
    <p>Laboratory operating hours:</p>
    <p>{{ lab_hours.START_TIME|time:"H:i" }} - {{ lab_hours.END_TIME|time:"H:i" }}</p>
    
    <!-- Where lab_hours is passed from view context -->
    context = {
        'lab_hours': LabOperatingHoursConstant
    }

Configuration Benefits:
- Single point of configuration for lab operating hours
- Easy maintenance when business rules change
- Consistent time validation across all modules
- Type safety with Python time objects
- Self-documenting code with descriptive constant names
- Reduced duplication of time values throughout codebase

Future Extensibility:
This module can be extended to include additional constants such as:
- Maximum booking duration limits
- Minimum advance booking time
- Holiday and weekend operating hour exceptions
- Different operating hours for different lab types
- Seasonal operating hour adjustments
"""

from .lab_operating_hours_constant import LabOperatingHoursConstant

__all__ = [
    "LabOperatingHoursConstant",
]
