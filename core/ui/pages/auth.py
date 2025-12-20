"""
Unified Auth Page with Tabbed Login/Register Forms

Provides a single auth page with tabs for login and register, with addon-aware
role selectors that dynamically load based on enabled addons.
"""
from fasthtml.common import *
from monsterui.all import *
from typing import Optional, List, Dict


def get_addon_roles() -> List[Dict[str, str]]:
    """
    Get available roles from enabled addons.
    
    Returns:
        List of role dictionaries with 'value', 'label', and 'addon' keys
    """
    try:
        from core.addon_loader import get_addon_loader
        
        addon_loader = get_addon_loader()
        roles = []
        
        # Add default roles
        roles.append({"value": "user", "label": "User", "addon": "core"})
        roles.append({"value": "admin", "label": "Administrator", "addon": "core"})
        
        # Add addon-specific roles
        for domain, manifest in addon_loader.loaded_addons.items():
            if hasattr(manifest, 'roles') and manifest.roles:
                for role in manifest.roles:
                    roles.append({
                        "value": role.id,
                        "label": role.name,
                        "addon": domain
                    })
        
        return roles
    except Exception as e:
        # Fallback to basic roles if addon system not available
        return [
            {"value": "user", "label": "User", "addon": "core"},
            {"value": "admin", "label": "Administrator", "addon": "core"}
        ]


