from fasthtml.common import *
from app.core.ui.components import Container, Card, Input, Button

def LoginPage():
    return Container(
        Card(
            H1("Login to FastApp", cls="text-3xl font-bold text-center mb-6"),
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
                Button("Login", type="submit", 
                       cls="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"),
                Div(
                    P(A("Don't have an account? Register here", href="/auth/register", cls="text-blue-600 hover:underline"), 
                      cls="text-center mt-4"),
                    cls="mt-6"
                ),
                hx_post="/auth/login",
                hx_target="#login-result",
                cls="space-y-4"
            ),
            Div(
                P("Or continue with", cls="text-center my-4 text-gray-600"),
                A(Button("Sign in with Google", cls="w-full bg-white border border-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-50 transition-colors flex items-center justify-center"),
                  href="/auth/google/login",
                  cls="block"
                ),
                cls="mt-6"
            ),
            Div(id="login-result", cls="mt-4"),
            cls="max-w-md w-full"
        ),
        cls="min-h-screen flex items-center justify-center py-12"
    )
