"""Auth Integration for LMS Add-on"""
from fasthtml.common import *
from typing import Optional, Dict
import sys
import os

# Add parent directory to path to import auth add-on
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from add_ons.auth.services import AuthService
from core.services.db import DBService
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize auth service
db_service = DBService()
auth_service = AuthService(db_service)


async def get_current_user(request: Request) -> Optional[Dict]:
    """
    Get current authenticated user from request.
    
    Args:
        request: FastHTML request object
        
    Returns:
        User dict if authenticated, None otherwise
    """
    try:
        # Try to get token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user_data = auth_service.verify_token(token)
            
            if user_data:
                user = await auth_service.get_user_by_id(user_data.get("sub"))
                return user
        
        # Try to get token from cookie
        token = request.cookies.get("auth_token")
        if token:
            user_data = auth_service.verify_token(token)
            if user_data:
                user = await auth_service.get_user_by_id(user_data.get("sub"))
                return user
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None


def require_auth(func):
    """
    Decorator to require authentication for a route.
    Redirects to login if not authenticated.
    """
    async def wrapper(request: Request, *args, **kwargs):
        user = await get_current_user(request)
        if not user:
            return RedirectResponse("/auth/login")
        return await func(request, user=user, *args, **kwargs)
    return wrapper


def require_role(role: str):
    """
    Decorator to require a specific role.
    
    Args:
        role: Required role (e.g., 'instructor', 'student', 'admin')
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user = await get_current_user(request)
            if not user:
                return RedirectResponse("/auth/login")
            
            user_roles = user.get("roles", [])
            if role not in user_roles and "admin" not in user_roles:
                return Div(
                    H1("Access Denied", cls="text-2xl font-bold mb-4"),
                    P(f"You need the '{role}' role to access this page.", cls="text-gray-600"),
                    A("Go Back", href="/", cls="btn btn-primary mt-4"),
                    cls="container mx-auto px-4 py-8 text-center"
                )
            
            return await func(request, user=user, *args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: str):
    """
    Decorator to require a specific permission.
    
    Args:
        permission: Required permission (e.g., 'courses.create', 'lessons.update')
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user = await get_current_user(request)
            if not user:
                return RedirectResponse("/auth/login")
            
            if not auth_service.has_permission(user.get("_id"), permission):
                return Div(
                    H1("Access Denied", cls="text-2xl font-bold mb-4"),
                    P(f"You don't have permission to perform this action.", cls="text-gray-600"),
                    A("Go Back", href="/", cls="btn btn-primary mt-4"),
                    cls="container mx-auto px-4 py-8 text-center"
                )
            
            return await func(request, user=user, *args, **kwargs)
        return wrapper
    return decorator


def is_instructor(user: Dict) -> bool:
    """Check if user is an instructor"""
    return "instructor" in user.get("roles", []) or "admin" in user.get("roles", [])


def is_student(user: Dict) -> bool:
    """Check if user is a student"""
    return "student" in user.get("roles", []) or "admin" in user.get("roles", [])


def is_admin(user: Dict) -> bool:
    """Check if user is an admin"""
    return "admin" in user.get("roles", [])
