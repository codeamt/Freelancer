"""
Landing Page Base Class

Abstract base class for all landing pages and example apps.
Provides interface integration with state system, workflows, and theme editor.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from fasthtml.common import Div
from core.ui.layout import Layout


@dataclass
class Section:
    """Represents a section in the landing page."""
    id: str
    type: str
    title: str
    content: Any
    order: int = 0
    visible: bool = True
    addon_type: Optional[str] = None  # Which addon this section belongs to
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SiteGraph:
    """Represents the site structure and sections."""
    sections: List[Section] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_section(self, section: Section):
        """Add a section to the site graph."""
        self.sections.append(section)
        self.sections.sort(key=lambda s: s.order)
    
    def get_section(self, section_id: str) -> Optional[Section]:
        """Get a section by ID."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None
    
    def remove_section(self, section_id: str) -> bool:
        """Remove a section by ID."""
        for i, section in enumerate(self.sections):
            if section.id == section_id:
                del self.sections[i]
                return True
        return False
    
    def reorder_section(self, section_id: str, new_order: int) -> bool:
        """Reorder a section."""
        section = self.get_section(section_id)
        if section:
            section.order = new_order
            self.sections.sort(key=lambda s: s.order)
            return True
        return False


@dataclass
class ThemeStyles:
    """Represents the theme styles for the landing page."""
    colors: Dict[str, str] = field(default_factory=dict)
    typography: Dict[str, str] = field(default_factory=dict)
    spacing: Dict[str, str] = field(default_factory=dict)
    custom_css: str = ""
    
    def to_css_string(self) -> str:
        """Convert theme styles to CSS string."""
        css_parts = []
        
        if self.colors:
            css_parts.append("/* Colors */")
            for key, value in self.colors.items():
                css_parts.append(f"  --{key}: {value};")
        
        if self.typography:
            css_parts.append("/* Typography */")
            for key, value in self.typography.items():
                css_parts.append(f"  --{key}: {value};")
        
        if self.spacing:
            css_parts.append("/* Spacing */")
            for key, value in self.spacing.items():
                css_parts.append(f"  --{key}: {value};")
        
        if self.custom_css:
            css_parts.append("/* Custom CSS */")
            css_parts.append(self.custom_css)
        
        return "\n".join(css_parts)


class LandingPage(ABC):
    """
    Abstract base class for all landing pages and example apps.
    
    This class provides the interface for:
    - State system integration (core/state)
    - Workflow management (core/workflows) 
    - Theme editor integration (core/ui/theme)
    - Omniview editing experience in admin dashboard
    """
    
    def __init__(self, site_id: str = "main"):
        self.site_id = site_id
        self.site_graph = SiteGraph()
        self.theme_styles = ThemeStyles()
        self.addons: Dict[str, Any] = {}
        self._is_dirty = False
    
    @abstractmethod
    def render_content(self) -> Div:
        """
        Render the main content of the landing page.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def get_default_sections(self) -> List[Section]:
        """
        Get the default sections for this landing page type.
        Must be implemented by subclasses.
        """
        pass
    
    def render(self, request=None, preview_mode: bool = False) -> Layout:
        """
        Render the complete landing page wrapped in Layout.
        """
        content = self.render_content()
        
        # Add theme styles if not in preview mode
        if not preview_mode and self.theme_styles.to_css_string():
            content = Div(
                Style(f":root {{\n{self.theme_styles.to_css_string()}\n}}"),
                content
            )
        
        # Get user info for layout if request is available
        user = getattr(request.state, 'user', None) if request else None
        user_dict = self._get_user_dict(user) if user else None
        
        return Layout(
            content,
            title=self.get_title(),
            current_path="/",
            user=user_dict,
            show_auth=False,
            demo=getattr(request.app.state, 'demo', False) if request else False
        )
    
    def get_title(self) -> str:
        """Get the page title."""
        return "Landing Page"
    
    def add_section(self, section: Section) -> None:
        """Add a section to the landing page."""
        self.site_graph.add_section(section)
        self._is_dirty = True
    
    def remove_section(self, section_id: str) -> bool:
        """Remove a section from the landing page."""
        result = self.site_graph.remove_section(section_id)
        if result:
            self._is_dirty = True
        return result
    
    def update_section(self, section_id: str, **kwargs) -> bool:
        """Update a section's properties."""
        section = self.site_graph.get_section(section_id)
        if section:
            for key, value in kwargs.items():
                if hasattr(section, key):
                    setattr(section, key, value)
                    self._is_dirty = True
            return True
        return False
    
    def update_theme(self, **kwargs) -> None:
        """Update theme styles."""
        for key, value in kwargs.items():
            if hasattr(self.theme_styles, key):
                setattr(self.theme_styles, key, value)
                self._is_dirty = True
    
    def add_addon(self, addon_name: str, addon_config: Dict[str, Any]) -> None:
        """Add an addon configuration."""
        self.addons[addon_name] = addon_config
        self._is_dirty = True
    
    def remove_addon(self, addon_name: str) -> bool:
        """Remove an addon configuration."""
        if addon_name in self.addons:
            del self.addons[addon_name]
            self._is_dirty = True
            return True
        return False
    
    def get_addon_sections(self, addon_name: str) -> List[Section]:
        """Get all sections belonging to a specific addon."""
        return [s for s in self.site_graph.sections if s.addon_type == addon_name]
    
    def is_dirty(self) -> bool:
        """Check if the page has unsaved changes."""
        return self._is_dirty
    
    def mark_clean(self) -> None:
        """Mark the page as clean (no unsaved changes)."""
        self._is_dirty = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert landing page to dictionary for storage."""
        return {
            "site_id": self.site_id,
            "site_graph": {
                "sections": [
                    {
                        "id": s.id,
                        "type": s.type,
                        "title": s.title,
                        "content": s.content,
                        "order": s.order,
                        "visible": s.visible,
                        "addon_type": s.addon_type,
                        "config": s.config
                    }
                    for s in self.site_graph.sections
                ],
                "metadata": self.site_graph.metadata
            },
            "theme_styles": {
                "colors": self.theme_styles.colors,
                "typography": self.theme_styles.typography,
                "spacing": self.theme_styles.spacing,
                "custom_css": self.theme_styles.custom_css
            },
            "addons": self.addons
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load landing page from dictionary."""
        # Load site graph
        if "site_graph" in data:
            self.site_graph = SiteGraph()
            for section_data in data["site_graph"].get("sections", []):
                section = Section(
                    id=section_data["id"],
                    type=section_data["type"],
                    title=section_data["title"],
                    content=section_data["content"],
                    order=section_data.get("order", 0),
                    visible=section_data.get("visible", True),
                    addon_type=section_data.get("addon_type"),
                    config=section_data.get("config", {})
                )
                self.site_graph.add_section(section)
            
            self.site_graph.metadata = data["site_graph"].get("metadata", {})
        
        # Load theme styles
        if "theme_styles" in data:
            theme_data = data["theme_styles"]
            self.theme_styles = ThemeStyles(
                colors=theme_data.get("colors", {}),
                typography=theme_data.get("typography", {}),
                spacing=theme_data.get("spacing", {}),
                custom_css=theme_data.get("custom_css", "")
            )
        
        # Load addons
        self.addons = data.get("addons", {})
        self._is_dirty = False
    
    def _get_user_dict(self, user) -> Optional[Dict[str, Any]]:
        """Convert user object to dictionary for Layout."""
        if not user:
            return None
        
        return {
            "id": getattr(user, "id", None),
            "email": getattr(user, "email", None),
            "role": getattr(user, "role", None),
            "display_name": getattr(user, "display_name", None)
        }
