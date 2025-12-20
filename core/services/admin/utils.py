"""Admin utility functions"""
from typing import Dict, Optional


def is_admin(user: Optional[Dict]) -> bool:
    """
    Check if user has admin role.
    
    Args:
        user: User data dict
        
    Returns:
        True if user is admin, False otherwise
    """
    if not user:
        return False
    return "admin" in user.get("roles", [])


def has_role(user: Optional[Dict], role: str) -> bool:
    """
    Check if user has a specific role.
    
    Args:
        user: User data dict
        role: Role name to check
        
    Returns:
        True if user has role, False otherwise
    """
    if not user:
        return False
    return role in user.get("roles", [])


def has_any_role(user: Optional[Dict], *roles) -> bool:
    """
    Check if user has any of the specified roles.
    
    Args:
        user: User data dict
        *roles: Role names to check
        
    Returns:
        True if user has any of the roles, False otherwise
    """
    if not user:
        return False
    user_roles = user.get("roles", [])
    return any(role in user_roles for role in roles)
