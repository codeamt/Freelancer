"""Clean Layout using FastHTML and MonsterUI"""
from fasthtml.common import *
from monsterui.all import *
from typing import Optional, Dict
from core.ui.components.cookie_consent import CookieConsentBanner

def Layout(
    page_content,
    title: str = "FastApp",
    current_path: str = "/",
    user: Optional[Dict] = None,
    cart_count: int = 0,
    show_auth: bool = False,
    demo: bool = False,
):
    """Global layout with MonsterUI components and user authentication
    
    Args:
        page_content: The main content to display
        title: Page title
        current_path: Current URL path
        user: User object if authenticated
        cart_count: Number of items in cart
        show_auth: Whether to show auth buttons/nav (True for demo apps, False for landing page)
        demo: Whether app is in demo mode (shows Addons dropdown if True, Blog link if False)
    """
    
    # Build nav items based on authentication status
    nav_items = [
        A("Home", href='/'),
        # Docs link with book icon
        A(
            UkIcon("book", cls="mr-1"),
            "Docs",
            href='/docs',
            cls="flex items-center gap-1"
        ),
        # GitHub repo link with icon
        A(
            UkIcon("github", cls="mr-1"),
            "Repo",
            href='https://github.com/codeamt/freelancer',
            target="_blank",
            cls="flex items-center gap-1"
        ),
    ]
    
    # Add demo-specific navigation: Addons dropdown for demo mode, Blog link otherwise
    if demo:
        nav_items.append(
            # Dropdown for example add-on apps
            Details(
                Summary(
                    UkIcon("grid", cls="mr-1"),
                    "Add-ons",
                    cls="flex items-center gap-1 cursor-pointer"
                ),
                Ul(
                    Li(A("🛍️ E-Shop", href='/eshop-example', cls="block px-4 py-2 hover:bg-base-200")),
                    Li(A("📚 LMS", href='/lms-example', cls="block px-4 py-2 hover:bg-base-200")),
                    Li(A("🌐 Social Network", href='/social-example', cls="block px-4 py-2 hover:bg-base-200")),
                    Li(A("📺 Streaming", href='/streaming-example', cls="block px-4 py-2 hover:bg-base-200")),
                    cls="menu bg-base-100 rounded-box shadow-lg absolute mt-2 w-56 z-50"
                ),
                cls="dropdown dropdown-end"
            )
        )
    else:
        nav_items.append(
            A(
                UkIcon("file-text", cls="mr-1"),
                "Blog",
                href='/blog',
                cls="flex items-center gap-1"
            )
        )
    
    # Add authenticated user items (only if show_auth is True)
    if show_auth:
        if user:
            # Determine dashboard link based on user role
            user_role = user.get("role", "user") if isinstance(user, dict) else getattr(user, "role", "user")
            dashboard_link = None
            dashboard_label = "Dashboard"
            
            if user_role in ["admin", "super_admin"]:
                dashboard_link = "/admin/dashboard"
                dashboard_label = "Admin Dashboard"
            elif user_role in ["instructor", "course_creator"]:
                dashboard_link = "/lms-example/instructor"
                dashboard_label = "Instructor Dashboard"
            elif user_role in ["shop_owner", "merchant"]:
                dashboard_link = "/eshop-example/admin"
                dashboard_label = "Shop Dashboard"
            
            nav_items.extend([
                # Cart icon with badge
                A(
                    Div(
                        UkIcon("shopping-cart", width="20", height="20"),
                        (Span(str(cart_count), cls="badge badge-sm badge-primary absolute -top-2 -right-2") if cart_count > 0 else None),
                        cls="relative"
                    ),
                    href='/eshop-example/cart',
                    cls="btn btn-ghost btn-sm",
                    title="Shopping Cart"
                ),
                # Dashboard link (role-based)
                (A(
                    UkIcon("layout-dashboard", width="20", height="20"),
                    href=dashboard_link,
                    cls="btn btn-ghost btn-sm",
                    title=dashboard_label
                ) if dashboard_link else None),
                # Settings icon
                A(
                    UkIcon("settings", width="20", height="20"),
                    href='/settings',
                    cls="btn btn-ghost btn-sm",
                    title="Settings"
                ),
                # Profile dropdown
                Details(
                    Summary(
                        Div(
                            UkIcon("user", width="20", height="20"),
                            Span(user.get("username", "User"), cls="ml-2 hidden md:inline"),
                            cls="flex items-center gap-1 cursor-pointer"
                        ),
                        cls="btn btn-ghost btn-sm"
                    ),
                    Ul(
                        # Dashboard link in dropdown too
                        (Li(A(
                            UkIcon("layout-dashboard", width="16", height="16", cls="mr-2"),
                            dashboard_label,
                            href=dashboard_link,
                            cls="flex items-center px-4 py-2 hover:bg-base-200"
                        )) if dashboard_link else None),
                        Li(A(
                            UkIcon("user", width="16", height="16", cls="mr-2"),
                            "Profile",
                            href='/profile',
                            cls="flex items-center px-4 py-2 hover:bg-base-200"
                        )),
                        Li(A(
                            UkIcon("settings", width="16", height="16", cls="mr-2"),
                            "Settings",
                            href='/settings',
                            cls="flex items-center px-4 py-2 hover:bg-base-200"
                        )),
                        Li(Div(cls="divider my-0")),
                        Li(Form(
                            Button(
                                UkIcon("log-out", width="16", height="16", cls="mr-2"),
                                "Logout",
                                type="submit",
                                cls="flex items-center px-4 py-2 hover:bg-base-200 text-error cursor-pointer w-full text-left bg-transparent border-0"
                            ),
                            method="post",
                            action="/auth/logout",
                            cls="m-0 p-0"
                        )),
                        cls="menu bg-base-100 rounded-box shadow-lg absolute mt-2 w-48 z-50 right-0"
                    ),
                    cls="dropdown dropdown-end"
                ),
            ])
        elif show_auth:
            # Add login/register buttons for non-authenticated users (only when show_auth=True)
            redirect_param = f"&redirect={current_path}" if current_path != "/" else ""
            nav_items.extend([
                A("Login", href=f'/auth?tab=login{redirect_param}', cls="btn btn-ghost btn-sm"),
                A("Register", href=f'/auth?tab=register{redirect_param}', cls="btn btn-primary btn-sm"),
            ])
    
    # Return Title and body content - FastHTML will wrap in proper structure
    return (
        Title(title),
        # Sticky nav wrapper
        Div(
            NavBar(
                *nav_items,
                brand=H3('FastApp')
            ),
            cls="sticky top-0 z-50 bg-base-100 border-b border-base-300"
        ),
        Div(
            page_content, 
            cls="container mx-auto px-4 py-8 pb-20"
        ),
        # Cookie consent banner (shows at very bottom, above footer)
        CookieConsentBanner(base_path=current_path.split('/')[1] if '/' in current_path and len(current_path) > 1 else ""),
        # Footer (fixed at bottom, below cookie banner when visible)
        Footer(
            Div(
                P("© 2025 FastApp. Built with FastHTML + MonsterUI.", cls=TextT.muted),
                cls="text-center py-4"
            ),
            id="main-footer",
            cls="fixed bottom-0 left-0 right-0 border-t bg-base-100 z-40"
        )
    )