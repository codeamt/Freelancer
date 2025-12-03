"""Clean Layout using FastHTML and MonsterUI"""
from fasthtml.common import *
from monsterui.all import *

def Layout(page_content, title: str = "FastApp", current_path: str = "/", user: dict = None, cart_count: int = 0, show_auth: bool = False):
    """Global layout with MonsterUI components and user authentication
    
    Args:
        page_content: The main content to display
        title: Page title
        current_path: Current URL path
        user: User object if authenticated
        cart_count: Number of items in cart
        show_auth: Whether to show auth buttons/nav (True for demo apps, False for landing page)
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
        ),
    ]
    
    # Add authenticated user items (only if show_auth is True)
    if show_auth:
        if user:
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
                # Settings icon
                A(
                    UkIcon("settings", width="20", height="20"),
                    href='/auth/settings',
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
                        Li(A(
                            UkIcon("user", width="16", height="16", cls="mr-2"),
                            "Profile",
                            href='/auth/profile',
                            cls="flex items-center px-4 py-2 hover:bg-base-200"
                        )),
                        Li(A(
                            UkIcon("settings", width="16", height="16", cls="mr-2"),
                            "Settings",
                            href='/auth/settings',
                            cls="flex items-center px-4 py-2 hover:bg-base-200"
                        )),
                        Li(Div(cls="divider my-0")),
                        Li(A(
                            UkIcon("log-out", width="16", height="16", cls="mr-2"),
                            "Logout",
                            href='/auth/logout',
                            cls="flex items-center px-4 py-2 hover:bg-base-200 text-error"
                        )),
                        cls="menu bg-base-100 rounded-box shadow-lg absolute mt-2 w-48 z-50 right-0"
                    ),
                    cls="dropdown dropdown-end"
                ),
            ])
        elif show_auth:
            # Add login/register buttons for non-authenticated users (only when show_auth=True)
            nav_items.extend([
                A("Login", href='/auth/login', cls="btn btn-ghost btn-sm"),
                A("Register", href='/auth/register', cls="btn btn-primary btn-sm"),
            ])
    
    # Return Title and body content - FastHTML will wrap in proper structure
    return (
        Title(title),
        NavBar(
            *nav_items,
            brand=H3('FastApp')
        ),
        Div(
            page_content, 
            cls="container mx-auto px-4 py-8 pb-20"
        ),
        # Footer (fixed at bottom)
        Footer(
            Div(
                P("© 2025 FastApp. Built with FastHTML + MonsterUI.", cls=TextT.muted),
                cls="text-center py-4"
            ),
            cls="fixed bottom-0 left-0 right-0 border-t bg-base-100 z-10"
        )
    )