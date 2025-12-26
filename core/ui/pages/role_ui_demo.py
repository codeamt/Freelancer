"""Demo page for role-based UI components"""

from fasthtml.common import *
from monsterui.all import *
from core.ui.helpers.role_ui import (
    RoleUI, if_role, if_any_role, if_all_roles, if_can_access,
    RoleBadge, UserMenu
)
from core.services.auth.models import UserRole
from core.services.auth.role_hierarchy import RoleHierarchy


class RoleUIDemoPage:
    """Demo page showing role-based UI components"""
    
    def render(self, request):
        user = getattr(request.state, 'user', None)
        user_roles = getattr(user, 'roles', []) if user else []
        
        return Title("Role UI Demo"), Main(
            Header(
                H1("Role-Based UI Demo", cls="uk-heading-small"),
                P(f"This page demonstrates role-based UI components."),
                cls="uk-container uk-container-small uk-margin"
            ),
            
            Container(
                # User info section
                Card(
                    Header(H3("Current User Info")),
                    Body(
                        P(Strong("Email:"), f" {user.email if user else 'Not logged in'}"),
                        P(Strong("Roles:")),
                        Div(
                            *[RoleBadge([role]) for role in user_roles] if user_roles else 
                            [Span("No roles", cls="badge badge-gray")],
                            cls="flex gap-2 mt-2"
                        ),
                        P(Strong("Primary Role:"), f" {RoleHierarchy.get_primary_role(user_roles).value if user_roles else 'None'}"),
                        P(Strong("Hierarchy Level:"), f" {RoleHierarchy.get_hierarchy_level(RoleHierarchy.get_primary_role(user_roles)) if user_roles else 'N/A'}")
                    )
                ),
                
                # Role-based visibility examples
                Card(
                    Header(H3("Role-Based Visibility Examples")),
                    Body(
                        H4("Content visible to different roles:"),
                        
                        # Guest content (always visible)
                        Div(
                            H5("Guest Content", cls="text-muted"),
                            P("This content is visible to everyone."),
                            cls="alert alert-secondary mb-3"
                        ),
                        
                        # User-only content
                        if_role(user_roles, UserRole.USER,
                            Div(
                                H5("User Content", cls="text-primary"),
                                P("This content is only visible to users and above."),
                                cls="alert alert-primary mb-3"
                            ),
                            ""
                        ),
                        
                        # Editor-only content
                        if_role(user_roles, UserRole.EDITOR,
                            Div(
                                H5("Editor Content", cls="text-success"),
                                P("This content is only visible to editors and above."),
                                cls="alert alert-success mb-3"
                            ),
                            ""
                        ),
                        
                        # Admin-only content
                        if_role(user_roles, UserRole.ADMIN,
                            Div(
                                H5("Admin Content", cls="text-warning"),
                                P("This content is only visible to admins and super admins."),
                                cls="alert alert-warning mb-3"
                            ),
                            ""
                        ),
                        
                        # Super admin-only content
                        if_role(user_roles, UserRole.SUPER_ADMIN,
                            Div(
                                H5("Super Admin Content", cls="text-danger"),
                                P("This content is only visible to super admins."),
                                cls="alert alert-danger mb-3"
                            ),
                            ""
                        ),
                        
                        # Multiple role check
                        if_any_role(user_roles, [UserRole.INSTRUCTOR, UserRole.ADMIN],
                            Div(
                                H5("Instructor or Admin Content", cls="text-info"),
                                P("This content is visible to instructors OR admins."),
                                cls="alert alert-info mb-3"
                            ),
                            ""
                        ),
                        
                        # Resource-based access
                        if_can_access(user_roles, "users",
                            Div(
                                H5("User Management Access", cls="text-dark"),
                                P("You can access user management."),
                                cls="alert alert-dark mb-3"
                            ),
                            "read",
                            ""
                        )
                    )
                ),
                
                # Role-based buttons
                Card(
                    Header(H3("Role-Based Buttons")),
                    Body(
                        H4("Buttons that appear based on your roles:"),
                        Div(
                            # Always visible
                            Button("Public Action", cls="btn btn-outline-primary mr-2 mb-2"),
                            
                            # User-only
                            if_role(user_roles, UserRole.USER,
                                Button("User Action", cls="btn btn-primary mr-2 mb-2"),
                                ""
                            ),
                            
                            # Editor-only
                            if_role(user_roles, UserRole.EDITOR,
                                Button("Editor Action", cls="btn btn-success mr-2 mb-2"),
                                ""
                            ),
                            
                            # Admin-only
                            if_role(user_roles, UserRole.ADMIN,
                                Button("Admin Action", cls="btn btn-warning mr-2 mb-2"),
                                ""
                            ),
                            
                            # Super admin-only
                            if_role(user_roles, UserRole.SUPER_ADMIN,
                                Button("Super Admin Action", cls="btn btn-danger mr-2 mb-2"),
                                ""
                            ),
                            
                            # Resource-based
                            if_can_access(user_roles, "content",
                                Button("Manage Content", cls="btn btn-info mr-2 mb-2"),
                                "write",
                                ""
                            )
                        )
                    )
                ),
                
                # Navigation menu example
                Card(
                    Header(H3("Role-Based Navigation")),
                    Body(
                        H4("Menu items based on your roles:"),
                        Nav(
                            Ul(
                                Li(A("Dashboard", href="/dashboard", cls="nav-link")),
                                Li(A("Profile", href="/profile", cls="nav-link")),
                                *UserMenu(user_roles)
                            ),
                            cls="nav flex-column"
                        )
                    )
                ),
                
                # Permission matrix
                Card(
                    Header(H3("Permission Matrix")),
                    Body(
                        Table(
                            Thead(
                                Tr(
                                    Th("Resource"),
                                    Th("Read"),
                                    Th("Write"),
                                    Th("Delete")
                                )
                            ),
                            Tbody(
                                *[
                                    Tr(
                                        Td(resource.capitalize()),
                                        Td("✓" if RoleUI.can_access_resource(user_roles, resource, "read") else "✗"),
                                        Td("✓" if RoleUI.can_access_resource(user_roles, resource, "write") else "✗"),
                                        Td("✓" if RoleUI.can_access_resource(user_roles, resource, "delete") else "✗")
                                    )
                                    for resource in ["users", "roles", "content", "courses", "blog", "analytics", "settings"]
                                ]
                            ),
                            cls="table table-striped"
                        )
                    )
                ),
                
                cls="uk-container uk-container-large uk-margin"
            ),
            
            Footer(
                Container(
                    P("FastApp Role-Based UI Demo", cls="text-center text-muted"),
                    cls="py-4"
                )
            )
        )
