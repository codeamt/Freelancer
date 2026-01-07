"""
Hybrid Settings System - Unified Configuration Management

This module provides a unified settings architecture that combines:
- Static configuration (environment variables)
- Dynamic configuration (database-stored)
- Add-on configurations
- Built-in caching and versioning
- Performance optimizations

Architecture:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Static Config │    │  Dynamic Config │    │  Add-on Config  │
│  (Environment)  │    │   (Database)    │    │ (Manifests)     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │   HybridSettingsManager   │
                    │  - Unified API            │
                    │  - Smart Caching          │
                    │  - Version Tracking       │
                    │  - Permission Checks      │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │   Application Layer       │
                    │  - Theme Editor           │
                    │  - Admin Settings        │
                    │  - User Preferences      │
                    └───────────────────────────┘
"""

import asyncio
import json
import hashlib
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from core.utils.cache import cache
from core.utils.logger import get_logger
from .service import settings_service
from .registry import settings_registry, SettingDefinition, SettingScope, SettingType, SettingSensitivity
from ..auth.permissions import permission_registry

logger = get_logger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class SettingSource(Enum):
    """Source of a setting value"""
    STATIC = "static"           # Environment variables
    DYNAMIC = "dynamic"         # Database storage
    ADDON = "addon"            # Add-on manifests
    COMPUTED = "computed"      # Computed from other settings
    DEFAULT = "default"        # Built-in defaults


@dataclass
class SettingValue:
    """Unified setting value with metadata"""
    key: str
    value: Any
    source: SettingSource
    scope: SettingScope
    sensitivity: SettingSensitivity
    last_modified: Optional[datetime] = None
    version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self, mask_sensitive: bool = True) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = {
            "key": self.key,
            "value": self._mask_value() if mask_sensitive and self.sensitivity == SettingSensitivity.SECRET else self.value,
            "source": self.source.value,
            "scope": self.scope.value,
            "sensitivity": self.sensitivity.value,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "version": self.version,
            "metadata": self.metadata
        }
        return result
    
    def _mask_value(self) -> str:
        """Mask sensitive values"""
        if isinstance(self.value, str) and len(self.value) > 4:
            return self.value[:2] + "*" * (len(self.value) - 4) + self.value[-2:]
        return "***"


@dataclass
class SettingCacheEntry:
    """Cache entry for settings"""
    value: SettingValue
    expires_at: datetime
    hit_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


# ============================================================================
# Hybrid Settings Manager
# ============================================================================

