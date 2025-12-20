"""
Auth Module Exports

Provides convenient access to auth services and utilities.
"""
from core.services.auth.auth_service import AuthService, AnonymousUser
from core.services.auth.user_service import UserService
from core.services.auth.providers.jwt import JWTProvider
from core.services.auth.decorators import (
    require_auth, 
    require_role as decorator_require_role, 
    require_permission as decorator_require_permission,
    requires_permission,
    requires_role,
    require_admin,
    require_super_admin
)
from core.services.auth.context import (
    UserContext, 
    current_user_context,
    create_user_context,
    create_anonymous_context
)
from core.services.auth.helpers import get_current_user_from_request, extract_token_from_request
from core.services.auth.permissions import Permission, Role, permission_registry
from core.services.auth.helpers import (
    get_current_user,
    get_current_user_from_context,
    require_role as helper_require_role,
    require_permission as helper_require_permission,
    is_instructor,
    is_student,
    is_admin
)
from core.services.auth.providers.adapters.google_oauth import GoogleOAuthService

# Import Pydantic models for type safety
from core.services.auth.models import (
    User,
    UserCreate,
    UserUpdate,
    LoginRequest,
    LoginResponse,
    TokenPayload,
    TokenRefreshRequest,
    TokenRefreshResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    PermissionCheck,
    PermissionCheckResponse,
    RoleAssignment,
    SessionInfo,
    UserRole,
    UserStatus,
)

__all__ = [
    # Services
    'AuthService',
    'UserService',
    'JWTProvider',
    'AnonymousUser',
    'GoogleOAuthService',
    
    # Pydantic Models
    'User',
    'UserCreate',
    'UserUpdate',
    'LoginRequest',
    'LoginResponse',
    'TokenPayload',
    'TokenRefreshRequest',
    'TokenRefreshResponse',
    'PasswordChangeRequest',
    'PasswordResetRequest',
    'PasswordResetConfirm',
    'PermissionCheck',
    'PermissionCheckResponse',
    'RoleAssignment',
    'SessionInfo',
    'UserRole',
    'UserStatus',
    
    # Decorators
    'require_auth',
    'decorator_require_role',
    'decorator_require_permission',
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
    'get_current_user',
    'get_current_user_from_context',
    
    # Helper decorators (framework compatible)
    'helper_require_role',
    'helper_require_permission',
    
    # Role helpers
    'is_instructor',
    'is_student',
    'is_admin',
]

# Provide backward compatibility aliases
require_role = helper_require_role
require_permission = helper_require_permission
