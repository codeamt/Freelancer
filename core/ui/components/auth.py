"""
Consolidated Auth UI Components - Reusable authentication forms.

Eliminates duplicate login/register forms across example apps.
"""
from fasthtml.common import *
from monsterui.all import *
from typing import Optional


def LoginForm(
    action: str = "/auth/login",
    redirect_to: Optional[str] = None,
    title: str = "Sign In",
    subtitle: Optional[str] = None,
    show_register_link: bool = True,
    register_href: str = "/auth/register"
) -> Div:
    """
    Reusable login form component.
    
    Args:
        action: Form submission endpoint
        redirect_to: URL to redirect after login
        title: Form title
        subtitle: Optional subtitle text
        show_register_link: Show "Create account" link
        register_href: Register page URL
        
    Returns:
        Styled login form
    """
    return Div(
        Card(
            CardBody(
                Div(
                    H2(title, cls="text-3xl font-bold text-center mb-2"),
                    P(subtitle, cls="text-center text-gray-500 mb-6") if subtitle else None,
                    cls="mb-6"
                ),
                Form(
                    Div(
                        Label("Email", cls="label"),
                        Input(
                            type="email",
                            name="email",
                            placeholder="Enter your email",
                            required=True,
                            cls="input input-bordered w-full"
                        ),
                        cls="form-control mb-4"
                    ),
                    Div(
                        Label("Password", cls="label"),
                        Input(
                            type="password",
                            name="password",
                            placeholder="Enter your password",
                            required=True,
                            cls="input input-bordered w-full"
                        ),
                        cls="form-control mb-4"
                    ),
                    Div(
                        Label(
                            Input(type="checkbox", name="remember", cls="checkbox checkbox-sm"),
                            Span("Remember me", cls="ml-2"),
                            cls="label cursor-pointer justify-start"
                        ),
                        A("Forgot password?", href="/auth/forgot-password", cls="link link-primary text-sm"),
                        cls="flex justify-between items-center mb-6"
                    ),
                    Input(type="hidden", name="redirect_to", value=redirect_to) if redirect_to else None,
                    Button("Sign In", type="submit", cls="btn btn-primary w-full mb-4"),
                    Div(
                        Span("Don't have an account? ", cls="text-gray-600"),
                        A("Create one", href=register_href, cls="link link-primary font-semibold"),
                        cls="text-center"
                    ) if show_register_link else None,
                    method="POST",
                    action=action,
                    cls="space-y-4"
                ),
                cls="p-8"
            ),
            cls="max-w-md mx-auto shadow-xl"
        ),
        cls="min-h-screen flex items-center justify-center bg-base-200 p-4"
    )


def RegisterForm(
    action: str = "/auth/register",
    redirect_to: Optional[str] = None,
    title: str = "Create Account",
    subtitle: Optional[str] = None,
    show_login_link: bool = True,
    login_href: str = "/auth/login",
    require_terms: bool = True
) -> Div:
    """
    Reusable registration form component.
    
    Args:
        action: Form submission endpoint
        redirect_to: URL to redirect after registration
        title: Form title
        subtitle: Optional subtitle text
        show_login_link: Show "Already have account" link
        login_href: Login page URL
        require_terms: Require terms acceptance checkbox
        
    Returns:
        Styled registration form
    """
    return Div(
        Card(
            CardBody(
                Div(
                    H2(title, cls="text-3xl font-bold text-center mb-2"),
                    P(subtitle, cls="text-center text-gray-500 mb-6") if subtitle else None,
                    cls="mb-6"
                ),
                Form(
                    Div(
                        Label("Full Name", cls="label"),
                        Input(type="text", name="name", placeholder="Enter your full name", required=True, cls="input input-bordered w-full"),
                        cls="form-control mb-4"
                    ),
                    Div(
                        Label("Email", cls="label"),
                        Input(type="email", name="email", placeholder="Enter your email", required=True, cls="input input-bordered w-full"),
                        cls="form-control mb-4"
                    ),
                    Div(
                        Label("Password", cls="label"),
                        Input(type="password", name="password", placeholder="Create a password", required=True, minlength="8", cls="input input-bordered w-full"),
                        Span("Minimum 8 characters", cls="text-xs text-gray-500 mt-1"),
                        cls="form-control mb-4"
                    ),
                    Div(
                        Label("Confirm Password", cls="label"),
                        Input(type="password", name="confirm_password", placeholder="Confirm your password", required=True, cls="input input-bordered w-full"),
                        cls="form-control mb-4"
                    ),
                    Div(
                        Label(
                            Input(type="checkbox", name="accept_terms", required=require_terms, cls="checkbox checkbox-sm"),
                            Span(
                                "I agree to the ",
                                A("Terms of Service", href="/terms", cls="link link-primary", target="_blank"),
                                " and ",
                                A("Privacy Policy", href="/privacy", cls="link link-primary", target="_blank"),
                                cls="ml-2 text-sm"
                            ),
                            cls="label cursor-pointer justify-start"
                        ),
                        cls="mb-6"
                    ) if require_terms else None,
                    Input(type="hidden", name="redirect_to", value=redirect_to) if redirect_to else None,
                    Button("Create Account", type="submit", cls="btn btn-primary w-full mb-4"),
                    Div(
                        Span("Already have an account? ", cls="text-gray-600"),
                        A("Sign in", href=login_href, cls="link link-primary font-semibold"),
                        cls="text-center"
                    ) if show_login_link else None,
                    method="POST",
                    action=action,
                    cls="space-y-4"
                ),
                cls="p-8"
            ),
            cls="max-w-md mx-auto shadow-xl"
        ),
        cls="min-h-screen flex items-center justify-center bg-base-200 p-4"
    )
