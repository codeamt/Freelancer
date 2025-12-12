"""User Context - Request-scoped user identity and permissions."""

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import List, Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from core.services.auth.permissions import Permission


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
    _outgoing_cookies: dict = field(default_factory=dict)
    
    # Resource ownership context (merged from PermissionContext)
    resource_owner_id: Optional[int] = None
    resource_type: Optional[str] = None
      
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
current_user_context: ContextVar[UserContext] = ContextVar('current_user_context')