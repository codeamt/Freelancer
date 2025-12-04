# app/core/services/auth/utils.py
from functools import wraps
from fasthtml.common import Request, HTTPException
from typing import Callable, Optional
from core.utils.logger import get_logger

logger = get_logger(__name__)

def auth_required(roles: list = None):
    """
    Decorator for route authentication and authorization
    
    Args:
        roles: List of required roles (None for any authenticated user)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get token from header or cookie
            token = (
                request.headers.get("Authorization", "").split(" ")[1] 
                if request.headers.get("Authorization", "").startswith("Bearer ") 
                else request.cookies.get("auth_token")
            )
            
            if not token:
                raise HTTPException(401, "Missing authentication token")
            
            # Verify token and get user
            user = await request.app.state.user_service.authenticate_token(token)
            if not user:
                raise HTTPException(401, "Invalid token")
            
            # Check roles if specified
            if roles and not any(role in user.get('roles', []) for role in roles):
                raise HTTPException(403, "Insufficient permissions")
            
            # Inject user into request context
            request.state.user = user
            return await func(request, *args, **kwargs)
            
        return wrapper
    return decorator
