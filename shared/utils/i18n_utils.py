"""
Internationalization (i18n) utilities for the Laboratory Management System.

This module provides helper functions for:
- Language switching
- Translation testing
- Common translated messages

Usage:
    from shared.utils.i18n_utils import get_common_messages, switch_language_for_test
"""

from django.utils.translation import activate, get_language
from django.utils.translation import gettext_lazy as _


def get_common_messages():
    """
    Get dictionary of commonly used translated messages for testing.
    
    Returns:
        dict: Common messages in current language
    """
    return {
        'pending': _('Pending'),
        'approved': _('Approved'),
        'rejected': _('Rejected'),
        'cancelled': _('Cancelled'),
        'completed': _('Completed'),
        'expired': _('Expired'),
        'present': _('Present'),
        'absent': _('Absent'),
        'late': _('Late'),
        'monday': _('Monday'),
        'tuesday': _('Tuesday'),
        'wednesday': _('Wednesday'),
        'thursday': _('Thursday'),
        'friday': _('Friday'),
        'saturday': _('Saturday'),
        'sunday': _('Sunday'),
        'january': _('January'),
        'february': _('February'),
        'march': _('March'),
        'april': _('April'),
        'may': _('May'),
        'june': _('June'),
        'july': _('July'),
        'august': _('August'),
        'september': _('September'),
        'october': _('October'),
        'november': _('November'),
        'december': _('December'),
        'created_by': _('Created By'),
        'created_at': _('Created At'),
        'updated_by': _('Updated By'),
        'updated_at': _('Updated At'),
        'is_active': _('Is Active'),
        'course': _('Course'),
        'student': _('Student'),
        'teaching_assistants': _('Teaching Assistants'),
        'practicum': _('Practicum'),
        'seminar': _('Seminar'),
        'experiment': _('Experiment'),
        'tutorial': _('Tutorial'),
        'lecture': _('Lecture'),
        'quiz': _('Quiz'),
        'exam': _('Exam'),
    }


def switch_language_for_test(language_code):
    """
    Switch language for testing purposes.
    
    Args:
        language_code (str): Language code ('en' or 'id')
        
    Returns:
        str: Previous language code
    """
    previous_language = get_language()
    activate(language_code)
    return previous_language


def test_translations():
    """
    Test function to verify translations work properly.
    
    Returns:
        dict: Translation results for both languages
    """
    results = {}
    
    # Test English
    switch_language_for_test('en')
    results['en'] = get_common_messages()
    
    # Test Indonesian
    switch_language_for_test('id')
    results['id'] = get_common_messages()
    
    return results


# Common error messages
ERROR_MESSAGES = {
    'invalid_date': _('Invalid date value.'),
    'date_in_past': _('Date cannot be in the past.'),
    'end_before_start': _('End time must be after start time.'),
    'schedule_conflict': _('Schedule conflicts with existing entries.'),
    'permission_denied': _('Only staff members can set status to \'{}\''),
}

# Common success messages  
SUCCESS_MESSAGES = {
    'created': _('Record created successfully'),
    'updated': _('Record updated successfully'),
    'deleted': _('Record deleted successfully'),
    'approved': _('Request approved successfully'),
    'rejected': _('Request rejected successfully'),
} 