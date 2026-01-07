"""
Hybrid Theme Manager - Theme Management with Hybrid Settings Integration

Replaces the original ThemeEditorManager with persistent storage,
version tracking, and single-site optimization using the hybrid settings system.

Benefits:
- Persistent theme storage (no more state-only)
- Version tracking and rollback
- Performance caching
- Single-site optimization
- Unified settings API
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from core.services.settings import (
    get_theme_settings_optimized,
    set_setting_optimized,
    set_setting_with_version,
    enhanced_settings
)
from core.ui.theme.editor import ColorScheme, Typography, Spacing
from core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ThemeState:
    """Complete theme state with all components"""
    colors: ColorScheme
    typography: Typography
    spacing: Spacing
    custom_css: str = ""
    version: Optional[str] = None
    last_modified: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "colors": self.colors.to_dict(),
            "typography": self.typography.to_dict(),
            "spacing": self.spacing.to_dict(),
            "custom_css": self.custom_css,
            "version": self.version,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThemeState":
        return cls(
            colors=ColorScheme(**data.get("colors", {})),
            typography=Typography(**data.get("typography", {})),
            spacing=Spacing(**data.get("spacing", {})),
            custom_css=data.get("custom_css", ""),
            version=data.get("version"),
            last_modified=datetime.fromisoformat(data["last_modified"]) if data.get("last_modified") else None
        )


class HybridThemeManager:
    """
    Theme manager with hybrid settings integration (optimized for single-site).
    
    Replaces ThemeEditorManager with persistent storage and version tracking.
    """
    
    def __init__(self):
        """Initialize hybrid theme manager"""
        self.presets = self._load_presets()
    
    def _load_presets(self) -> Dict[str, Dict[str, Any]]:
        """Load theme presets"""
        return {
            "modern": {
                "colors": {
                    "primary": "#3b82f6",
                    "secondary": "#8b5cf6",
                    "accent": "#ec4899",
                    "neutral": "#6b7280",
                    "base_100": "#ffffff",
                    "base_200": "#f3f4f6",
                    "base_300": "#e5e7eb",
                    "info": "#3abff8",
                    "success": "#36d399",
                    "warning": "#fbbd23",
                    "error": "#f87272"
                },
                "typography": {
                    "font_family_primary": "Inter, system-ui, sans-serif",
                    "font_family_secondary": "Georgia, serif",
                    "font_size_base": "16px",
                    "line_height_base": 1.6
                },
                "spacing": {
                    "container_max_width": "1280px",
                    "section_padding": "4rem",
                    "element_gap": "1rem"
                }
            },
            "ocean": {
                "colors": {
                    "primary": "#0077be",
                    "secondary": "#004d7a",
                    "accent": "#00a8cc",
                    "neutral": "#2c3e50",
                    "base_100": "#ffffff",
                    "base_200": "#f0f9ff",
                    "base_300": "#e0f2fe",
                    "info": "#0ea5e9",
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444"
                },
                "typography": {
                    "font_family_primary": "Inter, system-ui, sans-serif",
                    "font_family_secondary": "Merriweather, serif",
                    "font_size_base": "16px",
                    "line_height_base": 1.7
                },
                "spacing": {
                    "container_max_width": "1200px",
                    "section_padding": "3.5rem",
                    "element_gap": "1.25rem"
                }
            },
            "forest": {
                "colors": {
                    "primary": "#27ae60",
                    "secondary": "#229954",
                    "accent": "#52be80",
                    "neutral": "#1e5128",
                    "base_100": "#ffffff",
                    "base_200": "#f0fdf4",
                    "base_300": "#dcfce7",
                    "info": "#06b6d4",
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444"
                },
                "typography": {
                    "font_family_primary": "Inter, system-ui, sans-serif",
                    "font_family_secondary": "Lora, serif",
                    "font_size_base": "16px",
                    "line_height_base": 1.65
                },
                "spacing": {
                    "container_max_width": "1152px",
                    "section_padding": "3rem",
                    "element_gap": "1.5rem"
                }
            }
        }
    
    async def initialize_theme(
        self,
        preset: str = "modern",
        user_roles: List[str] = ["admin"],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize theme with preset (optimized for single-site).
        
        Args:
            preset: Theme preset name
            user_roles: User roles for permissions
            user_id: User ID for context
            
        Returns:
            Theme initialization result
        """
        if preset not in self.presets:
            return {"success": False, "error": f"Preset '{preset}' not found"}
        
        preset_data = self.presets[preset]
        
        try:
            # Save theme components using hybrid settings
            results = {}
            
            # Save colors
            colors_result = await set_setting_with_version(
                key="theme.colors",
                value=preset_data["colors"],
                user_roles=user_roles,
                context={"user_id": user_id} if user_id else {},
                change_reason=f"Theme initialized with preset '{preset}'"
            )
            results["colors"] = colors_result
            
            # Save typography
            typography_result = await set_setting_with_version(
                key="theme.typography",
                value=preset_data["typography"],
                user_roles=user_roles,
                context={"user_id": user_id} if user_id else {},
                change_reason=f"Typography initialized with preset '{preset}'"
            )
            results["typography"] = typography_result
            
            # Save spacing
            spacing_result = await set_setting_with_version(
                key="theme.spacing",
                value=preset_data["spacing"],
                user_roles=user_roles,
                context={"user_id": user_id} if user_id else {},
                change_reason=f"Spacing initialized with preset '{preset}'"
            )
            results["spacing"] = spacing_result
            
            # Check if all saves succeeded
            all_success = all(result.get("success", False) for result in results.values())
            
            if all_success:
                theme_state = await self.get_complete_theme(user_roles, user_id)
                return {
                    "success": True,
                    "preset": preset,
                    "theme_state": theme_state,
                    "version_ids": {
                        "colors": results["colors"].get("version_id"),
                        "typography": results["typography"].get("version_id"),
                        "spacing": results["spacing"].get("version_id")
                    },
                    "persisted": True,
                    "cache_optimized": True
                }
            else:
                failed = [key for key, result in results.items() if not result.get("success", False)]
                return {
                    "success": False,
                    "error": f"Failed to save theme components: {', '.join(failed)}",
                    "results": results
                }
                
        except Exception as e:
            logger.error(f"Failed to initialize theme: {e}")
            return {"success": False, "error": f"Theme initialization failed: {str(e)}"}
    
    async def update_theme_colors(
        self,
        colors: Dict[str, str],
        user_roles: List[str] = ["admin"],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update theme colors with version tracking (optimized for single-site).
        
        Args:
            colors: Color scheme dictionary
            user_roles: User roles for permissions
            user_id: User ID for context
            
        Returns:
            Update result with version information
        """
        try:
            result = await set_setting_with_version(
                key="theme.colors",
                value=colors,
                user_roles=user_roles,
                context={"user_id": user_id} if user_id else {},
                change_reason=f"Theme colors updated by user {user_id}"
            )
            
            if result["success"]:
                # Generate CSS
                css = self._generate_theme_css(colors)
                
                return {
                    "success": True,
                    "colors": colors,
                    "version_id": result.get("version_id"),
                    "theme_css": css,
                    "persisted": True,
                    "cache_optimized": True
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update theme colors: {e}")
            return {"success": False, "error": f"Color update failed: {str(e)}"}
    
    async def apply_preset(
        self,
        preset: str,
        preserve_custom_css: bool = True,
        user_roles: List[str] = ["admin"],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply theme preset with version tracking (optimized for single-site).
        
        Args:
            preset: Preset name
            preserve_custom_css: Whether to preserve custom CSS
            user_roles: User roles for permissions
            user_id: User ID for context
            
        Returns:
            Preset application result
        """
        if preset not in self.presets:
            return {"success": False, "error": f"Preset '{preset}' not found"}
        
        preset_data = self.presets[preset]
        
        try:
            # Get current custom CSS if preserving
            current_css = ""
            if preserve_custom_css:
                current_theme = await self.get_complete_theme(user_roles, user_id)
                current_css = current_theme.get("custom_css", "")
            
            # Apply preset with version tracking
            results = {}
            
            # Update colors
            colors_result = await set_setting_with_version(
                key="theme.colors",
                value=preset_data["colors"],
                user_roles=user_roles,
                context={"user_id": user_id} if user_id else {},
                change_reason=f"Applied preset '{preset}'"
            )
            results["colors"] = colors_result
            
            # Update typography
            typography_result = await set_setting_with_version(
                key="theme.typography",
                value=preset_data["typography"],
                user_roles=user_roles,
                context={"user_id": user_id} if user_id else {},
                change_reason=f"Applied preset '{preset}'"
            )
            results["typography"] = typography_result
            
            # Update spacing
            spacing_result = await set_setting_with_version(
                key="theme.spacing",
                value=preset_data["spacing"],
                user_roles=user_roles,
                context={"user_id": user_id} if user_id else {},
                change_reason=f"Applied preset '{preset}'"
            )
            results["spacing"] = spacing_result
            
            # Restore custom CSS if preserving
            if preserve_custom_css and current_css:
                await set_setting_single_site(
                    key="theme.custom_css",
                    value=current_css,
                    user_roles=user_roles,
                    context={"user_id": user_id} if user_id else {}
                )
            
            all_success = all(result.get("success", False) for result in results.values())
            
            if all_success:
                theme_state = await self.get_complete_theme(user_roles, user_id)
                css = self._generate_theme_css(theme_state.get("colors", {}))
                
                return {
                    "success": True,
                    "preset": preset,
                    "theme_state": theme_state,
                    "theme_css": css,
                    "version_ids": {
                        "colors": results["colors"].get("version_id"),
                        "typography": results["typography"].get("version_id"),
                        "spacing": results["spacing"].get("version_id")
                    },
                    "persisted": True
                }
            else:
                failed = [key for key, result in results.items() if not result.get("success", False)]
                return {
                    "success": False,
                    "error": f"Failed to apply preset: {', '.join(failed)}",
                    "results": results
                }
                
        except Exception as e:
            logger.error(f"Failed to apply preset: {e}")
            return {"success": False, "error": f"Preset application failed: {str(e)}"}
    
    async def get_complete_theme(
        self,
        user_roles: List[str] = ["admin"],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get complete theme state (optimized for single-site).
        
        Args:
            user_roles: User roles for permissions
            user_id: User ID for context
            
        Returns:
            Complete theme state
        """
        try:
            theme_settings = await get_theme_settings_optimized(
                user_roles,
                {"user_id": user_id} if user_id else {}
            )
            
            # Extract theme components
            colors = theme_settings.get("theme.colors", {}).get("value", {})
            typography = theme_settings.get("theme.typography", {}).get("value", {})
            spacing = theme_settings.get("theme.spacing", {}).get("value", {})
            custom_css = theme_settings.get("theme.custom_css", {}).get("value", "")
            
            return {
                "colors": colors,
                "typography": typography,
                "spacing": spacing,
                "custom_css": custom_css,
                "loaded_from": "hybrid_settings",
                "cache_optimized": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get theme state: {e}")
            return {"error": f"Failed to load theme: {str(e)}"}
    
    async def get_theme_history(
        self,
        component: str = "colors",
        user_roles: List[str] = ["admin"],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get theme change history (optimized for single-site).
        
        Args:
            component: Theme component ("colors", "typography", "spacing")
            user_roles: User roles for permissions
            user_id: User ID for context
            
        Returns:
            Theme history
        """
        try:
            key = f"theme.{component}"
            history_result = await enhanced_settings.get_setting_history(
                key=key,
                user_roles=user_roles,
                context={"user_id": user_id} if user_id else {}
            )
            
            return history_result
            
        except Exception as e:
            logger.error(f"Failed to get theme history: {e}")
            return {"success": False, "error": f"History retrieval failed: {str(e)}"}
    
    async def rollback_theme(
        self,
        component: str,
        version_id: str,
        user_roles: List[str] = ["admin"],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rollback theme component to previous version (optimized for single-site).
        
        Args:
            component: Theme component to rollback
            version_id: Target version ID
            user_roles: User roles for permissions
            user_id: User ID for context
            
        Returns:
            Rollback result
        """
        try:
            key = f"theme.{component}"
            rollback_result = await enhanced_settings.rollback_setting(
                key=key,
                version_id=version_id,
                user_roles=user_roles,
                context={"user_id": user_id} if user_id else {},
                change_reason=f"Rollback {component} to version {version_id}"
            )
            
            if rollback_result["success"]:
                # Get updated theme state
                theme_state = await self.get_complete_theme(user_roles, user_id)
                css = self._generate_theme_css(theme_state.get("colors", {}))
                
                return {
                    "success": True,
                    "component": component,
                    "version_id": version_id,
                    "theme_state": theme_state,
                    "theme_css": css,
                    "rollback_completed": True
                }
            
            return rollback_result
            
        except Exception as e:
            logger.error(f"Failed to rollback theme: {e}")
            return {"success": False, "error": f"Rollback failed: {str(e)}"}
    
    def _generate_theme_css(self, colors: Dict[str, str]) -> str:
        """Generate CSS from color scheme"""
        css_vars = []
        for name, value in colors.items():
            css_vars.append(f"  --theme-{name}: {value};")
        
        return f"""
:root {{
{chr(10).join(css_vars)}
}}

.theme {{
  color-scheme: light;
}}

/* Theme utilities */
.bg-primary {{ background-color: var(--theme-primary); }}
.bg-secondary {{ background-color: var(--theme-secondary); }}
.bg-accent {{ background-color: var(--theme-accent); }}
.text-primary {{ color: var(--theme-primary); }}
.text-secondary {{ color: var(--theme-secondary); }}
.text-accent {{ color: var(--theme-accent); }}
""".strip()
    
    def get_available_presets(self) -> List[str]:
        """Get list of available theme presets"""
        return list(self.presets.keys())
    
    def get_preset_preview(self, preset: str) -> Dict[str, Any]:
        """Get preview of theme preset"""
        if preset not in self.presets:
            return {"error": f"Preset '{preset}' not found"}
        
        preset_data = self.presets[preset]
        css = self._generate_theme_css(preset_data["colors"])
        
        return {
            "preset": preset,
            "colors": preset_data["colors"],
            "typography": preset_data["typography"],
            "spacing": preset_data["spacing"],
            "preview_css": css
        }
    
    async def apply_theme_to_ui_components(
        self,
        preset: str,
        component_ids: List[str],
        user_roles: List[str] = ["admin"],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply theme preset to specific UI components using their IDs.
        
        Args:
            preset: Theme preset name
            component_ids: List of UI component IDs to theme
            user_roles: User roles for permissions
            user_id: User ID for context
            
        Returns:
            Component theming result
        """
        if preset not in self.presets:
            return {"success": False, "error": f"Preset '{preset}' not found"}
        
        preset_data = self.presets[preset]
        
        try:
            # Generate component-specific theme mappings
            component_themes = {}
            
            for component_id in component_ids:
                # Create component-specific theme based on preset
                component_theme = self._generate_component_theme(
                    component_id=component_id,
                    preset_data=preset_data
                )
                component_themes[component_id] = component_theme
            
            # Save component themes using hybrid settings
            results = {}
            
            for component_id, theme_data in component_themes.items():
                key = f"ui_components.{component_id}.theme"
                
                result = await set_setting_with_version(
                    key=key,
                    value=theme_data,
                    user_roles=user_roles,
                    context={"user_id": user_id} if user_id else {},
                    change_reason=f"Applied preset '{preset}' to component {component_id}"
                )
                results[component_id] = result
            
            # Check if all applications succeeded
            all_success = all(result.get("success", False) for result in results.values())
            
            if all_success:
                return {
                    "success": True,
                    "preset": preset,
                    "component_ids": component_ids,
                    "component_themes": component_themes,
                    "version_ids": {
                        comp_id: result.get("version_id") 
                        for comp_id, result in results.items()
                    },
                    "persisted": True,
                    "cache_optimized": True
                }
            else:
                failed = [comp_id for comp_id, result in results.items() if not result.get("success", False)]
                return {
                    "success": False,
                    "error": f"Failed to theme components: {', '.join(failed)}",
                    "results": results
                }
                
        except Exception as e:
            logger.error(f"Failed to apply theme to UI components: {e}")
            return {"success": False, "error": f"Component theming failed: {str(e)}"}
    
    def _generate_component_theme(self, component_id: str, preset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate component-specific theme based on preset and component type.
        
        Args:
            component_id: UI component ID (e.g., "header", "sidebar", "button")
            preset_data: Theme preset data
            
        Returns:
            Component-specific theme data
        """
        colors = preset_data["colors"]
        typography = preset_data["typography"]
        spacing = preset_data["spacing"]
        
        # Component-specific theme mappings
        component_themes = {
            "header": {
                "background": colors.get("primary", colors["base_100"]),
                "text": colors.get("base_100", colors["neutral"]),
                "border": colors.get("secondary", colors["neutral"]),
                "font_family": typography["font_family_primary"],
                "font_size": "1.25rem",
                "padding": spacing["element_gap"],
                "css_classes": ["bg-primary", "text-base-100", "border-secondary"]
            },
            "sidebar": {
                "background": colors.get("base_200", colors["base_100"]),
                "text": colors.get("neutral", colors["base_300"]),
                "border": colors.get("base_300", colors["neutral"]),
                "font_family": typography["font_family_primary"],
                "font_size": typography["font_size_base"],
                "padding": spacing["element_gap"],
                "width": "250px",
                "css_classes": ["bg-base-200", "text-neutral", "border-base-300"]
            },
            "button": {
                "background": colors.get("primary", colors["accent"]),
                "text": colors.get("base_100", colors["base_200"]),
                "border": colors.get("primary", colors["accent"]),
                "font_family": typography["font_family_primary"],
                "font_size": typography["font_size_base"],
                "padding": f"0.5rem {spacing['element_gap']}",
                "border_radius": "0.375rem",
                "css_classes": ["bg-primary", "text-base-100", "border-primary", "rounded-md"]
            },
            "card": {
                "background": colors.get("base_100", colors["base_200"]),
                "text": colors.get("neutral", colors["base_300"]),
                "border": colors.get("base_300", colors["neutral"]),
                "font_family": typography["font_family_primary"],
                "font_size": typography["font_size_base"],
                "padding": spacing["element_gap"],
                "border_radius": "0.5rem",
                "css_classes": ["bg-base-100", "text-neutral", "border-base-300", "rounded-lg"]
            },
            "footer": {
                "background": colors.get("neutral", colors["base_300"]),
                "text": colors.get("base_100", colors["base_200"]),
                "border": colors.get("base_300", colors["neutral"]),
                "font_family": typography["font_family_secondary"],
                "font_size": "0.875rem",
                "padding": spacing["element_gap"],
                "css_classes": ["bg-neutral", "text-base-100", "border-base-300"]
            }
        }
        
        # Default theme for unknown components
        default_theme = {
            "background": colors.get("base_100", "#ffffff"),
            "text": colors.get("neutral", "#6b7280"),
            "border": colors.get("base_300", "#e5e7eb"),
            "font_family": typography["font_family_primary"],
            "font_size": typography["font_size_base"],
            "padding": spacing["element_gap"],
            "css_classes": ["bg-base-100", "text-neutral", "border-base-300"]
        }
        
        return component_themes.get(component_id, default_theme)
    
    async def get_component_theme(
        self,
        component_id: str,
        user_roles: List[str] = ["admin"],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get theme for a specific UI component.
        
        Args:
            component_id: UI component ID
            user_roles: User roles for permissions
            user_id: User ID for context
            
        Returns:
            Component theme data
        """
        try:
            from core.services.settings import get_setting_optimized
            
            key = f"ui_components.{component_id}.theme"
            result = await get_setting_optimized(
                key=key,
                user_roles=user_roles,
                user_id=user_id
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "component_id": component_id,
                    "theme": result["value"],
                    "cached": result.get("cached", False)
                }
            else:
                # Return default theme if component not themed
                default_theme = self._generate_component_theme(
                    component_id=component_id,
                    preset_data=self.presets["modern"]  # Use modern as default
                )
                return {
                    "success": True,
                    "component_id": component_id,
                    "theme": default_theme,
                    "default": True,
                    "cached": False
                }
                
        except Exception as e:
            logger.error(f"Failed to get component theme: {e}")
            return {"success": False, "error": f"Failed to load component theme: {str(e)}"}
    
    async def get_all_component_themes(
        self,
        user_roles: List[str] = ["admin"],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get themes for all UI components.
        
        Args:
            user_roles: User roles for permissions
            user_id: User ID for context
            
        Returns:
            All component themes
        """
        try:
            from core.services.settings import get_setting_optimized
            
            # Common component IDs to check
            component_ids = [
                "header", "sidebar", "button", "card", "footer",
                "navigation", "modal", "form", "table", "alert"
            ]
            
            component_themes = {}
            
            for component_id in component_ids:
                theme_result = await self.get_component_theme(
                    component_id=component_id,
                    user_roles=user_roles,
                    user_id=user_id
                )
                
                if theme_result["success"]:
                    component_themes[component_id] = theme_result["theme"]
            
            return {
                "success": True,
                "component_themes": component_themes,
                "total_components": len(component_themes),
                "cache_optimized": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get all component themes: {e}")
            return {"success": False, "error": f"Failed to load component themes: {str(e)}"}
    
    def get_supported_component_ids(self) -> List[str]:
        """Get list of supported UI component IDs for theming"""
        return [
            "header", "sidebar", "button", "card", "footer",
            "navigation", "modal", "form", "table", "alert",
            "dropdown", "tooltip", "badge", "progress", "tabs"
        ]
