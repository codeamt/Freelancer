"""Test Page - Simple page to verify MonsterUI styling"""
from fasthtml.common import *
from monsterui.all import *

def TestPage():
    """Simple test page to verify MonsterUI components render correctly"""
    return Div(
        # Hero Section
        Div(
            H1("MonsterUI Test Page", cls="text-4xl font-bold mb-4"),
            P("Testing MonsterUI components and Tailwind CSS styling", cls="text-xl text-gray-600 mb-8"),
            cls="text-center py-12"
        ),
        
        # Buttons Test
        Div(
            H2("Buttons", cls="text-2xl font-semibold mb-4"),
            Div(
                Button("Primary Button", cls="btn btn-primary mr-2"),
                Button("Secondary Button", cls="btn btn-secondary mr-2"),
                Button("Accent Button", cls="btn btn-accent"),
                cls="space-x-2"
            ),
            cls="mb-8"
        ),
        
        # Cards Test
        Div(
            H2("Cards", cls="text-2xl font-semibold mb-4"),
            Div(
                Card(
                    Div(
                        H3("Card Title", cls="text-xl font-semibold mb-2"),
                        P("This is a test card with MonsterUI styling.", cls="text-gray-600"),
                        cls="p-6"
                    ),
                    cls="shadow-md"
                ),
                cls="max-w-md"
            ),
            cls="mb-8"
        ),
        
        # Typography Test
        Div(
            H2("Typography", cls="text-2xl font-semibold mb-4"),
            H1("Heading 1", cls="text-4xl font-bold mb-2"),
            H2("Heading 2", cls="text-3xl font-bold mb-2"),
            H3("Heading 3", cls="text-2xl font-bold mb-2"),
            P("Regular paragraph text with Tailwind CSS styling.", cls="text-base mb-2"),
            P("Muted text example", cls="text-gray-500 mb-2"),
            cls="mb-8"
        ),
        
        # Grid Test
        Div(
            H2("Grid Layout", cls="text-2xl font-semibold mb-4"),
            Div(
                Div(
                    Card(
                        Div(P("Grid Item 1", cls="text-center p-4"))
                    ),
                    cls="w-full md:w-1/3 px-2 mb-4"
                ),
                Div(
                    Card(
                        Div(P("Grid Item 2", cls="text-center p-4"))
                    ),
                    cls="w-full md:w-1/3 px-2 mb-4"
                ),
                Div(
                    Card(
                        Div(P("Grid Item 3", cls="text-center p-4"))
                    ),
                    cls="w-full md:w-1/3 px-2 mb-4"
                ),
                cls="flex flex-wrap -mx-2"
            ),
            cls="mb-8"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
