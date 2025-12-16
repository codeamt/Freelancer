"""Auth Decorators - Route protection and permission enforcement."""

from functools import wraps
from typing import List, Optional
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from core.services.auth.auth_service import AnonymousUser
from core.services.auth.helpers import get_current_user_from_request
from core.utils.logger import get_logger

from .context import current_user_context
from .exceptions import PermissionDeniedError

logger = get_logger(__name__)


def require_auth(redirect_to: str = "/login"):
    """
    Decorator to require authentication.
    
    Usage:
        @require_auth()
        async def protected_route(request: Request):
            user = request.state.user  # Guaranteed to exist
            ...
    
    Args:
        redirect_to: URL to redirect to if not authenticated
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get auth service from app state
            auth_service = request.app.state.auth_service
            
            # Get current user
            user = await get_current_user_from_request(request, auth_service)
            
            # Check if authenticated
            if isinstance(user, AnonymousUser) or not user:
                logger.warning(f"Unauthenticated access attempt to {request.url.path}")
                
                # Check if API request (JSON)
                if request.headers.get("Accept") == "application/json":
                    return JSONResponse(
                        {"error": "Authentication required"},
                        status_code=401
                    )
                
                # Redirect to login
                return RedirectResponse(
                    f"{redirect_to}?redirect={request.url.path}",
                    status_code=303
                )
            
            # Attach user to request
            request.state.user = user
            
            # Call original function
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def requires_permission(resource: str, action: str, scope: str = "*"):
    """
    Decorator to require specific permission.
    
    Usage:
        @requires_permission("course", "update")
        async def update_course(request: Request):
            # User has permission to update courses
            ...
    
    Args:
        resource: Resource name (e.g., "course", "product")
        action: Action name (e.g., "read", "write", "delete")
        scope: Scope ("*" for all, "own" for user's own resources)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_context = current_user_context.get(None)
            if not user_context:
                raise RuntimeError("UserContext not set")
            
            if not user_context.has_permission(resource, action):
                raise PermissionDeniedError(
                    f"User {user_context.user_id} ({user_context.role}) "
                    f"lacks permission to {action} {resource}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
  
def requires_role(*roles: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_context = current_user_context.get(None)
            if not user_context:
                raise RuntimeError("UserContext not set")

            user_roles = set(getattr(user_context, "roles", None) or ([user_context.role] if user_context.role else []))

            if not user_roles.intersection(set(roles)):
                raise PermissionDeniedError(
                    f"User role(s) {sorted(user_roles) or [user_context.role]} not allowed. Required: {roles}"
                )
              
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Aliases for backward compatibility
require_role = requires_role
require_permission = requires_permission


def require_admin():
    """Convenience decorator to require admin role."""
    return requires_role("admin", "super_admin")


def require_super_admin():
    """Convenience decorator to require super admin role."""
    return requires_role("super_admin")