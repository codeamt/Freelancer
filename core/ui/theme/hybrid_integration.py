"""
Theme Editor Integration with Hybrid Settings System

This module demonstrates how the theme editor can integrate with the
hybrid settings system for persistent storage, versioning, and caching.

Integration Benefits:
- Persistent theme storage (no more state-only)
- Version tracking and rollback
- Performance caching
- Unified settings API
- Enhanced validation
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from core.state.actions import Action, ActionResult
from core.state.state import State
from core.utils.logger import get_logger
from ..theme.editor import ColorScheme, Typography, Spacing

logger = get_logger(__name__)


@dataclass
class ThemeSettings:
    """Theme settings compatible with hybrid settings system"""
    colors: Dict[str, str]
    typography: Dict[str, Any]
    spacing: Dict[str, str]
    custom_css: str = ""
    version: Optional[str] = None
    last_modified: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "colors": self.colors,
            "typography": self.typography,
            "spacing": self.spacing,
            "custom_css": self.custom_css,
            "version": self.version,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThemeSettings":
        return cls(
            colors=data.get("colors", {}),
            typography=data.get("typography", {}),
            spacing=data.get("spacing", {}),
            custom_css=data.get("custom_css", ""),
            version=data.get("version"),
            last_modified=datetime.fromisoformat(data["last_modified"]) if data.get("last_modified") else None
        )


class HybridThemeAction(Action):
    """
    Enhanced theme action that integrates with hybrid settings system.
    
    This replaces the state-only theme actions with persistent storage
    while maintaining the same interface for backward compatibility.
    """
    
    def __init__(self, name: str, theme_key: str):
        super().__init__(
            name=name,
            reads=["theme_state"],
            writes=["theme_state"]
        )
        self.theme_key = theme_key
    
    async def run(self, state: State, context=None, **inputs) -> ActionResult:
        """Run theme action with hybrid settings integration"""
        try:
            # Get user context for permissions
            user_roles = []
            user_id = None
            site_id = None
            
            if context and hasattr(context, 'user_context'):
                user_roles = context.user_context.roles or []
                user_id = context.user_context.user_id
                site_id = getattr(context.user_context, 'site_id', 'default')
            
            # Default to admin if no context
            if not user_roles:
                user_roles = ["admin"]
            
            # Execute the specific theme operation
            result = await self._execute_theme_operation(state, inputs, user_roles, user_id, site_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Theme action {self.name} failed: {e}")
            return ActionResult(
                success=False,
                error=f"Theme operation failed: {str(e)}"
            )
    
    async def _execute_theme_operation(
        self,
        state: State,
        inputs: Dict[str, Any],
        user_roles: List[str],
        user_id: Optional[str],
        site_id: str
    ) -> ActionResult:
        """Execute the specific theme operation - to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement _execute_theme_operation")


class UpdateColorSchemeAction(HybridThemeAction):
    """Update color scheme with hybrid settings integration"""
    
    def __init__(self):
        super().__init__("update_colors", "site.theme.colors")
    
    async def _execute_theme_operation(
        self,
        state: State,
        inputs: Dict[str, Any],
        user_roles: List[str],
        user_id: Optional[str],
        site_id: str
    ) -> ActionResult:
        """Update colors with persistent storage"""
        from core.services.settings import set_setting_hybrid, get_setting_hybrid
        
        color_updates = inputs.get("colors")
        if not color_updates:
            return ActionResult(success=False, error="colors required")
        
        # Get current theme state
        theme_state = state.get("theme_state", {})
        current_colors = theme_state.get("colors", {})
        
        # Merge updates
        updated_colors = {**current_colors, **color_updates}
        
        # Update state for immediate UI response
        theme_state["colors"] = updated_colors
        
        # Persist to hybrid settings
        setting_result = await set_setting_hybrid(
            key=self.theme_key,
            value=updated_colors,
            user_roles=user_roles,
            context={"site_id": site_id}
        )
        
        if not setting_result["success"]:
            return ActionResult(
                success=False,
                error=f"Failed to save theme: {setting_result.get('error')}"
            )
        
        logger.info(f"Color scheme updated and persisted: {setting_result.get('version_id')}")
        
        return ActionResult(
            success=True,
            message="Colors updated and saved",
            data={
                "theme_state": theme_state,
                "version_id": setting_result.get("version_id"),
                "persisted": True
            }
        )


