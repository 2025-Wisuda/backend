"""
URLs for i18n (internationalization) testing endpoints.
"""

from django.urls import path

from ..views.i18n_test_view import language_info, test_translations

app_name = "i18n"

urlpatterns = [
    path("test-translations/", test_translations, name="test_translations"),
    path("language-info/", language_info, name="language_info"),
] 