"""Role-based UI component rendering helpers"""

from typing import List, Optional, Union, Callable
from functools import wraps
from starlette.requests import Request
from fasthtml.common import Div, Span, NotStr
from core.services.auth.models import UserRole
from core.services.auth.role_hierarchy import RoleHierarchy


class RoleUI:
    """Helper class for role-based UI rendering"""
    
    @staticmethod
    def has_role(user_roles: List[str], required_role: str) -> bool:
        """Check if user has the required role or higher"""
        if not user_roles:
            return False
        
        # Get the highest privilege role
        highest_role = RoleHierarchy.get_primary_role(user_roles)
        if not highest_role:
            return False
        
        # Compare hierarchy levels
        user_level = RoleHierarchy.get_hierarchy_level(highest_role)
        required_level = RoleHierarchy.get_hierarchy_level(UserRole(required_role))
        
        return user_level >= required_level
    
    @staticmethod
    def has_any_role(user_roles: List[str], required_roles: List[str]) -> bool:
        """Check if user has any of the required roles"""
        if not user_roles or not required_roles:
            return False
        
        return any(role in user_roles for role in required_roles)
    
    @staticmethod
    def has_all_roles(user_roles: List[str], required_roles: List[str]) -> bool:
        """Check if user has all of the required roles"""
        if not user_roles or not required_roles:
            return False
        
        return all(role in user_roles for role in required_roles)
    
    @staticmethod
    def can_access_resource(user_roles: List[str], resource: str, action: str = "read") -> bool:
        """Check if user can access a specific resource based on role permissions"""
        # Define role permissions for common resources
        role_permissions = {
            # User management
            "users": {
                "read": ["super_admin", "admin"],
                "write": ["super_admin", "admin"],
                "delete": ["super_admin"]
            },
            # Role management
            "roles": {
                "read": ["super_admin", "admin"],
                "write": ["super_admin", "admin"],
                "delete": ["super_admin"]
            },
            # Content management
            "content": {
                "read": ["super_admin", "admin", "instructor", "editor"],
                "write": ["super_admin", "admin", "instructor", "editor"],
                "delete": ["super_admin", "admin"]
            },
            # Course management
            "courses": {
                "read": ["super_admin", "admin", "instructor", "student"],
                "write": ["super_admin", "admin", "instructor"],
                "delete": ["super_admin", "admin"]
            },
            # Blog management
            "blog": {
                "read": ["super_admin", "admin", "blog_admin", "blog_author"],
                "write": ["super_admin", "admin", "blog_admin", "blog_author"],
                "delete": ["super_admin", "admin", "blog_admin"]
            },
            # Commerce management
            "commerce": {
                "read": ["super_admin", "admin"],
                "write": ["super_admin", "admin"],
                "delete": ["super_admin"]
            },
            # Analytics
            "analytics": {
                "read": ["super_admin", "admin"],
                "write": ["super_admin"],
                "delete": ["super_admin"]
            },
            # Settings
            "settings": {
                "read": ["super_admin", "admin"],
                "write": ["super_admin", "admin"],
                "delete": ["super_admin"]
            }
        }
        
        # Get allowed roles for this resource and action
        allowed_roles = role_permissions.get(resource, {}).get(action, [])
        
        return RoleUI.has_any_role(user_roles, allowed_roles)


def role_visible(required_role: str, fallback_content: str = ""):
    """Decorator to make UI components visible only to users with required role or higher"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request: Request, *args, **kwargs):
            user = getattr(request.state, 'user', None)
            user_roles = getattr(user, 'roles', []) if user else []
            
            if RoleUI.has_role(user_roles, required_role):
                return func(request, *args, **kwargs)
            else:
                return NotStr(fallback_content)
        return wrapper
    return decorator


def role_visible_any(required_roles: List[str], fallback_content: str = ""):
    """Decorator to make UI components visible only to users with any of the required roles"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request: Request, *args, **kwargs):
            user = getattr(request.state, 'user', None)
            user_roles = getattr(user, 'roles', []) if user else []
            
            if RoleUI.has_any_role(user_roles, required_roles):
                return func(request, *args, **kwargs)
            else:
                return NotStr(fallback_content)
        return wrapper
    return decorator


