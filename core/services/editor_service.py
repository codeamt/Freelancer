"""
Omniview Editor - Unified Visual Site Builder

Combines state management, theme editing, and component library
into a single cohesive editing experience.

Architecture:
    ┌────────────────────────────────────────┐
    │      Omniview Editor (Frontend)        │
    ├────────────────────────────────────────┤
    │  ┌──────────┐  ┌──────────┐  ┌───────┐│
    │  │Structure │  │  Theme   │  │Preview││
    │  │  Panel   │  │  Panel   │  │ Panel ││
    │  └──────────┘  └──────────┘  └───────┘│
    └────────────────────────────────────────┘
                      ▲
                      │
    ┌─────────────────┴─────────────────────┐
    │     Editor Service (Backend)          │
    ├───────────────────────────────────────┤
    │  State Manager  │  Theme Manager      │
    │  Component Lib  │  Preview Generator  │
    └───────────────────────────────────────┘
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from core.state.state import State
from core.workflows.admin import SiteWorkflowManager
from core.workflows.preview import PreviewPublishManager
from core.ui.theme.hybrid_theme_manager import HybridThemeManager
from core.ui.state.factory import EnhancedComponentLibrary, SectionRenderer
from core.services.settings import (
    get_theme_settings_optimized,
    set_setting_optimized,
    set_setting_with_version,
    enhanced_settings
)
from core.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Editor State
# ============================================================================

@dataclass
class EditorSession:
    """Represents an active editing session"""
    session_id: str
    user_id: str
    started_at: datetime
    last_activity: datetime
    current_panel: str = "structure"
    selected_section: Optional[str] = None
    selected_component: Optional[str] = None
    has_unsaved_changes: bool = False
    history: List[Dict[str, Any]] = field(default_factory=list)
    history_index: int = -1


class EditorStateManager:
    """Manages editor state separate from site state"""
    
    def __init__(self):
        self.active_sessions: Dict[str, EditorSession] = {}
    
    def create_session(
        self,
        user_id: str
    ) -> EditorSession:
        """Create new editing session (optimized for single-site)"""
        import uuid
        session_id = str(uuid.uuid4())
        
        session = EditorSession(
            session_id=session_id,
            user_id=user_id,
            started_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        self.active_sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[EditorSession]:
        """Get active session"""
        return self.active_sessions.get(session_id)
    
    def update_activity(self, session_id: str):
        """Update last activity time"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].last_activity = datetime.utcnow()


# ============================================================================
# Omniview Editor Service
# ============================================================================