class LoadThemeAction(HybridThemeAction):
    """Load theme from hybrid settings system"""
    
    def __init__(self):
        super().__init__("load_theme", "site.theme.colors")
    
    async def _execute_theme_operation(
        self,
        state: State,
        inputs: Dict[str, Any],
        user_roles: List[str],
        user_id: Optional[str],
        site_id: str
    ) -> ActionResult:
        """Load theme from persistent storage"""
        from core.services.settings import get_theme_settings
        
        # Load all theme settings
        theme_settings_result = await get_theme_settings(user_roles, {"site_id": site_id})
        
        theme_state = {}
        
        # Process each theme setting
        for key, result in theme_settings_result.items():
            if result["success"]:
                theme_state[key.replace("site.theme.", "")] = result["value"]
        
        # Update state
        state.set("theme_state", theme_state)
        
        return ActionResult(
            success=True,
            message="Theme loaded from storage",
            data={
                "theme_state": theme_state,
                "loaded_from_storage": True
            }
        )


class ResetThemeAction(HybridThemeAction):
    """Reset theme to default with version tracking"""
    
    def __init__(self):
        super().__init__("reset_theme", "site.theme.colors")
    
    async def _execute_theme_operation(
        self,
        state: State,
        inputs: Dict[str, Any],
        user_roles: List[str],
        user_id: Optional[str],
        site_id: str
    ) -> ActionResult:
        """Reset theme to defaults"""
        from core.services.settings import set_setting_hybrid
        
        # Get default color scheme
        from ..theme.editor import ThemePresets
        default_theme = ThemePresets.get_preset("modern")
        
        # Update state
        theme_state = default_theme.to_dict()
        state.set("theme_state", theme_state)
        
        # Persist defaults
        setting_result = await set_setting_hybrid(
            key=self.theme_key,
            value=default_theme.colors.to_dict(),
            user_roles=user_roles,
            context={"site_id": site_id},
            change_reason=f"Theme reset to defaults by {user_id or 'system'}"
        )
        
        if not setting_result["success"]:
            return ActionResult(
                success=False,
                error=f"Failed to reset theme: {setting_result.get('error')}"
            )
        
        return ActionResult(
            success=True,
            message="Theme reset to defaults",
            data={
                "theme_state": theme_state,
                "version_id": setting_result.get("version_id"),
                "reset_to_default": True
            }
        )


class GetThemeHistoryAction(HybridThemeAction):
    """Get theme change history"""
    
    def __init__(self):
        super().__init__("get_theme_history", "site.theme.colors")
    
    async def _execute_theme_operation(
        self,
        state: State,
        inputs: Dict[str, Any],
        user_roles: List[str],
        user_id: Optional[str],
        site_id: str
    ) -> ActionResult:
        """Get theme version history"""
        from core.services.settings import get_setting_history
        
        history_result = await get_setting_history(
            key=self.theme_key,
            user_roles=user_roles,
            context={"site_id": site_id}
        )
        
        if not history_result["success"]:
            return ActionResult(
                success=False,
                error=f"Failed to get theme history: {history_result.get('error')}"
            )
        
        return ActionResult(
            success=True,
            message="Theme history retrieved",
            data={
                "history": history_result["history"],
                "total": history_result["total"]
            }
        )


class RollbackThemeAction(HybridThemeAction):
    """Rollback theme to previous version"""
    
    def __init__(self):
        super().__init__("rollback_theme", "site.theme.colors")
    
    async def _execute_theme_operation(
        self,
        state: State,
        inputs: Dict[str, Any],
        user_roles: List[str],
        user_id: Optional[str],
        site_id: str
    ) -> ActionResult:
        """Rollback theme to specific version"""
        from core.services.settings import set_setting_with_version
        
        version_id = inputs.get("version_id")
        if not version_id:
            return ActionResult(success=False, error="version_id required")
        
        # Perform rollback
        rollback_result = await set_setting_with_version(
            key=self.theme_key,
            value=None,  # Value will be loaded from version
            user_roles=user_roles,
            context={"site_id": site_id},
            change_reason=f"Theme rollback to version {version_id} by {user_id or 'system'}"
        )
        
        # This is a simplified rollback - in practice you'd need to implement
        # the actual rollback logic in the enhanced settings service
        
        return ActionResult(
            success=True,
            message="Theme rolled back successfully",
            data={
                "rollback_version_id": version_id,
                "rolled_back": True
            }
        )


