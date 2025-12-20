"""Component Factory - Create and render UI components"""
from typing import Dict, Any, List, Optional, Callable
from fasthtml.common import *
from monsterui.all import *
from .config import ComponentConfig, ComponentType


class EnhancedComponentLibrary:
    """
    Component library with registration and rendering capabilities.
    Supports custom components and theme-aware rendering.
    """
    
    def __init__(self):
        self._components: Dict[str, Callable] = {}
        self._register_default_components()
    
    def _register_default_components(self):
        """Register default component types"""
        self._components.update({
            ComponentType.HERO.value: self._render_hero,
            ComponentType.FEATURES.value: self._render_feature_grid,
            ComponentType.CTA.value: self._render_cta_banner,
            ComponentType.PRICING.value: self._render_pricing_table,
            ComponentType.TESTIMONIALS.value: self._render_testimonial,
            ComponentType.FORM.value: self._render_form,
            ComponentType.CONTENT.value: self._render_card,
            ComponentType.GALLERY.value: self._render_image,
            ComponentType.CUSTOM.value: self._render_custom,
        })
    
    def register(self, component_type: str, renderer: Callable):
        """Register a custom component renderer"""
        self._components[component_type] = renderer
    
    def render(self, config: ComponentConfig) -> Any:
        """Render a component from its configuration"""
        renderer = self._components.get(config.type.value if hasattr(config.type, 'value') else config.type)
        if not renderer:
            return Div(f"Unknown component type: {config.type}", cls="alert alert-error")
        
        return renderer(config)
    
    # Default component renderers
    def _render_hero(self, config: ComponentConfig):
        """Render hero section"""
        props = config.props
        return Div(
            Container(
                Div(
                    H1(props.get("title", "Welcome"), cls="text-5xl font-bold mb-4"),
                    P(props.get("subtitle", ""), cls="text-xl mb-6"),
                    Div(
                        A(props.get("cta_text", "Get Started"), 
                          href=props.get("cta_href", "#"), 
                          cls="btn btn-primary btn-lg"),
                        cls="flex gap-4"
                    ) if props.get("cta_text") else None,
                    cls="text-center py-20"
                )
            ),
            cls="hero min-h-screen bg-base-200"
        )
    
    def _render_feature_grid(self, config: ComponentConfig):
        """Render feature grid"""
        props = config.props
        features = props.get("features", [])
        return Div(
            *[Div(
                Card(
                    CardBody(
                        H3(f.get("title", ""), cls="card-title"),
                        P(f.get("description", ""), cls="text-gray-400")
                    )
                ),
                cls="col-span-1"
            ) for f in features],
            cls="grid grid-cols-1 md:grid-cols-3 gap-6 p-8"
        )
    
    def _render_cta_banner(self, config: ComponentConfig):
        """Render CTA banner"""
        props = config.props
        return Div(
            Container(
                H2(props.get("title", ""), cls="text-3xl font-bold mb-4"),
                P(props.get("description", ""), cls="text-xl mb-6"),
                A(props.get("cta_text", "Learn More"), 
                  href=props.get("cta_href", "#"), 
                  cls="btn btn-primary"),
                cls="text-center py-12"
            ),
            cls="bg-primary text-primary-content"
        )
    
    def _render_pricing_table(self, config: ComponentConfig):
        """Render pricing table"""
        props = config.props
        plans = props.get("plans", [])
        return Div(
            *[Div(
                Card(
                    CardBody(
                        H3(p.get("name", ""), cls="card-title"),
                        P(p.get("price", ""), cls="text-2xl font-bold"),
                        Ul(*[Li(f) for f in p.get("features", [])]),
                        A("Choose Plan", href=p.get("href", "#"), cls="btn btn-primary")
                    )
                ),
                cls="col-span-1"
            ) for p in plans],
            cls="grid grid-cols-1 md:grid-cols-3 gap-6 p-8"
        )
    
    def _render_testimonial(self, config: ComponentConfig):
        """Render testimonial"""
        props = config.props
        return Card(
            CardBody(
                P(f'"{props.get("quote", "")}"', cls="text-lg mb-4"),
                Div(
                    Strong(props.get("author", "")),
                    Br(),
                    Small(props.get("role", ""), cls="text-gray-400")
                )
            ),
            cls="shadow-lg"
        )
    
    def _render_faq(self, config: ComponentConfig):
        """Render FAQ accordion"""
        props = config.props
        faqs = props.get("items", [])
        return Div(
            *[Details(
                Summary(faq.get("question", "")),
                P(faq.get("answer", ""), cls="p-4")
            ) for faq in faqs],
            cls="space-y-2"
        )
    
    def _render_form(self, config: ComponentConfig):
        """Render form"""
        props = config.props
        fields = props.get("fields", [])
        return Form(
            *[Div(
                Label(f.get("label", ""), cls="label"),
                Input(
                    type=f.get("type", "text"),
                    name=f.get("name", ""),
                    placeholder=f.get("placeholder", ""),
                    required=f.get("required", False),
                    cls="input input-bordered w-full"
                ),
                cls="form-control mb-4"
            ) for f in fields],
            Button(props.get("submit_text", "Submit"), type="submit", cls="btn btn-primary"),
            method=props.get("method", "POST"),
            action=props.get("action", "/submit")
        )
    
    def _render_card(self, config: ComponentConfig):
        """Render card"""
        props = config.props
        return Card(
            CardBody(
                H3(props.get("title", ""), cls="card-title") if props.get("title") else None,
                P(props.get("content", "")),
                Div(
                    A(props.get("button_text", ""), 
                      href=props.get("button_href", "#"), 
                      cls="btn btn-primary")
                ) if props.get("button_text") else None
            ),
            cls="shadow-lg"
        )
    
    def _render_image(self, config: ComponentConfig):
        """Render image gallery"""
        props = config.props
        images = props.get("images", [])
        if not images:
            return Div("No images", cls="text-gray-400")
        
        return Div(
            *[Img(
                src=img.get("src", ""),
                alt=img.get("alt", ""),
                cls="w-full h-auto"
            ) for img in images],
            cls="grid grid-cols-1 md:grid-cols-3 gap-4"
        )
    
    def _render_custom(self, config: ComponentConfig):
        """Render custom component"""
        props = config.props
        return Div(
            H3(props.get("title", "Custom Component"), cls="text-xl font-bold mb-4"),
            Div(props.get("html", ""), cls="custom-content"),
            cls="custom-component p-4"
        )


