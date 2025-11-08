# Hardened Layout with SecurityWrapper and Safe FastHTML Components
from fasthtml.common import *
from app.core.ui.theme.context import ThemeContext
from app.core.ui.components import NavBar, Footer
from app.core.ui.utils.security import SecurityWrapper

# Initialize theme and security contexts
theme_context = ThemeContext()
security = SecurityWrapper(theme_context)

# ------------------------------------------------------------------------------
# Secure Layout Component
# ------------------------------------------------------------------------------

def Layout(page_content, title: str = "FastApp"):
    """Global layout wrapper that sanitizes content and theme tokens before render."""

    # Sanitize all FastHTML components in the page body
    safe_content = security.render_safe(page_content)

    # Sanitize theme tokens for safe CSS injection
    safe_colors, safe_aesthetic = security.safe_theme_tokens()
    css = theme_context.export_css()

    # Construct secure document tree using FastHTML primitives
    return Div([
        Head([
            Title(security.safe_input(title)),
            # Safe CSS injection using FastHTML Style() (not raw HTML)
            Style(css)
        ]),
        Body([
            NavBar([
                ("Home", "/"),
                ("LMS", "/lms"),
                ("Shop", "/commerce"),
                ("Social", "/social"),
            ]),
            safe_content,
            Footer()
        ])
    ])

# ------------------------------------------------------------------------------
# Example Usage (inside a FastAPI route)
# ------------------------------------------------------------------------------

"""
from fasthtml.common import *
from app.ui.layout import Layout

@app.get("/")
def homepage():
    content = Div([
        P("Welcome to FastApp!"),
        P("This content is fully sanitized and reactive."),
    ])
    return Layout(content, title="Home | FastApp")
"""