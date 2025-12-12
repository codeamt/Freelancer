"""
Actions for site state management - Burr-inspired action system.

Actions are the building blocks of workflows. They read from and write to state.
"""

from typing import List, Dict, Any, Optional, Callable, Tuple, TYPE_CHECKING
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .state import State
from core.utils.logger import get_logger

if TYPE_CHECKING:
    from core.di.container import ExecutionContext

logger = get_logger(__name__)


@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Action(ABC):
    """
    Base action class for state machine nodes.
    
    Actions define what can be done at each node in the workflow.
    They specify what they read from state and what they write to state.
    """
    
    def __init__(self, name: str, reads: List[str], writes: List[str]):
        """
        Initialize action.
        
        Args:
            name: Unique name for this action
            reads: List of state keys this action reads
            writes: List of state keys this action writes
        """
        self.name = name
        self.reads = reads
        self.writes = writes
    
    @abstractmethod
    async def run(
        self, 
        state: State, 
        context: Optional['ExecutionContext'] = None,
        **inputs
    ) -> ActionResult:
        """
        Execute the action.
        
        Args:
            state: Current state (subset to self.reads)
            context: Optional execution context with user permissions and services
            **inputs: Additional runtime inputs
            
        Returns:
            ActionResult with success status and optional data
        """
        pass
    
    def update(self, result: ActionResult, state: State) -> State:
        """
        Update state based on action result.
        
        This is called automatically after run() succeeds.
        
        Args:
            result: Result from run()
            state: Current state
            
        Returns:
            Updated state
        """
        if result.success and result.data:
            return state.update(**result.data)
        return state
    
    async def execute(
        self, 
        state: State, 
        context: Optional['ExecutionContext'] = None,
        **inputs
    ) -> Tuple[State, ActionResult]:
        """
        Execute action and update state.
        
        Args:
            state: Full current state
            context: Optional execution context with user permissions and services
            **inputs: Runtime inputs
            
        Returns:
            Tuple of (new_state, result)
        """
        try:
            # Subset state to only what action reads
            read_state = state.subset(self.reads) if self.reads else state
            
            # Run the action with context
            result = await self.run(read_state, context, **inputs)
            
            # Update state if successful
            if result.success:
                new_state = self.update(result, state)
                logger.info(f"Action '{self.name}' succeeded: {result.message}")
                return new_state, result
            else:
                logger.warning(f"Action '{self.name}' failed: {result.error}")
                return state, result
                
        except Exception as e:
            logger.error(f"Action '{self.name}' raised exception: {e}")
            return state, ActionResult(success=False, error=str(e))
    
    def __repr__(self) -> str:
        return f"Action(name='{self.name}', reads={self.reads}, writes={self.writes})"


# ============================================================================
# Site Management Actions
# ============================================================================

