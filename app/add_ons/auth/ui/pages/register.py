"""Register Page - Migrated from core"""
from fasthtml.common import *
from monsterui.all import *

def RegisterPage():
    """Registration page with email/password"""
    return Div(
        Card(
            Div(
                H1("Create an Account", cls="text-3xl font-bold text-center mb-6"),
                Form(
                    Div(
                        Label("Username", fr="username", cls="block text-sm font-medium mb-2"),
                        Input(
                            type="text",
                            id="username",
                            name="username",
                            placeholder="johndoe",
                            cls="input input-bordered w-full",
                            required=True
                        ),
                        cls="mb-4"
                    ),
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
                            required=True,
                            minlength="8"
                        ),
                        P("Minimum 8 characters", cls="text-xs text-gray-500 mt-1"),
                        cls="mb-4"
                    ),
                    Div(
                        Label("Confirm Password", fr="confirm_password", cls="block text-sm font-medium mb-2"),
                        Input(
                            type="password",
                            id="confirm_password",
                            name="confirm_password",
                            placeholder="••••••••",
                            cls="input input-bordered w-full",
                            required=True
                        ),
                        cls="mb-4"
                    ),
                    Div(
                        Label("I want to:", fr="role", cls="block text-sm font-medium mb-2"),
                        Select(
                            Option("Browse and shop (Customer)", value="user", selected=True),
                            Option("Learn courses (Student)", value="student"),
                            Option("Teach courses (Instructor)", value="instructor"),
                            id="role",
                            name="role",
                            cls="select select-bordered w-full"
                        ),
                        P("You can change this later in settings", cls="text-xs text-gray-500 mt-1"),
                        cls="mb-4"
                    ),
                    Button("Register", type="submit", cls="btn btn-success w-full mb-4"),
                    Div(
                        P(
                            A("Already have an account? Login here", 
                              href="/auth/login",
                              cls="link link-primary"),
                            cls="text-center text-sm"
                        ),
                    ),
                    hx_post="/auth/register",
                    hx_target="#register-result",
                    hx_swap="innerHTML"
                ),
                Div(id="register-result", cls="mt-4")
            ),
            cls="card-body"
        ),
        cls="card bg-base-100 shadow-xl max-w-md mx-auto mt-20"
    )
