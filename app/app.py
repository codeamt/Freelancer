from fasthtml.common import *
from monsterui.all import *
from core.routes import router_main, router_auth, router_ui, router_media, router_admin, router_webhooks, router_graphql
from core.middleware import security, session_middleware
from core.services.oauth import GoogleOAuthService
from core.utils.logger import get_logger
from core.routes import auth
# from app.add_ons.lms import router_lms  # Temporarily disabled - models need to be created
import os

logger = get_logger(__name__)

# Initialize FastHTML app with MonsterUI theme and Bootstrap Icons
app, rt = fast_app(
    hdrs=[
        *Theme.slate.headers(),
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"),
    ],
    #middleware=[],
    #exception_handlers={
   #     401: lambda req, exc: RedirectResponse('/auth/login'),
   #     403: lambda req, exc: RedirectResponse('/auth/login'),
   # }
)

# Apply middleware (session middleware disabled - requires Redis)
# app.add_middleware(session_middleware, redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"))
#security.apply_security(app)

# Setup all routes on the app
for router in [router_main, router_auth, router_ui, router_media, router_admin, router_webhooks, router_graphql]:
    router.to_app(app)

# Initialize Google OAuth service
oauth_service = None
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

if __name__ == "__main__":
    serve()


