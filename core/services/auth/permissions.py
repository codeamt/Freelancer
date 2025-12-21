# app/core/services/auth/permissions.py

from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from enum import Enum

from .context import UserContext


class PermissionLevel(Enum):
    """Permission levels from least to most privileged"""
    NONE = 0
    READ = 1
    WRITE = 2
    UPDATE = 3
    DELETE = 4
    ADMIN = 5


class ResourceType(Enum):
    """Core resource types"""
    SITE = "site"
    PAGE = "page"
    COMPONENT = "component"
    THEME = "theme"
    USER = "user"
    ROLE = "role"
    # Add-ons register their own resource types


@dataclass
class Permission:
    """Single permission definition"""
    resource: str  # e.g., "site", "course", "product"
    action: str    # e.g., "read", "write", "delete"
    scope: str = "*"  # e.g., "*" (all), "own" (user's own), "org:123"
    
    def matches(self, resource: str, action: str, context: Dict) -> bool:
        """Check if this permission allows the action"""
        if self.resource != resource and self.resource != "*":
            return False
        
        if self.action != action and self.action != "*":
            return False
        
        # Check scope
        if self.scope == "*":
            return True
        
        if self.scope == "own":
            return context.get("owner_id") == context.get("user_id")
        
        if self.scope.startswith("org:"):
            org_id = self.scope.split(":")[1]
            return org_id in context.get("user_orgs", [])
        
        return False


@dataclass
class Role:
    """Role definition with permissions"""
    id: str
    name: str
    description: str
    permissions: List[Permission]
    inherits_from: List[str] = None  # Role inheritance
    domain: str = "core"  # "core", "lms", "commerce", etc.
    
    def has_permission(self, resource: str, action: str, context: Dict) -> bool:
        """Check if role has permission for action"""
        return any(p.matches(resource, action, context) for p in self.permissions)


