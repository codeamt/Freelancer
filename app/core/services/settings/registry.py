"""
Settings Registry - Central repository for all setting definitions

This module defines all platform and core settings with their:
- Types and validation
- Permission requirements
- Sensitivity levels
- Default values
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from core.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Enums
# ============================================================================

class SettingScope(Enum):
    """Scope of setting application"""
    PLATFORM = "platform"      # Entire platform
    ORGANIZATION = "org"       # Per organization
    SITE = "site"             # Per site
    USER = "user"             # Per user
    ADDON = "addon"           # Add-on specific


class SettingSensitivity(Enum):
    """Sensitivity level for settings"""
    PUBLIC = "public"         # Can be shown to anyone with access
    INTERNAL = "internal"     # Can be shown to authorized users
    SENSITIVE = "sensitive"   # Should be masked in UI (passwords, tokens)
    SECRET = "secret"         # Should never be shown (encryption keys)


class SettingType(Enum):
    """Data type of setting"""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY = "array"
    ENCRYPTED = "encrypted"   # Automatically encrypted/decrypted


# ============================================================================
# Setting Definition
# ============================================================================

@dataclass
class SettingDefinition:
    """Definition of a setting"""
    key: str                              # e.g., "smtp.host"
    name: str                             # Human-readable name
    description: str                      # What it does
    type: SettingType                     # Data type
    scope: SettingScope                   # Where it applies
    sensitivity: SettingSensitivity       # How sensitive
    default: Any = None                   # Default value
    required: bool = False                # Must be set
    validation: Optional[Callable] = None # Validation function
    
    # Permission requirements
    read_permission: tuple = ("setting", "read")   # (resource, action)
    write_permission: tuple = ("setting", "write")
    
    # UI hints
    category: str = "general"             # For grouping in UI
    ui_component: str = "text"            # text/password/select/json
    options: List[Any] = field(default_factory=list)  # For select inputs
    placeholder: str = ""                 # Input placeholder
    help_text: str = ""                   # Additional help
    
    def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate setting value"""
        # Required check
        if self.required and not value:
            return False, "This setting is required"
        
        # Type validation
        if self.type == SettingType.BOOLEAN and not isinstance(value, bool):
            return False, "Must be a boolean"
        
        if self.type == SettingType.INTEGER:
            try:
                int(value)
            except (TypeError, ValueError):
                return False, "Must be an integer"
        
        if self.type == SettingType.JSON and value:
            import json
            try:
                if isinstance(value, str):
                    json.loads(value)
            except json.JSONDecodeError:
                return False, "Must be valid JSON"
        
        # Options check
        if self.options and value not in self.options:
            return False, f"Must be one of: {', '.join(map(str, self.options))}"
        
        # Custom validation
        if self.validation:
            try:
                if not self.validation(value):
                    return False, "Validation failed"
            except Exception as e:
                return False, str(e)
        
        return True, None


# ============================================================================
# Settings Registry
# ============================================================================

