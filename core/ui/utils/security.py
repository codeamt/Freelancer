# FastHTML Security Hardening Utilities
import html
import re
from typing import Any, Union
from fasthtml.common import FT, Div

# ------------------------------------------------------------------------------
# Basic Sanitization Helpers
# ------------------------------------------------------------------------------

def sanitize_html(value: str) -> str:
    if not isinstance(value, str):
        return value
    # Escape HTML special characters
    safe = html.escape(value, quote=True)
    # Remove remaining tags (belt and suspenders)
    return re.sub(r'<.*?>', '', safe)

def sanitize_css_value(value: str) -> str:
    if not isinstance(value, str):
        return value
    # Prevent JS injection in CSS
    value_lower = value.lower()
    if any(bad in value_lower for bad in ["javascript:", "expression(", "url("]):
        return ""
    # Strip all but safe CSS characters
    return re.sub(r'[^a-zA-Z0-9#(),.%\-\s]', '', value)

def sanitize_sql_input(value: str) -> str:
    if not isinstance(value, str):
        return value
    # Remove potential SQL control characters
    return re.sub(r'[;"\'\\]', '', value)

# ------------------------------------------------------------------------------
# Security Wrapper for FastHTML Components
# ------------------------------------------------------------------------------

class SecurityWrapper:
    """
    Provides component-level sanitization for FastHTML render trees, theme tokens,
    and general-purpose input filtering.
    """

    def __init__(self, theme_context):
        self.theme_context = theme_context

    # -----------------------------
    # Token Sanitization
    # -----------------------------

    def safe_theme_tokens(self):
        colors = self.theme_context.tokens.get("color", {})
        aesthetic = self.theme_context.aesthetic
        safe_colors = {k: sanitize_css_value(v) for k, v in colors.items()}
        safe_aesthetic = {k: sanitize_css_value(v) for k, v in aesthetic.items()}
        return safe_colors, safe_aesthetic

    # -----------------------------
    # Component Sanitization
    # -----------------------------

    def safe_component(self, component: Any) -> Any:
        """Recursively sanitize text and input-bearing FastHTML components."""
        try:
            if isinstance(component, FT) and hasattr(component, 'text'):
                component.text = sanitize_html(component.text)
                return component
            elif isinstance(component, Div) and hasattr(component, "children"):
                component.children = [self.safe_component(c) for c in component.children]
                return component
            elif hasattr(component, "props"):
                for key, value in vars(component).items():
                    if isinstance(value, str):
                        setattr(component, key, sanitize_html(value))
                return component
            elif isinstance(component, list):
                return [self.safe_component(c) for c in component]
            else:
                return component
        except Exception:
            # Fail closed — never propagate unsafe structures
            return FT("[unsafe content removed]")

    # -----------------------------
    # Input and Form Sanitization
    # -----------------------------

    def safe_input(self, form_value: Union[str, None], as_sql: bool = False) -> str:
        if not form_value:
            return ""
        val = sanitize_html(form_value)
        return sanitize_sql_input(val) if as_sql else val

    # -----------------------------
    # Safe Render Wrapper
    # -----------------------------

    def render_safe(self, component: Any) -> Any:
        """Apply sanitization before rendering to prevent HTML/CSS injection."""
        return self.safe_component(component)

# ------------------------------------------------------------------------------
# Example Usage (inside app/ui/layout.py)
# ------------------------------------------------------------------------------

"""
from app.ui.utils.security import SecurityWrapper
from app.ui.theme.context import ThemeContext
from fasthtml.common import *

theme_context = ThemeContext()
security = SecurityWrapper(theme_context)

# Before rendering any layout or page content:
page = Div([Head(), Body(), Footer()])
safe_page = security.render_safe(page)

# Then return safe_page — still a valid FastHTML component tree
"""