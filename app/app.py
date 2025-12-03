from fasthtml.common import *
from monsterui.all import *
import sys
import os
from pathlib import Path

# Add app directory to path if not already there
app_dir = Path(__file__).parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.routes.main import router_main
from core.utils.logger import get_logger
from core.middleware import apply_security, RedisSessionMiddleware
from examples.eshop import create_eshop_app
from examples.lms import create_lms_app
from examples.social import create_social_app
from examples.streaming import create_streaming_app

logger = get_logger(__name__)

# Initialize FastHTML app with MonsterUI theme
app, rt = fast_app(
    hdrs=[
        *Theme.slate.headers(),
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"),
    ],
)

# Apply security middlewares (CSP removed from SecurityHeaders for FastHTML compatibility)
try:
    from core.middleware.security import SecurityHeaders, RateLimitMiddleware, SecurityMiddleware
    
    # Apply security middlewares
    app.add_middleware(SecurityMiddleware)  # Input sanitization & logging
    app.add_middleware(RateLimitMiddleware)  # Rate limiting (60 req/min per IP)
    app.add_middleware(SecurityHeaders)  # Security headers (no CSP - FastHTML incompatible)
    # CSRFMiddleware disabled - breaks HTMX forms without proper token handling
    
    logger.info("✓ Security middlewares applied (Headers, Rate Limit, Sanitization)")
    logger.info("ℹ️  CSP disabled (FastHTML uses inline styles), CSRF disabled (needs HTMX integration)")
except Exception as e:
    logger.warning(f"⚠️ Failed to apply security middlewares: {e}")

# Apply Redis session middleware (for chat features in social/streaming)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
if redis_url and redis_url != "redis://localhost:6379":
    try:
        app.add_middleware(
            RedisSessionMiddleware,
            redis_url=redis_url,
            cookie_name="session_id",
            ttl_seconds=60 * 60 * 24 * 7,  # 7 days
            cookie_secure=os.getenv("ENVIRONMENT") == "production",
            cookie_samesite="lax"
        )
        logger.info(f"✓ Redis session middleware applied (URL: {redis_url})")
    except Exception as e:
        logger.warning(f"⚠️ Failed to apply Redis session middleware: {e}")
        logger.info("  → Chat features in social/streaming may not work without Redis")
else:
    logger.info("ℹ️  Redis not configured - using in-memory sessions")
    logger.info("  → Set REDIS_URL environment variable for persistent sessions")

# Mount core routes (landing pages only)
router_main.to_app(app)

# Note: Auth is now a service (add_ons/services/auth.py), not a mounted add-on
# Each example implements its own auth UI/routes using the auth service

# Mount e-shop example
try:
    eshop_app = create_eshop_app()
    app.mount("/eshop-example", eshop_app)
    logger.info("✓ E-Shop example mounted at /eshop-example")
except Exception as e:
    logger.error(f"Failed to mount e-shop example: {e}")

# Mount LMS example
try:
    lms_app = create_lms_app()
    app.mount("/lms-example", lms_app)
    logger.info("✓ LMS example mounted at /lms-example")
except Exception as e:
    logger.error(f"Failed to mount LMS example: {e}")

# Mount Social example
try:
    social_app = create_social_app()
    app.mount("/social-example", social_app)
    logger.info("✓ Social example mounted at /social-example")
except Exception as e:
    logger.error(f"Failed to mount Social example: {e}")

# Mount Streaming example
try:
    streaming_app = create_streaming_app()
    app.mount("/streaming-example", streaming_app)
    logger.info("✓ Streaming example mounted at /streaming-example")
except Exception as e:
    logger.error(f"Failed to mount Streaming example: {e}")

logger.info("FastApp started successfully")
logger.info("Available routes:")
logger.info("  - / (Home)")
logger.info("  - /docs (Documentation)")
logger.info("  - /eshop-example (E-Shop Demo with auth)")
logger.info("  - /lms-example (LMS Demo with auth)")
logger.info("  - /social-example (Social Network Demo)")
logger.info("  - /streaming-example (Streaming Platform Demo)")
logger.info("")
logger.info("Note: Auth is now a service - each example has its own login/register UI")



if __name__ == "__main__":
    #import uvicorn
    #uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    serve()