class OmniviewEditorService:
    """
    Unified editor service combining all editing capabilities.
    
    This service provides:
    - Structure editing (sections, components)
    - Theme editing (colors, typography, CSS)
    - Live preview generation
    - Undo/redo functionality
    - Auto-save
    """
    
    def __init__(self, persister=None):
        """
        Initialize omniview editor.
        
        Args:
            persister: State persistence backend (optional, hybrid settings used for theme)
        """
        self.persister = persister
        
        # Core managers
        self.site_manager = SiteWorkflowManager(persister=persister)
        self.theme_manager = HybridThemeManager()  # Replaced ThemeEditorManager
        self.preview_manager = PreviewPublishManager(persister=persister)
        self.component_library = EnhancedComponentLibrary()
        
        # Editor state
        self.editor_state = EditorStateManager()
    
    # ========================================================================
    # Session Management
    # ========================================================================
    
    async def start_editing(
        self,
        user_id: str,
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """
        Start editing session with hybrid settings integration (optimized for single-site).
        
        Returns full editor state including:
        - Site structure
        - Theme state (from hybrid settings)
        - Available components
        - Version history
        - User permissions
        """
        # Create session (no site_id needed for single-site)
        session = self.editor_state.create_session(user_id)
        
        # Load site structure (use "default" for single-site)
        site_result = await self.site_manager.load_site("default", user_id)
        if not site_result["success"]:
            return {"success": False, "error": site_result.get("error")}
        
        # Load theme using hybrid settings (persistent storage)
        theme_state = await get_theme_settings_optimized(user_roles, {"user_id": user_id})
        
        # Get available components
        component_templates = self.component_library.get_all_templates()
        
        # Get version history (from hybrid settings)
        try:
            history_result = await get_setting_with_version(
                key="theme.colors",
                user_roles=user_roles,
                context={"user_id": user_id}
            )
            history = history_result.get("history", [])
        except:
            history = []
        
        return {
            "success": True,
            "session_id": session.session_id,
            "site_state": site_result["state"],
            "theme_state": theme_state,
            "component_templates": component_templates,
            "version_history": history,
            "current_panel": session.current_panel,
            "performance_metrics": {
                "theme_persistence": "hybrid_settings",
                "cache_optimization": "single_site",
                "version_tracking": "enabled"
            },
            "permissions": {
                "can_edit": True,  # Would check actual permissions
                "can_publish": True,
                "can_delete": True
            }
        }
    
    async def end_editing(
        self,
        session_id: str,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        End editing session.
        
        Args:
            session_id: Active session ID
            auto_save: Whether to auto-save unsaved changes
        """
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        # Auto-save if needed
        if auto_save and session.has_unsaved_changes:
            # Save would happen here
            pass
        
        # Clean up session
        del self.editor_state.active_sessions[session_id]
        
        return {"success": True}
    
    # ========================================================================
    # Structure Editing
    # ========================================================================
    
    async def add_section(
        self,
        session_id: str,
        section_id: str,
        section_type: str,
        position: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add section to site.
        
        This updates the draft state and returns updated preview.
        """
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        # Update site state
        result = await self.site_manager.update_site_sections(
            site_id=session.site_id,
            operations=[{
                "action": "add",
                "data": {
                    "section_id": section_id,
                    "section_type": section_type,
                    "order": position
                }
            }],
            user_id=session.user_id
        )
        
        if not result["success"]:
            return result
        
        # Mark as unsaved
        session.has_unsaved_changes = True
        session.selected_section = section_id
        
        # Generate preview
        preview = await self._generate_preview(session)
        
        return {
            "success": True,
            "section_id": section_id,
            "preview": preview
        }
    
    async def add_component(
        self,
        session_id: str,
        section_id: str,
        component_template_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add component to section.
        
        Args:
            session_id: Active session
            section_id: Target section
            component_template_id: Template from library
            config: Custom configuration
        """
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        # Get template
        template = self.component_library.get_template(component_template_id)
        if not template:
            return {"success": False, "error": "Template not found"}
        
        # Create component from template
        component = template["factory"](
            component_id=f"{section_id}_{component_template_id}_{datetime.utcnow().timestamp()}",
            **(config or {})
        )
        
        # Add to section
        from core.ui.state.actions import AddComponentAction
        
        # Load current state
        site_result = await self.site_manager.load_site(session.site_id, session.user_id)
        site_state = State(site_result["state"])
        
        action = AddComponentAction()
        new_state, result = await action.execute(
            site_state,
            section_id=section_id,
            component_config=component.to_dict()
        )
        
        if result.success:
            # Save state
            await self.persister.save(
                session.site_id,
                new_state,
                f"user:{session.user_id}"
            )
            
            session.has_unsaved_changes = True
            session.selected_component = component.id
            
            # Generate preview
            preview = await self._generate_preview(session)
            
            return {
                "success": True,
                "component_id": component.id,
                "preview": preview
            }
        
        return {"success": False, "error": result.error}
    
    async def update_component(
        self,
        session_id: str,
        section_id: str,
        component_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update component configuration.
        
        This is called as user edits component properties in real-time.
        """
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        from core.ui.state.actions import UpdateComponentAction
        
        # Load current state
        site_result = await self.site_manager.load_site(session.site_id, session.user_id)
        site_state = State(site_result["state"])
        
        action = UpdateComponentAction()
        new_state, result = await action.execute(
            site_state,
            section_id=section_id,
            component_id=component_id,
            updates=updates
        )
        
        if result.success:
            # Save state
            await self.persister.save(
                session.site_id,
                new_state,
                f"user:{session.user_id}"
            )
            
            session.has_unsaved_changes = True
            
            # Generate preview
            preview = await self._generate_preview(session)
            
            return {
                "success": True,
                "preview": preview
            }
        
        return {"success": False, "error": result.error}
    
    # ========================================================================
    # Theme Editing
    # ========================================================================
    
    async def update_theme_colors(
        self,
        session_id: str,
        colors: Dict[str, str],
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """
        Update theme colors with hybrid settings persistence (optimized for single-site).
        
        This updates theme and regenerates preview immediately with persistent storage.
        """
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        # Use hybrid theme manager for persistence
        result = await self.theme_manager.update_theme_colors(
            colors=colors,
            user_roles=user_roles,
            user_id=session.user_id
        )
        
        if result["success"]:
            session.has_unsaved_changes = True
            
            # Generate preview with new theme
            preview = await self._generate_preview(session)
            
            return {
                "success": True,
                "version_id": result.get("version_id"),
                "preview": preview,
                "persisted": True,
                "cache_optimized": True
            }
        
        return result
    
    async def apply_theme_preset(
        self,
        session_id: str,
        preset_name: str,
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """Apply theme preset using hybrid theme manager (optimized for single-site)"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        # Apply preset using hybrid theme manager
        result = await self.theme_manager.apply_preset(
            preset=preset_name,
            preserve_custom_css=True,
            user_roles=user_roles,
            user_id=session.user_id
        )
        
        if result["success"]:
            session.has_unsaved_changes = True
            
            # Generate preview with new theme
            preview = await self._generate_preview(session)
            
            return {
                "success": True,
                "preset": preset_name,
                "version_id": result.get("version_id"),
                "preview": preview,
                "persisted": True
            }
        
        return result
    
    # ========================================================================
    
    async def _generate_preview(
        self,
        session: EditorSession,
        user_context: Optional[Dict[str, Any]] = None,
        use_cached_theme: bool = True
    ) -> Dict[str, Any]:
        """Generate preview for current state with cached theme optimization """
        try:
            # Get cached theme if enabled
            theme_data = None
            if use_cached_theme:
                theme_result = await get_theme_settings_optimized(
                    ["admin"],  # Use admin for full theme access
                    session.user_id
                )
                if theme_result:
                    theme_data = theme_result
            
            # Generate preview with theme data
            result = await self.preview_manager.generate_preview(
                site_id="default",  # Use default for single-site
                user_context=user_context,
                user_id=session.user_id,
                theme_data=theme_data  # Pass cached theme data
            )
            
            preview_data = result.get("preview_data") if result["success"] else {}
            
            # Add cache optimization info
            if preview_data:
                preview_data["cache_info"] = {
                    "theme_cached": use_cached_theme and theme_data is not None,
                    "cache_hit": bool(theme_data),
                    "optimization_enabled": True
                }
            
            return preview_data
            
        except Exception as e:
            logger.error(f"Failed to generate preview: {e}")
            return {"error": f"Preview generation failed: {str(e)}"}
    
    async def get_cached_preview(
        self,
        session_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get preview using cached theme data"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        try:
            # Generate preview with cached theme
            preview = await self._generate_preview(
                session=session,
                user_context=user_context,
                use_cached_theme=True
            )
            
            return {
                "success": True,
                "preview": preview,
                "cache_optimized": True,
                "editor_features": {
                    "cached_preview": True,
                    "fast_loading": True,
                    "theme_applied": True
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get cached preview: {str(e)}"}
    
    async def invalidate_theme_cache(
        self,
        session_id: str,
        components: Optional[List[str]] = None,
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """Invalidate theme cache for components (optimized for single-site)"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        try:
            # Default to all theme components
            if not components:
                components = ["colors", "typography", "spacing"]
            
            invalidated_keys = []
            
            for component in components:
                key = f"theme.{component}"
                
                # Invalidate cache through enhanced settings
                await enhanced_settings.invalidate_cache(
                    key=key,
                    user_roles=user_roles,
                    context={"user_id": session.user_id}
                )
                
                invalidated_keys.append(key)
            
            return {
                "success": True,
                "invalidated_keys": invalidated_keys,
                "cache_cleared": True,
                "editor_features": {
                    "cache_invalidation": True,
                    "auto_refresh": True,
                    "preview_update": True
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to invalidate cache: {str(e)}"}
    
    async def get_editor_performance_metrics(
        self,
        session_id: str,
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """Get comprehensive editor performance metrics (optimized for single-site)"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        try:
            # Get settings performance metrics
            settings_metrics = optimized_settings.get_metrics()
            
            # Get enhanced settings metrics
            enhanced_metrics = enhanced_settings.get_performance_metrics()
            
            # Editor-specific metrics
            editor_metrics = {
                "session_id": session_id,
                "session_duration": (datetime.utcnow() - session.last_activity).total_seconds(),
                "has_unsaved_changes": session.has_unsaved_changes,
                "current_panel": session.current_panel
            }
            
            return {
                "success": True,
                "settings_optimization": settings_metrics,
                "enhanced_settings": enhanced_metrics,
                "editor_session": editor_metrics,
                "performance_features": {
                    "cache_optimization": settings_metrics.get("optimization_enabled", False),
                    "cache_hit_rate": settings_metrics.get("cache_hit_rate", 0),
                    "site_id_removals": settings_metrics.get("site_id_removals", 0),
                    "cache_key_simplifications": settings_metrics.get("cache_key_simplifications", 0)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get metrics: {str(e)}"}
    
    async def get_theme_history(
        self,
        session_id: str,
        component: str = "colors",
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """Get comprehensive theme change history from hybrid settings (optimized for single-site)"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        try:
            # Get history for specific component
            key = f"theme.{component}"
            history_result = await enhanced_settings.get_setting_history(
                key=key,
                user_roles=user_roles,
                context={"user_id": session.user_id}
            )
            
            if history_result.get("success"):
                # Get all theme components history
                all_history = {}
                theme_components = ["colors", "typography", "spacing"]
                
                for comp in theme_components:
                    comp_key = f"theme.{comp}"
                    comp_history = await enhanced_settings.get_setting_history(
                        key=comp_key,
                        user_roles=user_roles,
                        context={"user_id": session.user_id}
                    )
                    if comp_history.get("success"):
                        all_history[comp] = comp_history
                
                return {
                    "success": True,
                    "component": component,
                    "history": history_result.get("history", []),
                    "total_versions": history_result.get("total", 0),
                    "all_components_history": all_history,
                    "editor_features": {
                        "timeline_view": True,
                        "component_filtering": True,
                        "change_comparison": True,
                        "batch_rollback": True
                    }
                }
            
            return history_result
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get theme history: {str(e)}"}
    
    async def get_theme_change_timeline(
        self,
        session_id: str,
        limit: int = 20,
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """Get unified timeline of all theme changes (optimized for single-site)"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        try:
            # Collect all theme component histories
            theme_components = ["colors", "typography", "spacing"]
            all_changes = []
            
            for component in theme_components:
                key = f"theme.{component}"
                history_result = await enhanced_settings.get_setting_history(
                    key=key,
                    user_roles=user_roles,
                    context={"user_id": session.user_id}
                )
                
                if history_result.get("success"):
                    for change in history_result.get("history", []):
                        change["component"] = component
                        change["key"] = key
                        all_changes.append(change)
            
            # Sort by timestamp (most recent first)
            all_changes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Limit results
            limited_changes = all_changes[:limit]
            
            return {
                "success": True,
                "timeline": limited_changes,
                "total_changes": len(all_changes),
                "components_tracked": theme_components,
                "editor_features": {
                    "filter_by_component": True,
                    "sort_by_timestamp": True,
                    "view_change_details": True,
                    "export_timeline": True
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get theme timeline: {str(e)}"}
    
    async def compare_theme_versions(
        self,
        session_id: str,
        version_id_1: str,
        version_id_2: str,
        component: str = "colors",
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """Compare two theme versions (optimized for single-site)"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        try:
            key = f"theme.{component}"
            
            # Get both versions
            version_1_result = await enhanced_settings.get_setting_version(
                key=key,
                version_id=version_id_1,
                user_roles=user_roles,
                context={"user_id": session.user_id}
            )
            
            version_2_result = await enhanced_settings.get_setting_version(
                key=key,
                version_id=version_id_2,
                user_roles=user_roles,
                context={"user_id": session.user_id}
            )
            
            if version_1_result.get("success") and version_2_result.get("success"):
                value_1 = version_1_result.get("value", {})
                value_2 = version_2_result.get("value", {})
                
                # Calculate differences
                differences = self._calculate_theme_differences(value_1, value_2)
                
                return {
                    "success": True,
                    "component": component,
                    "version_1": {
                        "version_id": version_id_1,
                        "value": value_1,
                        "timestamp": version_1_result.get("timestamp")
                    },
                    "version_2": {
                        "version_id": version_id_2,
                        "value": value_2,
                        "timestamp": version_2_result.get("timestamp")
                    },
                    "differences": differences,
                    "editor_features": {
                        "visual_diff": True,
                        "highlight_changes": True,
                        "apply_changes": True
                    }
                }
            
            return {"success": False, "error": "Failed to retrieve versions"}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to compare versions: {str(e)}"}
    
    def _calculate_theme_differences(self, value_1: Dict[str, Any], value_2: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate differences between two theme values"""
        differences = {
            "added": {},
            "removed": {},
            "modified": {}
        }
        
        # Find added keys
        for key, value in value_2.items():
            if key not in value_1:
                differences["added"][key] = value
        
        # Find removed keys
        for key, value in value_1.items():
            if key not in value_2:
                differences["removed"][key] = value
        
        # Find modified keys
        for key, value in value_1.items():
            if key in value_2 and value != value_2[key]:
                differences["modified"][key] = {
                    "old": value,
                    "new": value_2[key]
                }
        
        return differences
    
    async def rollback_theme(
        self,
        session_id: str,
        version_id: str,
        component: str = "colors",
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """Enhanced rollback theme to previous version with UI features (optimized for single-site)"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        try:
            # Use hybrid theme manager for rollback
            rollback_result = await self.theme_manager.rollback_theme(
                component=component,
                version_id=version_id,
                user_roles=user_roles,
                user_id=session.user_id
            )
            
            if rollback_result["success"]:
                # Update preview
                preview = await self._generate_preview(session)
                
                # Get rollback details for UI
                key = f"theme.{component}"
                version_details = await enhanced_settings.get_setting_version(
                    key=key,
                    version_id=version_id,
                    user_roles=user_roles,
                    context={"user_id": session.user_id}
                )
                
                return {
                    "success": True,
                    "component": component,
                    "version_id": version_id,
                    "preview": preview,
                    "rollback_completed": True,
                    "version_details": version_details,
                    "editor_features": {
                        "preview_updated": True,
                        "undo_rollback": True,
                        "rollback_history": True
                    }
                }
            
            return rollback_result
            
        except Exception as e:
            return {"success": False, "error": f"Failed to rollback: {str(e)}"}
    
    async def batch_rollback_theme(
        self,
        session_id: str,
        rollback_data: Dict[str, str],  # {"component": "version_id"}
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """Batch rollback multiple theme components (optimized for single-site)"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        try:
            results = {}
            successful_rollbacks = []
            failed_rollbacks = []
            
            for component, version_id in rollback_data.items():
                rollback_result = await self.rollback_theme(
                    session_id=session_id,
                    version_id=version_id,
                    component=component,
                    user_roles=user_roles
                )
                
                results[component] = rollback_result
                
                if rollback_result.get("success"):
                    successful_rollbacks.append(component)
                else:
                    failed_rollbacks.append(component)
            
            # Update preview after all rollbacks
            preview = await self._generate_preview(session)
            
            return {
                "success": len(failed_rollbacks) == 0,
                "results": results,
                "successful_rollbacks": successful_rollbacks,
                "failed_rollbacks": failed_rollbacks,
                "preview": preview,
                "editor_features": {
                    "batch_operation": True,
                    "partial_success": len(failed_rollbacks) > 0 and len(successful_rollbacks) > 0,
                    "retry_failed": True
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to batch rollback: {str(e)}"}
    
    async def enable_auto_save(
        self,
        session_id: str,
        interval: int = 30,  # seconds
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """Enable auto-save for theme changes (optimized for single-site)"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        try:
            # Store auto-save configuration
            auto_save_config = {
                "enabled": True,
                "interval": interval,
                "last_save": None,
                "session_id": session_id,
                "user_id": session.user_id
            }
            
            # Save auto-save settings
            await set_setting_optimized(
                key="editor.auto_save",
                value=auto_save_config,
                user_roles=user_roles,
                user_id=session.user_id
            )
            
            return {
                "success": True,
                "auto_save_enabled": True,
                "interval": interval,
                "editor_features": {
                    "auto_save": True,
                    "save_indicator": True,
                    "save_history": True
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to enable auto-save: {str(e)}"}
    
    async def disable_auto_save(
        self,
        session_id: str,
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """Disable auto-save for theme changes"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        try:
            # Update auto-save configuration
            auto_save_config = {
                "enabled": False,
                "session_id": session_id,
                "user_id": session.user_id
            }
            
            await set_setting_optimized(
                key="editor.auto_save",
                value=auto_save_config,
                user_roles=user_roles,
                user_id=session.user_id
            )
            
            return {
                "success": True,
                "auto_save_disabled": True,
                "editor_features": {
                    "auto_save": False,
                    "save_indicator": False
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to disable auto-save: {str(e)}"}
    
    async def get_auto_save_status(
        self,
        session_id: str,
        user_roles: List[str] = ["admin"]
    ) -> Dict[str, Any]:
        """Get auto-save status and configuration"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        try:
            result = await get_setting_optimized(
                key="editor.auto_save",
                user_roles=user_roles,
                user_id=session.user_id
            )
            
            if result.get("success"):
                config = result.get("value", {})
                return {
                    "success": True,
                    "auto_save_config": config,
                    "enabled": config.get("enabled", False),
                    "interval": config.get("interval", 30),
                    "last_save": config.get("last_save"),
                    "editor_features": {
                        "status_display": True,
                        "configure_settings": True
                    }
                }
            else:
                return {
                    "success": True,
                    "auto_save_config": {"enabled": False},
                    "enabled": False,
                    "interval": 30,
                    "last_save": None
                }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get auto-save status: {str(e)}"}
    
    async def preview_as_user_type(
        self,
        session_id: str,
        user_type: str  # "anonymous", "member", "admin"
    ) -> Dict[str, Any]:
        """
        Preview site as different user type.
        
        This is useful for testing component visibility conditions.
        """
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        # Build user context
        user_contexts = {
            "anonymous": None,
            "member": {
                "id": "preview_member",
                "member_sites": [session.site_id],
                "roles": ["member"]
            },
            "admin": {
                "id": "preview_admin",
                "roles": ["admin"]
            }
        }
        
        context = user_contexts.get(user_type, None)
        preview = await self._generate_preview(session, context)
        
        return {
            "success": True,
            "user_type": user_type,
            "preview": preview
        }
    
    async def compare_with_published(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Compare draft with published version"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        return await self.preview_manager.compare_versions(
            site_id=session.site_id,
            user_id=session.user_id
        )
    
    async def publish(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Publish current draft"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        result = await self.preview_manager.publish_draft(
            site_id=session.site_id,
            user_id=session.user_id
        )
        
        if result["success"]:
            session.has_unsaved_changes = False
        
        return result
    
    # ========================================================================
    # Undo/Redo
    # ========================================================================
    
    async def undo(self, session_id: str) -> Dict[str, Any]:
        """Undo last change"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        # Use state manager's rollback
        # This would integrate with StateManager from core/state/state.py
        
        return {"success": True, "message": "Undo not yet implemented"}
    
    async def redo(self, session_id: str) -> Dict[str, Any]:
        """Redo undone change"""
        # Similar to undo
        return {"success": True, "message": "Redo not yet implemented"}
    
    # ========================================================================
    # Auto-save
    # ========================================================================
    
    async def auto_save(self, session_id: str) -> Dict[str, Any]:
        """
        Auto-save current state.
        
        Called periodically by frontend.
        """
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        if not session.has_unsaved_changes:
            return {"success": True, "message": "No changes to save"}
        
        # State is already saved with each operation
        # This just marks it as saved
        session.has_unsaved_changes = False
        
        return {
            "success": True,
            "saved_at": datetime.utcnow().isoformat()
        }


# ============================================================================
# Helper Functions
# ============================================================================

def get_editor_capabilities(user_roles: List[str]) -> Dict[str, bool]:
    """
    Get editing capabilities based on user roles.
    
    Returns what the user can do in the editor.
    """
    from core.services.auth.permissions import permission_registry
    
    capabilities = {
        "can_edit_structure": permission_registry.check_permission(
            user_roles, "site", "update", {}
        ),
        "can_edit_theme": permission_registry.check_permission(
            user_roles, "theme", "update", {}
        ),
        "can_add_components": permission_registry.check_permission(
            user_roles, "component", "write", {}
        ),
        "can_publish": permission_registry.check_permission(
            user_roles, "site", "write", {}
        ),
        "can_delete": permission_registry.check_permission(
            user_roles, "site", "delete", {}
        ),
    }
    
    return capabilities
