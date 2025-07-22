"""
API views for testing i18n (internationalization) functionality.

These views demonstrate how language switching works in API responses
and can be used to verify that translations are working correctly.
"""

from django.utils.translation import gettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from shared.presenter import ResponsePresenter
from shared.utils.i18n_utils import get_common_messages


@api_view(['GET'])
@permission_classes([AllowAny])
def test_translations(request):
    """
    Test endpoint to demonstrate i18n translations.
    
    Query Parameters:
        lang (str, optional): Language code ('en' or 'id'). 
                             If not provided, uses request language or default.
    
    Returns:
        Response: JSON response with translated messages
    """
    
    # Get common translated messages
    messages = get_common_messages()
    
    # Create response with translated content
    response_data = {
        'current_language': request.LANGUAGE_CODE,
        'available_languages': ['en', 'id'],
        'common_messages': messages,
        'api_messages': {
            'success_message': _('Data retrieved successfully'),
            'welcome_message': _('Welcome to Laboratory Management System'),
            'error_message': _('An error occurred while processing your request'),
        },
        'status_examples': {
            'pending_status': _('Pending'),
            'approved_status': _('Approved'),
            'rejected_status': _('Rejected'),
        },
        'user_types': {
            'student': _('Student'),
            'teaching_assistant': _('Teaching Assistants'),
        }
    }
    
    return ResponsePresenter.success_response(
        message=_('Translation test completed successfully'),
        data=response_data
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def language_info(request):
    """
    Get current language information and available languages.
    
    Returns:
        Response: Language information
    """
    
    return ResponsePresenter.success_response(
        message=_('Language information retrieved successfully'),
        data={
            'current_language': {
                'code': request.LANGUAGE_CODE,
                'name': 'English' if request.LANGUAGE_CODE == 'en' else 'Bahasa Indonesia'
            },
            'available_languages': [
                {'code': 'en', 'name': 'English'},
                {'code': 'id', 'name': 'Bahasa Indonesia'}
            ],
            'instructions': {
                'header_method': _('Set Accept-Language header in your request'),
                'query_param_method': _('Add ?lang=en or ?lang=id to the URL'),
                'example': '/api/v1/test-translations?lang=id'
            }
        }
    ) 