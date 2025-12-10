# app/core/services/auth/decorators.py (new)
"""Auth Decorators"""
from functools import wraps
from typing import List, Optional
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from core.services.auth.auth_service import AuthService, AnonymousUser
from core.services.auth.utils import get_current_user_from_request
from core.utils.logger import get_logger

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


def require_role(*required_roles: str, redirect_to: str = "/"):
    """
    Decorator to require specific role(s).
    
    Usage:
        @require_role("admin", "moderator")
        async def admin_route(request: Request):
            ...
    
    Args:
        required_roles: Required role names
        redirect_to: URL to redirect to if insufficient permissions
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get auth service
            auth_service = request.app.state.auth_service
            
            # Get current user
            user = await get_current_user_from_request(request, auth_service)
            
            # Check authentication
            if isinstance(user, AnonymousUser) or not user:
                logger.warning(f"Unauthenticated access to role-protected route")
                return RedirectResponse("/login", status_code=303)
            
            # Check role
            if user.role not in required_roles:
                logger.warning(
                    f"User {user.id} ({user.role}) denied access "
                    f"to route requiring roles: {required_roles}"
                )
                
                if request.headers.get("Accept") == "application/json":
                    return JSONResponse(
                        {"error": "Insufficient permissions"},
                        status_code=403
                    )
                
                return RedirectResponse(redirect_to, status_code=303)
            
            # Attach user to request
            request.state.user = user
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(
    resource: str,
    action: str,
    redirect_to: str = "/"
):
    """
    Decorator to require specific permission.
    
    Usage:
        @require_permission("product", "write")
        async def create_product(request: Request):
            ...
    
    Args:
        resource: Resource name
        action: Action name
        redirect_to: URL to redirect to if insufficient permissions
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get auth service
            auth_service = request.app.state.auth_service
            
            # Get current user
            user = await get_current_user_from_request(request, auth_service)
            
            # Check authentication
            if isinstance(user, AnonymousUser) or not user:
                return RedirectResponse("/login", status_code=303)
            
            # Check permission
            has_perm = await auth_service.check_permission(
                user.id,
                resource,
                action
            )
            
            if not has_perm:
                logger.warning(
                    f"User {user.id} denied permission "
                    f"to {action} {resource}"
                )
                
                if request.headers.get("Accept") == "application/json":
                    return JSONResponse(
                        {"error": "Insufficient permissions"},
                        status_code=403
                    )
                
                return RedirectResponse(redirect_to, status_code=303)
            
            # Attach user to request
            request.state.user = user
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator