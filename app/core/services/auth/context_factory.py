"""
Context Factory - Build UserContext from User entity.

Helper functions to create UserContext with resolved permissions.
"""

from typing import Optional
from starlette.requests import Request

from core.services.auth.context import UserContext
from core.services.auth.permissions import permission_registry
from core.utils.logger import get_logger

logger = get_logger(__name__)


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
    # Resolve permissions from role(s)
    permissions = permission_registry.resolve_permissions([user.role])
    
    # Get client IP
    ip_address = request.client.host if request.client else "unknown"
    
    # Create context
    context = UserContext(
        user_id=user.id,
        role=user.role,
        permissions=permissions,
        request_cookies=dict(request.cookies),
        ip_address=ip_address,
        resource_owner_id=resource_owner_id,
        resource_type=resource_type
    )
    
    logger.debug(
        f"Created UserContext for user {user.id} ({user.role}) "
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
        permissions=[],
        request_cookies=dict(request.cookies),
        ip_address=ip_address
    )
