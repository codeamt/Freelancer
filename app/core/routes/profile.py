"""
User Profile Routes - Member role endpoints for managing own profile.

Routes:
- GET /profile - View own profile
- PUT /profile - Update own profile
- POST /profile/avatar - Upload avatar
- GET /profile/settings - Personal settings
"""

from fasthtml.common import *
from monsterui.all import *
from core.services.auth import require_auth
from core.ui.layout import Layout
from core.utils.logger import get_logger

logger = get_logger(__name__)

router_profile = APIRouter()


@router_profile.get("/profile")
@require_auth()
async def view_profile(request: Request):
    """View own profile."""
    user = request.state.user
    user_service = request.app.state.user_service
    demo = getattr(request.app.state, 'demo', False)
    
    # Get full user data
    user_data = await user_service.get_user(user.id)
    
    # Build user dict for Layout
    user_dict = {
        "username": getattr(user_data, 'username', user_data.email.split('@')[0]),
        "email": user_data.email,
        "role": user_data.role,
        "_id": str(user.id)
    }
    
    content = Card(
        Div(
            H2("My Profile", cls="text-2xl font-bold mb-6"),
            
            # Profile info
            Div(
                Div(
                    Label("Email", cls="block text-sm font-bold mb-1"),
                    P(user_data.email, cls="text-gray-700 mb-4")
                ),
                Div(
                    Label("Role", cls="block text-sm font-bold mb-1"),
                    Span(user_data.role.title(), cls="badge badge-primary mb-4")
                ),
                Div(
                    Label("Member Since", cls="block text-sm font-bold mb-1"),
                    P(
                        user_data.created_at.strftime("%B %d, %Y") if hasattr(user_data, 'created_at') else "N/A",
                        cls="text-gray-700 mb-4"
                    )
                ),
                cls="mb-6"
            ),
            
            # Edit profile button
            Button(
                "Edit Profile",
                hx_get="/profile/edit",
                hx_target="#profile-content",
                cls="btn btn-primary mr-2"
            ),
            
            Button(
                "Change Password",
                hx_get="/profile/password",
                hx_target="#profile-content",
                cls="btn btn-secondary"
            ),
            
            cls="p-6"
        ),
        id="profile-content"
    )
    
    return Layout(content, title="My Profile | FastApp", current_path="/profile", user=user_dict, show_auth=True, demo=demo)


@router_profile.get("/profile/edit")
@require_auth()
async def edit_profile_form(request: Request):
    """Show profile edit form."""
    user = request.state.user
    user_service = request.app.state.user_service
    
    user_data = await user_service.get_user(user.id)
    
    return Card(
        Div(
            H2("Edit Profile", cls="text-2xl font-bold mb-6"),
            
            Form(
                Div(
                    Label("Display Name", cls="block text-sm font-bold mb-1"),
                    Input(
                        type="text",
                        name="display_name",
                        value=getattr(user_data, 'display_name', ''),
                        placeholder="Your display name",
                        cls="input input-bordered w-full mb-4"
                    )
                ),
                
                Div(
                    Label("Bio", cls="block text-sm font-bold mb-1"),
                    Textarea(
                        getattr(user_data, 'bio', ''),
                        name="bio",
                        rows=4,
                        placeholder="Tell us about yourself",
                        cls="textarea textarea-bordered w-full mb-4"
                    )
                ),
                
                Div(
                    Button("Save Changes", type="submit", cls="mr-2"),
                    Button(
                        "Cancel",
                        hx_get="/profile",
                        hx_target="#profile-content"
                    ),
                    cls="flex gap-2"
                ),
                
                hx_put="/api/profile",
                hx_target="#profile-content"
            ),
            
            cls="p-6"
        )
    )


@router_profile.get("/profile/password")
@require_auth()
async def change_password_form(request: Request):
    """Show password change form."""
    return Card(
        Div(
            H2("Change Password", cls="text-2xl font-bold mb-6"),
            
            Form(
                Div(
                    Label("Current Password", cls="block text-sm font-bold mb-1"),
                    Input(
                        type="password",
                        name="current_password",
                        required=True,
                        cls="input input-bordered w-full mb-4"
                    )
                ),
                
                Div(
                    Label("New Password", cls="block text-sm font-bold mb-1"),
                    Input(
                        type="password",
                        name="new_password",
                        required=True,
                        cls="input input-bordered w-full mb-4"
                    )
                ),
                
                Div(
                    Label("Confirm New Password", cls="block text-sm font-bold mb-1"),
                    Input(
                        type="password",
                        name="confirm_password",
                        required=True,
                        cls="input input-bordered w-full mb-4"
                    )
                ),
                
                Div(
                    Button("Update Password", type="submit", cls="mr-2"),
                    Button(
                        "Cancel",
                        hx_get="/profile",
                        hx_target="#profile-content"
                    ),
                    cls="flex gap-2"
                ),
                
                hx_post="/api/profile/password",
                hx_target="#profile-content"
            ),
            
            cls="p-6"
        )
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router_profile.put("/api/profile")
@require_auth()
async def update_profile(request: Request):
    """Update user profile."""
    user = request.state.user
    user_service = request.app.state.user_service
    
    form = await request.form()
    updates = {
        "display_name": form.get("display_name"),
        "bio": form.get("bio")
    }
    
    try:
        result = await user_service.update_user(user.id, updates)
        
        if result["success"]:
            return Div(
                Alert("✓ Profile updated successfully!", cls="alert-success mb-4"),
                Button(
                    "Back to Profile",
                    hx_get="/profile",
                    hx_target="#profile-content"
                )
            )
        else:
            return Alert(f"Error: {result.get('error')}", cls="alert-error")
            
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return Alert("Failed to update profile", cls="alert-error")


@router_profile.post("/api/profile/password")
@require_auth()
async def change_password(request: Request):
    """Change user password."""
    user = request.state.user
    auth_service = request.app.state.auth_service
    
    form = await request.form()
    current_password = form.get("current_password")
    new_password = form.get("new_password")
    confirm_password = form.get("confirm_password")
    
    # Validate
    if new_password != confirm_password:
        return Alert("Passwords do not match", cls="alert-error")
    
    if len(new_password) < 8:
        return Alert("Password must be at least 8 characters", cls="alert-error")
    
    try:
        # Verify current password
        login_result = await auth_service.authenticate_user(user.email, current_password)
        if not login_result:
            return Alert("Current password is incorrect", cls="alert-error")
        
        # Update password
        result = await auth_service.update_password(user.id, new_password)
        
        if result["success"]:
            return Div(
                Alert("✓ Password updated successfully!", cls="alert-success mb-4"),
                Button(
                    "Back to Profile",
                    hx_get="/profile",
                    hx_target="#profile-content"
                )
            )
        else:
            return Alert(f"Error: {result.get('error')}", cls="alert-error")
            
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return Alert("Failed to change password", cls="alert-error")


@router_profile.post("/api/profile/avatar")
@require_auth()
async def upload_avatar(request: Request):
    """Upload profile avatar."""
    user = request.state.user
    
    # TODO: Implement file upload handling
    # This would integrate with MinIO or another storage service
    
    return Alert("Avatar upload not yet implemented", cls="alert-info")
