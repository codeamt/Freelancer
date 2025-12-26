"""
Role Hierarchy System

Implements role hierarchy validation, conflict resolution, and utilities
for managing multi-role assignments while maintaining backward compatibility.
"""
from typing import List, Set, Tuple, Optional, Dict
from enum import Enum
from core.services.auth.models import UserRole
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Numeric hierarchy levels - higher number = higher privilege
HIERARCHY_LEVEL: Dict[UserRole, int] = {
    UserRole.SUPER_ADMIN: 100,
    UserRole.ADMIN: 90,
    UserRole.INSTRUCTOR: 70,
    UserRole.EDITOR: 60,
    UserRole.STUDENT: 50,
    UserRole.USER: 40,
    UserRole.GUEST: 10,
    
    # Domain-specific roles
    UserRole.BLOG_ADMIN: 85,
    UserRole.BLOG_AUTHOR: 65,
    UserRole.LMS_ADMIN: 85,
    
    # Legacy roles (mapped to equivalents)
    UserRole.MEMBER: 40,  # Same as USER
    UserRole.SITE_OWNER: 90,  # Same as ADMIN
    UserRole.SITE_ADMIN: 90,  # Same as ADMIN
    UserRole.SUPPORT_STAFF: 95,  # Just below SUPER_ADMIN
}

# Conflicting role pairs that cannot coexist
CONFLICTING_PAIRS: Set[Tuple[UserRole, UserRole]] = {
    # Admin roles conflict with guest/user roles
    (UserRole.SUPER_ADMIN, UserRole.GUEST),
    (UserRole.ADMIN, UserRole.GUEST),
    (UserRole.INSTRUCTOR, UserRole.GUEST),
    (UserRole.EDITOR, UserRole.GUEST),
    
    # High privilege roles conflict with basic roles
    (UserRole.SUPER_ADMIN, UserRole.USER),
    (UserRole.ADMIN, UserRole.USER),
    (UserRole.SUPPORT_STAFF, UserRole.GUEST),
}

# Add reverse conflicts
for a, b in list(CONFLICTING_PAIRS):
    CONFLICTING_PAIRS.add((b, a))

class RoleConflictError(Exception):
    """Raised when conflicting roles are assigned"""
    pass

