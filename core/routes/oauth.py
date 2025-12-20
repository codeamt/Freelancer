# app/core/routes/oauth.py
from fasthtml.common import *
from monsterui.all import *
from starlette.responses import RedirectResponse
from core.services.auth.providers.oauth import OAuthProvider
from core.services.auth.models import LoginRequest
from core.utils.logger import get_logger
import os

logger = get_logger(__name__)
router_oauth = APIRouter()

# OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5001/auth/google/callback")

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:5001/auth/github/callback")

@router_oauth.get("/auth/google/login")
async def google_login(request: Request):
    """Initiate Google OAuth flow"""
    if not GOOGLE_CLIENT_ID:
        return RedirectResponse("/auth?tab=login&error=OAuth+not+configured", status_code=303)
    
    # Build Google OAuth URL
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline"
    )
    return RedirectResponse(auth_url, status_code=303)

@router_oauth.get("/auth/github/login")
async def github_login(request: Request):
    """Initiate GitHub OAuth flow"""
    if not GITHUB_CLIENT_ID:
        return RedirectResponse("/auth?tab=login&error=OAuth+not+configured", status_code=303)
    
    # Build GitHub OAuth URL
    auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={GITHUB_CLIENT_ID}&"
        f"redirect_uri={GITHUB_REDIRECT_URI}&"
        f"scope=user:email"
    )
    return RedirectResponse(auth_url, status_code=303)

@router_oauth.get("/auth/google/callback")
async def google_callback(request: Request, code: str = None, error: str = None):
    """Handle Google OAuth callback"""
    if error:
        logger.error(f"Google OAuth error: {error}")
        return RedirectResponse("/auth?tab=login&error=OAuth+failed", status_code=303)
    
    if not code:
        return RedirectResponse("/auth?tab=login&error=No+authorization+code", status_code=303)
    
    try:
        # Exchange code for token and get user info
        from core.services.auth.providers.adapters.google import GoogleOAuth
        google = GoogleOAuth(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI)
        user_data = await google.validate(request)
        
        if user_data:
            return await handle_oauth_login(request, user_data, "google")
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
    
    return RedirectResponse("/auth?tab=login&error=OAuth+authentication+failed", status_code=303)

@router_oauth.get("/auth/github/callback")
async def github_callback(request: Request, code: str = None, error: str = None):
    """Handle GitHub OAuth callback"""
    if error:
        logger.error(f"GitHub OAuth error: {error}")
        return RedirectResponse("/auth?tab=login&error=OAuth+failed", status_code=303)
    
    if not code:
        return RedirectResponse("/auth?tab=login&error=No+authorization+code", status_code=303)
    
    try:
        # Exchange code for token and get user info
        from core.services.auth.providers.adapters.github import GitHubOAuth
        github = GitHubOAuth(GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET)
        user_data = await github.validate(request)
        
        if user_data:
            return await handle_oauth_login(request, user_data, "github")
    except Exception as e:
        logger.error(f"GitHub OAuth callback error: {e}")
    
    return RedirectResponse("/auth?tab=login&error=OAuth+authentication+failed", status_code=303)

async def handle_oauth_login(request: Request, user_data: dict, provider: str):
    """Process successful OAuth login - create or login user"""
    user_service = request.app.state.user_service
    auth_service = request.app.state.auth_service
    
    email = user_data.get("email")
    if not email:
        return RedirectResponse("/auth?tab=login&error=No+email+from+provider", status_code=303)
    
    try:
        # Check if user exists
        existing_user = await user_service.get_user_by_email(email)
        
        if not existing_user:
            # Create new user with OAuth
            user_id = await user_service.create_user(
                email=email,
                password=f"oauth_{provider}_{user_data.get('id')}",  # OAuth users don't use password
                role="user",
                profile_data={
                    "username": user_data.get("name", email.split("@")[0]),
                    "avatar_url": user_data.get("picture", ""),
                    "oauth_provider": provider,
                    "oauth_id": user_data.get("id")
                }
            )
            logger.info(f"Created new user via {provider} OAuth: {email}")
        
        # Login the user - create LoginRequest for OAuth
        login_request = LoginRequest(
            username=email,
            password=f"oauth_{provider}_{user_data.get('id')}",
            remember_me=True
        )
        result = await auth_service.login(login_request)
        
        if result:
            response = RedirectResponse("/", status_code=303)
            response.set_cookie(
                "auth_token",
                result.access_token,
                httponly=True,
                secure=os.getenv("ENVIRONMENT") == "production",
                samesite="lax",
                max_age=result.expires_in
            )
            return response
    except Exception as e:
        logger.error(f"OAuth login handling error: {e}")
    
    return RedirectResponse("/auth?tab=login&error=Failed+to+create+account", status_code=303)