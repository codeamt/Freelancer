"""Admin decorators for route protection"""
from functools import wraps
from fasthtml.common import RedirectResponse
from core.utils.logger import get_logger

logger = get_logger(__name__)


def require_admin(func):
    """
    Decorator to require admin role for a route.
    
    Usage:
        @app.get("/admin/dashboard")
        @require_admin
        async def admin_dashboard(request: Request):
            ...
    """
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        # Get user from request
        user = request.state.user if hasattr(request.state, 'user') else None
        
        if not user:
            logger.warning("Unauthorized access attempt to admin route")
            return RedirectResponse("/auth/login?redirect=" + str(request.url.path))
        
        # Check if user has admin role
        if "admin" not in user.get("roles", []):
            logger.warning(f"Non-admin user {user.get('_id')} attempted to access admin route")
            return RedirectResponse("/")
        
        return await func(request, *args, **kwargs)
    
    return wrapper


def require_role(*required_roles):
    """
    Decorator to require specific role(s) for a route.
    
    Usage:
        @app.get("/instructor/dashboard")
        @require_role("instructor", "admin")
        async def instructor_dashboard(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            # Get user from request
            user = request.state.user if hasattr(request.state, 'user') else None
            
            if not user:
                logger.warning("Unauthorized access attempt to protected route")
                return RedirectResponse("/auth/login?redirect=" + str(request.url.path))
            
            # Check if user has any of the required roles
            user_roles = user.get("roles", [])
            if not any(role in user_roles for role in required_roles):
                logger.warning(f"User {user.get('_id')} with roles {user_roles} attempted to access route requiring {required_roles}")
                return RedirectResponse("/")
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator
