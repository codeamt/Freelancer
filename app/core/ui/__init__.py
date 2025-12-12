"""
Unified UI System - app/core/ui/__init__.py

This module combines components, theme, and library into a cohesive system.

Usage:
    # Simple component import
    from core.ui import HeroSection, Layout
    
    # Library and state
    from core.ui import ComponentConfig, EnhancedComponentLibrary
    
    # Theme system
    from core.ui import ThemeEditorManager, ThemePresets
    
    # Or import from submodules
    from core.ui.components.marketing import HeroSection
    from core.ui.library.config import ComponentConfig
"""

# =============================================================================
# Component Imports
# =============================================================================

# Marketing Components
from .components.marketing import (
    HeroSection,
    CTABanner,
    CTAButton,
)

# Content Components
from .components.content import (
    FeatureCard,
    FeatureGrid,
    FeatureCarousel,
    PricingCard,
    PricingTable,
    TestimonialCard,
    TestimonialCarousel,
    FAQAccordion,
)

# Form Components
from .components.forms import (
    EmailCaptureForm
)

# =============================================================================
# Layout & Pages
# =============================================================================

from .layout import Layout

# =============================================================================
# Component State (State Integration)
# =============================================================================

# Component Configuration
from .state.config import (
    ComponentConfig,
    ComponentType,
    VisibilityCondition,
)

# Component Factory
# TODO: Create factory.py module
# from .state.factory import (
#     EnhancedComponentLibrary,
#     ComponentRenderer,
#     SectionRenderer,
#     ThemeAwareComponent,
#     get_all_component_templates,
# )

# Component Actions
from .state.actions import (
    AddComponentAction,
    RemoveComponentAction,
    UpdateComponentAction,
    ToggleComponentAction,
    SetComponentVisibilityAction,
)

# =============================================================================
# Theme System
# =============================================================================

from .theme.editor import (
    ThemeEditorManager,
    ThemeConfig,
    ColorScheme,
    Typography,
    Spacing,
)

# TODO: Create ThemePresets class
# from .theme.presets import ThemePresets

# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Marketing Components
    "HeroSection",
    "CTABanner",
    "CTAButton",
    
    # Content Components
    "FeatureCard",
    "FeatureGrid",
    "FeatureCarousel",
    "PricingCard",
    "PricingTable",
    "TestimonialCard",
    "TestimonialCarousel",
    "FAQAccordion",
    
    # Form Components
    "EmailCaptureForm",
    "ContactForm",
    
    # Layout
    "Layout",
    
    # Library Configuration
    "ComponentConfig",
    "ComponentType",
    "VisibilityCondition",
    
    # Library Factory & Rendering
    "EnhancedComponentLibrary",
    "ComponentRenderer",
    "SectionRenderer",
    "ThemeAwareComponent",
    "get_all_component_templates",
    
    # Library Actions
    "AddComponentAction",
    "RemoveComponentAction",
    "UpdateComponentAction",
    "ToggleComponentAction",
    "SetComponentVisibilityAction",
    
    # Theme System
    "ThemeEditorManager",
    "ThemeConfig",
    "ColorScheme",
    "Typography",
    "Spacing",
    "ThemePresets",
]

# =============================================================================
# Submodule Documentation
# =============================================================================

__doc__ += """

Submodules:
-----------

components/
    marketing.py    - Hero, CTA, etc.
    content.py      - Features, Pricing, Testimonials, FAQ
    forms.py        - Email capture, Contact forms
    base.py         - Base component utilities

library/
    config.py       - ComponentConfig, enums, base classes
    factory.py      - Component factories and rendering
    actions.py      - State management actions for components

theme/
    editor.py       - Theme editor and configuration
    presets.py      - Pre-built theme presets
    renderer.py     - Theme-aware rendering utilities

layout.py           - Page layout components
pages/              - Page templates
utils/              - UI utilities

Examples:
---------

1. Use a component directly:
    >>> from core.ui import HeroSection
    >>> hero = HeroSection(
    ...     title="Welcome",
    ...     subtitle="Our Platform",
    ...     cta_text="Get Started"
    ... )

2. Create a state-managed component:
    >>> from core.ui import EnhancedComponentLibrary, ComponentConfig
    >>> library = EnhancedComponentLibrary()
    >>> hero = library.create_hero_section(
    ...     component_id="hero-1",
    ...     title="Welcome",
    ...     visibility=VisibilityCondition.ALWAYS
    ... )

3. Apply a theme:
    >>> from core.ui import ThemeEditorManager, ThemePresets
    >>> manager = ThemeEditorManager(persister=persister)
    >>> await manager.apply_preset(site_id, "modern", user_id)

4. Render with theme and state:
    >>> from core.ui import SectionRenderer
    >>> rendered = SectionRenderer.render_section(
    ...     section=section_data,
    ...     theme_state=theme,
    ...     user_context=current_user
    ... )
"""