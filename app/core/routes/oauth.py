# app/core/routes/webhooks.py
from fasthtml.common import *
from core.services.auth.providers.oauth import OAuthProvider

router_oauth = APIRouter()

@router_webhooks.get("/auth/{provider}/callback")
async def oauth_callback(request: Request, provider: str):
    """Handle OAuth provider callbacks"""
    oauth: OAuthProvider = request.app.state.oauth_provider
    try:
        user_data = await oauth.authenticate(request, provider)
        if user_data:
            return await handle_login(request, user_data)
    except Exception as e:
        log_oauth_error(e)
    return redirect("/login?error=auth_failed")

async def handle_login(request: Request, user_data: dict):
    """Process successful login"""
    # Your login logic here
    return redirect("/dashboard")

def log_oauth_error(error: Exception):
    """Centralized error logging"""
    from core.utils.logger import get_logger
    get_logger(__name__).error(f"OAuth error: {error}")