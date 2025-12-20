"""Blog Add-on Manifest

Registers:
- Roles
- Settings
- Components
- Routes
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from core.services.auth.permissions import Permission, Role
from core.services.settings import (
    SettingDefinition,
    register_addon_settings,
)
from core.utils.logger import get_logger

logger = get_logger(__name__)


# ==========================================================================
# Blog Roles
# ==========================================================================

BLOG_ROLES = [
    Role(
        id="blog_admin",
        name="Blog Administrator",
        description="Full blog management access",
        permissions=[
            Permission("blog", "*", "*"),
            Permission("blog_post", "*", "*"),
            Permission("integration", "write", "blog"),
        ],
        inherits_from=["admin"],
        domain="blog",
    ),
    Role(
        id="blog_author",
        name="Blog Author",
        description="Create and manage blog posts",
        permissions=[
            Permission("blog", "read", "*"),
            Permission("blog_post", "*", "own"),
        ],
        inherits_from=["member"],
        domain="blog",
    ),
]


# ==========================================================================
# Blog Settings
# ==========================================================================

BLOG_SETTINGS: List[SettingDefinition] = []


# ==========================================================================
# Blog Components
# ==========================================================================

BLOG_COMPONENTS: List[Dict[str, Any]] = []


# ==========================================================================
# Blog Routes
# ==========================================================================

BLOG_ROUTES: List[Dict[str, Any]] = []


# ==========================================================================
# Theme Extensions
# ==========================================================================

BLOG_THEME_EXTENSIONS: Dict[str, Any] = {}


# ==========================================================================
# Manifest
# ==========================================================================


@dataclass
class AddonManifest:
    """Manifest for add-on registration"""

    id: str
    name: str
    version: str
    description: str
    domain: str
    roles: List[Role]
    settings: List[SettingDefinition]
    components: List[Dict[str, Any]]
    routes: List[Dict[str, Any]]
    theme_extensions: Dict[str, Any]


BLOG_MANIFEST = AddonManifest(
    id="blog",
    name="Blog",
    version="0.1.0",
    description="Basic blogging addon (posts, publishing, and authoring)",
    domain="blog",
    roles=BLOG_ROLES,
    settings=BLOG_SETTINGS,
    components=BLOG_COMPONENTS,
    routes=BLOG_ROUTES,
    theme_extensions=BLOG_THEME_EXTENSIONS,
)


# ==========================================================================
# Registration Functions
# ==========================================================================


def register_blog_roles():
    """Register blog roles with permission system"""
    from core.services.auth.permissions import permission_registry

    for role in BLOG_ROLES:
        permission_registry.register_role(role)
        logger.info(f"Registered blog role: {role.id}")


def register_blog_settings():
    """Register blog settings"""
    register_addon_settings("blog", BLOG_SETTINGS)
    logger.info(f"Registered {len(BLOG_SETTINGS)} blog settings")


def register_blog_addon():
    """Complete blog add-on registration"""
    register_blog_roles()
    register_blog_settings()
    logger.info("✓ Blog add-on registered successfully")
