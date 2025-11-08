from fasthtml.common import *
from app.core.ui.components import Container, Card, Input, Button

def RegisterPage():
    return Container(
        Card(
            H1("Create an Account", cls="text-3xl font-bold text-center mb-6"),
            Form(
                Div(
                    Label("Email", fr="email", cls="block text-sm font-medium mb-1"),
                    Input(type="email", id="email", name="email", placeholder="your@email.com", 
                          cls="w-full px-3 py-2 border border-gray-300 rounded-md"),
                    cls="mb-4"
                ),
                Div(
                    Label("Password", fr="password", cls="block text-sm font-medium mb-1"),
                    Input(type="password", id="password", name="password", placeholder="••••••••", 
                          cls="w-full px-3 py-2 border border-gray-300 rounded-md"),
                    cls="mb-6"
                ),
                Button("Register", type="submit", 
                       cls="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors"),
                Div(
                    P(A("Already have an account? Login here", href="/auth/login", cls="text-green-600 hover:underline"), 
                      cls="text-center mt-4"),
                    cls="mt-6"
                ),
                hx_post="/auth/register",
                hx_target="#register-result",
                cls="space-y-4"
            ),
            Div(id="register-result", cls="mt-4"),
            cls="max-w-md w-full"
        ),
        cls="min-h-screen flex items-center justify-center py-12"
    )
