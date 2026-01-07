"""
Settings Service - Permission-aware configuration management

This module provides:
- Hierarchical settings (Platform → Org → Site → User → Add-on)
- Role-based access control
- Encryption for sensitive data
- Add-on settings registration
- Type validation and defaults

Usage:
    from core.services.settings import settings_service, settings_registry
    
    # Get a setting with permission check
    result = await settings_service.get_setting(
        key="integrations.stripe.secret_key",
        user_roles=["admin"],
        context={"site_id": "site123"}
    )
    
    # Register add-on settings
    from core.services.settings import register_addon_settings
    register_addon_settings("lms", [...])
"""

from .registry import (
    SettingsRegistry,
    SettingDefinition,
    SettingScope,
    SettingSensitivity,
    SettingType,
    settings_registry
)

from .service import (
    SettingsService,
    settings_service
)

from .encryption import (
    EncryptionService,
    encryption_service
)

from .session import (
    SessionManager,
    SessionConfig,
    CookieConfig,
    session_manager
)

# Import hybrid and enhanced settings
from .hybrid import (
    HybridSettingsManager,
    hybrid_settings,
    SettingValue,
    SettingSource,
    get_setting_hybrid,
    set_setting_hybrid,
    get_theme_settings,
    # Single-Site Optimized
    OptimizedSettingsManager,
    optimized_settings,
    get_setting_optimized,
    set_setting_optimized,
    get_theme_settings_optimized
)

from .enhancements import (
    EnhancedSettingsService,
    enhanced_settings,
    SettingVersion,
    ValidationResult,
    ValidationRule,
    get_setting_cached,
    set_setting_with_version,
    get_setting_history
)


def register_addon_settings(addon_id: str, settings: list):
    """
    Register add-on specific settings.
    
    Args:
        addon_id: Add-on identifier (e.g., "lms", "commerce")
        settings: List of SettingDefinition objects
        
    Example:
        register_addon_settings("lms", [
            SettingDefinition(
                key="zoom.api_key",
                name="Zoom API Key",
                type=SettingType.ENCRYPTED,
                scope=SettingScope.ADDON,
                ...
            )
        ])
    """
    for setting in settings:
        # Prefix key with addon ID
        setting.key = f"{addon_id}.{setting.key}"
        
        # Ensure addon scope
        if setting.scope == SettingScope.ADDON:
            setting.scope = SettingScope.ADDON
        
        # Register with global registry
        settings_registry.register(setting)


__all__ = [
    # Registry
    "SettingsRegistry",
    "SettingDefinition",
    "SettingScope",
    "SettingSensitivity",
    "SettingType",
    "settings_registry",
    
    # Service
    "SettingsService",
    "settings_service",
    
    # Encryption
    "EncryptionService",
    "encryption_service",
    
    # Session
    "SessionManager",
    "SessionConfig",
    "CookieConfig",
    "session_manager",
    
    # Hybrid Settings
    "HybridSettingsManager",
    "hybrid_settings",
    "SettingValue",
    "SettingSource",
    "get_setting_hybrid",
    "set_setting_hybrid",
    "get_theme_settings",
    
    # Single-Site Optimized
    "OptimizedSettingsManager",
    "optimized_settings",
    "get_setting_optimized",
    "set_setting_optimized",
    "get_theme_settings_optimized",
    
    # Enhanced Settings
    "EnhancedSettingsService",
    "enhanced_settings",
    "SettingVersion",
    "ValidationResult",
    "ValidationRule",
    "get_setting_cached",
    "set_setting_with_version",
    "get_setting_history",
    
    # Utilities
    "register_addon_settings",
]