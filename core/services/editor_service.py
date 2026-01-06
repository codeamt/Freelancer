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
from core.ui.theme.editor import ThemeEditorManager
from core.ui.state.factory import EnhancedComponentLibrary, SectionRenderer
from core.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Editor State
# ============================================================================

@dataclass
class EditorSession:
    """Represents an active editing session"""
    session_id: str
    site_id: str
    user_id: str
    started_at: datetime
    last_activity: datetime
    
    # Current state
    current_panel: str = "structure"  # "structure", "theme", "preview"
    selected_section: Optional[str] = None
    selected_component: Optional[str] = None
    
    # Undo/Redo
    history: List[Dict[str, Any]] = field(default_factory=list)
    history_index: int = -1
    
    # Unsaved changes
    has_unsaved_changes: bool = False


class EditorStateManager:
    """Manages editor state separate from site state"""
    
    def __init__(self):
        self.active_sessions: Dict[str, EditorSession] = {}
    
    def create_session(
        self,
        site_id: str,
        user_id: str
    ) -> EditorSession:
        """Create new editing session"""
        import uuid
        session_id = str(uuid.uuid4())
        
        session = EditorSession(
            session_id=session_id,
            site_id=site_id,
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
    
    def __init__(self, persister):
        """
        Initialize omniview editor.
        
        Args:
            persister: State persistence backend
        """
        self.persister = persister
        
        # Core managers
        self.site_manager = SiteWorkflowManager(persister=persister)
        self.theme_manager = ThemeEditorManager(persister=persister)
        self.preview_manager = PreviewPublishManager(persister=persister)
        self.component_library = EnhancedComponentLibrary()
        
        # Editor state
        self.editor_state = EditorStateManager()
    
    # ========================================================================
    # Session Management
    # ========================================================================
    
    async def start_editing(
        self,
        site_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Start editing session for a site.
        
        Returns full editor state including:
        - Site structure
        - Theme configuration
        - Available components
        - User permissions
        """
        # Create session
        session = self.editor_state.create_session(site_id, user_id)
        
        # Load site state
        site_result = await self.site_manager.load_site(site_id, user_id)
        if not site_result["success"]:
            return {"success": False, "error": site_result.get("error")}
        
        # Load theme
        theme_state = await self.persister.load(f"theme_{site_id}", f"user:{user_id}")
        
        # Get available components
        component_templates = self.component_library.get_all_templates()
        
        # Get version history
        history = await self.preview_manager.get_version_history(site_id, user_id)
        
        return {
            "success": True,
            "session_id": session.session_id,
            "site_state": site_result["state"],
            "theme_state": theme_state.get("theme_state") if theme_state else {},
            "component_templates": component_templates,
            "version_history": history.get("history", []) if history["success"] else [],
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
        colors: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Update theme colors in real-time.
        
        This updates theme and regenerates preview immediately.
        """
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        result = await self.theme_manager.update_theme_colors(
            site_id=session.site_id,
            colors=colors,
            user_id=session.user_id
        )
        
        if result["success"]:
            session.has_unsaved_changes = True
            
            # Generate preview with new theme
            preview = await self._generate_preview(session)
            
            return {
                "success": True,
                "theme_css": result.get("theme_css"),
                "preview": preview
            }
        
        return result
    
    async def apply_theme_preset(
        self,
        session_id: str,
        preset_name: str
    ) -> Dict[str, Any]:
        """Apply theme preset"""
        session = self.editor_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Invalid session"}
        
        result = await self.theme_manager.apply_preset(
            site_id=session.site_id,
            preset=preset_name,
            user_id=session.user_id
        )
        
        if result["success"]:
            session.has_unsaved_changes = True
            preview = await self._generate_preview(session)
            
            return {
                "success": True,
                "theme_state": result.get("theme_state"),
                "preview": preview
            }
        
        return result
    
    # ========================================================================
    # Preview & Publishing
    # ========================================================================
    
    async def _generate_preview(
        self,
        session: EditorSession,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate preview for current state"""
        result = await self.preview_manager.generate_preview(
            site_id=session.site_id,
            user_context=user_context,
            user_id=session.user_id
        )
        
        return result.get("preview_data") if result["success"] else {}
    
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
