"""
Streaming Platform Add-on Manifest

Registers:
- Roles (streamer, subscriber, stream_admin)
- Settings (streaming limits, quality, monetization, etc.)
- Components (video player, chat, stream list, etc.)
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
# Stream Roles
# ============================================================================

STREAM_ROLES = [
    Role(
        id="stream_admin",
        name="Stream Administrator",
        description="Full streaming platform management access",
        permissions=[
            Permission("stream", "*", "*"),          # All stream operations
            Permission("channel", "*", "*"),         # All channels
            Permission("subscriber", "*", "*"),      # All subscribers
            Permission("monetization", "*", "*"),    # Monetization settings
            Permission("moderation", "*", "*"),      # Moderation actions
            Permission("integration", "write", "stream"),  # Configure integrations
        ],
        inherits_from=["admin"],
        domain="stream"
    ),
    
    Role(
        id="streamer",
        name="Streamer",
        description="Create and manage live streams",
        permissions=[
            Permission("stream", "read", "*"),       # Read stream settings
            Permission("stream", "*", "own"),        # Manage own streams
            Permission("channel", "*", "own"),       # Manage own channel
            Permission("subscriber", "read", "own"), # View own subscribers
            Permission("chat", "*", "own"),          # Manage own chat
            Permission("monetization", "read", "own"), # View own earnings
            Permission("analytics", "read", "own"),  # View own analytics
        ],
        inherits_from=["member"],
        domain="stream"
    ),
    
    Role(
        id="subscriber",
        name="Subscriber",
        description="Subscribe to and watch streams",
        permissions=[
            Permission("stream", "read", "*"),       # Watch all streams
            Permission("channel", "read", "*"),      # View all channels
            Permission("chat", "create", "*"),       # Chat in streams
            Permission("subscription", "*", "own"),  # Manage own subscriptions
            Permission("donation", "create", "*"),   # Make donations
        ],
        inherits_from=["member"],
        domain="stream"
    )
]


# ============================================================================
# Stream Settings
# ============================================================================

STREAM_SETTINGS = [
    # Streaming Settings
    SettingDefinition(
        key="streaming.max_bitrate",
        name="Max Streaming Bitrate (kbps)",
        description="Maximum bitrate for streams",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=6000,
        category="stream",
        validation=lambda v: 500 <= int(v) <= 50000,
        read_permission=("stream", "read"),
        write_permission=("stream", "admin"),
        help_text="500-50000 kbps"
    ),
    
    SettingDefinition(
        key="streaming.max_resolution",
        name="Max Stream Resolution",
        description="Maximum resolution for streams",
        type=SettingType.STRING,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default="1080p",
        category="stream",
        ui_component="select",
        options=["480p", "720p", "1080p", "1440p", "4k"],
        read_permission=("stream", "read"),
        write_permission=("stream", "admin")
    ),
    
    SettingDefinition(
        key="streaming.max_concurrent_streams",
        name="Max Concurrent Streams Per User",
        description="Maximum number of concurrent streams per streamer",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=1,
        category="stream",
        validation=lambda v: 1 <= int(v) <= 10,
        read_permission=("stream", "read"),
        write_permission=("stream", "admin"),
        help_text="1-10 streams"
    ),
    
    SettingDefinition(
        key="streaming.enable_recording",
        name="Enable Stream Recording",
        description="Allow streamers to record their streams",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="stream",
        read_permission=("stream", "read"),
        write_permission=("stream", "admin")
    ),
    
    SettingDefinition(
        key="streaming.recording_retention_days",
        name="Recording Retention (Days)",
        description="Days to keep recorded streams",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=30,
        category="stream",
        validation=lambda v: 1 <= int(v) <= 365,
        read_permission=("stream", "read"),
        write_permission=("stream", "admin"),
        help_text="1-365 days"
    ),
    
    # CDN Settings
    SettingDefinition(
        key="cdn.provider",
        name="CDN Provider",
        description="Content delivery network provider",
        type=SettingType.STRING,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default="cloudflare",
        category="stream",
        ui_component="select",
        options=["cloudflare", "aws", "azure", "custom"],
        read_permission=("stream", "read"),
        write_permission=("stream", "admin")
    ),
    
    SettingDefinition(
        key="cdn.api_key",
        name="CDN API Key",
        description="API key for CDN provider",
        type=SettingType.ENCRYPTED,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.SECRET,
        category="stream",
        ui_component="password",
        read_permission=("stream", "admin"),
        write_permission=("stream", "admin"),
        help_text="Required for CDN integration"
    ),
    
    # Chat Settings
    SettingDefinition(
        key="chat.enabled",
        name="Chat Enabled",
        description="Enable live chat in streams",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="stream",
        read_permission=("stream", "read"),
        write_permission=("stream", "admin")
    ),
    
    SettingDefinition(
        key="chat.slow_mode_seconds",
        name="Slow Mode Delay (Seconds)",
        description="Minimum seconds between chat messages",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=0,
        category="stream",
        validation=lambda v: 0 <= int(v) <= 120,
        read_permission=("stream", "read"),
        write_permission=("stream", "admin"),
        help_text="0 = disabled, 1-120 seconds"
    ),
    
    SettingDefinition(
        key="chat.max_message_length",
        name="Max Chat Message Length",
        description="Maximum characters per chat message",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=500,
        category="stream",
        validation=lambda v: 50 <= int(v) <= 2000,
        read_permission=("stream", "read"),
        write_permission=("stream", "admin"),
        help_text="50-2000 characters"
    ),
    
    SettingDefinition(
        key="chat.profanity_filter",
        name="Chat Profanity Filter",
        description="Filter profanity in chat messages",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="stream",
        read_permission=("stream", "read"),
        write_permission=("stream", "admin")
    ),
    
    # Monetization Settings
    SettingDefinition(
        key="monetization.enabled",
        name="Monetization Enabled",
        description="Enable monetization features",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="stream",
        read_permission=("stream", "read"),
        write_permission=("stream", "admin")
    ),
    
    SettingDefinition(
        key="monetization.subscription_tiers",
        name="Subscription Tiers",
        description="Available subscription tier prices (comma-separated)",
        type=SettingType.STRING,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default="4.99,9.99,24.99",
        category="stream",
        read_permission=("stream", "read"),
        write_permission=("stream", "admin"),
        placeholder="4.99,9.99,24.99"
    ),
    
    SettingDefinition(
        key="monetization.platform_fee_percent",
        name="Platform Fee (%)",
        description="Platform fee percentage on subscriptions/donations",
        type=SettingType.FLOAT,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=20.0,
        category="stream",
        validation=lambda v: 0 <= float(v) <= 50,
        read_permission=("stream", "read"),
        write_permission=("stream", "admin"),
        help_text="0-50%"
    ),
    
    SettingDefinition(
        key="monetization.min_payout_amount",
        name="Minimum Payout Amount",
        description="Minimum balance for payout",
        type=SettingType.FLOAT,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=100.0,
        category="stream",
        read_permission=("stream", "read"),
        write_permission=("stream", "admin"),
        help_text="Minimum balance in dollars"
    ),
    
    # Notification Settings
    SettingDefinition(
        key="notifications.stream_start",
        name="Notify on Stream Start",
        description="Notify subscribers when streamer goes live",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="stream",
        read_permission=("stream", "read"),
        write_permission=("stream", "admin")
    ),
    
    SettingDefinition(
        key="notifications.new_subscriber",
        name="Notify on New Subscriber",
        description="Notify streamer of new subscribers",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="stream",
        read_permission=("stream", "read"),
        write_permission=("stream", "admin")
    ),
    
    SettingDefinition(
        key="notifications.donation_received",
        name="Notify on Donation",
        description="Notify streamer of donations",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="stream",
        read_permission=("stream", "read"),
        write_permission=("stream", "admin")
    )
]


# ============================================================================
# Stream Components
# ============================================================================

STREAM_COMPONENTS = [
    {
        "id": "live_stream_player",
        "name": "Live Stream Player",
        "type": "content",
        "description": "Live video player with controls",
        "factory": "stream.components.create_stream_player",
        "category": "stream"
    },
    {
        "id": "stream_list",
        "name": "Stream List",
        "type": "content",
        "description": "Display list of live streams",
        "factory": "stream.components.create_stream_list",
        "category": "stream"
    },
    {
        "id": "chat_widget",
        "name": "Live Chat",
        "type": "widget",
        "description": "Real-time chat for streams",
        "factory": "stream.components.create_chat_widget",
        "category": "stream"
    },
    {
        "id": "channel_page",
        "name": "Channel Page",
        "type": "content",
        "description": "Streamer channel page",
        "factory": "stream.components.create_channel_page",
        "category": "stream"
    },
    {
        "id": "subscribe_button",
        "name": "Subscribe Button",
        "type": "widget",
        "description": "Channel subscription button",
        "factory": "stream.components.create_subscribe_button",
        "category": "stream"
    },
    {
        "id": "donation_widget",
        "name": "Donation Widget",
        "type": "widget",
        "description": "Accept donations during stream",
        "factory": "stream.components.create_donation_widget",
        "category": "stream"
    }
]


# ============================================================================
# Stream Routes
# ============================================================================

STREAM_ROUTES = [
    {
        "path": "/live",
        "handler": "stream.routes.list_live_streams",
        "methods": ["GET"],
        "permission": ("stream", "read")
    },
    {
        "path": "/stream/{stream_id}",
        "handler": "stream.routes.watch_stream",
        "methods": ["GET"],
        "permission": ("stream", "read")
    },
    {
        "path": "/channel/{channel_id}",
        "handler": "stream.routes.view_channel",
        "methods": ["GET"],
        "permission": ("channel", "read")
    },
    {
        "path": "/stream/start",
        "handler": "stream.routes.start_stream",
        "methods": ["POST"],
        "permission": ("stream", "create")
    },
    {
        "path": "/stream/{stream_id}/end",
        "handler": "stream.routes.end_stream",
        "methods": ["POST"],
        "permission": ("stream", "update")
    },
    {
        "path": "/subscribe/{channel_id}",
        "handler": "stream.routes.subscribe_channel",
        "methods": ["POST"],
        "permission": ("subscription", "create")
    },
    {
        "path": "/donate/{channel_id}",
        "handler": "stream.routes.donate",
        "methods": ["POST"],
        "permission": ("donation", "create")
    }
]


# ============================================================================
# Theme Extensions
# ============================================================================

STREAM_THEME_EXTENSIONS = {
    "colors": {
        "stream_primary": "#9333ea",
        "stream_secondary": "#c026d3",
        "live_indicator": "#ef4444",
        "subscriber_badge": "#f59e0b"
    },
    "components": {
        "stream_card": {
            "border_radius": "0.5rem",
            "shadow": "lg",
            "hover_shadow": "xl"
        },
        "chat_widget": {
            "bg_color": "#1f2937",
            "text_color": "#f3f4f6"
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


STREAM_MANIFEST = AddonManifest(
    id="stream",
    name="Streaming Platform",
    version="1.0.0",
    description="Complete streaming platform with live video, chat, and monetization",
    domain="stream",
    roles=STREAM_ROLES,
    settings=STREAM_SETTINGS,
    components=STREAM_COMPONENTS,
    routes=STREAM_ROUTES,
    theme_extensions=STREAM_THEME_EXTENSIONS
)


# ============================================================================
# Registration Functions
# ============================================================================

def register_stream_roles():
    """Register stream roles with permission system"""
    from core.services.auth.permissions import permission_registry
    
    for role in STREAM_ROLES:
        permission_registry.register_role(role)
        logger.info(f"Registered stream role: {role.id}")


def register_stream_settings():
    """Register stream settings"""
    register_addon_settings("stream", STREAM_SETTINGS)
    logger.info(f"Registered {len(STREAM_SETTINGS)} stream settings")


def register_stream_addon():
    """Complete stream add-on registration"""
    register_stream_roles()
    register_stream_settings()
    logger.info("✓ Stream add-on registered successfully")
