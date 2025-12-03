"""Auth Routes - Login, Register, Profile, Settings, Logout"""
from fasthtml.common import *
from core.ui.layout import Layout
from add_ons.auth.ui.pages import LoginPage, RegisterPage, ProfilePage, SettingsPage
from add_ons.auth.services import AuthService, UserService
from core.services.db import DBService
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize router
router_auth = APIRouter()

# Initialize services
db_service = DBService()
auth_service = AuthService(db_service)
user_service = UserService(db_service)


# ============================================================================
# UI Routes
# ============================================================================

@router_auth.get("/auth/login")
def login_page():
    """Display login page"""
    return Layout(LoginPage(), title="Login | FastApp")


@router_auth.get("/auth/register")
def register_page():
    """Display registration page"""
    return Layout(RegisterPage(), title="Register | FastApp")


@router_auth.get("/auth/profile")
async def profile_page(request: Request):
    """Display user profile page"""
    # Get user from session/token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return RedirectResponse("/auth/login")
    
    token = auth_header.split(" ")[1]
    user_data = auth_service.verify_token(token)
    
    if not user_data:
        return RedirectResponse("/auth/login")
    
    # Get full user profile
    user = await auth_service.get_user_by_id(user_data.get("sub"))
    if not user:
        return RedirectResponse("/auth/login")
    
    return Layout(ProfilePage(user), title="Profile | FastApp")


@router_auth.get("/auth/settings")
async def settings_page(request: Request):
    """Display account settings page"""
    # Get user from session/token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return RedirectResponse("/auth/login")
    
    token = auth_header.split(" ")[1]
    user_data = auth_service.verify_token(token)
    
    if not user_data:
        return RedirectResponse("/auth/login")
    
    # Get full user profile
    user = await auth_service.get_user_by_id(user_data.get("sub"))
    if not user:
        return RedirectResponse("/auth/login")
    
    return Layout(SettingsPage(user), title="Account Settings | FastApp")


# ============================================================================
# API Routes
# ============================================================================

