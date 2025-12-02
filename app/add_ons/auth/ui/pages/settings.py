"""Account Settings Page"""
from fasthtml.common import *
from monsterui.all import *

def SettingsPage(user: dict):
    """
    Comprehensive account settings page.
    Includes account info, security, privacy, and preferences.
    """
    return Div(
        H1("Account Settings", cls="text-3xl font-bold mb-8"),
        
        # Settings Navigation Tabs
        Div(
            Div(
                A("Account", href="#account", cls="tab tab-bordered tab-active"),
                A("Security", href="#security", cls="tab tab-bordered"),
                A("Privacy", href="#privacy", cls="tab tab-bordered"),
                A("Notifications", href="#notifications", cls="tab tab-bordered"),
                cls="tabs tabs-boxed mb-6"
            ),
        ),
        
        # Account Settings Section
        Div(
            Card(
                Div(
                    H2("Account Information", cls="text-2xl font-bold mb-6"),
                    Form(
                        # Username
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
                            P("Your unique username across the platform", cls="text-xs text-gray-500 mt-1"),
                            cls="mb-4"
                        ),
                        
                        # Email
                        Div(
                            Label("Email Address", fr="email", cls="block text-sm font-medium mb-2"),
                            Input(
                                type="email",
                                id="email",
                                name="email",
                                value=user.get("email", ""),
                                cls="input input-bordered w-full",
                                required=True
                            ),
                            P("Used for login and notifications", cls="text-xs text-gray-500 mt-1"),
                            cls="mb-4"
                        ),
                        
                        # Full Name
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
                        
                        # Bio
                        Div(
                            Label("Bio", fr="bio", cls="block text-sm font-medium mb-2"),
                            Textarea(
                                user.get("bio", ""),
                                id="bio",
                                name="bio",
                                cls="textarea textarea-bordered w-full",
                                rows="4",
                                placeholder="Tell us about yourself..."
                            ),
                            cls="mb-6"
                        ),
                        
                        Button("Save Changes", type="submit", cls="btn btn-primary"),
                        hx_put=f"/auth/settings/account/{user.get('_id')}",
                        hx_target="#account-result",
                        hx_swap="innerHTML"
                    ),
                    Div(id="account-result", cls="mt-4"),
                    cls="card-body"
                ),
                id="account",
                cls="mb-6"
            ),
            
            # Security Settings Section
            Card(
                Div(
                    H2("Security Settings", cls="text-2xl font-bold mb-6"),
                    
                    # Change Password
                    Div(
                        H3("Change Password", cls="text-lg font-semibold mb-4"),
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
                                P("Minimum 8 characters", cls="text-xs text-gray-500 mt-1"),
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
                        cls="mb-8"
                    ),
                    
                    # Two-Factor Authentication
                    Div(
                        H3("Two-Factor Authentication", cls="text-lg font-semibold mb-4"),
                        Div(
                            Div(
                                UkIcon("shield", width="24", height="24", cls="text-blue-600"),
                                cls="mr-4"
                            ),
                            Div(
                                P("Add an extra layer of security to your account", cls="font-medium"),
                                P("Require a code from your phone in addition to your password", cls="text-sm text-gray-500"),
                                cls="flex-1"
                            ),
                            Button(
                                "Enable 2FA" if not user.get("two_factor_enabled") else "Disable 2FA",
                                cls="btn btn-outline btn-sm",
                                hx_post="/auth/settings/2fa/toggle",
                                hx_target="#2fa-result"
                            ),
                            cls="flex items-center"
                        ),
                        Div(id="2fa-result", cls="mt-4"),
                        cls="mb-8"
                    ),
                    
                    # Active Sessions
                    Div(
                        H3("Active Sessions", cls="text-lg font-semibold mb-4"),
                        P("Manage devices where you're currently logged in", cls="text-sm text-gray-500 mb-4"),
                        Div(
                            # Current session
                            Div(
                                Div(
                                    UkIcon("monitor", width="20", height="20", cls="mr-3"),
                                    Div(
                                        P("Current Device", cls="font-medium"),
                                        P("Last active: Just now", cls="text-xs text-gray-500"),
                                        cls="flex-1"
                                    ),
                                    Span("Active", cls="badge badge-success"),
                                    cls="flex items-center"
                                ),
                                cls="p-4 border rounded-lg mb-2"
                            ),
                            Button("Sign Out All Other Devices", cls="btn btn-outline btn-sm mt-4"),
                            cls="mb-4"
                        ),
                        cls="mb-8"
                    ),
                    
                    cls="card-body"
                ),
                id="security",
                cls="mb-6"
            ),
            
            # Privacy Settings Section
            Card(
                Div(
                    H2("Privacy Settings", cls="text-2xl font-bold mb-6"),
                    Form(
                        # Profile Visibility
                        Div(
                            Label("Profile Visibility", cls="block text-sm font-medium mb-2"),
                            Select(
                                Option("Public - Anyone can see your profile", value="public", selected=user.get("profile_visibility") == "public"),
                                Option("Private - Only you can see your profile", value="private", selected=user.get("profile_visibility") == "private"),
                                Option("Friends Only - Only connections can see", value="friends", selected=user.get("profile_visibility") == "friends"),
                                name="profile_visibility",
                                cls="select select-bordered w-full"
                            ),
                            cls="mb-4"
                        ),
                        
                        # Email Visibility
                        Div(
                            Label(
                                Input(type="checkbox", name="show_email", checked=user.get("show_email", False), cls="checkbox mr-2"),
                                "Show my email address on my profile",
                                cls="flex items-center cursor-pointer"
                            ),
                            cls="mb-4"
                        ),
                        
                        # Activity Visibility
                        Div(
                            Label(
                                Input(type="checkbox", name="show_activity", checked=user.get("show_activity", True), cls="checkbox mr-2"),
                                "Show my activity (courses, posts, etc.)",
                                cls="flex items-center cursor-pointer"
                            ),
                            cls="mb-6"
                        ),
                        
                        Button("Save Privacy Settings", type="submit", cls="btn btn-primary"),
                        hx_put=f"/auth/settings/privacy/{user.get('_id')}",
                        hx_target="#privacy-result",
                        hx_swap="innerHTML"
                    ),
                    Div(id="privacy-result", cls="mt-4"),
                    cls="card-body"
                ),
                id="privacy",
                cls="mb-6"
            ),
            
            # Notification Preferences Section
            Card(
                Div(
                    H2("Notification Preferences", cls="text-2xl font-bold mb-6"),
                    P("Choose how you want to be notified", cls="text-gray-500 mb-6"),
                    Form(
                        # Email Notifications
                        Div(
                            H3("Email Notifications", cls="text-lg font-semibold mb-4"),
                            Div(
                                Label(
                                    Input(type="checkbox", name="email_login", checked=user.get("email_login", True), cls="checkbox mr-2"),
                                    "New login from unrecognized device",
                                    cls="flex items-center cursor-pointer mb-3"
                                ),
                                Label(
                                    Input(type="checkbox", name="email_password_change", checked=user.get("email_password_change", True), cls="checkbox mr-2"),
                                    "Password changes",
                                    cls="flex items-center cursor-pointer mb-3"
                                ),
                                Label(
                                    Input(type="checkbox", name="email_account_updates", checked=user.get("email_account_updates", True), cls="checkbox mr-2"),
                                    "Account updates and security alerts",
                                    cls="flex items-center cursor-pointer mb-3"
                                ),
                            ),
                            cls="mb-6"
                        ),
                        
                        # Marketing Emails
                        Div(
                            H3("Marketing & Updates", cls="text-lg font-semibold mb-4"),
                            Div(
                                Label(
                                    Input(type="checkbox", name="marketing_emails", checked=user.get("marketing_emails", False), cls="checkbox mr-2"),
                                    "Product updates and announcements",
                                    cls="flex items-center cursor-pointer mb-3"
                                ),
                                Label(
                                    Input(type="checkbox", name="newsletter", checked=user.get("newsletter", False), cls="checkbox mr-2"),
                                    "Weekly newsletter",
                                    cls="flex items-center cursor-pointer mb-3"
                                ),
                            ),
                            cls="mb-6"
                        ),
                        
                        Button("Save Notification Preferences", type="submit", cls="btn btn-primary"),
                        hx_put=f"/auth/settings/notifications/{user.get('_id')}",
                        hx_target="#notifications-result",
                        hx_swap="innerHTML"
                    ),
                    Div(id="notifications-result", cls="mt-4"),
                    cls="card-body"
                ),
                id="notifications",
                cls="mb-6"
            ),
            
            # Danger Zone
            Card(
                Div(
                    H2("Danger Zone", cls="text-2xl font-bold text-error mb-6"),
                    Div(
                        Div(
                            H3("Delete Account", cls="text-lg font-semibold mb-2"),
                            P("Once you delete your account, there is no going back. Please be certain.", cls="text-sm text-gray-500 mb-4"),
                            Button(
                                "Delete My Account",
                                cls="btn btn-error btn-outline",
                                onclick="if(confirm('Are you sure you want to delete your account? This cannot be undone.')) { /* trigger delete */ }"
                            ),
                        ),
                        cls="border border-error rounded-lg p-4"
                    ),
                    cls="card-body"
                ),
                cls="mb-6"
            ),
            
            cls="space-y-6"
        ),
        
        cls="container mx-auto px-4 py-8 max-w-4xl"
    )
