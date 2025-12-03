"""Auth utility functions"""
from fasthtml.common import Request
from typing import Optional, Dict
from core.utils.logger import get_logger

logger = get_logger(__name__)


async def get_current_user(request: Request, auth_service) -> Optional[Dict]:
    """
    Get current authenticated user from request.
    
    Args:
        request: FastHTML Request object
        auth_service: AuthService instance
        
    Returns:
        User data dict if authenticated, None otherwise
    """
    try:
        # Try Authorization header first
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user_data = auth_service.verify_token(token)
            if user_data:
                return await auth_service.get_user_by_id(user_data.get("sub"))
        
        # Try cookie
        token = request.cookies.get("auth_token")
        if token:
            user_data = auth_service.verify_token(token)
            if user_data:
                return await auth_service.get_user_by_id(user_data.get("sub"))
        
        return None
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None
