"""
Theme editor workflow system.

Provides comprehensive theme editing capabilities with:
- Color scheme management
- Typography settings
- Spacing and layout
- Component-level styling
- Theme presets
- Custom CSS
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from core.state.actions import Action, ActionResult
from core.state.state import State
from core.state.builder import SiteStateBuilder
from core.state.transitions import on_success


# ============================================================================
# Theme Schema
# ============================================================================

@dataclass
class ColorScheme:
    """Color scheme for the theme."""
    primary: str = "#3b82f6"
    secondary: str = "#8b5cf6"
    accent: str = "#ec4899"
    neutral: str = "#6b7280"
    base_100: str = "#ffffff"
    base_200: str = "#f3f4f6"
    base_300: str = "#e5e7eb"
    info: str = "#3abff8"
    success: str = "#36d399"
    warning: str = "#fbbd23"
    error: str = "#f87272"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "neutral": self.neutral,
            "base_100": self.base_100,
            "base_200": self.base_200,
            "base_300": self.base_300,
            "info": self.info,
            "success": self.success,
            "warning": self.warning,
            "error": self.error
        }


@dataclass
class Typography:
    """Typography settings."""
    font_family_primary: str = "Inter, system-ui, sans-serif"
    font_family_secondary: str = "Georgia, serif"
    font_family_mono: str = "Menlo, monospace"
    font_size_base: str = "16px"
    font_size_scale: float = 1.25  # Scale ratio for headings
    line_height_base: float = 1.6
    line_height_heading: float = 1.2
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "font_family_primary": self.font_family_primary,
            "font_family_secondary": self.font_family_secondary,
            "font_family_mono": self.font_family_mono,
            "font_size_base": self.font_size_base,
            "font_size_scale": self.font_size_scale,
            "line_height_base": self.line_height_base,
            "line_height_heading": self.line_height_heading
        }


@dataclass
class Spacing:
    """Spacing and layout settings."""
    container_max_width: str = "1280px"
    section_padding: str = "4rem"
    element_gap: str = "1rem"
    border_radius_sm: str = "0.25rem"
    border_radius_md: str = "0.5rem"
    border_radius_lg: str = "1rem"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "container_max_width": self.container_max_width,
            "section_padding": self.section_padding,
            "element_gap": self.element_gap,
            "border_radius_sm": self.border_radius_sm,
            "border_radius_md": self.border_radius_md,
            "border_radius_lg": self.border_radius_lg
        }


@dataclass
class ThemeConfig:
    """Complete theme configuration."""
    name: str
    base_theme: str = "slate"  # DaisyUI theme
    colors: ColorScheme = field(default_factory=ColorScheme)
    typography: Typography = field(default_factory=Typography)
    spacing: Spacing = field(default_factory=Spacing)
    custom_css: str = ""
    dark_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "base_theme": self.base_theme,
            "colors": self.colors.to_dict(),
            "typography": self.typography.to_dict(),
            "spacing": self.spacing.to_dict(),
            "custom_css": self.custom_css,
            "dark_mode": self.dark_mode
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThemeConfig":
        colors_data = data.get("colors", {})
        typography_data = data.get("typography", {})
        spacing_data = data.get("spacing", {})
        
        return cls(
            name=data["name"],
            base_theme=data.get("base_theme", "slate"),
            colors=ColorScheme(**colors_data) if colors_data else ColorScheme(),
            typography=Typography(**typography_data) if typography_data else Typography(),
            spacing=Spacing(**spacing_data) if spacing_data else Spacing(),
            custom_css=data.get("custom_css", ""),
            dark_mode=data.get("dark_mode", False)
        )
    
    def generate_css(self) -> str:
        """Generate CSS from theme configuration."""
        css = f"""
/* Theme: {self.name} */
:root {{
  /* Colors */
  --color-primary: {self.colors.primary};
  --color-secondary: {self.colors.secondary};
  --color-accent: {self.colors.accent};
  --color-neutral: {self.colors.neutral};
  --color-base-100: {self.colors.base_100};
  --color-base-200: {self.colors.base_200};
  --color-base-300: {self.colors.base_300};
  
  /* Typography */
  --font-primary: {self.typography.font_family_primary};
  --font-secondary: {self.typography.font_family_secondary};
  --font-mono: {self.typography.font_family_mono};
  --font-size-base: {self.typography.font_size_base};
  --line-height-base: {self.typography.line_height_base};
  --line-height-heading: {self.typography.line_height_heading};
  
  /* Spacing */
  --container-max-width: {self.spacing.container_max_width};
  --section-padding: {self.spacing.section_padding};
  --element-gap: {self.spacing.element_gap};
  --border-radius-sm: {self.spacing.border_radius_sm};
  --border-radius-md: {self.spacing.border_radius_md};
  --border-radius-lg: {self.spacing.border_radius_lg};
}}

body {{
  font-family: var(--font-primary);
  font-size: var(--font-size-base);
  line-height: var(--line-height-base);
  background-color: var(--color-base-100);
  color: var(--color-neutral);
}}

.container {{
  max-width: var(--container-max-width);
  margin: 0 auto;
  padding: 0 var(--element-gap);
}}

section {{
  padding: var(--section-padding) 0;
}}

/* Custom CSS */
{self.custom_css}
"""
        return css


# ============================================================================
# Theme Presets
# ============================================================================

class ThemePresets:
    """Pre-defined theme presets."""
    
    @staticmethod
    def get_preset(name: str) -> ThemeConfig:
        """Get a theme preset by name."""
        presets = {
            "modern": ThemePresets.modern(),
            "minimal": ThemePresets.minimal(),
            "bold": ThemePresets.bold(),
            "dark": ThemePresets.dark(),
            "warm": ThemePresets.warm(),
            "cool": ThemePresets.cool()
        }
        return presets.get(name, ThemePresets.modern())
    
    @staticmethod
    def modern() -> ThemeConfig:
        """Modern, clean theme."""
        return ThemeConfig(
            name="Modern",
            base_theme="light",
            colors=ColorScheme(
                primary="#3b82f6",
                secondary="#8b5cf6",
                accent="#ec4899"
            )
        )
    
    @staticmethod
    def minimal() -> ThemeConfig:
        """Minimal, monochrome theme."""
        return ThemeConfig(
            name="Minimal",
            base_theme="light",
            colors=ColorScheme(
                primary="#1f2937",
                secondary="#4b5563",
                accent="#9ca3af"
            ),
            typography=Typography(
                font_family_primary="system-ui, sans-serif"
            )
        )
    
    @staticmethod
    def bold() -> ThemeConfig:
        """Bold, vibrant theme."""
        return ThemeConfig(
            name="Bold",
            base_theme="light",
            colors=ColorScheme(
                primary="#ef4444",
                secondary="#f59e0b",
                accent="#8b5cf6"
            ),
            typography=Typography(
                font_size_base="18px",
                font_size_scale=1.3
            )
        )
    
    @staticmethod
    def dark() -> ThemeConfig:
        """Dark mode theme."""
        return ThemeConfig(
            name="Dark",
            base_theme="dark",
            colors=ColorScheme(
                primary="#60a5fa",
                secondary="#a78bfa",
                accent="#f472b6",
                base_100="#1f2937",
                base_200="#111827",
                base_300="#0f172a"
            ),
            dark_mode=True
        )
    
    @staticmethod
    def warm() -> ThemeConfig:
        """Warm, inviting theme."""
        return ThemeConfig(
            name="Warm",
            base_theme="light",
            colors=ColorScheme(
                primary="#f59e0b",
                secondary="#ef4444",
                accent="#ec4899",
                base_100="#fffbeb",
                base_200="#fef3c7"
            )
        )
    
    @staticmethod
    def cool() -> ThemeConfig:
        """Cool, professional theme."""
        return ThemeConfig(
            name="Cool",
            base_theme="light",
            colors=ColorScheme(
                primary="#0ea5e9",
                secondary="#06b6d4",
                accent="#6366f1",
                base_100="#f0f9ff",
                base_200="#e0f2fe"
            )
        )


# ============================================================================
# Theme Actions
# ============================================================================

class InitializeThemeAction(Action):
    """Initialize theme configuration."""
    
    def __init__(self):
        super().__init__(
            name="initialize_theme",
            reads=["theme_state"],
            writes=["theme_state"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Initialize theme with preset or defaults."""
        preset_name = inputs.get("preset", "modern")
        
        theme = ThemePresets.get_preset(preset_name)
        
        return ActionResult(
            success=True,
            message=f"Theme initialized with '{preset_name}' preset",
            data={"theme_state": theme.to_dict()}
        )