class InitializeSiteAction(Action):
    """Initialize a new site configuration."""
    
    def __init__(self):
        super().__init__(
            name="initialize_site",
            reads=[],
            writes=["site_id", "site_graph", "theme_state", "settings", "created_at"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Initialize site with default configuration."""
        from datetime import datetime
        import uuid
        
        site_id = inputs.get("site_id", str(uuid.uuid4()))
        site_name = inputs.get("site_name", "New Site")
        
        return ActionResult(
            success=True,
            message=f"Site '{site_name}' initialized",
            data={
                "site_id": site_id,
                "site_name": site_name,
                "site_graph": {
                    "sections": [],
                    "connections": {}
                },
                "theme_state": {
                    "theme": "slate",
                    "custom_css": "",
                    "fonts": {}
                },
                "settings": {
                    "integrations": {},
                    "seo": {},
                    "analytics": {}
                },
                "created_at": datetime.utcnow().isoformat(),
                "status": "draft"
            }
        )


class AddSectionAction(Action):
    """Add a new section to the site graph."""
    
    def __init__(self):
        super().__init__(
            name="add_section",
            reads=["site_graph"],
            writes=["site_graph"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Add section to site graph."""
        section_id = inputs.get("section_id")
        section_type = inputs.get("section_type")
        section_data = inputs.get("section_data", {})
        
        if not section_id or not section_type:
            return ActionResult(
                success=False,
                error="section_id and section_type are required"
            )
        
        site_graph = state.get("site_graph", {"sections": [], "connections": {}})
        
        # Check if section already exists
        if any(s["id"] == section_id for s in site_graph["sections"]):
            return ActionResult(
                success=False,
                error=f"Section '{section_id}' already exists"
            )
        
        # Add new section
        new_section = {
            "id": section_id,
            "type": section_type,
            "order": len(site_graph["sections"]),
            **section_data
        }
        site_graph["sections"].append(new_section)
        
        return ActionResult(
            success=True,
            message=f"Section '{section_id}' added",
            data={"site_graph": site_graph}
        )


class RemoveSectionAction(Action):
    """Remove a section from the site graph."""
    
    def __init__(self):
        super().__init__(
            name="remove_section",
            reads=["site_graph"],
            writes=["site_graph"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Remove section from site graph."""
        section_id = inputs.get("section_id")
        
        if not section_id:
            return ActionResult(success=False, error="section_id is required")
        
        site_graph = state.get("site_graph", {"sections": [], "connections": {}})
        
        # Remove section
        original_len = len(site_graph["sections"])
        site_graph["sections"] = [s for s in site_graph["sections"] if s["id"] != section_id]
        
        if len(site_graph["sections"]) == original_len:
            return ActionResult(
                success=False,
                error=f"Section '{section_id}' not found"
            )
        
        # Remove connections
        if section_id in site_graph["connections"]:
            del site_graph["connections"][section_id]
        for conns in site_graph["connections"].values():
            if section_id in conns:
                conns.remove(section_id)
        
        return ActionResult(
            success=True,
            message=f"Section '{section_id}' removed",
            data={"site_graph": site_graph}
        )


class ReorderSectionsAction(Action):
    """Reorder sections in the site graph."""
    
    def __init__(self):
        super().__init__(
            name="reorder_sections",
            reads=["site_graph"],
            writes=["site_graph"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Reorder sections."""
        new_order = inputs.get("order")  # List of section IDs in new order
        
        if not new_order or not isinstance(new_order, list):
            return ActionResult(success=False, error="order must be a list of section IDs")
        
        site_graph = state.get("site_graph", {"sections": [], "connections": {}})
        
        # Create lookup
        section_map = {s["id"]: s for s in site_graph["sections"]}
        
        # Validate all IDs exist
        if set(new_order) != set(section_map.keys()):
            return ActionResult(success=False, error="order must contain all section IDs")
        
        # Reorder and update order property
        site_graph["sections"] = [section_map[sid] for sid in new_order]
        for i, section in enumerate(site_graph["sections"]):
            section["order"] = i
        
        return ActionResult(
            success=True,
            message="Sections reordered",
            data={"site_graph": site_graph}
        )


class UpdateThemeAction(Action):
    """Update site theme configuration."""
    
    def __init__(self):
        super().__init__(
            name="update_theme",
            reads=["theme_state"],
            writes=["theme_state"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Update theme state."""
        theme_updates = inputs.get("theme_updates", {})
        
        if not theme_updates:
            return ActionResult(success=False, error="theme_updates required")
        
        theme_state = state.get("theme_state", {})
        theme_state.update(theme_updates)
        
        return ActionResult(
            success=True,
            message="Theme updated",
            data={"theme_state": theme_state}
        )


class UpdateSettingsAction(Action):
    """Update site settings and integrations."""
    
    def __init__(self):
        super().__init__(
            name="update_settings",
            reads=["settings"],
            writes=["settings"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Update settings."""
        settings_updates = inputs.get("settings_updates", {})
        
        if not settings_updates:
            return ActionResult(success=False, error="settings_updates required")
        
        settings = state.get("settings", {})
        
        # Deep merge for nested settings
        for key, value in settings_updates.items():
            if isinstance(value, dict) and key in settings and isinstance(settings[key], dict):
                settings[key].update(value)
            else:
                settings[key] = value
        
        return ActionResult(
            success=True,
            message="Settings updated",
            data={"settings": settings}
        )


class PublishSiteAction(Action):
    """Publish site (change status to published)."""
    
    def __init__(self):
        super().__init__(
            name="publish_site",
            reads=["site_graph", "status"],
            writes=["status", "published_at"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Publish the site."""
        from datetime import datetime
        
        site_graph = state.get("site_graph", {"sections": []})
        
        # Validate site has sections
        if not site_graph["sections"]:
            return ActionResult(
                success=False,
                error="Cannot publish site with no sections"
            )
        
        return ActionResult(
            success=True,
            message="Site published",
            data={
                "status": "published",
                "published_at": datetime.utcnow().isoformat()
            }
        )


class UnpublishSiteAction(Action):
    """Unpublish site (change status to draft)."""
    
    def __init__(self):
        super().__init__(
            name="unpublish_site",
            reads=["status"],
            writes=["status"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Unpublish the site."""
        return ActionResult(
            success=True,
            message="Site unpublished",
            data={"status": "draft"}
        )


class ValidateSiteAction(Action):
    """Validate site configuration."""
    
    def __init__(self):
        super().__init__(
            name="validate_site",
            reads=["site_graph", "theme_state", "settings"],
            writes=["validation_errors"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Validate site configuration."""
        errors = []
        
        site_graph = state.get("site_graph", {})
        theme_state = state.get("theme_state", {})
        settings = state.get("settings", {})
        
        # Validate site graph
        if not site_graph.get("sections"):
            errors.append("Site must have at least one section")
        
        # Validate theme
        if not theme_state.get("theme"):
            errors.append("Theme must be specified")
        
        # Validate required settings
        # Add more validation as needed
        
        if errors:
            return ActionResult(
                success=False,
                error="Validation failed",
                data={"validation_errors": errors}
            )
        
        return ActionResult(
            success=True,
            message="Site validation passed",
            data={"validation_errors": []}
        )