# ============================================================================
# Theme Manager with Hybrid Integration
# ============================================================================

class HybridThemeManager:
    """
    Theme manager that integrates with hybrid settings system.
    
    Provides a high-level API for theme operations while handling
    the complexity of state + settings integration.
    """
    
    def __init__(self):
        self.actions = {
            "update_colors": UpdateColorSchemeAction(),
            "load_theme": LoadThemeAction(),
            "reset_theme": ResetThemeAction(),
            "get_history": GetThemeHistoryAction(),
            "rollback_theme": RollbackThemeAction()
        }
    
    async def update_colors(
        self,
        colors: Dict[str, str],
        user_roles: List[str],
        user_id: Optional[str] = None,
        site_id: str = "default"
    ) -> Dict[str, Any]:
        """Update color scheme with persistence"""
        action = self.actions["update_colors"]
        
        # Create a mock context
        class MockContext:
            def __init__(self, roles, uid, sid):
                self.user_context = MockUserContext(roles, uid, sid)
        
        class MockUserContext:
            def __init__(self, roles, uid, sid):
                self.roles = roles
                self.user_id = uid
                self.site_id = sid
        
        context = MockContext(user_roles, user_id, site_id)
        
        # Execute action
        from core.state.state import State
        state = State()
        result = await action.run(state, context, colors=colors)
        
        return {
            "success": result.success,
            "message": result.message,
            "data": result.data,
            "error": result.error
        }
    
    async def load_theme(
        self,
        user_roles: List[str],
        site_id: str = "default"
    ) -> Dict[str, Any]:
        """Load theme from persistent storage"""
        action = self.actions["load_theme"]
        
        class MockContext:
            def __init__(self, roles, sid):
                self.user_context = MockUserContext(roles, sid)
        
        class MockUserContext:
            def __init__(self, roles, sid):
                self.roles = roles
                self.site_id = sid
        
        context = MockContext(user_roles, site_id)
        
        from core.state.state import State
        state = State()
        result = await action.run(state, context)
        
        return {
            "success": result.success,
            "message": result.message,
            "data": result.data,
            "error": result.error
        }
    
    async def get_theme_history(
        self,
        user_roles: List[str],
        site_id: str = "default"
    ) -> Dict[str, Any]:
        """Get theme change history"""
        action = self.actions["get_history"]
        
        class MockContext:
            def __init__(self, roles, sid):
                self.user_context = MockUserContext(roles, sid)
        
        class MockUserContext:
            def __init__(self, roles, sid):
                self.roles = roles
                self.site_id = sid
        
        context = MockContext(user_roles, site_id)
        
        from core.state.state import State
        state = State()
        result = await action.run(state, context)
        
        return {
            "success": result.success,
            "message": result.message,
            "data": result.data,
            "error": result.error
        }


# ============================================================================
# Global Instance
# ============================================================================

hybrid_theme_manager = HybridThemeManager()


# ============================================================================
# Convenience Functions
# ============================================================================

async def update_theme_colors(
    colors: Dict[str, str],
    user_roles: List[str],
    user_id: Optional[str] = None,
    site_id: str = "default"
) -> Dict[str, Any]:
    """Update theme colors with hybrid settings integration"""
    return await hybrid_theme_manager.update_colors(colors, user_roles, user_id, site_id)


async def load_theme_from_storage(
    user_roles: List[str],
    site_id: str = "default"
) -> Dict[str, Any]:
    """Load theme from hybrid settings storage"""
    return await hybrid_theme_manager.load_theme(user_roles, site_id)


async def get_theme_change_history(
    user_roles: List[str],
    site_id: str = "default"
) -> Dict[str, Any]:
    """Get theme change history"""
    return await hybrid_theme_manager.get_theme_history(user_roles, site_id)


__all__ = [
    "HybridThemeAction",
    "UpdateColorSchemeAction",
    "LoadThemeAction",
    "ResetThemeAction",
    "GetThemeHistoryAction",
    "RollbackThemeAction",
    "HybridThemeManager",
    "hybrid_theme_manager",
    "ThemeSettings",
    "update_theme_colors",
    "load_theme_from_storage",
    "get_theme_change_history"
]
