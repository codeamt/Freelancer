"""
Web Admin Authentication Page

Separate auth page for web administrators (super_admin, admin roles)
that leads to the site and theme editor.
"""
from fasthtml.common import *
from monsterui.all import *
from typing import Optional


def WebAdminAuthPage(
    error: Optional[str] = None,
    success: Optional[str] = None,
    redirect_url: Optional[str] = None
):
    """
    Web Admin authentication page - separate from regular user auth.
    
    This is for platform administrators who manage the site, themes,
    and overall platform configuration.
    """
    
    content = Div(
        # Header with back button
        Div(
            A(
                UkIcon("arrow-left", width="20", height="20", cls="mr-2"),
                "Back to User Login",
                href="/auth",
                cls="btn btn-ghost btn-sm"
            ),
            cls="mb-8"
        ),
        
        # Admin Auth Card
        Div(
            Div(
                # Admin badge
                Div(
                    UkIcon("shield", width="32", height="32", cls="text-primary"),
                    cls="flex justify-center mb-4"
                ),
                
                # Title
                H1("Web Admin Portal", cls="text-3xl font-bold text-center mb-2"),
                P("Access site management, theme editor, and platform settings", cls="text-center text-gray-600 mb-8"),
                
                # Alert messages
                (Div(
                    P(error, cls="text-error"),
                    cls="alert alert-error mb-4"
                ) if error else None),
                
                (Div(
                    P(success, cls="text-success"),
                    cls="alert alert-success mb-4"
                ) if success else None),
                
                # Admin notice
                Div(
                    UkIcon("info", width="16", height="16", cls="mr-2"),
                    Span("This portal is for platform administrators only. Regular users should use the ", cls="text-sm"),
                    A("standard login", href="/auth", cls="link link-primary text-sm"),
                    Span(".", cls="text-sm"),
                    cls="alert alert-info mb-6 flex items-center"
                ),
                
                # Login Form
                Form(
                    Div(
                        Label("Admin Email", cls="label"),
                        Input(
                            type="email",
                            name="email",
                            placeholder="admin@example.com",
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
                    Input(
                        type="hidden",
                        name="redirect",
                        value=redirect_url or "/admin/dashboard"
                    ),
                    Input(
                        type="hidden",
                        name="require_admin",
                        value="true"
                    ),
                    Button(
                        UkIcon("lock", width="18", height="18", cls="mr-2"),
                        "Sign In as Admin",
                        type="submit",
                        cls="btn btn-primary w-full"
                    ),
                    method="post",
                    action="/admin/auth/login"
                ),
                
                # Quick links
                Div(
                    Div(cls="divider", data_content="Admin Resources"),
                    Div(
                        A(
                            UkIcon("book-open", width="16", height="16", cls="mr-1"),
                            "Admin Documentation",
                            href="/docs/admin",
                            cls="link link-hover text-sm"
                        ),
                        A(
                            UkIcon("help-circle", width="16", height="16", cls="mr-1"),
                            "Support",
                            href="/support",
                            cls="link link-hover text-sm"
                        ),
                        cls="flex justify-center gap-6"
                    ),
                    cls="mt-6"
                ),
                
                cls="p-8"
            ),
            cls="card bg-base-100 shadow-xl max-w-md w-full border-2 border-primary/20"
        ),
        
        cls="container mx-auto px-4 py-8 flex flex-col items-center min-h-screen justify-center"
    )
    
    return content


def WebAdminDashboard(user: dict, metrics: Optional[dict] = None):
    """
    Web Admin dashboard with links to site editor, theme editor, and settings.
    """
    if not metrics:
        metrics = {
            "total_users": 0,
            "active_sessions": 0,
            "page_views_today": 0,
            "pending_updates": 0
        }
    
    return Div(
        # Header
        Div(
            Div(
                H1("Web Admin Dashboard", cls="text-3xl font-bold"),
                P(f"Welcome back, {user.get('email', 'Admin')}", cls="text-gray-600"),
                cls="flex-1"
            ),
            Div(
                A(
                    UkIcon("log-out", width="18", height="18", cls="mr-2"),
                    "Logout",
                    href="/auth/logout",
                    cls="btn btn-ghost btn-sm"
                ),
            ),
            cls="flex justify-between items-center mb-8"
        ),
        
        # Quick Stats
        Div(
            Div(
                Div(
                    UkIcon("users", width="24", height="24", cls="text-blue-500"),
                    cls="mb-2"
                ),
                H3(str(metrics.get("total_users", 0)), cls="text-3xl font-bold"),
                P("Total Users", cls="text-gray-600 text-sm"),
                cls="stat bg-base-100 rounded-lg shadow p-4"
            ),
            Div(
                Div(
                    UkIcon("activity", width="24", height="24", cls="text-green-500"),
                    cls="mb-2"
                ),
                H3(str(metrics.get("active_sessions", 0)), cls="text-3xl font-bold"),
                P("Active Sessions", cls="text-gray-600 text-sm"),
                cls="stat bg-base-100 rounded-lg shadow p-4"
            ),
            Div(
                Div(
                    UkIcon("eye", width="24", height="24", cls="text-purple-500"),
                    cls="mb-2"
                ),
                H3(str(metrics.get("page_views_today", 0)), cls="text-3xl font-bold"),
                P("Page Views Today", cls="text-gray-600 text-sm"),
                cls="stat bg-base-100 rounded-lg shadow p-4"
            ),
            Div(
                Div(
                    UkIcon("alert-circle", width="24", height="24", cls="text-orange-500"),
                    cls="mb-2"
                ),
                H3(str(metrics.get("pending_updates", 0)), cls="text-3xl font-bold"),
                P("Pending Updates", cls="text-gray-600 text-sm"),
                cls="stat bg-base-100 rounded-lg shadow p-4"
            ),
            cls="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
        ),
        
        # Main Actions
        H2("Site Management", cls="text-2xl font-bold mb-4"),
        Div(
            # Site Editor
            A(
                Div(
                    Div(
                        UkIcon("layout", width="32", height="32", cls="text-primary"),
                        cls="mb-4"
                    ),
                    H3("Site Editor", cls="text-xl font-bold mb-2"),
                    P("Manage site structure, sections, and components", cls="text-gray-600 text-sm"),
                    cls="p-6"
                ),
                href="/admin/site/components",
                cls="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
            ),
            
            # Theme Editor
            A(
                Div(
                    Div(
                        UkIcon("palette", width="32", height="32", cls="text-secondary"),
                        cls="mb-4"
                    ),
                    H3("Theme Editor", cls="text-xl font-bold mb-2"),
                    P("Customize colors, typography, and styling", cls="text-gray-600 text-sm"),
                    cls="p-6"
                ),
                href="/admin/site/theme",
                cls="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
            ),
            
            # User Management
            A(
                Div(
                    Div(
                        UkIcon("users", width="32", height="32", cls="text-accent"),
                        cls="mb-4"
                    ),
                    H3("User Management", cls="text-xl font-bold mb-2"),
                    P("Manage users, roles, and permissions", cls="text-gray-600 text-sm"),
                    cls="p-6"
                ),
                href="/admin/users",
                cls="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
            ),
            
            # Settings
            A(
                Div(
                    Div(
                        UkIcon("settings", width="32", height="32", cls="text-neutral"),
                        cls="mb-4"
                    ),
                    H3("Platform Settings", cls="text-xl font-bold mb-2"),
                    P("Configure platform-wide settings and integrations", cls="text-gray-600 text-sm"),
                    cls="p-6"
                ),
                href="/settings",
                cls="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
            ),
            
            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        ),
        
        # Preview & Publish
        H2("Publishing", cls="text-2xl font-bold mb-4"),
        Div(
            Div(
                Div(
                    H3("Draft Version", cls="text-lg font-bold mb-2"),
                    P("Preview and test changes before publishing", cls="text-gray-600 text-sm mb-4"),
                    A("Preview Site", href="/admin/site/preview", cls="btn btn-outline btn-sm"),
                    cls="p-4"
                ),
                cls="card bg-base-100 shadow"
            ),
            Div(
                Div(
                    H3("Publish Changes", cls="text-lg font-bold mb-2"),
                    P("Push draft changes to the live site", cls="text-gray-600 text-sm mb-4"),
                    A("Compare & Publish", href="/admin/site/compare", cls="btn btn-primary btn-sm"),
                    cls="p-4"
                ),
                cls="card bg-base-100 shadow"
            ),
            Div(
                Div(
                    H3("Version History", cls="text-lg font-bold mb-2"),
                    P("View and rollback to previous versions", cls="text-gray-600 text-sm mb-4"),
                    A("View History", href="/admin/site/history", cls="btn btn-ghost btn-sm"),
                    cls="p-4"
                ),
                cls="card bg-base-100 shadow"
            ),
            cls="grid grid-cols-1 md:grid-cols-3 gap-4"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
