"""Clean Layout using FastHTML and MonsterUI"""
from fasthtml.common import *
from monsterui.all import *

def Layout(page_content, title: str = "FastApp", current_path: str = "/"):
    """Global layout with MonsterUI components"""
    
    # Return Title and body content - FastHTML will wrap in proper structure
    return (
        Title(title),
        NavBar(
            A("Home", href='/'),
            # Docs link with book icon
            A(
                UkIcon("book", cls="mr-1"),
                "Docs",
                href='/docs',
                cls="flex items-center gap-1"
            ),
            # GitHub repo link with icon
            A(
                UkIcon("github", cls="mr-1"),
                "Repo",
                href='https://github.com/codeamt/freelancer',
                target="_blank",
                cls="flex items-center gap-1"
            ),
            # Dropdown for example add-on apps
            Details(
                Summary(
                    UkIcon("grid", cls="mr-1"),
                    "Add-ons",
                    cls="flex items-center gap-1 cursor-pointer"
                ),
                Ul(
                    Li(A("🛍️ E-Shop", href='/eshop-example', cls="block px-4 py-2 hover:bg-base-200")),
                    Li(A("📚 LMS", href='/lms-example', cls="block px-4 py-2 hover:bg-base-200")),
                    Li(A("🌐 Social Network", href='/social-example', cls="block px-4 py-2 hover:bg-base-200")),
                    Li(A("📺 Streaming", href='/streaming-example', cls="block px-4 py-2 hover:bg-base-200")),
                    cls="menu bg-base-100 rounded-box shadow-lg absolute mt-2 w-56 z-50"
                ),
                cls="dropdown dropdown-end"
            ),
            brand=H3('FastApp')
        ),
        Div(
            page_content, 
            cls="container mx-auto px-4 py-8"
        ),
        # Footer
        Footer(
            Div(
                P("© 2025 FastApp. Built with FastHTML + MonsterUI.", cls=TextT.muted),
                cls="text-center py-4"
            ),
            cls="mt-auto border-t"
        )
    )