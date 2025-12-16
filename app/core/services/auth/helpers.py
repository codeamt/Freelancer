"""
Auth Helper Functions

Consolidated module providing:
- Helper functions for authentication and authorization
- Request utilities (merged from utils.py)
"""
from typing import Optional, Dict
from starlette.exceptions import HTTPException
from starlette.requests import Request
from functools import wraps
from core.services.auth.auth_service import AuthService, AnonymousUser
from core.services.auth.context import current_user_context, UserContext
from core.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Request Utilities (merged from utils.py)
# ============================================================================

async def get_current_user_from_request(
    request: Request,
    auth_service: AuthService
):
    """
    Extract and verify user from request.
    
    Checks (in order):
    1. Authorization header (Bearer token)
    2. Cookie (auth_token)
    
    Args:
        request: Starlette request
        auth_service: AuthService instance
        
    Returns:
        User entity or AnonymousUser if not authenticated
    """
    token = None
    
    # Try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    # Try cookie
    if not token:
        token = request.cookies.get("auth_token")
    
    # No token found
    if not token:
        return AnonymousUser()
    
    # Verify token and get user
    try:
        user = await auth_service.get_current_user(token)
        if user:
            return user
    except Exception as e:
        logger.warning(f"Failed to get current user: {e}")
    
    return AnonymousUser()


def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extract token from request.
    
    Args:
        request: Starlette request
        
    Returns:
        Token string or None
    """
    # Try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    # Try cookie
    return request.cookies.get("auth_token")


# ============================================================================
# Context Helpers
# ============================================================================


def get_current_user_from_context() -> Optional[Dict]:
    """
    Get current user from context state (set by middleware).
    
    This is the preferred method when middleware has already set the user context.
    Returns a dict representation of the user for backward compatibility.
    
    Returns:
        User data dict or None if not authenticated
    """
    try:
        user_context = current_user_context.get(None)
        if not user_context:
            return None
        
        return {
            "id": user_context.user_id,
            "_id": str(user_context.user_id),
            "role": user_context.role,
            "roles": list(getattr(user_context, "roles", []) or []),
        }
    except Exception as e:
        logger.warning(f"Failed to get user from context: {e}")
        return None


async def get_current_user(request: Request, auth_service: AuthService = None) -> Optional[Dict]:
    """
    Get current user from request (cookie or header).
    
    Args:
        request: Starlette request
        auth_service: AuthService instance (optional)
        
    Returns:
        User data dict or None if not authenticated
    """
    token = request.cookies.get("auth_token")
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        return None
    
    try:
        if not auth_service:
            auth_service = AuthService()
        
        user_id = auth_service.jwt.verify(token).get("user_id") if auth_service.jwt.verify(token) else None
        
        if user_id:
            user = await auth_service.get_user_by_id(str(user_id))
            return user
        
        return None
        
    except Exception as e:
        logger.warning(f"Failed to get current user: {e}")
        return None


def require_role(required_role: str):
    """
    Decorator to require specific role for route access.
    
    Usage:
        @require_role("admin")
        async def admin_dashboard(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = next((a for a in args if isinstance(a, Request)), None)
            if not request:
                raise HTTPException(status_code=400, detail="Request not found")
            
            user = await get_current_user(request)
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            auth_service = AuthService()
            user_roles = auth_service.get_user_roles(user.get("_id") or str(user.get("id")))
            
            if required_role not in user_roles and "admin" not in user_roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(required_permission: str):
    """
    Decorator to require specific permission for route access.
    
    Usage:
        @require_permission("courses.create")
        async def create_course(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = next((a for a in args if isinstance(a, Request)), None)
            if not request:
                raise HTTPException(status_code=400, detail="Request not found")
            
            user = await get_current_user(request)
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            auth_service = AuthService()
            user_id = user.get("_id") or str(user.get("id"))
            
            if not auth_service.has_permission(user_id, required_permission):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def is_instructor(user: Dict) -> bool:
    """Check if user is an instructor"""
    roles = user.get("roles", [user.get("role")])
    return "instructor" in roles or "admin" in roles


def is_student(user: Dict) -> bool:
    """Check if user is a student"""
    roles = user.get("roles", [user.get("role")])
    return "student" in roles or "admin" in roles


def is_admin(user: Dict) -> bool:
    """Check if user is an admin"""
    roles = user.get("roles", [user.get("role")])
    return "admin" in roles or "super_admin" in roles


__all__ = [
    # Request utilities (from utils.py)
    "get_current_user_from_request",
    "extract_token_from_request",
    # Context helpers
    "get_current_user_from_context",
    "get_current_user",
    # Decorators
    "require_role",
    "require_permission",
    # Role checks
    "is_instructor",
    "is_student",
    "is_admin",
]
