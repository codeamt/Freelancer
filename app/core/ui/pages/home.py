from fasthtml.common import *
from app.core.ui.components import CTAButton

def HomePage():
    return section(
        div(
            H1("Build modular apps at lightning speed ⚡", cls="text-4xl font-bold"),
            P("FastApp combines FastHTML + MonsterUI + HTMX for reactive full-stack development."),
            CTAButton("Get Started", href="/auth/register"),
            cls="text-center my-12"
        )
    )