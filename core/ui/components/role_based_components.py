"""Role-based UI components for FastApp"""

from typing import List, Optional
from fasthtml.common import *
from monsterui.all import *
from core.ui.helpers.role_ui import (
    RoleUI, if_role, if_any_role, if_all_roles, if_can_access,
    AdminOnly, SuperAdminOnly, InstructorOnly, EditorOnly,
    UserMenu, RoleBadge
)
from core.services.auth.models import UserRole
from core.services.auth.role_hierarchy import RoleHierarchy


class RoleBasedNav:
    """Navigation component that adapts based on user roles"""
    
    @staticmethod
    def render(user_roles: List[str]):
        """Render navigation menu with role-based items"""
        nav_items = []
        
        # Basic items for all users
        nav_items.append(
            Li(A("Home", href="/", cls="nav-link"))
        )
        
        # Dashboard for authenticated users
        if user_roles:
            nav_items.append(
                Li(A("Dashboard", href="/dashboard", cls="nav-link"))
            )
        
        # Content section for content creators and admins
        if RoleUI.can_access_resource(user_roles, "content", "read"):
            nav_items.append(
                Li(
                    Div("Content", cls="nav-link dropdown-toggle"),
                    Ul(
                        Li(A("Posts", href="/content/posts")),
                        Li(A("Media", href="/content/media")),
                        Li(A("Categories", href="/content/categories")),
                        cls="dropdown-menu"
                    ),
                    cls="nav-item dropdown"
                )
            )
        
        # Course section for instructors and admins
        if RoleUI.can_access_resource(user_roles, "courses", "read"):
            nav_items.append(
                Li(
                    Div("Courses", cls="nav-link dropdown-toggle"),
                    Ul(
                        Li(A("My Courses", href="/courses/my")),
                        Li(A("All Courses", href="/courses")),
                        if_can_access(user_roles, "courses",
                            Li(A("Create Course", href="/courses/create")),
                            "write",
                            ""
                        ),
                        cls="dropdown-menu"
                    ),
                    cls="nav-item dropdown"
                )
            )
        
        # Blog section for blog authors and admins
        if RoleUI.can_access_resource(user_roles, "blog", "read"):
            nav_items.append(
                Li(
                    Div("Blog", cls="nav-link dropdown-toggle"),
                    Ul(
                        Li(A("Blog Home", href="/blog")),
                        if_any_role(user_roles, [UserRole.BLOG_AUTHOR, UserRole.BLOG_ADMIN, UserRole.ADMIN],
                            Li(A("Write Post", href="/blog/write")),
                            ""
                        ),
                        if_can_access(user_roles, "blog",
                            Li(A("Manage Posts", href="/blog/admin")),
                            "write",
                            ""
                        ),
                        cls="dropdown-menu"
                    ),
                    cls="nav-item dropdown"
                )
            )
        
        # Admin section for admins only
        if RoleUI.has_role(user_roles, UserRole.ADMIN):
            nav_items.append(
                Li(
                    Div("Admin", cls="nav-link dropdown-toggle"),
                    Ul(
                        Li(A("Dashboard", href="/admin")),
                        if_can_access(user_roles, "users",
                            Li(A("Users", href="/admin/users")),
                            "read",
                            ""
                        ),
                        if_can_access(user_roles, "roles",
                            Li(A("Roles", href="/admin/roles")),
                            "read",
                            ""
                        ),
                        if_can_access(user_roles, "analytics",
                            Li(A("Analytics", href="/admin/analytics")),
                            "read",
                            ""
                        ),
                        if_can_access(user_roles, "settings",
                            Li(A("Settings", href="/admin/settings")),
                            "read",
                            ""
                        ),
                        cls="dropdown-menu"
                    ),
                    cls="nav-item dropdown"
                )
            )
        
        return Nav(
            Ul(*nav_items, cls="navbar-nav"),
            cls="navbar navbar-expand-lg"
        )


