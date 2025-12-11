# app/core/services/auth/decorators.py (new)
"""Auth Decorators"""
from functools import wraps
from typing import List, Optional
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from core.services.auth.auth_service import AuthService, AnonymousUser
from core.services.auth.utils import get_current_user_from_request
from core.utils.logger import get_logger

from .context import current_user_context, Permission
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


def requires_permission(permission: Permission):
      def decorator(func):
          @wraps(func)
          async def wrapper(*args, **kwargs):
              user_context = current_user_context.get(None)
              if not user_context:
                  raise RuntimeError("UserContext not set")
              
              if not user_context.has_permission(permission):
                  raise PermissionDeniedError(
                      f"User {user_context.user_id} missing permission: {permission.value}"
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
              
            if user_context.role not in roles:
                raise PermissionDeniedError(
                    f"User role {user_context.role} not allowed. Required: {roles}"
                )
              
            return await func(*args, **kwargs)
        return wrapper
    return decorator