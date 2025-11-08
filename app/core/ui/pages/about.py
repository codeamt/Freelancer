from fasthtml.common import *
from app.core.ui.components import CTAButton

def AboutPage():
    return section(
        div(
            H1("About FastApp", cls="text-4xl font-bold mb-6"),
            P("FastApp is a modern web application framework built on top of FastHTML, "
              "designed to help developers build reactive, full-stack applications at lightning speed.", 
              cls="text-lg mb-4"),
            H2("Our Mission", cls="text-2xl font-bold mt-8 mb-4"),
            P("We believe that building web applications should be simple, fast, and enjoyable. "
              "Our mission is to provide developers with the tools they need to create "
              "powerful applications without the complexity.", cls="mb-4"),
            H2("Key Features", cls="text-2xl font-bold mt-8 mb-4"),
            Ul(
                Li("Lightning-fast development with FastHTML", cls="mb-2"),
                Li("Reactive UI components with HTMX", cls="mb-2"),
                Li("Beautiful design system with MonsterUI", cls="mb-2"),
                Li("Secure by default with built-in sanitization", cls="mb-2"),
                Li("Full-stack capabilities with Python everywhere", cls="mb-2"),
                cls="list-disc pl-6 mb-6"
            ),
            cls="max-w-3xl mx-auto py-12"
        )
    )