class PermissionRegistry:
    """Central registry for roles and permissions"""
    
    def __init__(self):
        self._roles: Dict[str, Role] = {}
        self._resource_types: Set[str] = set()
        self._initialize_core_roles()
    
    def _initialize_core_roles(self):
        """Initialize core platform roles with canonical vocabulary"""
        
        # Platform ops roles (installation/provider-facing)
        self.register_role(Role(
            id="super_admin",
            name="Super Admin",
            description="Full platform access - break-glass, install-wide",
            permissions=[
                Permission("*", "*", "*")  # Wildcard: all resources, all actions
            ],
            domain="core"
        ))
        
        self.register_role(Role(
            id="support_staff",
            name="Support Staff",
            description="Platform troubleshooting and read-only access",
            permissions=[
                Permission("site", "read", "*"),
                Permission("user", "read", "*"),
                Permission("admin", "access", "*"),
                Permission("support", "impersonate", "*"),  # Optional, dangerous
            ],
            domain="core"
        ))
        
        # Site staff roles (site/operator-facing)
        self.register_role(Role(
            id="site_owner",
            name="Site Owner",
            description="Highest privilege for a site - full site control",
            permissions=[
                Permission("site", "*", "*"),
                Permission("user", "*", "*"),
                Permission("content", "*", "*"),
                Permission("theme", "*", "*"),
                Permission("addons", "manage", "*"),
                Permission("billing", "*", "*"),
            ],
            domain="core"
        ))
        
        self.register_role(Role(
            id="site_admin",
            name="Site Administrator",
            description="Site management - content + settings, not billing/ownership",
            permissions=[
                Permission("site", "manage", "*"),
                Permission("content", "*", "*"),
                Permission("user", "manage", "*"),
                Permission("theme", "update", "*"),
                Permission("settings", "update", "*"),
            ],
            domain="core"
        ))
        
        self.register_role(Role(
            id="editor",
            name="Editor",
            description="Content editing and management",
            permissions=[
                Permission("page", "*", "*"),
                Permission("component", "*", "*"),
                Permission("theme", "read", "*"),
                Permission("media", "upload", "*"),
            ],
            domain="core"
        ))
        
        # Primary site roles (end-user / customer-facing)
        self.register_role(Role(
            id="member",
            name="Member",
            description="Paid/entitled user with enhanced access",
            permissions=[
                Permission("site", "read", "*"),
                Permission("page", "read", "*"),
                Permission("user", "read", "own"),
                Permission("user", "update", "own"),
                Permission("profile", "view", "own"),
                Permission("profile", "update", "own"),
                Permission("premium", "access", "*"),
            ],
            domain="core"
        ))
        
        self.register_role(Role(
            id="user",
            name="User",
            description="Basic authenticated user",
            permissions=[
                Permission("profile", "view", "own"),
                Permission("profile", "update", "own"),
                Permission("user", "read", "own"),
                Permission("user", "update", "own"),
                Permission("setting", "read", "own"),
            ],
            domain="core"
        ))
        
        # Legacy role aliases for backward compatibility
        self.register_role(Role(
            id="admin",
            name="Administrator (Legacy)",
            description="Legacy admin role - maps to site_admin",
            permissions=[
                Permission("site", "manage", "*"),
                Permission("content", "*", "*"),
                Permission("user", "manage", "*"),
            ],
            domain="core"
        ))
        
        # LMS-specific roles (domain-specific)
        self.register_role(Role(
            id="instructor",
            name="Instructor",
            description="Course and lesson management",
            permissions=[
                Permission("courses", "create", "*"),
                Permission("courses", "update", "*"),
                Permission("courses", "delete", "*"),
                Permission("lessons", "create", "*"),
                Permission("lessons", "update", "*"),
                Permission("lessons", "delete", "*"),
            ],
            domain="lms"
        ))
        
        self.register_role(Role(
            id="student",
            name="Student",
            description="Course enrollment and learning",
            permissions=[
                Permission("courses", "view", "*"),
                Permission("courses", "enroll", "*"),
                Permission("lessons", "view", "*"),
                Permission("assessments", "take", "*"),
            ],
            domain="lms"
        ))
        
        # Commerce-specific roles (domain-specific)
        self.register_role(Role(
            id="shop_owner",
            name="Shop Owner",
            description="E-commerce store management",
            permissions=[
                Permission("shop", "*", "*"),
                Permission("product", "*", "*"),
                Permission("order", "*", "*"),
                Permission("inventory", "*", "*"),
            ],
            domain="commerce"
        ))
        
        self.register_role(Role(
            id="merchant",
            name="Merchant",
            description="Commerce operations",
            permissions=[
                Permission("product", "manage", "*"),
                Permission("order", "process", "*"),
                Permission("inventory", "update", "*"),
            ],
            domain="commerce"
        ))
        
        self.register_role(Role(
            id="course_creator",
            name="Course Creator",
            description="Educational content creation",
            permissions=[
                Permission("courses", "create", "*"),
                Permission("lessons", "create", "*"),
                Permission("content", "manage", "own"),
            ],
            domain="lms"
        ))
    
    def register_role(self, role: Role):
        """Register a role (used by add-ons)"""
        self._roles[role.id] = role
        
        # Extract resource types
        for perm in role.permissions:
            if perm.resource != "*":
                self._resource_types.add(perm.resource)
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """Get role by ID"""
        return self._roles.get(role_id)
    
    def get_roles_by_domain(self, domain: str) -> List[Role]:
        """Get all roles for a domain"""
        return [r for r in self._roles.values() if r.domain == domain]
    
    def resolve_permissions(self, role_ids: List[str]) -> List[Permission]:
        """Resolve all permissions from role IDs (handles inheritance)"""
        permissions = []
        seen_roles = set()
        
        def collect_permissions(role_id: str):
            if role_id in seen_roles:
                return
            
            seen_roles.add(role_id)
            role = self.get_role(role_id)
            
            if not role:
                return
            
            # Collect inherited permissions first
            if role.inherits_from:
                for parent_id in role.inherits_from:
                    collect_permissions(parent_id)
            
            # Add this role's permissions
            permissions.extend(role.permissions)
        
        for role_id in role_ids:
            collect_permissions(role_id)
        
        return permissions
    
    def check_permission(
        self,
        role_ids: List[str],
        resource: str,
        action: str,
        context: Dict
    ) -> bool:
        """Check if user has permission"""
        permissions = self.resolve_permissions(role_ids)
        return any(p.matches(resource, action, context) for p in permissions)


# Global registry
permission_registry = PermissionRegistry()