class UpdateColorSchemeAction(Action):
    """Update theme color scheme."""
    
    def __init__(self):
        super().__init__(
            name="update_colors",
            reads=["theme_state"],
            writes=["theme_state"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Update color values."""
        color_updates = inputs.get("colors")
        
        if not color_updates:
            return ActionResult(success=False, error="colors required")
        
        theme_state = state.get("theme_state", {})
        colors = theme_state.get("colors", {})
        colors.update(color_updates)
        theme_state["colors"] = colors
        
        return ActionResult(
            success=True,
            message="Colors updated",
            data={"theme_state": theme_state}
        )


class UpdateTypographyAction(Action):
    """Update theme typography."""
    
    def __init__(self):
        super().__init__(
            name="update_typography",
            reads=["theme_state"],
            writes=["theme_state"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Update typography settings."""
        typography_updates = inputs.get("typography")
        
        if not typography_updates:
            return ActionResult(success=False, error="typography required")
        
        theme_state = state.get("theme_state", {})
        typography = theme_state.get("typography", {})
        typography.update(typography_updates)
        theme_state["typography"] = typography
        
        return ActionResult(
            success=True,
            message="Typography updated",
            data={"theme_state": theme_state}
        )


class UpdateSpacingAction(Action):
    """Update theme spacing."""
    
    def __init__(self):
        super().__init__(
            name="update_spacing",
            reads=["theme_state"],
            writes=["theme_state"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Update spacing settings."""
        spacing_updates = inputs.get("spacing")
        
        if not spacing_updates:
            return ActionResult(success=False, error="spacing required")
        
        theme_state = state.get("theme_state", {})
        spacing = theme_state.get("spacing", {})
        spacing.update(spacing_updates)
        theme_state["spacing"] = spacing
        
        return ActionResult(
            success=True,
            message="Spacing updated",
            data={"theme_state": theme_state}
        )


class AddCustomCSSAction(Action):
    """Add or update custom CSS."""
    
    def __init__(self):
        super().__init__(
            name="add_custom_css",
            reads=["theme_state"],
            writes=["theme_state"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Add custom CSS to theme."""
        custom_css = inputs.get("custom_css")
        append = inputs.get("append", False)
        
        if custom_css is None:
            return ActionResult(success=False, error="custom_css required")
        
        theme_state = state.get("theme_state", {})
        
        if append and "custom_css" in theme_state:
            theme_state["custom_css"] += "\n\n" + custom_css
        else:
            theme_state["custom_css"] = custom_css
        
        return ActionResult(
            success=True,
            message="Custom CSS updated",
            data={"theme_state": theme_state}
        )


class ApplyThemePresetAction(Action):
    """Apply a complete theme preset."""
    
    def __init__(self):
        super().__init__(
            name="apply_preset",
            reads=["theme_state"],
            writes=["theme_state"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Apply theme preset."""
        preset_name = inputs.get("preset")
        preserve_custom_css = inputs.get("preserve_custom_css", True)
        
        if not preset_name:
            return ActionResult(success=False, error="preset name required")
        
        # Get current custom CSS if preserving
        current_theme = state.get("theme_state", {})
        custom_css = current_theme.get("custom_css", "") if preserve_custom_css else ""
        
        # Get preset
        theme = ThemePresets.get_preset(preset_name)
        theme_dict = theme.to_dict()
        
        # Preserve custom CSS
        if custom_css:
            theme_dict["custom_css"] = custom_css
        
        return ActionResult(
            success=True,
            message=f"Applied '{preset_name}' preset",
            data={"theme_state": theme_dict}
        )


class ToggleDarkModeAction(Action):
    """Toggle dark mode."""
    
    def __init__(self):
        super().__init__(
            name="toggle_dark_mode",
            reads=["theme_state"],
            writes=["theme_state"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Toggle dark mode setting."""
        theme_state = state.get("theme_state", {})
        current_dark = theme_state.get("dark_mode", False)
        theme_state["dark_mode"] = not current_dark
        
        # Update base theme
        theme_state["base_theme"] = "dark" if theme_state["dark_mode"] else "light"
        
        return ActionResult(
            success=True,
            message=f"Dark mode {'enabled' if theme_state['dark_mode'] else 'disabled'}",
            data={"theme_state": theme_state}
        )


class GenerateThemeCSSAction(Action):
    """Generate CSS from current theme state."""
    
    def __init__(self):
        super().__init__(
            name="generate_css",
            reads=["theme_state"],
            writes=["theme_css"]
        )
    
    async def run(self, state: State, **inputs) -> ActionResult:
        """Generate CSS string from theme."""
        theme_state = state.get("theme_state", {})
        
        try:
            theme = ThemeConfig.from_dict(theme_state)
            css = theme.generate_css()
            
            return ActionResult(
                success=True,
                message="CSS generated",
                data={"theme_css": css}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                error=f"Failed to generate CSS: {str(e)}"
            )


# ============================================================================
# Theme Editor Workflow
# ============================================================================

def create_theme_editor_workflow():
    """
    Create workflow for theme editing.
    
    Flow:
    1. Initialize theme (with preset or existing)
    2. Edit colors, typography, spacing, or custom CSS
    3. Preview changes
    4. Generate CSS
    5. Save theme
    """
    initialize = InitializeThemeAction()
    update_colors = UpdateColorSchemeAction()
    update_typography = UpdateTypographyAction()
    update_spacing = UpdateSpacingAction()
    add_custom_css = AddCustomCSSAction()
    apply_preset = ApplyThemePresetAction()
    toggle_dark = ToggleDarkModeAction()
    generate_css = GenerateThemeCSSAction()
    
    app = (
        SiteStateBuilder()
        .with_actions(
            initialize,
            update_colors,
            update_typography,
            update_spacing,
            add_custom_css,
            apply_preset,
            toggle_dark,
            generate_css
        )
        .with_transitions(
            # All editing actions can go to generate_css
            ("initialize_theme", "update_colors", on_success),
            ("update_colors", "generate_css", on_success),
            ("update_typography", "generate_css", on_success),
            ("update_spacing", "generate_css", on_success),
            ("add_custom_css", "generate_css", on_success),
            ("apply_preset", "generate_css", on_success),
            ("toggle_dark_mode", "generate_css", on_success)
        )
        .with_entrypoint("initialize_theme")
        .build()
    )
    
    return app


class ThemeEditorManager:
    """Manager for theme editing workflows."""
    
    def __init__(self, persister=None):
        """Initialize theme editor manager."""
        self.persister = persister
    
    async def initialize_theme(
        self,
        site_id: str,
        preset: str = "modern",
        user_id: str = None
    ) -> Dict[str, Any]:
        """Initialize theme for a site."""
        workflow = create_theme_editor_workflow()
        
        action, result, state = await workflow.step(preset=preset)
        
        if result.success and self.persister:
            partition_key = f"user:{user_id}" if user_id else None
            await self.persister.save(f"theme_{site_id}", state, partition_key)
        
        return {
            "success": result.success,
            "theme_state": state.get("theme_state"),
            "error": result.error if not result.success else None
        }
    
    async def update_theme_colors(
        self,
        site_id: str,
        colors: Dict[str, str],
        user_id: str = None
    ) -> Dict[str, Any]:
        """Update theme colors."""
        # Load current theme
        partition_key = f"user:{user_id}" if user_id else None
        state = await self.persister.load(f"theme_{site_id}", partition_key)
        
        if not state:
            return {"success": False, "error": "Theme not found"}
        
        # Apply update
        action = UpdateColorSchemeAction()
        new_state, result = await action.execute(state, colors=colors)
        
        # Generate CSS
        css_action = GenerateThemeCSSAction()
        new_state, css_result = await css_action.execute(new_state)
        
        # Save
        if result.success and self.persister:
            await self.persister.save(f"theme_{site_id}", new_state, partition_key)
        
        return {
            "success": result.success,
            "theme_state": new_state.get("theme_state"),
            "theme_css": new_state.get("theme_css"),
            "error": result.error if not result.success else None
        }
    
    async def apply_preset(
        self,
        site_id: str,
        preset: str,
        preserve_custom_css: bool = True,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Apply a theme preset."""
        partition_key = f"user:{user_id}" if user_id else None
        state = await self.persister.load(f"theme_{site_id}", partition_key)
        
        action = ApplyThemePresetAction()
        new_state, result = await action.execute(
            state or State(),
            preset=preset,
            preserve_custom_css=preserve_custom_css
        )
        
        # Generate CSS
        css_action = GenerateThemeCSSAction()
        new_state, css_result = await css_action.execute(new_state)
        
        if result.success and self.persister:
            await self.persister.save(f"theme_{site_id}", new_state, partition_key)
        
        return {
            "success": result.success,
            "theme_state": new_state.get("theme_state"),
            "theme_css": new_state.get("theme_css")
        }