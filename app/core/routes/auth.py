from fastapi import APIRouter, Form, HTTPException, Request
from starlette.responses import HTMLResponse
from app.core.services.auth import AuthService, require_scope
from app.core.services.db import DBService
from app.core.services.event_bus import bus
from app.core.services.email import EmailService
from app.core.ui.layout import Layout
from app.core.ui.pages import HomePage, LoginPage, RegisterPage, ProfilePage
from app.core.utils.logger import get_logger
from app.core.security import hash_password, verify_password
from app.core.services.oauth import GoogleOAuthService

logger = get_logger(__name__)

router_auth = APIRouter(prefix="/auth", tags=["auth"])

# Initialize Google OAuth service (this will be properly initialized in main app)
google_oauth = None

@router_auth.get("/login")
async def login_page():
    content = LoginPage()
    return Layout(content, title="Login")

@router_auth.get("/register")
async def register_page():
    content = RegisterPage()
    return Layout(content, title="Register")

def init_google_oauth(app):
    """Initialize Google OAuth service with the FastHTML app"""
    global google_oauth
    google_oauth = GoogleOAuthService(app)
    return google_oauth

@router_auth.get("/google/login")
async def google_login_redirect(request: Request):
    """Redirect user to Google OAuth login"""
    if google_oauth is None:
        raise HTTPException(status_code=500, detail="Google OAuth not initialized")
    return RedirectResponse(google_oauth.login_link(request))

@router_auth.get("/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback - this is handled by the OAuth service"""
    # This route is automatically handled by the GoogleOAuthService
    # The get_auth method will be called with the user info
    pass

@router_auth.post("/register")
async def register_user(email: str = Form(...), password: str = Form(...)):
    mongo = DBService.mongo()
    existing = await mongo.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = {
        "email": email,
        "password_hash": hash_password(password),
        "role": "user",
        "scopes": ["view:content"],
    }
    await mongo.users.insert_one(user)

    # Send welcome email and emit event
    EmailService.send_email(
        to_email=email,
        subject="Welcome to FastApp ⚡",
        html=f"<h3>Hi {email},</h3><p>Welcome to FastApp! Start building amazing things.</p>",
    )
    await bus.publish("user.registered", {"email": email})

    token = AuthService.create_token({"sub": email, "role": "user", "scopes": ["view:content"]})
    return {"access_token": token, "status": "created"}

@router_auth.post("/login")
async def login_user(email: str = Form(...), password: str = Form(...)):
    mongo = DBService.mongo()
    user = await mongo.users.find_one({"email": email})
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(user["password_hash"], password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = AuthService.create_token({"sub": email, "role": user.get("role", "user"), "scopes": user.get("scopes", ["view:content"])})
    return {"access_token": token}

@router_auth.get("/profile")
@require_scope("view:content")
async def profile(request: Request):
    user = AuthService.get_current_user(request)
    content = ProfilePage(user)
    return Layout(content, title="Profile")

@router_auth.post("/logout")
async def logout():
    # In a real application, you would invalidate the token here
    # For now, we'll return HTMX-compatible content that redirects the page
    return HTMLResponse("""
    <script>
        // Clear any auth tokens from localStorage/cookies if needed
        // Then redirect to login page
        window.location.href = '/auth/login';
    </script>
    """)