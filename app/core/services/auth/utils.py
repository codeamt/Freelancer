# app/core/services/auth/utils.py
"""Auth Utilities"""
from typing import Optional
from starlette.requests import Request
from core.services.auth.auth_service import AuthService, AnonymousUser
from core.utils.logger import get_logger

logger = get_logger(__name__)


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