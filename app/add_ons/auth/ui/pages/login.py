"""Login Page - Migrated from core"""
from fasthtml.common import *
from monsterui.all import *

def LoginPage():
    """Login page with email/password and OAuth options"""
    return Div(
        Card(
            Div(
                H1("Login to FastApp", cls="text-3xl font-bold text-center mb-6"),
                Form(
                    Div(
                        Label("Email", fr="email", cls="block text-sm font-medium mb-2"),
                        Input(
                            type="email",
                            id="email",
                            name="email",
                            placeholder="your@email.com",
                            cls="input input-bordered w-full",
                            required=True
                        ),
                        cls="mb-4"
                    ),
                    Div(
                        Label("Password", fr="password", cls="block text-sm font-medium mb-2"),
                        Input(
                            type="password",
                            id="password",
                            name="password",
                            placeholder="••••••••",
                            cls="input input-bordered w-full",
                            required=True
                        ),
                        cls="mb-4"
                    ),
                    Button("Login", type="submit", cls="btn btn-primary w-full mb-4"),
                    Div(
                        P(
                            A("Don't have an account? Register here", 
                              href="/auth/register",
                              cls="link link-primary"),
                            cls="text-center text-sm"
                        ),
                    ),
                    hx_post="/auth/login",
                    hx_target="#login-result",
                    hx_swap="innerHTML"
                ),
                Div(cls="divider my-6", data_content="OR"),
                Div(
                    A(
                        Button(
                            UkIcon("google", width="20", height="20", cls="mr-2"),
                            "Sign in with Google",
                            cls="btn btn-outline w-full"
                        ),
                        href="/auth/oauth/google"
                    ),
                    cls="mb-3"
                ),
                Div(id="login-result", cls="mt-4")
            ),
            cls="card-body"
        ),
        cls="card bg-base-100 shadow-xl max-w-md mx-auto mt-20"
    )
