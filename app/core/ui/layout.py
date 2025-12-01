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
            A("About", href='/about'),
            A("Contact", href='/contact'),
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