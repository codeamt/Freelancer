"""LMS Specific Auth UI - Simple student registration"""
from fasthtml.common import *
from monsterui.all import *


def LMSLoginPage(redirect_url: str = "/lms-example", error: str = None):
    """LMS login page - focused on learning"""
    # Error messages
    error_messages = {
        "missing_fields": "Email and password are required",
        "invalid_credentials": "Invalid email or password",
        "server_error": "An error occurred. Please try again."
    }
    
    return Div(
        # Header
        Div(
            H1("📚 Welcome Back", cls="text-4xl font-bold mb-2"),
            P("Sign in to continue your learning journey", cls="text-xl text-gray-500 mb-8"),
            cls="text-center mb-8"
        ),
        
        # Error message
        (Div(
            P(f"⚠️ {error_messages.get(error, 'An error occurred')}", cls="text-error"),
            cls="alert alert-error max-w-md mx-auto mb-4"
        ) if error else None),
        
        # Login Form
        Card(
            Form(
                # Email
                Div(
                    Label("Email", cls="label"),
                    Input(
                        type="email",
                        name="email",
                        placeholder="your@email.com",
                        required=True,
                        cls="input input-bordered w-full"
                    ),
                    cls="form-control mb-4"
                ),
                
                # Password
                Div(
                    Label("Password", cls="label"),
                    Input(
                        type="password",
                        name="password",
                        placeholder="••••••••",
                        required=True,
                        cls="input input-bordered w-full"
                    ),
                    cls="form-control mb-4"
                ),
                
                # Submit
                Button(
                    "Sign In",
                    type="submit",
                    cls="btn btn-primary w-full btn-lg"
                ),
                
                # Register link
                Div(
                    Span("New to learning? ", cls="text-gray-500"),
                    A("Create account", href=f"/lms-example/register?redirect={redirect_url}", cls="link link-primary"),
                    cls="text-center mt-4"
                ),
                
                method="post",
                action=f"/lms-example/auth/login?redirect={redirect_url}"
            ),
            cls="max-w-md mx-auto p-8"
        ),
        
        cls="container mx-auto px-4 py-8"
    )


def LMSRegisterPage(redirect_url: str = "/lms-example", error: str = None):
    """LMS registration page - simple student registration only"""
    # Error messages
    error_messages = {
        "missing_fields": "All fields are required",
        "password_mismatch": "Passwords do not match",
        "password_short": "Password must be at least 8 characters",
        "user_exists": "User already exists. Please sign in instead.",
        "server_error": "An error occurred. Please try again."
    }
    
    return Div(
        # Header
        Div(
            H1("📚 Start Learning Today", cls="text-4xl font-bold mb-2"),
            P("Create your account and access thousands of courses", cls="text-xl text-gray-500 mb-8"),
            cls="text-center mb-8"
        ),
        
        # Error message
        (Div(
            P(f"⚠️ {error_messages.get(error, 'An error occurred')}", cls="text-error"),
            cls="alert alert-error max-w-md mx-auto mb-4"
        ) if error else None),
        
        # Registration Form
        Card(
            Form(
                # Email
                Div(
                    Label("Email", cls="label"),
                    Input(
                        type="email",
                        name="email",
                        placeholder="your@email.com",
                        required=True,
                        cls="input input-bordered w-full"
                    ),
                    cls="form-control mb-4"
                ),
                
                # Password
                Div(
                    Label("Password", cls="label"),
                    Input(
                        type="password",
                        name="password",
                        placeholder="••••••••",
                        required=True,
                        minlength="8",
                        cls="input input-bordered w-full"
                    ),
                    P("Minimum 8 characters", cls="text-sm text-gray-500 mt-1"),
                    cls="form-control mb-4"
                ),
                
                # Confirm Password
                Div(
                    Label("Confirm Password", cls="label"),
                    Input(
                        type="password",
                        name="confirm_password",
                        placeholder="••••••••",
                        required=True,
                        cls="input input-bordered w-full"
                    ),
                    cls="form-control mb-4"
                ),
                
                # Role selector
                Div(
                    Label("I am a:", cls="label"),
                    Select(
                        Option("Student", value="student", selected=True),
                        Option("Instructor", value="instructor"),
                        Option("Admin", value="admin"),
                        name="role",
                        required=True,
                        cls="select select-bordered w-full"
                    ),
                    cls="form-control mb-4"
                ),
                
                # Submit
                Button(
                    "Create Account & Start Learning",
                    type="submit",
                    cls="btn btn-primary w-full btn-lg"
                ),
                
                # Login link
                Div(
                    Span("Already have an account? ", cls="text-gray-500"),
                    A("Sign in", href=f"/lms-example/login?redirect={redirect_url}", cls="link link-primary"),
                    cls="text-center mt-4"
                ),
                
                method="post",
                action=f"/lms-example/auth/register?redirect={redirect_url}"
            ),
            cls="max-w-md mx-auto p-8"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
