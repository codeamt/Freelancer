"""
Auth Module Exports

Provides convenient access to auth services and utilities.
"""
from core.services.auth.auth_service import AuthService, AnonymousUser
from core.services.auth.user_service import UserService
from core.services.auth.providers.jwt import JWTProvider
from core.services.auth.decorators import (
    require_auth, 
    require_role, 
    require_permission,
    requires_permission,
    requires_role,
    require_admin,
    require_super_admin
)
from core.services.auth.utils import get_current_user_from_request
from core.services.auth.context import UserContext, current_user_context
from core.services.auth.context_factory import create_user_context, create_anonymous_context
from core.services.auth.permissions import Permission, Role, permission_registry

__all__ = [
    # Services
    'AuthService',
    'UserService',
    'JWTProvider',
    'AnonymousUser',
    
    # Decorators
    'require_auth',
    'require_role',
    'require_permission',
    'requires_permission',
    'requires_role',
    'require_admin',
    'require_super_admin',
    
    # Context
    'UserContext',
    'current_user_context',
    'create_user_context',
    'create_anonymous_context',
    
    # Permissions
    'Permission',
    'Role',
    'permission_registry',
    
    # Utils
    'get_current_user_from_request',
]