class RoleBasedDashboard:
    """Dashboard component that shows different widgets based on roles"""
    
    @staticmethod
    def render(user_roles: List[str]):
        """Render dashboard with role-appropriate widgets"""
        widgets = []
        
        # Welcome widget for all users
        widgets.append(
            Div(
                H3("Welcome to FastApp!"),
                P("This is your personalized dashboard."),
                cls="card mb-4"
            )
        )
        
        # User info widget
        if user_roles:
            widgets.append(
                Div(
                    H4("Your Roles"),
                    Div(
                        *[RoleBadge([role]) for role in user_roles],
                        cls="flex gap-2 mb-2"
                    ),
                    P(f"Primary Role: {RoleHierarchy.get_primary_role(user_roles).value.title()}"),
                    cls="card mb-4"
                )
            )
        
        # Admin widgets
        if RoleUI.has_role(user_roles, UserRole.ADMIN):
            widgets.append(
                Div(
                    H4("Admin Quick Actions"),
                    Div(
                        if_can_access(user_roles, "users",
                            A("Manage Users", href="/admin/users", cls="btn btn-primary mr-2"),
                            "read",
                            ""
                        ),
                        if_can_access(user_roles, "roles",
                            A("Manage Roles", href="/admin/roles", cls="btn btn-secondary mr-2"),
                            "read",
                            ""
                        ),
                        if_can_access(user_roles, "analytics",
                            A("View Analytics", href="/admin/analytics", cls="btn btn-info"),
                            "read",
                            ""
                        ),
                        cls="card-body"
                    ),
                    cls="card mb-4"
                )
            )
        
        # Instructor widgets
        if RoleUI.has_role(user_roles, UserRole.INSTRUCTOR):
            widgets.append(
                Div(
                    H4("Instructor Tools"),
                    Div(
                        A("My Courses", href="/instructor/courses", cls="btn btn-primary mr-2"),
                        A("Create Course", href="/courses/create", cls="btn btn-success"),
                        cls="card-body"
                    ),
                    cls="card mb-4"
                )
            )
        
        # Student widgets
        if RoleUI.has_role(user_roles, UserRole.STUDENT):
            widgets.append(
                Div(
                    H4("My Learning"),
                    Div(
                        A("My Courses", href="/student/courses", cls="btn btn-primary mr-2"),
                        A("Progress", href="/student/progress", cls="btn btn-info"),
                        cls="card-body"
                    ),
                    cls="card mb-4"
                )
            )
        
        # Blog author widgets
        if RoleUI.has_any_role(user_roles, [UserRole.BLOG_AUTHOR, UserRole.BLOG_ADMIN]):
            widgets.append(
                Div(
                    H4("Blog Management"),
                    Div(
                        A("Write Post", href="/blog/write", cls="btn btn-primary mr-2"),
                        A("My Posts", href="/blog/my-posts", cls="btn btn-secondary"),
                        cls="card-body"
                    ),
                    cls="card mb-4"
                )
            )
        
        return Div(*widgets, cls="container-fluid")


class RoleBasedButton:
    """Button that shows/hides based on roles"""
    
    @staticmethod
    def create(text: str, href: str, required_roles: List[str], 
               require_all: bool = False, cls: str = "btn btn-primary"):
        """Create a button that's visible only to users with required roles"""
        button = A(text, href=href, cls=cls)
        
        if require_all:
            return if_all_roles([], required_roles, button, "")
        else:
            return if_any_role([], required_roles, button, "")
    
    @staticmethod
    def create_resource(text: str, href: str, resource: str, 
                       action: str = "read", cls: str = "btn btn-primary"):
        """Create a button for resource-specific access"""
        button = A(text, href=href, cls=cls)
        return if_can_access([], resource, button, action, "")


class RoleBasedCard:
    """Card component that shows/hides based on roles"""
    
    @staticmethod
    def create(title: str, content, required_roles: List[str] = None,
               resource: str = None, action: str = "read", cls: str = "card"):
        """Create a card that's visible only to users with required roles"""
        card = Div(
            Div(H4(title), cls="card-header"),
            Div(content, cls="card-body"),
            cls=cls
        )
        
        if resource:
            return if_can_access([], resource, card, action, "")
        elif required_roles:
            return if_any_role([], required_roles, card, "")
        else:
            return card


# Example usage in a FastHTML route
def render_dashboard_page(request: Request):
    """Example of how to use role-based components"""
    user = getattr(request.state, 'user', None)
    user_roles = getattr(user, 'roles', []) if user else []
    
    return Title("Dashboard"), Main(
        Header(RoleBasedNav.render(user_roles)),
        Container(
            H1("Dashboard"),
            RoleBasedDashboard.render(user_roles)
        )
    )


# Example of role-based forms
def RoleBasedForm(user_roles: List[str]):
    """Generate form fields based on user roles"""
    fields = []
    
    # Basic fields for all users
    fields.extend([
        Div(Label("Name"), Input(type="text", name="name"), cls="form-group"),
        Div(Label("Email"), Input(type="email", name="email"), cls="form-group")
    ])
    
    # Admin-only fields
    fields.append(
        if_role(user_roles, UserRole.ADMIN,
            Div(Label("Admin Notes"), Textarea(name="admin_notes"), cls="form-group"),
            ""
        )
    )
    
    # Super-admin-only fields
    fields.append(
        if_role(user_roles, UserRole.SUPER_ADMIN,
            Div(Label("System Access"), Select(
                Option("None", value="none"),
                Option("Read", value="read"),
                Option("Write", value="write"),
                Option("Full", value="full"),
                name="system_access"
            ), cls="form-group"),
            ""
        )
    )
    
    return Form(*fields, Button("Submit", cls="btn btn-primary"), cls="form")
