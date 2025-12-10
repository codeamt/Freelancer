"""Main Application Setup"""
from fasthtml.common import *
from monsterui.all import *
import os

# Middleware 
from core.middleware import apply_security, RedisSessionMiddleware

# Database adapters
from core.db.adapters.postgres_adapter import PostgresAdapter
from core.db.adapters.mongodb_adapter import MongoDBAdapter
from core.db.adapters.redis_adapter import RedisAdapter

# Repositories
from core.db.repositories.user_repository import UserRepository

# Services
from core.services.auth import AuthService, UserService
from core.services.auth.providers.jwt import JWTProvider
from core.services.settings import (
    initialize_settings_service,
    initialize_session_manager
)

# Routes
from core.routes import *


# Examples
from examples.eshop import create_eshop_app
from examples.lms import create_lms_app
from examples.social import create_social_app
from examples.streaming import create_streaming_app

from dotenv import load_dotenv
load_dotenv('app.config.env')

# ============================================================================
# Database Setup
# ============================================================================

# Initialize adapters
postgres = PostgresAdapter(
    connection_string=os.getenv("POSTGRES_URL"),
    min_size=10,
    max_size=20
)

mongodb = MongoDBAdapter(
    connection_string=os.getenv("MONGO_URL"),
    database=os.getenv("MONGO_DB", "app_db")
)

redis = RedisAdapter(
    connection_string=os.getenv("REDIS_URL")
)

# ============================================================================
# Repository Setup
# ============================================================================

# User repository (core)
user_repo = UserRepository(postgres, mongodb, redis)

# ============================================================================
# Service Setup
# ============================================================================

# JWT provider
jwt_provider = JWTProvider()

# Auth service (authentication/authorization)
auth_service = AuthService(user_repo, jwt_provider)

# User service (user management)
user_service = UserService(user_repo)

# ============================================================================
# FastHTML App
# ============================================================================

app, rt = fast_app(
    hdrs=[
        *Theme.slate.headers(),
        Link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"
        ),
    ],
)

# Attach services to app state (for access in routes/decorators)
app.state.auth_service = auth_service
app.state.user_service = user_service
# app.state.jwt_provider = jwt_provider
# app.state.settimngs_service = initialize_settings_service(db)
# app.state.session_manager = initialize_session_manager(db)
app.state.user_repo = user_repo

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
# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize database connections"""
    await postgres.connect()
    await mongodb.connect()
    await redis.connect()
    logger.info("✓ Database adapters connected")

@app.on_event("shutdown")
async def shutdown():
    """Close database connections"""
    await postgres.disconnect()
    await mongodb.disconnect()
    await redis.disconnect()
    logger.info("✓ Database adapters disconnected")

# Add Redis middleware
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
# ============================================================================
# Mount Routes
# ============================================================================

router_main.to_app(app)
router_oauth.to_app(app)
router_editor.to_app(app)
router_admin_sites.to_app(app)
router_settings.to_app(app)
# ... other routers


# ============================================================================
# Mount Example Apps 
# ============================================================================

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
    serve()