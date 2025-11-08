from fasthtml.common import *
from app.core.ui.components import Container, Card, Button
from app.core.ui.layout import Layout

def ProfilePage(user):
    return Container(
        Card(
            H1(f"Welcome, {user['sub']}", cls="text-3xl font-bold mb-2"),
            Div(
                Span("Role: ", cls="font-semibold"),
                Span(user['role'], cls="text-gray-700"),
                cls="mb-4"
            ),
            Div(
                Span("Email: ", cls="font-semibold"),
                Span(user['sub'], cls="text-gray-700"),
                cls="mb-4"
            ),
            Div(
                Span("Scopes: ", cls="font-semibold"),
                Span(", ".join(user.get('scopes', [])), cls="text-gray-700"),
                cls="mb-6"
            ),
            Div(
                Button("Logout", 
                       hx_post="/auth/logout", 
                       hx_target="body", 
                       hx_swap="outerHTML",
                       cls="bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 transition-colors"),
                cls="mt-6"
            ),
            cls="max-w-2xl w-full"
        ),
        cls="min-h-screen flex items-center justify-center py-12"
    )