@router_auth.post("/auth/login")
async def login(request: Request):
    """
    Handle login request with role-based redirect.
    
    Returns different redirects based on user role:
    - Admin → /admin/dashboard
    - Instructor → /lms/instructor/dashboard
    - Student → /lms/student/dashboard
    - User → /profile
    """
    try:
        # Parse form data
        form_data = await request.form()
        email = form_data.get("email")
        password = form_data.get("password")
        
        if not email or not password:
            return Div(
                P("Email and password are required", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Authenticate user
        user = await auth_service.authenticate_user(email, password)
        
        if not user:
            return Div(
                P("Invalid email or password", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Create JWT token
        token_data = {
            "sub": user["_id"],
            "email": user["email"],
            "username": user.get("username"),
            "roles": user.get("roles", ["user"])
        }
        token = auth_service.create_token(token_data)
        
        # Check for redirect parameter in query string
        redirect_param = request.query_params.get("redirect")
        
        if redirect_param:
            redirect_url = redirect_param
        else:
            # Determine redirect based on role
            roles = user.get("roles", ["user"])
            
            if "admin" in roles:
                redirect_url = "/admin/dashboard"  # TODO: Build admin dashboard
            elif "instructor" in roles:
                redirect_url = "/lms-example"  # Temp: redirect to LMS example
            elif "student" in roles:
                redirect_url = "/lms-example"  # Temp: redirect to LMS example
            else:
                # Default users go to home page (can browse shop)
                redirect_url = "/"
        
        logger.info(f"User {email} logged in successfully, redirecting to {redirect_url}")
        
        # Return success with redirect and set cookie
        response = Div(
            Div(
                P(f"✓ Login successful! Redirecting...", cls="text-success"),
                cls="alert alert-success mb-4"
            ),
            Script(f"""
                localStorage.setItem('auth_token', '{token}');
                document.cookie = 'auth_token={token}; path=/; max-age=86400';
                setTimeout(() => {{
                    window.location.href = '{redirect_url}';
                }}, 1000);
            """)
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return Div(
            P(f"Login failed: {str(e)}", cls="text-error"),
            cls="alert alert-error"
        )


@router_auth.post("/auth/register")
async def register(request: Request):
    """Handle user registration"""
    try:
        # Parse form data
        form_data = await request.form()
        username = form_data.get("username")
        email = form_data.get("email")
        password = form_data.get("password")
        confirm_password = form_data.get("confirm_password")
        role = form_data.get("role", "user")  # Default to "user" if not provided
        
        # Validation
        if not all([username, email, password, confirm_password]):
            return Div(
                P("All fields are required", cls="text-error"),
                cls="alert alert-error"
            )
        
        if password != confirm_password:
            return Div(
                P("Passwords do not match", cls="text-error"),
                cls="alert alert-error"
            )
        
        if len(password) < 8:
            return Div(
                P("Password must be at least 8 characters", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Validate role
        valid_roles = ["user", "student", "instructor"]
        if role not in valid_roles:
            role = "user"
        
        # Register user with selected role
        user = await auth_service.register_user(
            email=email,
            password=password,
            username=username,
            roles=[role]  # Pass role as list
        )
        
        if not user:
            return Div(
                P("Registration failed. User may already exist.", cls="text-error"),
                cls="alert alert-error"
            )
        
        logger.info(f"User {email} registered successfully")
        
        # Auto-login: Generate token for the new user
        token_data = {
            "sub": str(user.get("_id")),
            "email": email,
            "username": user.get("username"),
            "roles": user.get("roles", ["user"])
        }
        token = auth_service.create_token(token_data)
        
        # Check for redirect parameter
        redirect_param = request.query_params.get("redirect", "")
        
        # Determine redirect URL based on role or redirect param
        if redirect_param:
            redirect_url = redirect_param
        else:
            # Default redirect based on role
            user_roles = user.get("roles", [])
            if "admin" in user_roles:
                redirect_url = "/admin/dashboard"
            elif "instructor" in user_roles:
                redirect_url = "/lms/instructor/dashboard"
            elif "student" in user_roles:
                redirect_url = "/lms/student/dashboard"
            else:
                redirect_url = "/"
        
        logger.info(f"User {email} auto-logged in after registration, redirecting to {redirect_url}")
        
        # Return success with auto-login and redirect
        return Div(
            Div(
                P("✓ Registration successful! Logging you in...", cls="text-success"),
                cls="alert alert-success mb-4"
            ),
            Script(f"""
                localStorage.setItem('auth_token', '{token}');
                document.cookie = 'auth_token={token}; path=/; max-age=86400';
                setTimeout(() => {{
                    window.location.href = '{redirect_url}';
                }}, 1000);
            """)
        )
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return Div(
            P(f"Registration failed: {str(e)}", cls="text-error"),
            cls="alert alert-error"
        )


@router_auth.put("/auth/profile/{user_id}")
async def update_profile(request: Request, user_id: str):
    """Update user profile"""
    try:
        # Verify user is authenticated and updating their own profile
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Div(
                P("Unauthorized", cls="text-error"),
                cls="alert alert-error"
            )
        
        token = auth_header.split(" ")[1]
        user_data = auth_service.verify_token(token)
        
        if not user_data or user_data.get("sub") != user_id:
            return Div(
                P("Unauthorized", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Parse form data
        form_data = await request.form()
        updates = {
            "username": form_data.get("username"),
            "full_name": form_data.get("full_name"),
            "bio": form_data.get("bio")
        }
        
        # Update profile
        updated_user = await user_service.update_user_profile(user_id, updates)
        
        if not updated_user:
            return Div(
                P("Profile update failed", cls="text-error"),
                cls="alert alert-error"
            )
        
        logger.info(f"Profile updated for user {user_id}")
        
        return Div(
            P("✓ Profile updated successfully!", cls="text-success"),
            cls="alert alert-success"
        )
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return Div(
            P(f"Update failed: {str(e)}", cls="text-error"),
            cls="alert alert-error"
        )


@router_auth.post("/auth/password/change")
async def change_password(request: Request):
    """Change user password"""
    try:
        # Verify user is authenticated
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Div(
                P("Unauthorized", cls="text-error"),
                cls="alert alert-error"
            )
        
        token = auth_header.split(" ")[1]
        user_data = auth_service.verify_token(token)
        
        if not user_data:
            return Div(
                P("Unauthorized", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Parse form data
        form_data = await request.form()
        old_password = form_data.get("old_password")
        new_password = form_data.get("new_password")
        confirm_password = form_data.get("confirm_password")
        
        # Validation
        if not all([old_password, new_password, confirm_password]):
            return Div(
                P("All fields are required", cls="text-error"),
                cls="alert alert-error"
            )
        
        if new_password != confirm_password:
            return Div(
                P("New passwords do not match", cls="text-error"),
                cls="alert alert-error"
            )
        
        if len(new_password) < 8:
            return Div(
                P("Password must be at least 8 characters", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Change password
        success = await user_service.change_password(
            user_data.get("sub"),
            old_password,
            new_password
        )
        
        if not success:
            return Div(
                P("Password change failed. Check your current password.", cls="text-error"),
                cls="alert alert-error"
            )
        
        logger.info(f"Password changed for user {user_data.get('sub')}")
        
        return Div(
            P("✓ Password changed successfully!", cls="text-success"),
            cls="alert alert-success"
        )
        
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return Div(
            P(f"Password change failed: {str(e)}", cls="text-error"),
            cls="alert alert-error"
        )


@router_auth.post("/auth/logout")
def logout():
    """Handle logout"""
    return Div(
        Script("""
            localStorage.removeItem('auth_token');
            window.location.href = '/';
        """)
    )


# ============================================================================
# Settings API Routes
# ============================================================================

@router_auth.put("/auth/settings/account/{user_id}")
async def update_account_settings(request: Request, user_id: str):
    """Update account information"""
    try:
        # Verify user is authenticated and updating their own settings
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Div(
                P("Unauthorized", cls="text-error"),
                cls="alert alert-error"
            )
        
        token = auth_header.split(" ")[1]
        user_data = auth_service.verify_token(token)
        
        if not user_data or user_data.get("sub") != user_id:
            return Div(
                P("Unauthorized", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Parse form data
        form_data = await request.form()
        updates = {
            "username": form_data.get("username"),
            "email": form_data.get("email"),
            "full_name": form_data.get("full_name"),
            "bio": form_data.get("bio")
        }
        
        # Update account
        updated_user = await user_service.update_user_profile(user_id, updates)
        
        if not updated_user:
            return Div(
                P("Account update failed", cls="text-error"),
                cls="alert alert-error"
            )
        
        logger.info(f"Account settings updated for user {user_id}")
        
        return Div(
            P("✓ Account settings updated successfully!", cls="text-success"),
            cls="alert alert-success"
        )
        
    except Exception as e:
        logger.error(f"Account settings update error: {e}")
        return Div(
            P(f"Update failed: {str(e)}", cls="text-error"),
            cls="alert alert-error"
        )


@router_auth.put("/auth/settings/privacy/{user_id}")
async def update_privacy_settings(request: Request, user_id: str):
    """Update privacy settings"""
    try:
        # Verify user is authenticated
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Div(
                P("Unauthorized", cls="text-error"),
                cls="alert alert-error"
            )
        
        token = auth_header.split(" ")[1]
        user_data = auth_service.verify_token(token)
        
        if not user_data or user_data.get("sub") != user_id:
            return Div(
                P("Unauthorized", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Parse form data
        form_data = await request.form()
        updates = {
            "profile_visibility": form_data.get("profile_visibility"),
            "show_email": form_data.get("show_email") == "on",
            "show_activity": form_data.get("show_activity") == "on"
        }
        
        # Update privacy settings
        updated_user = await user_service.update_user_profile(user_id, updates)
        
        if not updated_user:
            return Div(
                P("Privacy settings update failed", cls="text-error"),
                cls="alert alert-error"
            )
        
        logger.info(f"Privacy settings updated for user {user_id}")
        
        return Div(
            P("✓ Privacy settings updated successfully!", cls="text-success"),
            cls="alert alert-success"
        )
        
    except Exception as e:
        logger.error(f"Privacy settings update error: {e}")
        return Div(
            P(f"Update failed: {str(e)}", cls="text-error"),
            cls="alert alert-error"
        )


@router_auth.put("/auth/settings/notifications/{user_id}")
async def update_notification_settings(request: Request, user_id: str):
    """Update notification preferences"""
    try:
        # Verify user is authenticated
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Div(
                P("Unauthorized", cls="text-error"),
                cls="alert alert-error"
            )
        
        token = auth_header.split(" ")[1]
        user_data = auth_service.verify_token(token)
        
        if not user_data or user_data.get("sub") != user_id:
            return Div(
                P("Unauthorized", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Parse form data
        form_data = await request.form()
        updates = {
            "email_login": form_data.get("email_login") == "on",
            "email_password_change": form_data.get("email_password_change") == "on",
            "email_account_updates": form_data.get("email_account_updates") == "on",
            "marketing_emails": form_data.get("marketing_emails") == "on",
            "newsletter": form_data.get("newsletter") == "on"
        }
        
        # Update notification settings
        updated_user = await user_service.update_user_profile(user_id, updates)
        
        if not updated_user:
            return Div(
                P("Notification settings update failed", cls="text-error"),
                cls="alert alert-error"
            )
        
        logger.info(f"Notification settings updated for user {user_id}")
        
        return Div(
            P("✓ Notification preferences updated successfully!", cls="text-success"),
            cls="alert alert-success"
        )
        
    except Exception as e:
        logger.error(f"Notification settings update error: {e}")
        return Div(
            P(f"Update failed: {str(e)}", cls="text-error"),
            cls="alert alert-error"
        )


@router_auth.post("/auth/settings/2fa/toggle")
async def toggle_2fa(request: Request):
    """Toggle two-factor authentication"""
    try:
        # Verify user is authenticated
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Div(
                P("Unauthorized", cls="text-error"),
                cls="alert alert-error"
            )
        
        token = auth_header.split(" ")[1]
        user_data = auth_service.verify_token(token)
        
        if not user_data:
            return Div(
                P("Unauthorized", cls="text-error"),
                cls="alert alert-error"
            )
        
        user_id = user_data.get("sub")
        user = await auth_service.get_user_by_id(user_id)
        
        if not user:
            return Div(
                P("User not found", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Toggle 2FA status
        current_status = user.get("two_factor_enabled", False)
        new_status = not current_status
        
        await user_service.update_user_profile(user_id, {
            "two_factor_enabled": new_status
        })
        
        status_text = "enabled" if new_status else "disabled"
        logger.info(f"2FA {status_text} for user {user_id}")
        
        return Div(
            P(f"✓ Two-factor authentication {status_text}!", cls="text-success"),
            cls="alert alert-success"
        )
        
    except Exception as e:
        logger.error(f"2FA toggle error: {e}")
        return Div(
            P(f"Failed to toggle 2FA: {str(e)}", cls="text-error"),
            cls="alert alert-error"
        )


# ============================================================================
# Helper: Get current user from request
# ============================================================================

async def get_current_user(request: Request) -> Optional[dict]:
    """
    Extract and verify user from request.
    Returns user data or None if not authenticated.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    user_data = auth_service.verify_token(token)
    
    if not user_data:
        return None
    
    return await auth_service.get_user_by_id(user_data.get("sub"))
