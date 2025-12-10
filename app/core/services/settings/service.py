"""
Settings Service - Permission-aware CRUD for settings

Handles:
- Reading settings with permission checks
- Writing settings with validation and permissions
- Encryption/decryption of sensitive values
- Scoping (platform/org/site/user/addon)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from core.services.auth.permissions import permission_registry
from core.utils.logger import get_logger

from .registry import settings_registry, SettingScope, SettingType, SettingSensitivity
from .encryption import encryption_service

logger = get_logger(__name__)


class SettingsService:
    """
    Service for managing settings with permission checks.
    
    All read/write operations check permissions based on:
    - User's roles
    - Setting scope
    - Context (site_id, org_id, etc.)
    """
    
    def __init__(self, db_service=None):
        """
        Initialize settings service.
        
        Args:
            db_service: Database service for persistence
        """
        self.db = db_service
        self.registry = settings_registry
        self.encryption = encryption_service
    
    # ========================================================================
    # Read Operations
    # ========================================================================
    
    async def get_setting(
        self,
        key: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        decrypt: bool = True
    ) -> Dict[str, Any]:
        """
        Get a setting value with permission check.
        
        Args:
            key: Setting key (e.g., "smtp.host")
            user_roles: User's roles
            context: Context (site_id, user_id, etc.)
            decrypt: Whether to decrypt encrypted values
            
        Returns:
            {
                "success": bool,
                "value": Any,
                "masked": bool,
                "definition": dict,
                "error": str
            }
        """
        definition = self.registry.get(key)
        if not definition:
            return {"success": False, "error": f"Setting '{key}' not found"}
        
        # Check read permission
        resource, action = definition.read_permission
        context = context or {}
        
        has_permission = permission_registry.check_permission(
            user_roles, resource, action, context
        )
        
        if not has_permission:
            return {"success": False, "error": "Permission denied"}
        
        # Get value from database
        scope_key = self._get_scope_key(definition.scope, context)
        value = await self._fetch_value(key, scope_key)
        
        # Use default if not set
        if value is None:
            value = definition.default
        
        # Handle encryption
        masked = False
        if definition.type == SettingType.ENCRYPTED and value:
            if decrypt:
                try:
                    value = self.encryption.decrypt(value)
                except Exception as e:
                    logger.error(f"Failed to decrypt setting {key}: {e}")
                    return {"success": False, "error": "Decryption failed"}
            else:
                # Mask for security
                if definition.sensitivity in [SettingSensitivity.SENSITIVE, SettingSensitivity.SECRET]:
                    value = "********"
                    masked = True
        
        return {
            "success": True,
            "value": value,
            "masked": masked,
            "definition": {
                "name": definition.name,
                "description": definition.description,
                "type": definition.type.value,
                "category": definition.category,
                "ui_component": definition.ui_component,
                "options": definition.options,
                "placeholder": definition.placeholder,
                "help_text": definition.help_text
            }
        }
    
    async def get_category_settings(
        self,
        category: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get all settings in a category that user can read.
        
        Returns only settings user has permission to see.
        """
        definitions = self.registry.get_by_category(category)
        settings = {}
        
        for definition in definitions:
            result = await self.get_setting(
                definition.key,
                user_roles,
                context,
                decrypt=False  # Don't decrypt for bulk fetch
            )
            
            if result["success"]:
                settings[definition.key] = result
        
        return {
            "success": True,
            "category": category,
            "settings": settings
        }
    
    async def get_all_settings(
        self,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get all settings user has permission to see.
        
        Returns:
            {
                "success": True,
                "settings": {
                    "category1": {
                        "key1": {...},
                        "key2": {...}
                    },
                    "category2": {...}
                }
            }
        """
        all_settings = {}
        
        for definition in self.registry.get_all().values():
            result = await self.get_setting(
                definition.key,
                user_roles,
                context,
                decrypt=False
            )
            
            if result["success"]:
                category = definition.category
                if category not in all_settings:
                    all_settings[category] = {}
                
                all_settings[category][definition.key] = result
        
        return {
            "success": True,
            "settings": all_settings
        }
    
    # ========================================================================
    # Write Operations
    # ========================================================================
    
    async def set_setting(
        self,
        key: str,
        value: Any,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Set a setting value with permission check.
        
        Args:
            key: Setting key
            value: New value
            user_roles: User's roles
            context: Context (site_id, user_id, etc.)
            
        Returns:
            {"success": bool, "error": str}
        """
        definition = self.registry.get(key)
        if not definition:
            return {"success": False, "error": f"Setting '{key}' not found"}
        
        # Check write permission
        resource, action = definition.write_permission
        context = context or {}
        
        has_permission = permission_registry.check_permission(
            user_roles, resource, action, context
        )
        
        if not has_permission:
            return {"success": False, "error": "Permission denied"}
        
        # Validate value
        valid, error = definition.validate(value)
        if not valid:
            return {"success": False, "error": error}
        
        # Encrypt if needed
        if definition.type == SettingType.ENCRYPTED:
            try:
                value = self.encryption.encrypt(str(value))
            except Exception as e:
                logger.error(f"Failed to encrypt setting {key}: {e}")
                return {"success": False, "error": "Encryption failed"}
        
        # Save to database
        scope_key = self._get_scope_key(definition.scope, context)
        user_id = context.get("user_id", "system")
        
        success = await self._save_value(key, value, scope_key, user_id)
        
        if success:
            logger.info(f"Setting updated: {key} (scope: {scope_key}, user: {user_id})")
            return {"success": True}
        else:
            return {"success": False, "error": "Failed to save setting"}
    
    async def set_multiple_settings(
        self,
        settings: Dict[str, Any],
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Set multiple settings at once.
        
        Args:
            settings: Dictionary of {key: value}
            user_roles: User's roles
            context: Context
            
        Returns:
            {
                "success": bool,
                "results": {key: {"success": bool, "error": str}},
                "succeeded": int,
                "failed": int
            }
        """
        results = {}
        succeeded = 0
        failed = 0
        
        for key, value in settings.items():
            result = await self.set_setting(key, value, user_roles, context)
            results[key] = result
            
            if result["success"]:
                succeeded += 1
            else:
                failed += 1
        
        return {
            "success": failed == 0,
            "results": results,
            "succeeded": succeeded,
            "failed": failed
        }
    
    async def delete_setting(
        self,
        key: str,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Delete a setting (reset to default).
        
        Requires write permission.
        """
        definition = self.registry.get(key)
        if not definition:
            return {"success": False, "error": f"Setting '{key}' not found"}
        
        # Check write permission
        resource, action = definition.write_permission
        context = context or {}
        
        has_permission = permission_registry.check_permission(
            user_roles, resource, action, context
        )
        
        if not has_permission:
            return {"success": False, "error": "Permission denied"}
        
        # Delete from database
        scope_key = self._get_scope_key(definition.scope, context)
        success = await self._delete_value(key, scope_key)
        
        if success:
            logger.info(f"Setting deleted: {key} (scope: {scope_key})")
            return {"success": True}
        else:
            return {"success": False, "error": "Failed to delete setting"}
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _get_scope_key(self, scope: SettingScope, context: Optional[Dict]) -> str:
        """Generate scope key for database storage"""
        if scope == SettingScope.PLATFORM:
            return "platform"
        
        elif scope == SettingScope.ORGANIZATION:
            org_id = context.get("org_id") if context else None
            return f"org:{org_id}" if org_id else "platform"
        
        elif scope == SettingScope.SITE:
            site_id = context.get("site_id") if context else None
            return f"site:{site_id}" if site_id else "platform"
        
        elif scope == SettingScope.USER:
            user_id = context.get("user_id") if context else None
            return f"user:{user_id}" if user_id else "platform"
        
        elif scope == SettingScope.ADDON:
            addon_id = context.get("addon_id") if context else None
            return f"addon:{addon_id}" if addon_id else "platform"
        
        return "platform"
    
    async def _fetch_value(self, key: str, scope_key: str) -> Any:
        """Fetch value from database"""
        if not self.db:
            logger.warning("No database service configured")
            return None
        
        try:
            result = await self.db.find_one("settings", {
                "key": key,
                "scope": scope_key
            })
            return result.get("value") if result else None
        except Exception as e:
            logger.error(f"Error fetching setting {key}: {e}")
            return None
    
    async def _save_value(
        self,
        key: str,
        value: Any,
        scope_key: str,
        user_id: str
    ) -> bool:
        """Save value to database"""
        if not self.db:
            logger.warning("No database service configured")
            return False
        
        try:
            await self.db.update_one(
                "settings",
                {"key": key, "scope": scope_key},
                {
                    "key": key,
                    "value": value,
                    "scope": scope_key,
                    "updated_at": datetime.utcnow(),
                    "updated_by": user_id
                },
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving setting {key}: {e}")
            return False
    
    async def _delete_value(self, key: str, scope_key: str) -> bool:
        """Delete value from database"""
        if not self.db:
            logger.warning("No database service configured")
            return False
        
        try:
            await self.db.delete_one("settings", {
                "key": key,
                "scope": scope_key
            })
            return True
        except Exception as e:
            logger.error(f"Error deleting setting {key}: {e}")
            return False
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    async def export_settings(
        self,
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        include_secrets: bool = False
    ) -> Dict[str, Any]:
        """
        Export all settings user can read.
        
        Args:
            user_roles: User's roles
            context: Context
            include_secrets: Include encrypted/secret values (admins only)
            
        Returns:
            Dictionary of settings suitable for backup/transfer
        """
        result = await self.get_all_settings(user_roles, context)
        
        if not result["success"]:
            return result
        
        export_data = {}
        
        for category, settings in result["settings"].items():
            export_data[category] = {}
            
            for key, setting in settings.items():
                # Skip masked/secret values unless explicitly included
                if setting.get("masked") and not include_secrets:
                    continue
                
                export_data[category][key] = setting["value"]
        
        return {
            "success": True,
            "data": export_data,
            "exported_at": datetime.utcnow().isoformat()
        }
    
    async def import_settings(
        self,
        data: Dict[str, Dict[str, Any]],
        user_roles: List[str],
        context: Optional[Dict[str, Any]] = None,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Import settings from exported data.
        
        Args:
            data: Exported settings data
            user_roles: User's roles
            context: Context
            overwrite: Whether to overwrite existing values
            
        Returns:
            Import results
        """
        results = {}
        succeeded = 0
        failed = 0
        skipped = 0
        
        for category, settings in data.items():
            for key, value in settings.items():
                # Check if setting exists
                if not overwrite:
                    existing = await self.get_setting(key, user_roles, context)
                    if existing["success"] and existing["value"] is not None:
                        results[key] = {"success": False, "error": "Already exists"}
                        skipped += 1
                        continue
                
                # Set the value
                result = await self.set_setting(key, value, user_roles, context)
                results[key] = result
                
                if result["success"]:
                    succeeded += 1
                else:
                    failed += 1
        
        return {
            "success": failed == 0,
            "results": results,
            "succeeded": succeeded,
            "failed": failed,
            "skipped": skipped
        }


# Global service instance
# Will be initialized with proper db_service by application
settings_service = SettingsService()


# Initialization function to be called by app
def initialize_settings_service(db_service):
    """Initialize settings service with database"""
    global settings_service
    settings_service = SettingsService(db_service)
    logger.info("Settings service initialized")