def AuthPage(
    error: Optional[str] = None,
    success: Optional[str] = None,
    default_tab: str = "login",
    show_role_selector: bool = True,
    redirect_url: Optional[str] = None
):
    """
    Unified authentication page with tabbed login/register forms.
    
    Args:
        error: Error message to display
        success: Success message to display
        default_tab: Which tab to show by default ('login' or 'register')
        show_role_selector: Whether to show role selector in registration
        redirect_url: URL to redirect to after successful auth
    """
    
    # Get available roles from enabled addons
    available_roles = get_addon_roles() if show_role_selector else []
    
    # Build role selector options
    role_options = []
    if show_role_selector and available_roles:
        # Group roles by addon
        core_roles = [r for r in available_roles if r["addon"] == "core"]
        addon_roles = [r for r in available_roles if r["addon"] != "core"]
        
        # Add core roles
        for role in core_roles:
            role_options.append(Option(role["label"], value=role["value"]))
        
        # Add addon roles with optgroup
        if addon_roles:
            addons_seen = set()
            for role in addon_roles:
                addon = role["addon"]
                if addon not in addons_seen:
                    addons_seen.add(addon)
                    # Add optgroup for this addon
                    addon_role_group = [r for r in addon_roles if r["addon"] == addon]
                    role_options.append(
                        Optgroup(
                            *[Option(r["label"], value=r["value"]) for r in addon_role_group],
                            label=f"{addon.title()} Roles"
                        )
                    )
    
    content = Div(
        # Header with back button
        Div(
            A(
                UkIcon("arrow-left", width="20", height="20", cls="mr-2"),
                "Back to Home",
                href="/",
                cls="btn btn-ghost btn-sm"
            ),
            cls="mb-8"
        ),
        
        # Auth Card
        Div(
            Div(
                # Title
                H1("Welcome to FastApp", cls="text-3xl font-bold text-center mb-2"),
                P("Sign in to your account or create a new one", cls="text-center text-gray-600 mb-8"),
                
                # Alert messages
                (Div(
                    P(error, cls="text-error"),
                    cls="alert alert-error mb-4"
                ) if error else None),
                
                (Div(
                    P(success, cls="text-success"),
                    cls="alert alert-success mb-4"
                ) if success else None),
                
                # Tabs
                Div(
                    # Tab buttons
                    Div(
                        Button(
                            "Login",
                            cls=f"tab tab-lifted {'tab-active' if default_tab == 'login' else ''}",
                            hx_get="/auth/page?tab=login" + (f"&redirect={redirect_url}" if redirect_url else ""),
                            hx_target="#auth-content",
                            hx_swap="innerHTML"
                        ),
                        Button(
                            "Register",
                            cls=f"tab tab-lifted {'tab-active' if default_tab == 'register' else ''}",
                            hx_get="/auth/page?tab=register" + (f"&redirect={redirect_url}" if redirect_url else ""),
                            hx_target="#auth-content",
                            hx_swap="innerHTML"
                        ),
                        cls="tabs tabs-lifted mb-0"
                    ),
                    
                    # Tab content
                    Div(
                        # Login Form
                        (Div(
                            Form(
                                Div(
                                    Label("Email", cls="label"),
                                    Input(
                                        type="email",
                                        name="email",
                                        placeholder="your@email.com",
                                        cls="input input-bordered w-full",
                                        required=True
                                    ),
                                    cls="form-control mb-4"
                                ),
                                Div(
                                    Label("Password", cls="label"),
                                    Input(
                                        type="password",
                                        name="password",
                                        placeholder="••••••••",
                                        cls="input input-bordered w-full",
                                        required=True
                                    ),
                                    cls="form-control mb-4"
                                ),
                                (Input(
                                    type="hidden",
                                    name="redirect",
                                    value=redirect_url
                                ) if redirect_url else None),
                                Div(
                                    A("Forgot password?", href="/auth/forgot-password", cls="link link-primary text-sm"),
                                    cls="mb-4"
                                ),
                                Button(
                                    "Sign In",
                                    type="submit",
                                    cls="btn btn-primary w-full"
                                ),
                                method="post",
                                action="/auth/login"
                            ),
                            # Divider
                            Div(
                                Div(cls="divider", text="OR"),
                                cls="my-4"
                            ),
                            # OAuth Buttons
                            Div(
                                A(
                                    UkIcon("github", width="20", height="20", cls="mr-2"),
                                    "Continue with GitHub",
                                    href="/auth/github/login",
                                    cls="btn btn-outline w-full mb-3 flex items-center justify-center"
                                ),
                                A(
                                    Span("G", cls="font-bold text-lg mr-2"),
                                    "Continue with Google",
                                    href="/auth/google/login",
                                    cls="btn btn-outline w-full flex items-center justify-center"
                                ),
                                cls="mb-4"
                            ),
                            cls="p-6"
                        ) if default_tab == "login" else None),
                        
                        # Register Form
                        (Div(
                            Form(
                                Div(
                                    Label("Email", cls="label"),
                                    Input(
                                        type="email",
                                        name="email",
                                        placeholder="your@email.com",
                                        cls="input input-bordered w-full",
                                        required=True
                                    ),
                                    cls="form-control mb-4"
                                ),
                                Div(
                                    Label("Password", cls="label"),
                                    Input(
                                        type="password",
                                        name="password",
                                        placeholder="••••••••",
                                        cls="input input-bordered w-full",
                                        required=True,
                                        minlength="8"
                                    ),
                                    cls="form-control mb-4"
                                ),
                                Div(
                                    Label("Confirm Password", cls="label"),
                                    Input(
                                        type="password",
                                        name="confirm_password",
                                        placeholder="••••••••",
                                        cls="input input-bordered w-full",
                                        required=True,
                                        minlength="8"
                                    ),
                                    cls="form-control mb-4"
                                ),
                                (Div(
                                    Label("Account Type", cls="label"),
                                    Select(
                                        Option("Select an option", value="", selected=True, disabled=True),
                                        # Core roles (not grouped)
                                        *[Option(role["label"], value=role["value"]) for role in available_roles if role["addon"] == "core"],
                                        # Addon roles (grouped)
                                        *[
                                            Optgroup(
                                                *[Option(role["label"], value=role["value"]) for role in available_roles if role["addon"] == addon],
                                                label=f"{addon.upper()} Roles"
                                            )
                                            for addon in sorted(set(r["addon"] for r in available_roles if r["addon"] != "core"))
                                        ],
                                        name="role",
                                        cls="select select-bordered w-full"
                                    ),
                                    P("Select your account type based on how you'll use the platform", cls="text-sm text-gray-500 mt-1"),
                                    cls="form-control mb-4"
                                ) if show_role_selector else None),
                                (Input(
                                    type="hidden",
                                    name="redirect",
                                    value=redirect_url
                                ) if redirect_url else None),
                                Div(
                                    Label(
                                        Input(type="checkbox", name="terms", cls="checkbox checkbox-sm mr-2", required=True),
                                        Span("I agree to the ", cls="text-sm"),
                                        A("Terms of Service", href="/terms", cls="link link-primary text-sm"),
                                        Span(" and ", cls="text-sm"),
                                        A("Privacy Policy", href="/privacy", cls="link link-primary text-sm"),
                                        cls="label cursor-pointer justify-start"
                                    ),
                                    cls="mb-4"
                                ),
                                Button(
                                    "Create Account",
                                    type="submit",
                                    cls="btn btn-primary w-full"
                                ),
                                method="post",
                                action="/auth/register"
                            ),
                            # Divider
                            Div(
                                Div(cls="divider", text="OR"),
                                cls="my-4"
                            ),
                            # OAuth Buttons
                            Div(
                                A(
                                    UkIcon("github", width="20", height="20", cls="mr-2"),
                                    "Sign up with GitHub",
                                    href="/auth/github/login",
                                    cls="btn btn-outline w-full mb-3 flex items-center justify-center"
                                ),
                                A(
                                    Span("G", cls="font-bold text-lg mr-2"),
                                    "Sign up with Google",
                                    href="/auth/google/login",
                                    cls="btn btn-outline w-full flex items-center justify-center"
                                ),
                                cls="mb-4"
                            ),
                            cls="p-6"
                        ) if default_tab == "register" else None),
                        
                        id="auth-content",
                        cls="bg-base-100 border border-base-300 border-t-0 rounded-b-lg"
                    ),
                ),
                
                cls="card bg-base-100 shadow-xl max-w-md w-full"
            ),
            cls="flex justify-center items-center min-h-[600px]"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return content


def AuthTabContent(tab: str = "login", redirect_url: Optional[str] = None, show_role_selector: bool = True):
    """
    Returns just the tab content for HTMX swapping.
    
    Args:
        tab: Which tab content to return ('login' or 'register')
        redirect_url: URL to redirect to after successful auth
        show_role_selector: Whether to show role selector in registration
    """
    
    available_roles = get_addon_roles() if show_role_selector else []
    
    # Build role selector options
    role_options = []
    if show_role_selector and available_roles:
        core_roles = [r for r in available_roles if r["addon"] == "core"]
        addon_roles = [r for r in available_roles if r["addon"] != "core"]
        
        for role in core_roles:
            role_options.append(Option(role["label"], value=role["value"]))
        
        if addon_roles:
            addons_seen = set()
            for role in addon_roles:
                addon = role["addon"]
                if addon not in addons_seen:
                    addons_seen.add(addon)
                    addon_role_group = [r for r in addon_roles if r["addon"] == addon]
                    role_options.append(
                        Optgroup(
                            *[Option(r["label"], value=r["value"]) for r in addon_role_group],
                            label=f"{addon.title()} Roles"
                        )
                    )
    
    if tab == "login":
        return Div(
            Form(
                Div(
                    Label("Email", cls="label"),
                    Input(
                        type="email",
                        name="email",
                        placeholder="your@email.com",
                        cls="input input-bordered w-full",
                        required=True
                    ),
                    cls="form-control mb-4"
                ),
                Div(
                    Label("Password", cls="label"),
                    Input(
                        type="password",
                        name="password",
                        placeholder="••••••••",
                        cls="input input-bordered w-full",
                        required=True
                    ),
                    cls="form-control mb-4"
                ),
                (Input(
                    type="hidden",
                    name="redirect",
                    value=redirect_url
                ) if redirect_url else None),
                Div(
                    A("Forgot password?", href="/auth/forgot-password", cls="link link-primary text-sm"),
                    cls="mb-4"
                ),
                Button(
                    "Sign In",
                    type="submit",
                    cls="btn btn-primary w-full"
                ),
                method="post",
                action="/auth/login"
            ),
            # Divider
            Div(
                Div(cls="divider", text="OR"),
                cls="my-4"
            ),
            # OAuth Buttons
            Div(
                A(
                    UkIcon("github", width="20", height="20", cls="mr-2"),
                    "Continue with GitHub",
                    href="/auth/github/login",
                    cls="btn btn-outline w-full mb-3 flex items-center justify-center"
                ),
                A(
                    Span("G", cls="font-bold text-lg mr-2"),
                    "Continue with Google",
                    href="/auth/google/login",
                    cls="btn btn-outline w-full flex items-center justify-center"
                ),
                cls="mb-4"
            ),
            cls="p-6"
        )
    else:  # register
        return Div(
            Form(
                Div(
                    Label("Email", cls="label"),
                    Input(
                        type="email",
                        name="email",
                        placeholder="your@email.com",
                        cls="input input-bordered w-full",
                        required=True
                    ),
                    cls="form-control mb-4"
                ),
                Div(
                    Label("Password", cls="label"),
                    Input(
                        type="password",
                        name="password",
                        placeholder="••••••••",
                        cls="input input-bordered w-full",
                        required=True,
                        minlength="8"
                    ),
                    cls="form-control mb-4"
                ),
                Div(
                    Label("Confirm Password", cls="label"),
                    Input(
                        type="password",
                        name="confirm_password",
                        placeholder="••••••••",
                        cls="input input-bordered w-full",
                        required=True,
                        minlength="8"
                    ),
                    cls="form-control mb-4"
                ),
                (Div(
                    Label("Account Type", cls="label"),
                    Select(
                        *role_options,
                        name="role",
                        cls="select select-bordered w-full"
                    ),
                    P("Select your account type based on how you'll use the platform", cls="text-xs text-gray-500 mt-1"),
                    cls="form-control mb-4"
                ) if show_role_selector and role_options else None),
                (Input(
                    type="hidden",
                    name="redirect",
                    value=redirect_url
                ) if redirect_url else None),
                Div(
                    Label(
                        Input(type="checkbox", name="terms", cls="checkbox checkbox-sm mr-2", required=True),
                        Span("I agree to the ", cls="text-sm"),
                        A("Terms of Service", href="/terms", cls="link link-primary text-sm"),
                        Span(" and ", cls="text-sm"),
                        A("Privacy Policy", href="/privacy", cls="link link-primary text-sm"),
                        cls="label cursor-pointer justify-start"
                    ),
                    cls="mb-4"
                ),
                Button(
                    "Create Account",
                    type="submit",
                    cls="btn btn-primary w-full"
                ),
                method="post",
                action="/auth/register"
            ),
            # Divider
            Div(
                Div(cls="divider", text="OR"),
                cls="my-4"
            ),
            # OAuth Buttons
            Div(
                A(
                    UkIcon("github", width="20", height="20", cls="mr-2"),
                    "Sign up with GitHub",
                    href="/auth/github/login",
                    cls="btn btn-outline w-full mb-3 flex items-center justify-center"
                ),
                A(
                    Span("G", cls="font-bold text-lg mr-2"),
                    "Sign up with Google",
                    href="/auth/google/login",
                    cls="btn btn-outline w-full flex items-center justify-center"
                ),
                cls="mb-4"
            ),
            cls="p-6"
        )