class SettingsRegistry:
    """Central registry for all settings definitions"""
    
    def __init__(self):
        self._definitions: Dict[str, SettingDefinition] = {}
        self._register_core_settings()
    
    def _register_core_settings(self):
        """Register core platform settings"""
        
        # ====================================================================
        # Platform Settings
        # ====================================================================
        
        self.register(SettingDefinition(
            key="platform.name",
            name="Platform Name",
            description="Name of the platform",
            type=SettingType.STRING,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.PUBLIC,
            default="Freelancer Platform",
            category="platform",
            read_permission=("setting", "read"),
            write_permission=("platform", "admin"),
            placeholder="My Platform"
        ))
        
        self.register(SettingDefinition(
            key="platform.url",
            name="Platform URL",
            description="Base URL of the platform",
            type=SettingType.STRING,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.PUBLIC,
            default="http://localhost:5001",
            category="platform",
            read_permission=("setting", "read"),
            write_permission=("platform", "admin"),
            placeholder="https://example.com"
        ))
        
        self.register(SettingDefinition(
            key="platform.maintenance_mode",
            name="Maintenance Mode",
            description="Enable maintenance mode for the entire platform",
            type=SettingType.BOOLEAN,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.INTERNAL,
            default=False,
            category="platform",
            read_permission=("platform", "admin"),
            write_permission=("platform", "admin"),
            help_text="When enabled, only admins can access the platform"
        ))
        
        # ====================================================================
        # Authentication & Session Settings
        # ====================================================================
        
        self.register(SettingDefinition(
            key="auth.session_timeout",
            name="Session Timeout (minutes)",
            description="How long sessions last before expiring",
            type=SettingType.INTEGER,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.INTERNAL,
            default=60,
            category="auth",
            validation=lambda v: 5 <= int(v) <= 1440,
            read_permission=("setting", "read"),
            write_permission=("platform", "admin"),
            help_text="Min: 5, Max: 1440 (24 hours)"
        ))
        
        self.register(SettingDefinition(
            key="auth.jwt_secret",
            name="JWT Secret Key",
            description="Secret key for JWT token signing",
            type=SettingType.ENCRYPTED,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.SECRET,
            required=True,
            category="auth",
            ui_component="password",
            read_permission=("platform", "admin"),
            write_permission=("platform", "admin"),
            help_text="Keep this secret! Used to sign authentication tokens"
        ))
        
        self.register(SettingDefinition(
            key="auth.jwt_expiry",
            name="JWT Token Expiry (hours)",
            description="How long JWT tokens remain valid",
            type=SettingType.INTEGER,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.INTERNAL,
            default=24,
            category="auth",
            validation=lambda v: 1 <= int(v) <= 168,
            read_permission=("setting", "read"),
            write_permission=("platform", "admin")
        ))
        
        # ====================================================================
        # Cookie Settings
        # ====================================================================
        
        self.register(SettingDefinition(
            key="auth.cookie_secure",
            name="Secure Cookies",
            description="Require HTTPS for cookies",
            type=SettingType.BOOLEAN,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.INTERNAL,
            default=True,
            category="auth",
            read_permission=("setting", "read"),
            write_permission=("platform", "admin"),
            help_text="Should be True in production"
        ))
        
        self.register(SettingDefinition(
            key="auth.cookie_httponly",
            name="HTTP-Only Cookies",
            description="Prevent JavaScript access to cookies",
            type=SettingType.BOOLEAN,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.INTERNAL,
            default=True,
            category="auth",
            read_permission=("setting", "read"),
            write_permission=("platform", "admin"),
            help_text="Recommended for security"
        ))
        
        self.register(SettingDefinition(
            key="auth.cookie_samesite",
            name="SameSite Cookie Policy",
            description="SameSite attribute for cookies",
            type=SettingType.STRING,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.INTERNAL,
            default="Lax",
            category="auth",
            ui_component="select",
            options=["Strict", "Lax", "None"],
            read_permission=("setting", "read"),
            write_permission=("platform", "admin"),
            help_text="Lax is recommended for most applications"
        ))
        
        self.register(SettingDefinition(
            key="auth.cookie_max_age",
            name="Cookie Max Age (seconds)",
            description="Maximum age for session cookies",
            type=SettingType.INTEGER,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.INTERNAL,
            default=3600,
            category="auth",
            validation=lambda v: 300 <= int(v) <= 86400,
            read_permission=("setting", "read"),
            write_permission=("platform", "admin"),
            help_text="300 (5 min) to 86400 (24 hours)"
        ))
        
        # ====================================================================
        # Integration Settings
        # ====================================================================
        
        # SMTP
        self.register(SettingDefinition(
            key="integrations.smtp.host",
            name="SMTP Host",
            description="Email server hostname",
            type=SettingType.STRING,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.INTERNAL,
            category="integrations",
            read_permission=("integration", "read"),
            write_permission=("integration", "write"),
            placeholder="smtp.gmail.com"
        ))
        
        self.register(SettingDefinition(
            key="integrations.smtp.port",
            name="SMTP Port",
            description="Email server port",
            type=SettingType.INTEGER,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.INTERNAL,
            default=587,
            category="integrations",
            read_permission=("integration", "read"),
            write_permission=("integration", "write"),
            help_text="Common: 587 (TLS), 465 (SSL), 25 (unencrypted)"
        ))
        
        self.register(SettingDefinition(
            key="integrations.smtp.username",
            name="SMTP Username",
            description="Email server username",
            type=SettingType.STRING,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.INTERNAL,
            category="integrations",
            read_permission=("integration", "read"),
            write_permission=("integration", "write")
        ))
        
        self.register(SettingDefinition(
            key="integrations.smtp.password",
            name="SMTP Password",
            description="Email server password",
            type=SettingType.ENCRYPTED,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.SENSITIVE,
            category="integrations",
            ui_component="password",
            read_permission=("integration", "read"),
            write_permission=("integration", "write")
        ))
        
        # Stripe
        self.register(SettingDefinition(
            key="integrations.stripe.public_key",
            name="Stripe Public Key",
            description="Stripe publishable key",
            type=SettingType.STRING,
            scope=SettingScope.SITE,
            sensitivity=SettingSensitivity.PUBLIC,
            category="integrations",
            read_permission=("integration", "read"),
            write_permission=("integration", "write"),
            placeholder="pk_live_..."
        ))
        
        self.register(SettingDefinition(
            key="integrations.stripe.secret_key",
            name="Stripe Secret Key",
            description="Stripe secret key",
            type=SettingType.ENCRYPTED,
            scope=SettingScope.SITE,
            sensitivity=SettingSensitivity.SECRET,
            category="integrations",
            ui_component="password",
            read_permission=("integration", "admin"),
            write_permission=("integration", "admin"),
            placeholder="sk_live_..."
        ))
        
        # Anthropic
        self.register(SettingDefinition(
            key="integrations.anthropic.api_key",
            name="Anthropic API Key",
            description="API key for Claude integration",
            type=SettingType.ENCRYPTED,
            scope=SettingScope.PLATFORM,
            sensitivity=SettingSensitivity.SECRET,
            category="integrations",
            ui_component="password",
            read_permission=("integration", "admin"),
            write_permission=("integration", "admin"),
            placeholder="sk-ant-..."
        ))
        
        # ====================================================================
        # Site Settings
        # ====================================================================
        
        self.register(SettingDefinition(
            key="site.analytics.google_id",
            name="Google Analytics ID",
            description="Google Analytics tracking ID",
            type=SettingType.STRING,
            scope=SettingScope.SITE,
            sensitivity=SettingSensitivity.INTERNAL,
            category="analytics",
            read_permission=("site", "read"),
            write_permission=("site", "update"),
            placeholder="UA-XXXXXXXXX-X"
        ))
        
        self.register(SettingDefinition(
            key="site.seo.title",
            name="Default Site Title",
            description="Default title for SEO",
            type=SettingType.STRING,
            scope=SettingScope.SITE,
            sensitivity=SettingSensitivity.PUBLIC,
            category="seo",
            read_permission=("site", "read"),
            write_permission=("site", "update"),
            placeholder="My Awesome Site"
        ))
        
        self.register(SettingDefinition(
            key="site.seo.description",
            name="Default Meta Description",
            description="Default meta description for SEO",
            type=SettingType.STRING,
            scope=SettingScope.SITE,
            sensitivity=SettingSensitivity.PUBLIC,
            category="seo",
            read_permission=("site", "read"),
            write_permission=("site", "update"),
            placeholder="A brief description of your site"
        ))
        
        # ====================================================================
        # User Preferences
        # ====================================================================
        
        self.register(SettingDefinition(
            key="user.theme",
            name="Theme Preference",
            description="User's preferred color theme",
            type=SettingType.STRING,
            scope=SettingScope.USER,
            sensitivity=SettingSensitivity.PUBLIC,
            default="light",
            category="preferences",
            ui_component="select",
            options=["light", "dark", "auto"],
            read_permission=("user", "read"),
            write_permission=("user", "update")
        ))
        
        self.register(SettingDefinition(
            key="user.notifications.email",
            name="Email Notifications",
            description="Receive email notifications",
            type=SettingType.BOOLEAN,
            scope=SettingScope.USER,
            sensitivity=SettingSensitivity.PUBLIC,
            default=True,
            category="preferences",
            read_permission=("user", "read"),
            write_permission=("user", "update")
        ))
        
        self.register(SettingDefinition(
            key="user.notifications.push",
            name="Push Notifications",
            description="Receive push notifications",
            type=SettingType.BOOLEAN,
            scope=SettingScope.USER,
            sensitivity=SettingSensitivity.PUBLIC,
            default=False,
            category="preferences",
            read_permission=("user", "read"),
            write_permission=("user", "update")
        ))
    
    def register(self, definition: SettingDefinition):
        """Register a setting definition"""
        self._definitions[definition.key] = definition
        logger.debug(f"Registered setting: {definition.key}")
    
    def get(self, key: str) -> Optional[SettingDefinition]:
        """Get setting definition by key"""
        return self._definitions.get(key)
    
    def get_by_category(self, category: str) -> List[SettingDefinition]:
        """Get all settings in a category"""
        return [d for d in self._definitions.values() if d.category == category]
    
    def get_by_scope(self, scope: SettingScope) -> List[SettingDefinition]:
        """Get all settings for a scope"""
        return [d for d in self._definitions.values() if d.scope == scope]
    
    def get_all_categories(self) -> List[str]:
        """Get list of all categories"""
        categories = set(d.category for d in self._definitions.values())
        return sorted(categories)
    
    def get_all(self) -> Dict[str, SettingDefinition]:
        """Get all setting definitions"""
        return self._definitions.copy()


# Global registry instance
settings_registry = SettingsRegistry()