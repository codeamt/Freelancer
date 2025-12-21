"""Admin decorators for route protection"""
from functools import wraps
from fasthtml.common import RedirectResponse
from core.utils.logger import get_logger
from core.services.auth.models import UserRole

logger = get_logger(__name__)

# Role hierarchy mapping for permission checking
ROLE_HIERARCHY = {
    UserRole.SUPER_ADMIN: 100,
    UserRole.ADMIN: 80,
    UserRole.LMS_ADMIN: 75,
    UserRole.BLOG_ADMIN: 70,
    UserRole.INSTRUCTOR: 60,
    UserRole.EDITOR: 50,
    UserRole.BLOG_AUTHOR: 45,
    UserRole.STUDENT: 40,
    UserRole.USER: 20,
    UserRole.GUEST: 10,
    # Legacy roles
    UserRole.SITE_OWNER: 80,
    UserRole.SITE_ADMIN: 80,
    UserRole.SUPPORT_STAFF: 100,
    UserRole.MEMBER: 20,
}


def require_admin(func):
    """
    Decorator to require admin-level role for a route.
    
    Allows access to users with admin-level roles or higher:
    - SUPER_ADMIN (100)
    - ADMIN (80) 
    - LMS_ADMIN (75)
    - BLOG_ADMIN (70)
    - Legacy: SITE_OWNER, SITE_ADMIN, SUPPORT_STAFF
    
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
        
        # Get user roles (support both single role and roles array)
        user_role = user.get("role")
        user_roles = user.get("roles", [])
        
        # Normalize to roles array for new system
        if user_role and not user_roles:
            user_roles = [user_role]
        
        # Check if user has admin-level role using hierarchy
        has_admin_access = False
        for role_str in user_roles:
            try:
                role_enum = UserRole(role_str)
                user_level = ROLE_HIERARCHY.get(role_enum, 0)
                if user_level >= ROLE_HIERARCHY[UserRole.ADMIN]:  # 80 or higher
                    has_admin_access = True
                    break
            except ValueError:
                # Skip invalid roles
                continue
        
        if not has_admin_access:
            logger.warning(f"Non-admin user {user.get('_id')} with roles {user_roles} attempted to access admin route")
            return RedirectResponse("/")
        
        return await func(request, *args, **kwargs)
    
    return wrapper


def require_role(*required_roles):
    """
    Decorator to require specific role(s) for a route using hierarchy.
    
    Usage:
        @app.get("/instructor/dashboard")
        @require_role("instructor", "admin")
        async def instructor_dashboard(request: Request):
            ...
    
    Allows access if user has any of the required roles OR a higher role in hierarchy.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            # Get user from request
            user = request.state.user if hasattr(request.state, 'user') else None
            
            if not user:
                logger.warning("Unauthorized access attempt to protected route")
                return RedirectResponse("/auth/login?redirect=" + str(request.url.path))
            
            # Get user roles (support both single role and roles array)
            user_role = user.get("role")
            user_roles = user.get("roles", [])
            
            # Normalize to roles array for new system
            if user_role and not user_roles:
                user_roles = [user_role]
            
            # Check if user has any of the required roles or higher
            has_access = False
            required_min_level = 0
            
            # Find the minimum required level from all required roles
            for req_role_str in required_roles:
                try:
                    req_role_enum = UserRole(req_role_str)
                    req_level = ROLE_HIERARCHY.get(req_role_enum, 0)
                    required_min_level = max(required_min_level, req_level)
                except ValueError:
                    continue
            
            # Check if user has role at or above required level
            for role_str in user_roles:
                try:
                    role_enum = UserRole(role_str)
                    user_level = ROLE_HIERARCHY.get(role_enum, 0)
                    if user_level >= required_min_level:
                        has_access = True
                        break
                except ValueError:
                    continue
            
            if not has_access:
                logger.warning(f"User {user.get('_id')} with roles {user_roles} attempted to access route requiring {required_roles}")
                return RedirectResponse("/")
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_super_admin(func):
    """
    Decorator to require super admin role for a route.
    
    Only allows access to SUPER_ADMIN and legacy SUPPORT_STAFF roles.
    
    Usage:
        @app.get("/admin/platform")
        @require_super_admin
        async def platform_settings(request: Request):
            ...
    """
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        # Get user from request
        user = request.state.user if hasattr(request.state, 'user') else None
        
        if not user:
            logger.warning("Unauthorized access attempt to super admin route")
            return RedirectResponse("/auth/login?redirect=" + str(request.url.path))
        
        # Get user roles (support both single role and roles array)
        user_role = user.get("role")
        user_roles = user.get("roles", [])
        
        # Normalize to roles array for new system
        if user_role and not user_roles:
            user_roles = [user_role]
        
        # Check if user has super admin level role
        has_super_admin = False
        for role_str in user_roles:
            try:
                role_enum = UserRole(role_str)
                user_level = ROLE_HIERARCHY.get(role_enum, 0)
                if user_level >= ROLE_HIERARCHY[UserRole.SUPER_ADMIN]:  # 100
                    has_super_admin = True
                    break
            except ValueError:
                continue
        
        if not has_super_admin:
            logger.warning(f"Non-super-admin user {user.get('_id')} with roles {user_roles} attempted to access super admin route")
            return RedirectResponse("/")
        
        return await func(request, *args, **kwargs)
    
    return wrapper