class ComponentRenderer:
    """Renders individual components with theme support"""
    
    def __init__(self, library: Optional[EnhancedComponentLibrary] = None):
        self.library = library or EnhancedComponentLibrary()
    
    def render(self, config: ComponentConfig, theme: Optional[Dict[str, Any]] = None) -> Any:
        """Render a component with optional theme"""
        return self.library.render(config)


class SectionRenderer:
    """Renders sections containing multiple components"""
    
    def __init__(self, component_renderer: Optional[ComponentRenderer] = None):
        self.component_renderer = component_renderer or ComponentRenderer()
    
    def render(self, section: Dict[str, Any], theme: Optional[Dict[str, Any]] = None) -> Any:
        """Render a section with its components"""
        components = section.get("components", [])
        
        return Div(
            *[self.component_renderer.render(comp, theme) for comp in components],
            id=section.get("id", ""),
            cls=section.get("class", "")
        )


class ThemeAwareComponent:
    """Base class for theme-aware components"""
    
    def __init__(self, theme: Optional[Dict[str, Any]] = None):
        self.theme = theme or {}
    
    def get_theme_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the theme"""
        keys = key.split(".")
        value = self.theme
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def render(self) -> Any:
        """Override in subclasses"""
        raise NotImplementedError


def get_all_component_templates() -> Dict[str, Dict[str, Any]]:
    """Get all available component templates"""
    return {
        "hero": {
            "type": ComponentType.HERO.value,
            "name": "Hero Section",
            "description": "Large banner with title and CTA",
            "props": {
                "title": "Welcome to Our Site",
                "subtitle": "Build amazing things",
                "cta_text": "Get Started",
                "cta_href": "#"
            }
        },
        "feature_grid": {
            "type": ComponentType.FEATURE_GRID.value,
            "name": "Feature Grid",
            "description": "Grid of feature cards",
            "props": {
                "features": [
                    {"title": "Feature 1", "description": "Description 1"},
                    {"title": "Feature 2", "description": "Description 2"},
                    {"title": "Feature 3", "description": "Description 3"}
                ]
            }
        },
        "cta_banner": {
            "type": ComponentType.CTA_BANNER.value,
            "name": "CTA Banner",
            "description": "Call-to-action banner",
            "props": {
                "title": "Ready to get started?",
                "description": "Join thousands of satisfied customers",
                "cta_text": "Sign Up Now",
                "cta_href": "/signup"
            }
        }
    }