"""
Anonymous User Fix Middleware

Handles AnonymousUser attribute access issues in Django admin
by adding group property to AnonymousUser instances.
"""

from django.contrib.auth.models import AnonymousUser


class AnonymousUserFixMiddleware:
    """
    Middleware to add group attribute to AnonymousUser instances.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Add group property to AnonymousUser class
        if not hasattr(AnonymousUser, "group"):
            AnonymousUser.group = property(lambda self: None)

    def __call__(self, request):
        # Ensure AnonymousUser has group attribute
        if hasattr(request, "user") and isinstance(request.user, AnonymousUser):
            if not hasattr(request.user, "group"):
                request.user.group = None

        response = self.get_response(request)
        return response