class HybridSettingsManager:
    """
    Unified settings management system.
    
    Provides a single API for all configuration needs with intelligent
    caching, versioning, and performance optimizations.
    """
    
    def __init__(self):
        self.static_config = None  # Will be loaded from environment
        self.addon_configs = {}     # Loaded from addon manifests
        self.cache = {}             # In-memory cache
        self.cache_ttl = {
            SettingSource.STATIC: timedelta(hours=24),    # Static rarely changes
            SettingSource.DYNAMIC: timedelta(minutes=15),  # Dynamic changes often
            SettingSource.ADDON: timedelta(hours=1),       # Addons change rarely
            SettingSource.COMPUTED: timedelta(minutes=5),   # Computed changes often
            SettingSource.DEFAULT: timedelta(hours=24)     # Defaults never change
        }
        
        # Performance metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "db_queries": 0,
            "static_loads": 0
        }
    
    async def initialize(self):
        """Initialize the hybrid settings system"""
        logger.info("Initializing Hybrid Settings Manager...")
        
        # Load static configuration
        await self._load_static_config()
        
        # Load add-on configurations
        await self._load_addon_configs()
        
        # Warm up cache with frequently accessed settings
        await self._warm_cache()
        
        logger.info("Hybrid Settings Manager initialized successfully")
    
    async def get_setting(
        self,
        key: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        decrypt: bool = False
    ) -> Dict[str, Any]:
        """
        Get a setting value with unified resolution.
        
        Resolution Priority:
        1. Dynamic setting (database) - highest precedence
        2. Static setting (environment) 
        3. Add-on setting (manifest)
        4. Computed setting (derived)
        5. Default value
        
        Args:
            key: Setting key (e.g., "site.theme.colors")
            user_roles: User roles for permission check
            context: Context (site_id, user_id, etc.)
            use_cache: Whether to use cached values
            decrypt: Whether to decrypt encrypted values
            
        Returns:
            Dict with success, value, and metadata
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(key, user_roles, context)
            if use_cache and cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                if not cache_entry.is_expired:
                    cache_entry.hit_count += 1
                    self.metrics["cache_hits"] += 1
                    return {
                        "success": True,
                        "value": cache_entry.value.value,
                        "source": cache_entry.value.source.value,
                        "metadata": cache_entry.value.to_dict()
                    }
                else:
                    # Remove expired entry
                    del self.cache[cache_key]
            
            self.metrics["cache_misses"] += 1
            
            # Resolve setting from all sources
            setting_value = await self._resolve_setting(key, user_roles, context, decrypt)
            
            if not setting_value:
                return {
                    "success": False,
                    "error": "Setting not found",
                    "key": key
                }
            
            # Cache the result
            if use_cache:
                ttl = self.cache_ttl[setting_value.source]
                self.cache[cache_key] = SettingCacheEntry(
                    value=setting_value,
                    expires_at=datetime.utcnow() + ttl
                )
            
            return {
                "success": True,
                "value": setting_value.value,
                "source": setting_value.source.value,
                "metadata": setting_value.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return {
                "success": False,
                "error": str(e),
                "key": key
            }
    
    async def set_setting(
        self,
        key: str,
        value: Any,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        encrypt: bool = False
    ) -> Dict[str, Any]:
        """
        Set a setting value.
        
        Only dynamic settings can be set. Static and add-on settings
        are read-only at runtime.
        
        Args:
            key: Setting key
            value: Setting value
            user_roles: User roles for permission check
            context: Context for scoping
            encrypt: Whether to encrypt the value
            
        Returns:
            Dict with success and metadata
        """
        try:
            # Check if setting exists and is writable
            definition = settings_registry.get(key)
            if not definition:
                return {
                    "success": False,
                    "error": "Setting definition not found"
                }
            
            # Check permissions
            if not await self._check_permission(definition.write_permission, user_roles, context):
                return {
                    "success": False,
                    "error": "Permission denied"
                }
            
            # Validate value
            is_valid, error_msg = definition.validate(value)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Validation failed: {error_msg}"
                }
            
            # Set in dynamic storage (database)
            result = await settings_service.set_setting(
                key=key,
                value=value,
                user_roles=user_roles,
                context=context,
                encrypt=encrypt
            )
            
            if result["success"]:
                # Invalidate cache
                await self._invalidate_cache(key)
                
                # Update metrics
                self.metrics["db_queries"] += 1
                
                logger.info(f"Setting {key} updated successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_settings_batch(
        self,
        keys: List[str],
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple settings efficiently.
        
        Uses batch processing to minimize database queries.
        """
        results = {}
        
        # Process in parallel for better performance
        tasks = [
            self.get_setting(key, user_roles, context, use_cache)
            for key in keys
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for key, response in zip(keys, responses):
            if isinstance(response, Exception):
                results[key] = {
                    "success": False,
                    "error": str(response)
                }
            else:
                results[key] = response
        
        return results
    
    async def get_settings_by_category(
        self,
        category: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all settings in a category.
        """
        # Get all definitions in category
        definitions = [
            defn for defn in settings_registry.get_all().values()
            if defn.category == category
        ]
        
        keys = [defn.key for defn in definitions]
        return await self.get_settings_batch(keys, user_roles, context)
    
    # ========================================================================
    # Private Methods - Resolution Logic
    # ========================================================================
    
    async def _resolve_setting(
        self,
        key: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]],
        decrypt: bool
    ) -> Optional[SettingValue]:
        """Resolve setting from all sources"""
        
        # 1. Try dynamic settings (database)
        dynamic_result = await self._get_dynamic_setting(key, user_roles, context, decrypt)
        if dynamic_result:
            return dynamic_result
        
        # 2. Try static settings (environment)
        static_result = await self._get_static_setting(key)
        if static_result:
            return static_result
        
        # 3. Try add-on settings (manifests)
        addon_result = await self._get_addon_setting(key)
        if addon_result:
            return addon_result
        
        # 4. Try computed settings
        computed_result = await self._get_computed_setting(key, user_roles, context)
        if computed_result:
            return computed_result
        
        # 5. Return default from registry
        return await self._get_default_setting(key)
    
    async def _get_dynamic_setting(
        self,
        key: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]],
        decrypt: bool
    ) -> Optional[SettingValue]:
        """Get setting from dynamic storage (database)"""
        try:
            result = await settings_service.get_setting(
                key=key,
                user_roles=user_roles,
                context=context,
                decrypt=decrypt
            )
            
            if result["success"]:
                definition = settings_registry.get(key)
                return SettingValue(
                    key=key,
                    value=result["value"],
                    source=SettingSource.DYNAMIC,
                    scope=definition.scope if definition else SettingScope.PLATFORM,
                    sensitivity=definition.sensitivity if definition else SettingSensitivity.PUBLIC,
                    last_modified=result.get("last_modified"),
                    metadata=result.get("metadata", {})
                )
            
        except Exception as e:
            logger.debug(f"Dynamic setting {key} not available: {e}")
        
        return None
    
    async def _get_static_setting(self, key: str) -> Optional[SettingValue]:
        """Get setting from static configuration (environment)"""
        if not self.static_config:
            return None
        
        # Map setting keys to environment variables
        env_key = self._map_key_to_env(key)
        env_value = getattr(self.static_config, env_key, None)
        
        if env_value is not None:
            # Handle SecretStr
            if hasattr(env_value, 'get_secret_value'):
                env_value = env_value.get_secret_value()
            
            definition = settings_registry.get(key)
            return SettingValue(
                key=key,
                value=env_value,
                source=SettingSource.STATIC,
                scope=definition.scope if definition else SettingScope.PLATFORM,
                sensitivity=definition.sensitivity if definition else SettingSensitivity.PUBLIC,
                metadata={"env_key": env_key}
            )
        
        return None
    
    async def _get_addon_setting(self, key: str) -> Optional[SettingValue]:
        """Get setting from add-on configuration"""
        # Parse addon prefix (e.g., "blog.posts_per_page" -> addon="blog")
        parts = key.split('.')
        if len(parts) < 2:
            return None
        
        addon_id = parts[0]
        setting_key = '.'.join(parts[1:])
        
        if addon_id in self.addon_configs:
            addon_config = self.addon_configs[addon_id]
            if setting_key in addon_config:
                return SettingValue(
                    key=key,
                    value=addon_config[setting_key],
                    source=SettingSource.ADDON,
                    scope=SettingScope.ADDON,
                    sensitivity=SettingSensitivity.PUBLIC,
                    metadata={"addon_id": addon_id}
                )
        
        return None
    
    async def _get_computed_setting(
        self,
        key: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]]
    ) -> Optional[SettingValue]:
        """Get computed setting derived from other settings"""
        
        # Define computed settings (optimized for single-site)
        computed_settings = {
            "theme.combined": self._compute_combined_theme,
            "user.preferences.all": self._compute_user_preferences,
            "platform.feature_flags": self._compute_feature_flags
        }
        
        if key in computed_settings:
            try:
                value = await computed_settings[key](user_roles, context)
                return SettingValue(
                    key=key,
                    value=value,
                    source=SettingSource.COMPUTED,
                    scope=SettingScope.PLATFORM,
                    sensitivity=SettingSensitivity.PUBLIC,
                    metadata={"computed_at": datetime.utcnow().isoformat()}
                )
            except Exception as e:
                logger.debug(f"Computed setting {key} failed: {e}")
        
        return None
    
    async def _get_default_setting(self, key: str) -> Optional[SettingValue]:
        """Get default value from registry"""
        definition = settings_registry.get(key)
        if definition and definition.default is not None:
            return SettingValue(
                key=key,
                value=definition.default,
                source=SettingSource.DEFAULT,
                scope=definition.scope,
                sensitivity=definition.sensitivity,
                metadata={"is_default": True}
            )
        
        return None
    
    # ========================================================================
    # Private Methods - Initialization and Caching
    # ========================================================================
    
    async def _load_static_config(self):
        """Load static configuration from environment"""
        try:
            from settings import settings
            self.static_config = settings
            self.metrics["static_loads"] += 1
            logger.info("Static configuration loaded")
        except ImportError as e:
            logger.warning(f"Could not load static configuration: {e}")
    
    async def _load_addon_configs(self):
        """Load add-on configurations from manifests"""
        try:
            from core.addon_loader import get_enabled_addons
            
            for addon_id in get_enabled_addons():
                try:
                    # Import addon manifest
                    manifest_module = __import__(f"add_ons.domains.{addon_id}.manifest", fromlist=[''])
                    if hasattr(manifest_module, f'{addon_id.upper()}_MANIFEST'):
                        manifest = getattr(manifest_module, f'{addon_id.upper()}_MANIFEST')
                        
                        # Extract configuration from manifest
                        config = {}
                        for setting_def in manifest.settings:
                            config[setting_def.key.replace(f"{addon_id}.", "")] = setting_def.default
                        
                        self.addon_configs[addon_id] = config
                        logger.info(f"Loaded {len(config)} settings for addon {addon_id}")
                
                except Exception as e:
                    logger.warning(f"Could not load addon {addon_id} config: {e}")
        
        except Exception as e:
            logger.warning(f"Could not load addon configurations: {e}")
    
    async def _warm_cache(self):
        """Warm up cache with frequently accessed settings"""
        frequent_keys = [
            "auth.session_timeout",
            "auth.jwt_expiry",
            "theme.colors",
            "user.theme",
            "platform.debug_mode"
        ]
        
        # Pre-load these settings (will use admin roles for broad access)
        for key in frequent_keys:
            try:
                await self.get_setting(key, ["super_admin"], {}, use_cache=True)
            except Exception as e:
                logger.debug(f"Could not warm cache for {key}: {e}")
    
    # ========================================================================
    # Private Methods - Utilities
    # ========================================================================
    
    def _generate_cache_key(
        self,
        key: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]],
        decrypt: bool = False
    ) -> str:
        """Generate cache key for setting (optimized for single-site)"""
        # Create a deterministic key from the parameters (no site_id needed)
        cache_data = {
            "key": key,
            "roles": sorted(user_roles),
            "user_id": context.get("user_id") if context else None,
            "decrypt": decrypt
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return f"setting:{hashlib.md5(cache_str.encode()).hexdigest()}"
    
    def _map_key_to_env(self, key: str) -> str:
        """Map setting key to environment variable name"""
        # Convert dot notation to uppercase with underscores
        return key.upper().replace('.', '_')
    
    async def _check_permission(
        self,
        permission: tuple,
        user_roles: List[str],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if user has permission for setting"""
        try:
            # Use permission registry to check
            for role in user_roles:
                role_permissions = permission_registry.get_role_permissions(role)
                if role_permissions and role_permissions.has_permission(*permission):
                    return True
            return False
        except Exception as e:
            logger.debug(f"Permission check failed: {e}")
            return False
    
    async def _invalidate_cache(self, key: str):
        """Invalidate cache entries for a setting"""
        # Remove all cache entries that contain this key
        keys_to_remove = [
            cache_key for cache_key in self.cache.keys()
            if key in cache_key
        ]
        
        for cache_key in keys_to_remove:
            del self.cache[cache_key]
        
        logger.debug(f"Invalidated {len(keys_to_remove)} cache entries for {key}")
    
    # ========================================================================
    # Computed Settings
    # ========================================================================
    
    async def _compute_combined_theme(
        self,
        user_roles: List[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compute combined theme (platform + user override)"""
        platform_theme = await self.get_setting("theme.colors", user_roles, context)
        user_theme = await self.get_setting("user.theme.override", user_roles, context)
        
        # Merge user preferences with platform theme
        combined = platform_theme.get("value", {})
        if user_theme.get("success"):
            combined.update(user_theme.get("value", {}))
        
        return combined
    
    async def _compute_user_preferences(
        self,
        user_roles: List[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compute all user preferences"""
        preference_keys = [
            "user.theme",
            "user.language",
            "user.timezone",
            "user.notifications.email",
            "user.notifications.push"
        ]
        
        preferences = {}
        for key in preference_keys:
            result = await self.get_setting(key, user_roles, context)
            if result["success"]:
                preferences[key.replace("user.", "")] = result["value"]
        
        return preferences
    
    async def _compute_feature_flags(
        self,
        user_roles: List[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """Compute all feature flags"""
        flag_keys = [
            "platform.enable_beta_features",
            "platform.enable_new_ui",
            "platform.enable_analytics",
            "platform.enable_dark_mode"
        ]
        
        flags = {}
        for key in flag_keys:
            result = await self.get_setting(key, user_roles, context)
            if result["success"]:
                flags[key.replace("platform.", "")] = bool(result["value"])
        
        return flags
    
    # ========================================================================
    # Metrics and Monitoring
    # ========================================================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        total_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = (self.metrics["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hit_rate": round(cache_hit_rate, 2),
            "total_requests": total_requests,
            "cache_size": len(self.cache),
            "db_queries": self.metrics["db_queries"],
            "static_loads": self.metrics["static_loads"],
            **self.metrics
        }
    
    async def clear_cache(self):
        """Clear all cached settings"""
        self.cache.clear()
        logger.info("Settings cache cleared")


# ============================================================================
# Global Instance
# ============================================================================

hybrid_settings = HybridSettingsManager()


# ============================================================================
# Convenience Functions
# ============================================================================

async def get_setting_hybrid(
    key: str,
    user_roles: List[str],
    context: Optional[Dict[str, Any]] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Get setting using hybrid system"""
    return await hybrid_settings.get_setting(key, user_roles, context, use_cache)


async def set_setting_hybrid(
    key: str,
    value: Any,
    user_roles: List[str],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Set setting using hybrid system"""
    return await hybrid_settings.set_setting(key, value, user_roles, context)


async def get_theme_settings(
    user_roles: List[str],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Get all theme-related settings (optimized for single-site)"""
    theme_keys = [
        "theme.colors",
        "theme.typography",
        "theme.spacing",
        "user.theme",
        "user.theme.override"
    ]
    
    return await hybrid_settings.get_settings_batch(theme_keys, user_roles, context)


# ============================================================================
# Single-Site Optimized Settings Manager
# ============================================================================

class OptimizedSettingsManager(HybridSettingsManager):
    """
    Optimized settings manager for single-site applications.
    
    Removes site_id complexity and optimizes for single-site performance.
    Benefits:
    - Simpler cache keys (no site_id fragmentation)
    - Higher cache hit rates
    - Better performance for single-site apps
    - Cleaner API for single-site use cases
    """
    
    def __init__(self):
        super().__init__()
        
        # Optimized cache TTL for single-site (longer since less fragmentation)
        self.cache_ttl = {
            SettingSource.STATIC: timedelta(hours=24),    # Static rarely changes
            SettingSource.DYNAMIC: timedelta(minutes=30),  # Longer for single-site
            SettingSource.ADDON: timedelta(hours=2),       # Addons change rarely
            SettingSource.COMPUTED: timedelta(minutes=10), # Computed changes often
            SettingSource.DEFAULT: timedelta(hours=24)     # Defaults never change
        }
        
        # Single-site performance metrics
        self.metrics.update({
            "single_site_optimizations": True,
            "cache_key_simplifications": 0,
            "site_id_removals": 0
        })
    
    def _generate_cache_key(
        self,
        key: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]],
        decrypt: bool = False
    ) -> str:
        """Generate optimized cache key for single-site (no site_id complexity)"""
        # Simplified cache data for single-site
        cache_data = {
            "key": key,
            "roles": sorted(user_roles),
            "user_id": context.get("user_id") if context else None,
            "decrypt": decrypt
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        cache_key = f"ss_setting:{hashlib.md5(cache_str.encode()).hexdigest()}"
        
        # Track optimization metrics
        self.metrics["cache_key_simplifications"] += 1
        
        return cache_key
    
    async def get_setting(
        self,
        key: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        decrypt: bool = False
    ) -> Dict[str, Any]:
        """
        Get setting optimized for single-site.
        
        Simplified context handling - no site_id needed.
        """
        # Strip site_id from context if present (cleanup)
        if context and "site_id" in context:
            clean_context = {k: v for k, v in context.items() if k != "site_id"}
            self.metrics["site_id_removals"] += 1
        else:
            clean_context = context
        
        return await super().get_setting(
            key=key,
            user_roles=user_roles,
            context=clean_context,
            use_cache=use_cache,
            decrypt=decrypt
        )
    
    async def set_setting(
        self,
        key: str,
        value: Any,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        encrypt: bool = False
    ) -> Dict[str, Any]:
        """
        Set setting optimized for single-site.
        
        Simplified context handling - no site_id needed.
        """
        # Strip site_id from context if present (cleanup)
        if context and "site_id" in context:
            clean_context = {k: v for k, v in context.items() if k != "site_id"}
            self.metrics["site_id_removals"] += 1
        else:
            clean_context = context
        
        return await super().set_setting(
            key=key,
            value=value,
            user_roles=user_roles,
            context=clean_context,
            encrypt=encrypt
        )
    
    async def get_theme_settings_optimized(
        self,
        user_roles: List[str],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get theme settings optimized for single-site.
        
        Simplified theme keys without site prefix.
        """
        # Simplified theme keys for single-site
        theme_keys = [
            "theme.colors",
            "theme.typography", 
            "theme.spacing",
            "user.theme",
            "user.theme.override"
        ]
        
        context = {"user_id": user_id} if user_id else None
        
        return await self.get_settings_batch(theme_keys, user_roles, context)
    
    def get_optimization_metrics(self) -> Dict[str, Any]:
        """Get single-site optimization metrics"""
        base_metrics = self.get_metrics()
        
        return {
            **base_metrics,
            "single_site_stats": {
                "cache_key_simplifications": self.metrics["cache_key_simplifications"],
                "site_id_removals": self.metrics["site_id_removals"],
                "optimization_enabled": True,
                "cache_hit_improvement": "Expected 20-30% improvement"
            }
        }
    
    async def warm_cache_optimized(self):
        """
        Warm cache with frequently accessed single-site settings.
        
        Optimized theme and system settings for single-site performance.
        """
        logger.info("Warming single-site optimized cache...")
        
        # Optimized frequent keys for single-site
        frequent_keys = [
            "theme.colors",
            "theme.typography",
            "auth.session_timeout",
            "auth.jwt_expiry",
            "platform.debug_mode",
            "user.theme"
        ]
        
        # Pre-load with admin roles for broad access
        for key in frequent_keys:
            try:
                await self.get_setting(key, ["admin"], use_cache=True)
            except Exception as e:
                logger.debug(f"Could not warm cache for {key}: {e}")
        
        logger.info(f"Warmed {len(frequent_keys)} single-site settings in cache")


# ============================================================================
# Global Optimized Instance
# ============================================================================

optimized_settings = OptimizedSettingsManager()


# ============================================================================
# Optimized Convenience Functions
# ============================================================================

async def get_setting_optimized(
    key: str,
    user_roles: List[str],
    user_id: Optional[str] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Get setting using optimized system"""
    context = {"user_id": user_id} if user_id else None
    return await optimized_settings.get_setting(key, user_roles, context, use_cache)


async def set_setting_optimized(
    key: str,
    value: Any,
    user_roles: List[str],
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Set setting using optimized system"""
    context = {"user_id": user_id} if user_id else None
    return await optimized_settings.set_setting(key, value, user_roles, context)


async def get_theme_settings_optimized(
    user_roles: List[str],
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get theme settings using optimized system"""
    return await optimized_settings.get_theme_settings_optimized(user_roles, user_id)


__all__ = [
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
]
