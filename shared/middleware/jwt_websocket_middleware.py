"""
JWT Authentication Middleware for Django Channels WebSocket connections.

Allows WebSocket connections to authenticate using Simple JWT tokens.
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT authentication middleware for WebSocket connections.
    
    Accepts JWT tokens via:
    1. Authorization header: Bearer <token>
    2. Query parameters: ?token=<token>
    """

    async def __call__(self, scope, receive, send):
        # Extract token from headers or query params
        token = await self.get_token_from_scope(scope)
        
        # Authenticate user
        user = await self.get_user_from_token(token)
        scope['user'] = user
        
        return await super().__call__(scope, receive, send)

    async def get_token_from_scope(self, scope):
        """Extract JWT token from WebSocket scope."""
        
        # Try to get token from Authorization header
        headers = dict(scope.get('headers', []))
        auth_header = headers.get(b'authorization')
        
        if auth_header:
            auth_header = auth_header.decode('utf-8')
            if auth_header.startswith('Bearer '):
                return auth_header.split(' ')[1]
        
        # Try to get token from query parameters
        query_params = parse_qs(scope.get('query_string', b'').decode())
        token = query_params.get('token')
        
        if token and len(token) > 0:
            return token[0]
        
        return None

    @database_sync_to_async
    def get_user_from_token(self, token):
        """Get user from Simple JWT token."""
        
        if not token:
            return AnonymousUser()
        
        try:
            # Use Simple JWT authentication
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            return user
                
        except (InvalidToken, TokenError, Exception):
            pass
            
        return AnonymousUser() 