class RoleHierarchy:
    """Utility class for role hierarchy operations"""
    
    @staticmethod
    def get_primary_role(roles: List[UserRole]) -> Optional[UserRole]:
        """
        Get the primary (highest privilege) role from a list of roles.
        
        Args:
            roles: List of user roles
            
        Returns:
            The role with the highest hierarchy level, or None if no roles
        """
        if not roles:
            return None
        
        return max(roles, key=lambda r: HIERARCHY_LEVEL.get(r, 0))
    
    @staticmethod
    def get_hierarchy_level(role: UserRole) -> int:
        """Get the numeric hierarchy level for a role"""
        return HIERARCHY_LEVEL.get(role, 0)
    
    @staticmethod
    def is_higher_or_equal(role_a: UserRole, role_b: UserRole) -> bool:
        """
        Check if role_a has higher or equal privilege than role_b.
        
        Args:
            role_a: First role
            role_b: Second role
            
        Returns:
            True if role_a >= role_b in hierarchy
        """
        return HIERARCHY_LEVEL.get(role_a, 0) >= HIERARCHY_LEVEL.get(role_b, 0)
    
    @staticmethod
    def check_conflicts(roles: List[UserRole]) -> List[Tuple[UserRole, UserRole]]:
        """
        Check for conflicting role pairs in a list of roles.
        
        Args:
            roles: List of roles to check
            
        Returns:
            List of conflicting pairs found
        """
        conflicts = []
        role_set = set(roles)
        
        for role_a, role_b in CONFLICTING_PAIRS:
            if role_a in role_set and role_b in role_set:
                conflicts.append((role_a, role_b))
        
        return conflicts
    
    @staticmethod
    def validate_role_assignment(
        current_roles: List[UserRole],
        new_roles: List[UserRole]
    ) -> Tuple[bool, List[str]]:
        """
        Validate a role assignment, checking for conflicts.
        
        Args:
            current_roles: User's current roles
            new_roles: Roles to assign
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        # Combine current and new roles
        all_roles = list(set(current_roles + new_roles))
        
        # Check for conflicts
        conflicts = RoleHierarchy.check_conflicts(all_roles)
        
        if conflicts:
            error_messages = [
                f"Conflicting roles: {conflict[0].value} and {conflict[1].value}"
                for conflict in conflicts
            ]
            return False, error_messages
        
        return True, []
    
    @staticmethod
    def get_effective_permissions(roles: List[UserRole]) -> Set[str]:
        """
        Get the effective permissions from multiple roles.
        This would integrate with the permission registry.
        
        Args:
            roles: List of user roles
            
        Returns:
            Set of effective permission strings
        """
        from core.services.auth.permissions import permission_registry
        
        permissions = set()
        role_ids = [role.value for role in roles]
        
        # Get permissions from registry
        role_permissions = permission_registry.resolve_permissions(role_ids)
        
        for perm in role_permissions:
            # Convert permission to string representation
            perm_str = f"{perm.resource}:{perm.action}:{perm.scope}"
            permissions.add(perm_str)
        
        return permissions
    
    @staticmethod
    def filter_roles_by_level(
        roles: List[UserRole],
        min_level: Optional[int] = None,
        max_level: Optional[int] = None
    ) -> List[UserRole]:
        """
        Filter roles by hierarchy level.
        
        Args:
            roles: List of roles to filter
            min_level: Minimum hierarchy level (inclusive)
            max_level: Maximum hierarchy level (inclusive)
            
        Returns:
            Filtered list of roles
        """
        filtered = []
        
        for role in roles:
            level = HIERARCHY_LEVEL.get(role, 0)
            
            if min_level is not None and level < min_level:
                continue
            if max_level is not None and level > max_level:
                continue
                
            filtered.append(role)
        
        return filtered
    
    @staticmethod
    def get_role_summary(roles: List[UserRole]) -> Dict:
        """
        Get a summary of role information for UI display.
        
        Args:
            roles: List of user roles
            
        Returns:
            Dictionary with role summary information
        """
        if not roles:
            return {
                "primary_role": None,
                "role_count": 0,
                "highest_level": 0,
                "is_admin": False,
                "is_moderator": False,
                "roles": []
            }
        
        primary = RoleHierarchy.get_primary_role(roles)
        highest_level = HIERARCHY_LEVEL.get(primary, 0) if primary else 0
        
        # Check for admin-level roles
        admin_roles = RoleHierarchy.filter_roles_by_level(
            roles, min_level=HIERARCHY_LEVEL[UserRole.ADMIN]
        )
        
        # Check for moderator-level roles (instructor, editor, etc.)
        moderator_roles = RoleHierarchy.filter_roles_by_level(
            roles, min_level=HIERARCHY_LEVEL[UserRole.INSTRUCTOR]
        )
        
        return {
            "primary_role": primary.value if primary else None,
            "role_count": len(roles),
            "highest_level": highest_level,
            "is_admin": len(admin_roles) > 0,
            "is_moderator": len(moderator_roles) > 0,
            "roles": [role.value for role in sorted(roles, key=lambda r: HIERARCHY_LEVEL.get(r, 0), reverse=True)]
        }


def validate_role_hierarchy(roles: List[UserRole]) -> bool:
    """
    Validate that a list of roles follows hierarchy rules.
    
    Args:
        roles: List of roles to validate
        
    Returns:
        True if valid, raises RoleConflictError if invalid
    """
    conflicts = RoleHierarchy.check_conflicts(roles)
    
    if conflicts:
        conflict_str = ", ".join([f"{a.value}+{b.value}" for a, b in conflicts])
        raise RoleConflictError(f"Conflicting roles: {conflict_str}")
    
    return True


def resolve_role_conflicts(roles: List[UserRole]) -> List[UserRole]:
    """
    Automatically resolve role conflicts by keeping higher privilege roles.
    
    Args:
        roles: List of roles with potential conflicts
        
    Returns:
        Resolved list of roles
    """
    # Sort by hierarchy level (highest first)
    sorted_roles = sorted(
        roles,
        key=lambda r: HIERARCHY_LEVEL.get(r, 0),
        reverse=True
    )
    
    resolved = []
    seen_levels = set()
    
    for role in sorted_roles:
        level = HIERARCHY_LEVEL.get(role, 0)
        
        # Skip if we already have a role at this level or higher
        if any(level <= existing_level for existing_level in seen_levels):
            continue
        
        resolved.append(role)
        seen_levels.add(level)
    
    return resolved
