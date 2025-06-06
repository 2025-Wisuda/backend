"""
Django Language Parameter Middleware

This middleware provides dynamic language switching functionality based on URL
query parameters. It allows users to change the application language on-the-fly
by adding a 'lang' parameter to any URL, enabling better internationalization
support for multi-language applications.

Features:
- Dynamic language switching via URL query parameters
- Session persistence for selected language
- Fallback to default language for invalid language codes
- Integration with Django's internationalization framework
- Support for all languages configured in Django settings

Usage:
1. Add to Django middleware in settings.py:
   MIDDLEWARE = [
       'shared.middleware.LanguageParameterMiddleware',
       # ... other middleware
   ]

2. Use in URLs:
   http://example.com/api/users/?lang=en
   http://example.com/api/users/?lang=id

Supported Languages:
- Determined by LANGUAGES setting in Django configuration
- Falls back to LANGUAGE_CODE setting for invalid/missing parameters

Security Notes:
- Only accepts language codes defined in Django LANGUAGES setting
- Automatically falls back to default language for security
"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import activate


class LanguageParameterMiddleware(MiddlewareMixin):
    """
    Middleware to set the language based on a 'lang' query parameter.
    If the language is not available, it defaults to the language set in settings.
    """

    def process_request(self, request):
        language = request.GET.get("lang")
        available = dict(settings.LANGUAGES)
        if language in available:
            activate(language)
            if hasattr(request, "session"):
                request.session["django_language"] = language
        else:
            activate(settings.LANGUAGE_CODE)
