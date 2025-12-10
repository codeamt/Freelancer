"""
Auth Module Exports

Provides convenient access to auth services and utilities.
"""
from core.services.auth.auth_service import AuthService, AnonymousUser
from core.services.auth.user_service import UserService
from core.services.auth.providers.jwt import JWTProvider
from core.services.auth.decorators import require_auth, require_role, require_permission
from core.services.auth.utils import get_current_user_from_request

__all__ = [
    'AuthService',
    'UserService',
    'JWTProvider',
    'AnonymousUser',
    'require_auth',
    'require_role',
    'require_permission',
    'get_current_user_from_request',
]
