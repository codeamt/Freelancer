"""
Social Networking Add-on Manifest

Registers:
- Roles (moderator, content_creator, social_member)
- Settings (post limits, moderation, notifications, etc.)
- Components (feed, posts, comments, likes, etc.)
- Routes
"""

from dataclasses import dataclass
from typing import List, Dict, Any

from core.services.auth.permissions import Role, Permission
from core.services.settings import (
    SettingDefinition,
    SettingType,
    SettingSensitivity,
    SettingScope,
    register_addon_settings
)
from core.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Social Roles
# ============================================================================

SOCIAL_ROLES = [
    Role(
        id="social_admin",
        name="Social Administrator",
        description="Full social platform management access",
        permissions=[
            Permission("social", "*", "*"),           # All social operations
            Permission("post", "*", "*"),             # All posts
            Permission("comment", "*", "*"),          # All comments
            Permission("user_profile", "*", "*"),     # All profiles
            Permission("moderation", "*", "*"),       # Moderation actions
            Permission("report", "*", "*"),           # Handle reports
            Permission("integration", "write", "social"),  # Configure integrations
        ],
        inherits_from=["admin"],
        domain="social"
    ),
    
    Role(
        id="moderator",
        name="Moderator",
        description="Moderate content and handle reports",
        permissions=[
            Permission("social", "read", "*"),        # Read social settings
            Permission("post", "read", "*"),          # View all posts
            Permission("post", "delete", "*"),        # Delete any post
            Permission("comment", "*", "*"),          # Manage all comments
            Permission("moderation", "*", "*"),       # Moderation actions
            Permission("report", "*", "*"),           # Handle reports
            Permission("user_profile", "read", "*"),  # View profiles
        ],
        inherits_from=["member"],
        domain="social"
    ),
    
    Role(
        id="content_creator",
        name="Content Creator",
        description="Create and manage content with enhanced features",
        permissions=[
            Permission("post", "*", "own"),           # Manage own posts
            Permission("post", "read", "*"),          # View all posts
            Permission("comment", "*", "own"),        # Manage own comments
            Permission("comment", "create", "*"),     # Comment on any post
            Permission("like", "*", "*"),             # Like/unlike
            Permission("follow", "*", "*"),           # Follow/unfollow
            Permission("analytics", "read", "own"),   # View own analytics
        ],
        inherits_from=["member"],
        domain="social"
    ),
    
    Role(
        id="social_member",
        name="Social Member",
        description="Basic social platform access",
        permissions=[
            Permission("post", "*", "own"),           # Manage own posts
            Permission("post", "read", "*"),          # View all posts
            Permission("comment", "*", "own"),        # Manage own comments
            Permission("comment", "create", "*"),     # Comment on posts
            Permission("like", "*", "*"),             # Like/unlike
            Permission("follow", "*", "*"),           # Follow/unfollow
            Permission("report", "create", "*"),      # Report content
        ],
        inherits_from=["member"],
        domain="social"
    )
]


# ============================================================================
# Social Settings
# ============================================================================

SOCIAL_SETTINGS = [
    # Content Settings
    SettingDefinition(
        key="posts.max_length",
        name="Max Post Length",
        description="Maximum character length for posts",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=5000,
        category="social",
        validation=lambda v: 100 <= int(v) <= 50000,
        read_permission=("social", "read"),
        write_permission=("social", "admin"),
        help_text="100-50000 characters"
    ),
    
    SettingDefinition(
        key="posts.allow_images",
        name="Allow Images in Posts",
        description="Enable image uploads in posts",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="social",
        read_permission=("social", "read"),
        write_permission=("social", "admin")
    ),
    
    SettingDefinition(
        key="posts.allow_videos",
        name="Allow Videos in Posts",
        description="Enable video uploads in posts",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="social",
        read_permission=("social", "read"),
        write_permission=("social", "admin")
    ),
    
    SettingDefinition(
        key="posts.max_images",
        name="Max Images Per Post",
        description="Maximum number of images per post",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=10,
        category="social",
        validation=lambda v: 1 <= int(v) <= 50,
        read_permission=("social", "read"),
        write_permission=("social", "admin"),
        help_text="1-50 images"
    ),
    
    # Moderation Settings
    SettingDefinition(
        key="moderation.auto_moderate",
        name="Auto-Moderation Enabled",
        description="Enable automatic content moderation",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="social",
        read_permission=("social", "read"),
        write_permission=("social", "admin")
    ),
    
    SettingDefinition(
        key="moderation.profanity_filter",
        name="Profanity Filter",
        description="Filter profanity in posts and comments",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="social",
        read_permission=("social", "read"),
        write_permission=("social", "admin")
    ),
    
    SettingDefinition(
        key="moderation.require_approval",
        name="Require Post Approval",
        description="Require moderator approval for new posts",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=False,
        category="social",
        read_permission=("social", "read"),
        write_permission=("social", "admin")
    ),
    
    # Rate Limiting
    SettingDefinition(
        key="rate_limit.posts_per_hour",
        name="Posts Per Hour Limit",
        description="Maximum posts per user per hour",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=10,
        category="social",
        validation=lambda v: 1 <= int(v) <= 100,
        read_permission=("social", "read"),
        write_permission=("social", "admin"),
        help_text="1-100 posts"
    ),
    
    SettingDefinition(
        key="rate_limit.comments_per_hour",
        name="Comments Per Hour Limit",
        description="Maximum comments per user per hour",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=50,
        category="social",
        validation=lambda v: 1 <= int(v) <= 500,
        read_permission=("social", "read"),
        write_permission=("social", "admin"),
        help_text="1-500 comments"
    ),
    
    # Privacy Settings
    SettingDefinition(
        key="privacy.default_post_visibility",
        name="Default Post Visibility",
        description="Default visibility for new posts",
        type=SettingType.STRING,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default="public",
        category="social",
        ui_component="select",
        options=["public", "followers", "private"],
        read_permission=("social", "read"),
        write_permission=("social", "admin")
    ),
    
    SettingDefinition(
        key="privacy.allow_private_profiles",
        name="Allow Private Profiles",
        description="Allow users to make profiles private",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="social",
        read_permission=("social", "read"),
        write_permission=("social", "admin")
    ),
    
    # Notification Settings
    SettingDefinition(
        key="notifications.new_follower",
        name="Notify on New Follower",
        description="Send notification when someone follows user",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="social",
        read_permission=("social", "read"),
        write_permission=("social", "admin")
    ),
    
    SettingDefinition(
        key="notifications.post_liked",
        name="Notify on Post Like",
        description="Send notification when post is liked",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="social",
        read_permission=("social", "read"),
        write_permission=("social", "admin")
    ),
    
    SettingDefinition(
        key="notifications.new_comment",
        name="Notify on New Comment",
        description="Send notification when post receives comment",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="social",
        read_permission=("social", "read"),
        write_permission=("social", "admin")
    )
]