def role_visible_all(required_roles: List[str], fallback_content: str = ""):
    """Decorator to make UI components visible only to users with all of the required roles"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request: Request, *args, **kwargs):
            user = getattr(request.state, 'user', None)
            user_roles = getattr(user, 'roles', []) if user else []
            
            if RoleUI.has_all_roles(user_roles, required_roles):
                return func(request, *args, **kwargs)
            else:
                return NotStr(fallback_content)
        return wrapper
    return decorator


def if_role(user_roles: List[str], required_role: str, content, fallback_content: str = ""):
    """Render content only if user has required role or higher"""
    if RoleUI.has_role(user_roles, required_role):
        return content
    return NotStr(fallback_content)


def if_any_role(user_roles: List[str], required_roles: List[str], content, fallback_content: str = ""):
    """Render content only if user has any of the required roles"""
    if RoleUI.has_any_role(user_roles, required_roles):
        return content
    return NotStr(fallback_content)


def if_all_roles(user_roles: List[str], required_roles: List[str], content, fallback_content: str = ""):
    """Render content only if user has all of the required roles"""
    if RoleUI.has_all_roles(user_roles, required_roles):
        return content
    return NotStr(fallback_content)


def if_can_access(user_roles: List[str], resource: str, content, action: str = "read", fallback_content: str = ""):
    """Render content only if user can access the resource"""
    if RoleUI.can_access_resource(user_roles, resource, action):
        return content
    return NotStr(fallback_content)


# Common UI components with role-based visibility
def AdminOnly(content, fallback_content: str = ""):
    """Render content only for admins and super admins"""
    return if_role([], UserRole.ADMIN, content, fallback_content)


def SuperAdminOnly(content, fallback_content: str = ""):
    """Render content only for super admins"""
    return if_role([], UserRole.SUPER_ADMIN, content, fallback_content)


def InstructorOnly(content, fallback_content: str = ""):
    """Render content only for instructors and above"""
    return if_role([], UserRole.INSTRUCTOR, content, fallback_content)


def EditorOnly(content, fallback_content: str = ""):
    """Render content only for editors and above"""
    return if_role([], UserRole.EDITOR, content, fallback_content)


def UserMenu(user_roles: List[str]):
    """Generate user menu items based on roles"""
    from fasthtml.common import Li, A
    
    menu_items = []
    
    # Dashboard - available to all authenticated users
    menu_items.append(Li(A("Dashboard", href="/dashboard")))
    
    # Profile - available to all authenticated users
    menu_items.append(Li(A("Profile", href="/profile")))
    
    # Admin menu
    if RoleUI.has_role(user_roles, UserRole.ADMIN):
        menu_items.append(Li(A("Admin Panel", href="/admin")))
        
        # User management
        if RoleUI.can_access_resource(user_roles, "users", "read"):
            menu_items.append(Li(A("User Management", href="/admin/users", cls="ml-4")))
        
        # Role management
        if RoleUI.can_access_resource(user_roles, "roles", "read"):
            menu_items.append(Li(A("Role Management", href="/admin/roles", cls="ml-4")))
    
    # Content management
    if RoleUI.can_access_resource(user_roles, "content", "read"):
        menu_items.append(Li(A("Content", href="/content")))
    
    # Course management
    if RoleUI.can_access_resource(user_roles, "courses", "read"):
        menu_items.append(Li(A("Courses", href="/courses")))
    
    # Blog management
    if RoleUI.can_access_resource(user_roles, "blog", "read"):
        menu_items.append(Li(A("Blog", href="/blog/admin")))
    
    # Analytics
    if RoleUI.can_access_resource(user_roles, "analytics", "read"):
        menu_items.append(Li(A("Analytics", href="/analytics")))
    
    # Settings
    if RoleUI.can_access_resource(user_roles, "settings", "read"):
        menu_items.append(Li(A("Settings", href="/settings")))
    
    return menu_items


def RoleBadge(user_roles: List[str]):
    """Generate a badge showing the user's primary role"""
    from fasthtml.common import Span
    
    if not user_roles:
        return Span("Guest", cls="badge badge-gray")
    
    primary_role = RoleHierarchy.get_primary_role(user_roles)
    
    role_colors = {
        UserRole.SUPER_ADMIN: "badge-red",
        UserRole.ADMIN: "badge-orange",
        UserRole.INSTRUCTOR: "badge-blue",
        UserRole.EDITOR: "badge-green",
        UserRole.STUDENT: "badge-purple",
        UserRole.USER: "badge-gray",
        UserRole.GUEST: "badge-light-gray",
        UserRole.BLOG_ADMIN: "badge-pink",
        UserRole.BLOG_AUTHOR: "badge-yellow",
        UserRole.LMS_ADMIN: "badge-indigo"
    }
    
    color = role_colors.get(primary_role, "badge-gray")
    role_name = primary_role.value.replace("_", " ").title()
    
    return Span(role_name, cls=f"badge {color}")
