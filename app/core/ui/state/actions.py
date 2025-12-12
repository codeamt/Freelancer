from typing import Dict, Any, List, Optional, TYPE_CHECKING
from core.state.actions import Action, ActionResult
from core.state.state import State

if TYPE_CHECKING:
    from .config import ComponentConfig


class AddComponentAction(Action):
    """Add a component to a section."""
    
    def __init__(self):
        super().__init__(
            name="add_component",
            reads=["site_graph"],
            writes=["site_graph"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Add component to section."""
        section_id = inputs.get("section_id")
        component_config = inputs.get("component_config")
        
        if not section_id or not component_config:
            return ActionResult(
                success=False,
                error="section_id and component_config are required"
            )
        
        site_graph = state.get("site_graph", {"sections": []})
        
        # Find section
        section = None
        for s in site_graph["sections"]:
            if s["id"] == section_id:
                section = s
                break
        
        if not section:
            return ActionResult(
                success=False,
                error=f"Section '{section_id}' not found"
            )
        
        # Initialize components list if needed
        if "components" not in section:
            section["components"] = []
        
        # Check for duplicate component ID
        if any(c["id"] == component_config["id"] for c in section["components"]):
            return ActionResult(
                success=False,
                error=f"Component '{component_config['id']}' already exists in section"
            )
        
        # Add component
        section["components"].append(component_config)
        
        return ActionResult(
            success=True,
            message=f"Component '{component_config['id']}' added to section '{section_id}'",
            data={"site_graph": site_graph}
        )


class RemoveComponentAction(Action):
    """Remove a component from a section."""
    
    def __init__(self):
        super().__init__(
            name="remove_component",
            reads=["site_graph"],
            writes=["site_graph"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Remove component from section."""
        section_id = inputs.get("section_id")
        component_id = inputs.get("component_id")
        
        if not section_id or not component_id:
            return ActionResult(
                success=False,
                error="section_id and component_id are required"
            )
        
        site_graph = state.get("site_graph", {"sections": []})
        
        # Find section
        section = None
        for s in site_graph["sections"]:
            if s["id"] == section_id:
                section = s
                break
        
        if not section:
            return ActionResult(
                success=False,
                error=f"Section '{section_id}' not found"
            )
        
        if "components" not in section:
            return ActionResult(
                success=False,
                error=f"Section '{section_id}' has no components"
            )
        
        # Remove component
        original_len = len(section["components"])
        section["components"] = [c for c in section["components"] if c["id"] != component_id]
        
        if len(section["components"]) == original_len:
            return ActionResult(
                success=False,
                error=f"Component '{component_id}' not found in section"
            )
        
        return ActionResult(
            success=True,
            message=f"Component '{component_id}' removed from section '{section_id}'",
            data={"site_graph": site_graph}
        )


class UpdateComponentAction(Action):
    """Update a component's configuration."""
    
    def __init__(self):
        super().__init__(
            name="update_component",
            reads=["site_graph"],
            writes=["site_graph"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Update component configuration."""
        section_id = inputs.get("section_id")
        component_id = inputs.get("component_id")
        updates = inputs.get("updates")
        
        if not section_id or not component_id or not updates:
            return ActionResult(
                success=False,
                error="section_id, component_id, and updates are required"
            )
        
        site_graph = state.get("site_graph", {"sections": []})
        
        # Find section
        section = None
        for s in site_graph["sections"]:
            if s["id"] == section_id:
                section = s
                break
        
        if not section or "components" not in section:
            return ActionResult(
                success=False,
                error=f"Section '{section_id}' not found or has no components"
            )
        
        # Find and update component
        component = None
        for c in section["components"]:
            if c["id"] == component_id:
                component = c
                break
        
        if not component:
            return ActionResult(
                success=False,
                error=f"Component '{component_id}' not found"
            )
        
        # Apply updates
        for key, value in updates.items():
            if key in ["content", "styles", "visibility_params"]:
                # Deep merge for nested dicts
                if key not in component:
                    component[key] = {}
                component[key].update(value)
            else:
                component[key] = value
        
        return ActionResult(
            success=True,
            message=f"Component '{component_id}' updated",
            data={"site_graph": site_graph}
        )


class ToggleComponentAction(Action):
    """Toggle a component's enabled state."""
    
    def __init__(self):
        super().__init__(
            name="toggle_component",
            reads=["site_graph"],
            writes=["site_graph"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Toggle component enabled state."""
        section_id = inputs.get("section_id")
        component_id = inputs.get("component_id")
        enabled = inputs.get("enabled")
        
        if not section_id or not component_id:
            return ActionResult(
                success=False,
                error="section_id and component_id are required"
            )
        
        site_graph = state.get("site_graph", {"sections": []})
        
        # Find component
        for section in site_graph["sections"]:
            if section["id"] == section_id and "components" in section:
                for component in section["components"]:
                    if component["id"] == component_id:
                        # Toggle if enabled not specified
                        if enabled is None:
                            component["enabled"] = not component.get("enabled", True)
                        else:
                            component["enabled"] = enabled
                        
                        return ActionResult(
                            success=True,
                            message=f"Component '{component_id}' {'enabled' if component['enabled'] else 'disabled'}",
                            data={"site_graph": site_graph}
                        )
        
        return ActionResult(
            success=False,
            error=f"Component '{component_id}' not found in section '{section_id}'"
        )


class SetComponentVisibilityAction(Action):
    """Set component visibility conditions."""
    
    def __init__(self):
        super().__init__(
            name="set_component_visibility",
            reads=["site_graph"],
            writes=["site_graph"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Set component visibility."""
        section_id = inputs.get("section_id")
        component_id = inputs.get("component_id")
        visibility = inputs.get("visibility")
        visibility_params = inputs.get("visibility_params", {})
        
        if not section_id or not component_id or not visibility:
            return ActionResult(
                success=False,
                error="section_id, component_id, and visibility are required"
            )
        
        # Validate visibility value
        try:
            visibility_enum = VisibilityCondition(visibility)
        except ValueError:
            return ActionResult(
                success=False,
                error=f"Invalid visibility condition: {visibility}"
            )
        
        site_graph = state.get("site_graph", {"sections": []})
        
        # Find and update component
        for section in site_graph["sections"]:
            if section["id"] == section_id and "components" in section:
                for component in section["components"]:
                    if component["id"] == component_id:
                        component["visibility"] = visibility
                        component["visibility_params"] = visibility_params
                        
                        return ActionResult(
                            success=True,
                            message=f"Component '{component_id}' visibility set to '{visibility}'",
                            data={"site_graph": site_graph}
                        )
        
        return ActionResult(
            success=False,
            error=f"Component '{component_id}' not found in section '{section_id}'"
        )


# ============================================================================
# Component Rendering Utilities
# ============================================================================

def render_section_components(
    section: Dict[str, Any],
    user: Optional[Dict[str, Any]] = None
) -> List["ComponentConfig"]:
    """
    Get renderable components for a section.
    
    Args:
        section: Section dictionary with components
        user: Current user context
        
    Returns:
        List of ComponentConfig instances that should be rendered
    """
    components = section.get("components", [])
    renderable = []
    
    for comp_data in components:
        component = ComponentConfig.from_dict(comp_data)
        if component.should_render(user):
            renderable.append(component)
    
    # Sort by order
    renderable.sort(key=lambda c: c.order)
    
    return renderable


def get_site_components_summary(site_graph: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get summary of all components in site.
    
    Args:
        site_graph: Site graph with sections and components
        
    Returns:
        Dictionary with component statistics
    """
    sections = site_graph.get("sections", [])
    
    total_components = 0
    enabled_components = 0
    components_by_type = {}
    components_by_visibility = {}
    
    for section in sections:
        for comp_data in section.get("components", []):
            component = ComponentConfig.from_dict(comp_data)
            total_components += 1
            
            if component.enabled:
                enabled_components += 1
            
            # Count by type
            comp_type = component.type.value
            components_by_type[comp_type] = components_by_type.get(comp_type, 0) + 1
            
            # Count by visibility
            visibility = component.visibility.value
            components_by_visibility[visibility] = components_by_visibility.get(visibility, 0) + 1
    
    return {
        "total_components": total_components,
        "enabled_components": enabled_components,
        "disabled_components": total_components - enabled_components,
        "by_type": components_by_type,
        "by_visibility": components_by_visibility
    }