# ============================================================================
# Social Components
# ============================================================================

SOCIAL_COMPONENTS = [
    {
        "id": "activity_feed",
        "name": "Activity Feed",
        "type": "content",
        "description": "Display user activity feed",
        "factory": "social.components.create_activity_feed",
        "category": "social"
    },
    {
        "id": "post_composer",
        "name": "Post Composer",
        "type": "form",
        "description": "Create new posts",
        "factory": "social.components.create_post_composer",
        "category": "social"
    },
    {
        "id": "post_card",
        "name": "Post Card",
        "type": "content",
        "description": "Display individual post with interactions",
        "factory": "social.components.create_post_card",
        "category": "social"
    },
    {
        "id": "comment_thread",
        "name": "Comment Thread",
        "type": "content",
        "description": "Threaded comments display",
        "factory": "social.components.create_comment_thread",
        "category": "social"
    },
    {
        "id": "user_profile_card",
        "name": "User Profile Card",
        "type": "content",
        "description": "User profile summary card",
        "factory": "social.components.create_profile_card",
        "category": "social"
    },
    {
        "id": "follow_button",
        "name": "Follow Button",
        "type": "widget",
        "description": "Follow/unfollow button",
        "factory": "social.components.create_follow_button",
        "category": "social"
    }
]


# ============================================================================
# Social Routes
# ============================================================================

SOCIAL_ROUTES = [
    {
        "path": "/feed",
        "handler": "social.routes.view_feed",
        "methods": ["GET"],
        "permission": ("post", "read")
    },
    {
        "path": "/posts",
        "handler": "social.routes.create_post",
        "methods": ["POST"],
        "permission": ("post", "create")
    },
    {
        "path": "/posts/{post_id}",
        "handler": "social.routes.get_post",
        "methods": ["GET"],
        "permission": ("post", "read")
    },
    {
        "path": "/posts/{post_id}/like",
        "handler": "social.routes.like_post",
        "methods": ["POST"],
        "permission": ("like", "create")
    },
    {
        "path": "/posts/{post_id}/comments",
        "handler": "social.routes.post_comments",
        "methods": ["GET", "POST"],
        "permission": ("comment", "read")
    },
    {
        "path": "/profile/{user_id}",
        "handler": "social.routes.view_profile",
        "methods": ["GET"],
        "permission": ("user_profile", "read")
    },
    {
        "path": "/follow/{user_id}",
        "handler": "social.routes.follow_user",
        "methods": ["POST"],
        "permission": ("follow", "create")
    }
]


# ============================================================================
# Theme Extensions
# ============================================================================

SOCIAL_THEME_EXTENSIONS = {
    "colors": {
        "social_primary": "#3b82f6",
        "social_secondary": "#8b5cf6",
        "like_color": "#ef4444",
        "comment_color": "#10b981"
    },
    "components": {
        "post_card": {
            "border_radius": "0.5rem",
            "shadow": "sm",
            "hover_shadow": "md"
        },
        "follow_button": {
            "bg_color": "social_primary",
            "hover_bg": "social_secondary"
        }
    }
}


# ============================================================================
# Manifest
# ============================================================================

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


SOCIAL_MANIFEST = AddonManifest(
    id="social",
    name="Social Networking",
    version="1.0.0",
    description="Complete social platform with posts, comments, likes, and follows",
    domain="social",
    roles=SOCIAL_ROLES,
    settings=SOCIAL_SETTINGS,
    components=SOCIAL_COMPONENTS,
    routes=SOCIAL_ROUTES,
    theme_extensions=SOCIAL_THEME_EXTENSIONS
)


# ============================================================================
# Registration Functions
# ============================================================================

def register_social_roles():
    """Register social roles with permission system"""
    from core.services.auth.permissions import permission_registry
    
    for role in SOCIAL_ROLES:
        permission_registry.register_role(role)
        logger.info(f"Registered social role: {role.id}")


def register_social_settings():
    """Register social settings"""
    register_addon_settings("social", SOCIAL_SETTINGS)
    logger.info(f"Registered {len(SOCIAL_SETTINGS)} social settings")


def register_social_addon():
    """Complete social add-on registration"""
    register_social_roles()
    register_social_settings()
    logger.info("✓ Social add-on registered successfully")
