"""Profile Page - Migrated from core"""
from fasthtml.common import *
from monsterui.all import *

def ProfilePage(user: dict):
    """User profile page with edit capabilities"""
    return Div(
        # Profile Header
        Card(
            Div(
                Div(
                    Div(
                        Div(
                            Span(user.get("username", "U")[0].upper(), 
                                 cls="text-4xl font-bold"),
                            cls="avatar placeholder"
                        ),
                        cls="w-24 h-24 rounded-full bg-primary text-primary-content flex items-center justify-center"
                    ),
                    Div(
                        H2(user.get("username", "User"), cls="text-2xl font-bold"),
                        P(user.get("email", ""), cls="text-gray-500"),
                        Div(
                            *[Span(role.capitalize(), cls="badge badge-primary mr-2") 
                              for role in user.get("roles", ["user"])],
                            cls="mt-2"
                        ),
                        cls="ml-6"
                    ),
                    cls="flex items-center"
                ),
                cls="card-body"
            ),
            cls="mb-6"
        ),
        
        # Profile Information
        Div(
            # Edit Profile Form
            Card(
                Div(
                    H3("Profile Information", cls="text-xl font-bold mb-4"),
                    Form(
                        Div(
                            Label("Username", fr="username", cls="block text-sm font-medium mb-2"),
                            Input(
                                type="text",
                                id="username",
                                name="username",
                                value=user.get("username", ""),
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
                                value=user.get("email", ""),
                                cls="input input-bordered w-full",
                                required=True
                            ),
                            cls="mb-4"
                        ),
                        Div(
                            Label("Full Name", fr="full_name", cls="block text-sm font-medium mb-2"),
                            Input(
                                type="text",
                                id="full_name",
                                name="full_name",
                                value=user.get("full_name", ""),
                                cls="input input-bordered w-full"
                            ),
                            cls="mb-4"
                        ),
                        Div(
                            Label("Bio", fr="bio", cls="block text-sm font-medium mb-2"),
                            Textarea(
                                user.get("bio", ""),
                                id="bio",
                                name="bio",
                                cls="textarea textarea-bordered w-full",
                                rows="4"
                            ),
                            cls="mb-4"
                        ),
                        Button("Update Profile", type="submit", cls="btn btn-primary"),
                        hx_put=f"/auth/profile/{user.get('_id')}",
                        hx_target="#profile-result",
                        hx_swap="innerHTML"
                    ),
                    Div(id="profile-result", cls="mt-4"),
                    cls="card-body"
                )
            ),
            
            # Change Password
            Card(
                Div(
                    H3("Change Password", cls="text-xl font-bold mb-4"),
                    Form(
                        Div(
                            Label("Current Password", fr="old_password", cls="block text-sm font-medium mb-2"),
                            Input(
                                type="password",
                                id="old_password",
                                name="old_password",
                                cls="input input-bordered w-full",
                                required=True
                            ),
                            cls="mb-4"
                        ),
                        Div(
                            Label("New Password", fr="new_password", cls="block text-sm font-medium mb-2"),
                            Input(
                                type="password",
                                id="new_password",
                                name="new_password",
                                cls="input input-bordered w-full",
                                required=True,
                                minlength="8"
                            ),
                            cls="mb-4"
                        ),
                        Div(
                            Label("Confirm New Password", fr="confirm_password", cls="block text-sm font-medium mb-2"),
                            Input(
                                type="password",
                                id="confirm_password",
                                name="confirm_password",
                                cls="input input-bordered w-full",
                                required=True
                            ),
                            cls="mb-4"
                        ),
                        Button("Change Password", type="submit", cls="btn btn-secondary"),
                        hx_post="/auth/password/change",
                        hx_target="#password-result",
                        hx_swap="innerHTML"
                    ),
                    Div(id="password-result", cls="mt-4"),
                    cls="card-body"
                ),
                cls="mt-6"
            ),
            cls="grid grid-cols-1 gap-6"
        ),
        cls="container mx-auto px-4 py-8 max-w-4xl"
    )
