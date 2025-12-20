"""
User Context - Request-scoped user identity and permissions.

Consolidated module containing:
- UserContext dataclass
- Context variable management
- Context factory functions
"""

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import List, Optional, Dict, TYPE_CHECKING
from starlette.requests import Request

if TYPE_CHECKING:
    from core.services.auth.permissions import Permission


_ROLE_PRIORITY: dict[str, int] = {
    "super_admin": 1000,
    "site_owner": 900,
    "admin": 800,
    "support_staff": 700,
    "web_admin": 650,
    "editor": 600,
    "stream_admin": 550,
    "shop_owner": 520,
    "merchant": 510,
    "course_creator": 505,
    "instructor": 500,
    "streamer": 450,
    "member": 100,
    "user": 90,
    "student": 80,
    "anonymous": 0,
}


def _select_primary_role(roles: List[str]) -> str:
    if not roles:
        return "anonymous"
    return max(roles, key=lambda r: (_ROLE_PRIORITY.get(r, 1), r))


@dataclass
class UserContext:
    """
    Request-scoped user context with permissions and cookies.
    
    Consolidates user identity, permissions, and request/response state.
    Replaces both old UserContext and PermissionContext.
    """
    user_id: int
    role: str
    permissions: List['Permission']  # Dataclass-based from permissions.py
    request_cookies: dict
    ip_address: str
    roles: List[str] = field(default_factory=list)
    _outgoing_cookies: dict = field(default_factory=dict)
    
    # Resource ownership context (merged from PermissionContext)
    resource_owner_id: Optional[int] = None
    resource_type: Optional[str] = None

    def __post_init__(self):
        if not self.roles and self.role:
            self.roles = [self.role]
        if self.roles:
            self.role = _select_primary_role(self.roles)
      
    def has_permission(self, resource: str, action: str, scope_context: Optional[Dict] = None) -> bool:
        """
        Check if user has permission for resource/action.
        
        Args:
            resource: Resource name (e.g., "course", "product")
            action: Action name (e.g., "read", "write", "delete")
            scope_context: Optional context for scope checking (e.g., owner_id)
            
        Returns:
            True if user has permission
        """
        ctx = scope_context or {}
        ctx["user_id"] = self.user_id
        
        # Add resource owner to context if set
        if self.resource_owner_id is not None:
            ctx["owner_id"] = self.resource_owner_id
        
        # Check if any permission matches
        return any(p.matches(resource, action, ctx) for p in self.permissions)
    
    def is_owner(self) -> bool:
        """Check if user is the resource owner."""
        return self.resource_owner_id is not None and self.user_id == self.resource_owner_id
    
    def can_access(self, resource: str, action: str) -> bool:
        """
        Check if user can access based on permission or ownership.
        
        Args:
            resource: Resource name
            action: Action name
            
        Returns:
            True if user has permission or is owner
        """
        return self.has_permission(resource, action) or self.is_owner()
      
    def set_cookie(self, key: str, value: str, **kwargs):
        """Queue a cookie to be set on the response."""
        self._outgoing_cookies[key] = (value, kwargs)
      
    def get_cookie(self, key: str, default=None):
        """Get cookie value (checks outgoing first, then incoming)."""
        if key in self._outgoing_cookies:
            return self._outgoing_cookies[key][0]
        return self.request_cookies.get(key, default)


# Global context variable
current_user_context: ContextVar[Optional[UserContext]] = ContextVar('current_user_context', default=None)


def set_user_context(context: UserContext) -> None:
    """Set the current user context for this request."""
    current_user_context.set(context)


def get_user_context() -> Optional[UserContext]:
    """Get the current user context for this request."""
    return current_user_context.get()


def clear_user_context() -> None:
    """Clear the current user context."""
    current_user_context.set(None)


# ============================================================================
# Context Factory Functions (merged from context_factory.py)
# ============================================================================

def create_user_context(
    user,  # User entity from repository
    request: Request,
    resource_owner_id: Optional[int] = None,
    resource_type: Optional[str] = None
) -> UserContext:
    """
    Create UserContext from User entity with resolved permissions.
    
    Args:
        user: User entity (has id, email, role)
        request: Starlette request
        resource_owner_id: Optional resource owner for permission checks
        resource_type: Optional resource type
        
    Returns:
        UserContext with resolved permissions
    """
    # Import here to avoid circular imports
    from core.services.auth.permissions import permission_registry
    from core.utils.logger import get_logger
    
    logger = get_logger(__name__)
    
    roles = getattr(user, "roles", None) or [getattr(user, "role", "user")]
    roles = [r for r in roles if r]
    primary_role = _select_primary_role(roles)

    # Resolve permissions from role(s)
    permissions = permission_registry.resolve_permissions(roles)
    
    # Get client IP
    ip_address = request.client.host if request.client else "unknown"
    
    # Create context
    context = UserContext(
        user_id=user.id,
        role=primary_role,
        roles=roles,
        permissions=permissions,
        request_cookies=dict(request.cookies),
        ip_address=ip_address,
        resource_owner_id=resource_owner_id,
        resource_type=resource_type
    )
    
    logger.debug(
        f"Created UserContext for user {user.id} ({context.role}) "
        f"with {len(permissions)} permissions"
    )
    
    return context


def create_anonymous_context(request: Request) -> UserContext:
    """
    Create UserContext for anonymous (unauthenticated) user.
    
    Args:
        request: Starlette request
        
    Returns:
        UserContext with no permissions
    """
    ip_address = request.client.host if request.client else "unknown"
    
    return UserContext(
        user_id=0,
        role="anonymous",
        roles=["anonymous"],
        permissions=[],
        request_cookies=dict(request.cookies),
        ip_address=ip_address
    )