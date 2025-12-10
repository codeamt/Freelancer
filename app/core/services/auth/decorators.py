# app/core/services/auth/decorators.py (new)

from functools import wraps
from fasthtml.common import RedirectResponse
from core.services.auth.permissions import permission_registry


def require_permission(resource: str, action: str):
    """
    Decorator to require specific permission.
    
    Usage:
        @app.post("/sites/{site_id}/publish")
        @require_permission("site", "write")
        async def publish_site(request, site_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            user = request.state.user if hasattr(request.state, 'user') else None
            
            if not user:
                return RedirectResponse("/auth/login")
            
            # Build context
            context = {
                "user_id": user.get("_id"),
                "user_orgs": user.get("organizations", []),
            }
            
            # Check permission
            roles = user.get("roles", [])
            if not permission_registry.check_permission(roles, resource, action, context):
                return RedirectResponse("/unauthorized")
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_resource_permission(resource_type: str, action: str, id_param: str = None):
    """
    Decorator for resource-specific permissions.
    
    Usage:
        @app.put("/sites/{site_id}")
        @require_resource_permission("site", "update", id_param="site_id")
        async def update_site(request, site_id: str):
            # Context includes site_id for ownership checking
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            user = request.state.user if hasattr(request.state, 'user') else None
            
            if not user:
                return RedirectResponse("/auth/login")
            
            # Build context with resource ID
            context = {
                "user_id": user.get("_id"),
                "user_orgs": user.get("organizations", []),
            }
            
            if id_param and id_param in kwargs:
                context["resource_id"] = kwargs[id_param]
                # Could fetch resource to check ownership
                # resource = await get_resource(resource_type, kwargs[id_param])
                # context["owner_id"] = resource.get("owner_id")
            
            roles = user.get("roles", [])
            if not permission_registry.check_permission(roles, resource_type, action, context):
                return RedirectResponse("/unauthorized")
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator