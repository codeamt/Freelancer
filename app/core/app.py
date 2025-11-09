from fasthtml.common import *
from app.core.routes import auth, ui, media, admin, webhooks, graphql, main
from app.core.middleware import security, session_middleware
from app.core.services.oauth import GoogleOAuthService
from app.core.utils.logger import get_logger
import os

logger = get_logger(__name__)

# Initialize FastHTML app
app = FastHTML(
    hdrs=(
        Link(rel='stylesheet', href='https://unpkg.com/normalize.css'),
        Link(rel='stylesheet', href='https://unpkg.com/sakura.css/css/sakura.css'),
        Script(src='https://unpkg.com/htmx.org@1.9.10'),
    ),
    middleware=[],
    exception_handlers={
        401: lambda req, exc: RedirectResponse('/auth/login'),
        403: lambda req, exc: RedirectResponse('/auth/login'),
    }
)

# Apply middleware
app.add_middleware(session_middleware, redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"))
security.apply_security(app)

# Initialize Google OAuth service
oauth_service = None

def init_app():
    """Initialize the application with all routes and services"""
    global oauth_service
    
    # Include all routes
    app.mount("/auth", auth.router_auth)
    app.mount("/", main.router_main)
    app.mount("/theme", ui.router)
    app.mount("/media", media.router_media)
    app.mount("/admin", admin.router_admin)
    app.mount("/webhooks", webhooks.router_webhooks)
    app.mount("/graphql", graphql.router_graphql)
    
    # Initialize Google OAuth service
    try:
        if os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"):
            oauth_service = GoogleOAuthService(app)
            # Initialize the auth routes with OAuth service
            auth.init_google_oauth(app)
            logger.info("Google OAuth service initialized successfully")
        else:
            logger.warning("Google OAuth not configured: GOOGLE_CLIENT_ID and/or GOOGLE_CLIENT_SECRET not set")
    except Exception as e:
        logger.error(f"Failed to initialize Google OAuth service: {e}")
    
    return app

if __name__ == "__main__":
    # Initialize the app only when running as main module
    init_app()
    import uvicorn
    uvicorn.run("app.core.app:app", host="0.0.0.0", port=8002, reload=True)
