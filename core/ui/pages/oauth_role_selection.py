"""
OAuth Role Selection Page

Allows new OAuth users to select their roles during signup.
"""
from fasthtml.common import *
from monsterui.all import *
from core.services.auth.models import UserRole
from core.services.auth.role_hierarchy import RoleHierarchy, HIERARCHY_LEVEL


def OAuthRoleSelectionPage(oauth_data: dict, provider: str):
    """
    Render the role selection page for OAuth signup.
    
    Args:
        oauth_data: OAuth provider data (email, name, picture, etc.)
        provider: OAuth provider name (google, github, etc.)
    """
    # Store OAuth data in hidden form fields
    oauth_fields = [
        Hidden(name="oauth_provider", value=provider),
        Hidden(name="oauth_id", value=oauth_data.get("id", "")),
        Hidden(name="oauth_email", value=oauth_data.get("email", "")),
        Hidden(name="oauth_name", value=oauth_data.get("name", "")),
        Hidden(name="oauth_picture", value=oauth_data.get("picture", "")),
    ]
    
    # Define available roles for selection
    role_options = [
        {
            "value": UserRole.USER.value,
            "label": "User",
            "description": "Basic access - create profile, browse content",
            "level": HIERARCHY_LEVEL[UserRole.USER],
            "default": True
        },
        {
            "value": UserRole.STUDENT.value,
            "label": "Student",
            "description": "Enroll in courses, track progress, access learning materials",
            "level": HIERARCHY_LEVEL[UserRole.STUDENT],
            "default": False
        },
        {
            "value": UserRole.INSTRUCTOR.value,
            "label": "Instructor",
            "description": "Create and manage courses, teach students",
            "level": HIERARCHY_LEVEL[UserRole.INSTRUCTOR],
            "default": False
        },
        {
            "value": UserRole.EDITOR.value,
            "label": "Editor",
            "description": "Create and edit content, manage pages",
            "level": HIERARCHY_LEVEL[UserRole.EDITOR],
            "default": False
        }
    ]
    
    # Sort by hierarchy level
    role_options.sort(key=lambda r: r["level"])
    
    # Create role selection cards
    role_cards = []
    for role in role_options:
        card_id = f"role_{role['value']}"
        
        card = Div(
            Label(
                Div(
                    Div(
                        Input(
                            type="radio",
                            name="selected_roles",
                            value=role["value"],
                            checked=role["default"],
                            cls="radio radio-primary"
                        ),
                        Div(
                            H4(role["label"], cls="card-title"),
                            P(role["description"], cls="text-sm opacity-70"),
                            cls="card-body"
                        ),
                        cls="flex items-start gap-3"
                    ),
                    cls="card card-border bg-base-100 cursor-pointer hover:shadow-md transition-shadow",
                    id=card_id
                ),
                for_=card_id,
                cls="cursor-pointer"
            ),
            cls="col-span-1"
        )
        role_cards.append(card)
    
    # Add JavaScript for card selection
    script = Script("""
        document.querySelectorAll('input[name="selected_roles"]').forEach(radio => {
            radio.addEventListener('change', function() {
                // Remove selected state from all cards
                document.querySelectorAll('.card').forEach(card => {
                    card.classList.remove('border-primary', 'bg-primary/5');
                });
                
                // Add selected state to checked card's parent
                if (this.checked) {
                    const card = this.closest('.card');
                    if (card) {
                        card.classList.add('border-primary', 'bg-primary/5');
                    }
                }
            });
        });
        
        // Initialize with default selection
        const defaultRadio = document.querySelector('input[name="selected_roles"]:checked');
        if (defaultRadio) {
            defaultRadio.dispatchEvent(new Event('change'));
        }
    """)
    
    page = Page(
        Title("Select Your Role - FastApp"),
        Container(
            Div(
                # Header
                Div(
                    Div(
                        H2("Welcome to FastApp!", cls="text-3xl font-bold"),
                        P(
                            f"You're signing in with {provider.title()} as {oauth_data.get('email', '')}",
                            cls="text-base-content/70 mt-2"
                        ),
                        cls="text-center mb-8"
                    ),
                    cls="col-span-full"
                ),
                
                # Role selection form
                Form(
                    *oauth_fields,
                    Div(
                        H3("Choose your primary role:", cls="text-lg font-semibold mb-4"),
                        Grid(
                            *role_cards,
                            cls="grid-cols-1 md:grid-cols-2 gap-4 mb-6"
                        ),
                        cls="col-span-full"
                    ),
                    
                    # Additional options
                    Div(
                        Div(
                            Label(
                                Span("I agree to the Terms of Service and Privacy Policy", cls="label-text"),
                                Input(
                                    type="checkbox",
                                    name="agree_terms",
                                    required=True,
                                    cls="checkbox checkbox-primary"
                                ),
                                cls="label cursor-pointer"
                            ),
                            cls="form-control"
                        ),
                        cls="col-span-full mb-6"
                    ),
                    
                    # Action buttons
                    Div(
                        Button(
                            "Continue",
                            type="submit",
                            cls="btn btn-primary w-full"
                        ),
                        A(
                            "Cancel",
                            href="/auth?tab=login",
                            cls="btn btn-ghost w-full mt-2"
                        ),
                        cls="col-span-full"
                    ),
                    hx_post="/auth/oauth/complete",
                    hx_target="#main-content",
                    cls="grid grid-cols-1 gap-4"
                ),
                cls="grid grid-cols-1 max-w-2xl mx-auto"
            ),
            cls="min-h-screen py-8"
        ),
        script
    )
    
    return page


def OAuthRoleErrorPage(error_message: str, provider: str):
    """Render OAuth error page"""
    return Page(
        Title("OAuth Error - FastApp"),
        Container(
            Div(
                Div(
                    Div(
                        H2("OAuth Error", cls="text-3xl font-bold text-error"),
                        P(error_message, cls="mt-4"),
                        A(
                            "Try Again",
                            href=f"/auth/{provider}/login",
                            cls="btn btn-primary mt-4"
                        ),
                        A(
                            "Back to Login",
                            href="/auth?tab=login",
                            cls="btn btn-ghost mt-2 ml-2"
                        ),
                        cls="text-center"
                    ),
                    cls="col-span-full"
                ),
                cls="grid grid-cols-1 max-w-md mx-auto min-h-screen content-center"
            ),
            cls="py-8"
        )
    )
