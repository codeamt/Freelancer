"""
Main Application Setup

Initializes all database adapters, repositories, services, and routes.
Provides dependency injection through app.state for child applications.
"""
from fasthtml.common import *
from monsterui.all import *
import os
from dotenv import load_dotenv

# Load environment first
load_dotenv('app.config.env')

# Validate configuration before proceeding
from core.config.validation import validate_config
validate_config()  # Will raise ConfigurationError if validation fails in production

# Logging
from core.utils.logger import get_logger

# Database components
from core.db.adapters import PostgresAdapter, MongoDBAdapter, RedisAdapter
from core.db.repositories import UserRepository
from core.db import initialize_session_manager, get_pool_manager

# Services
from core.services.auth import AuthService, UserService
from core.services.auth.providers.jwt import JWTProvider

# Middleware
from core.middleware.security import (
    SecurityHeaders, 
    RateLimitMiddleware, 
    SecurityMiddleware
)
from core.middleware import RedisSessionMiddleware

# Routes
from core.routes import (
    router_main,
    router_editor,
    router_admin_sites,
    router_admin_users,
    router_auth,
    router_settings,
    router_profile,
    router_oauth,
    router as router_cart
)

from core.middleware.auth_context import inject_user_context, set_response_cookies

# Add-on loader
from core.addon_loader import load_all_addons, get_addon_loader, get_addon_route

# Example apps
from examples.eshop import create_eshop_app
from examples.lms import create_lms_app
from examples.social import create_social_app
from examples.streaming import create_streaming_app

logger = get_logger(__name__)

# ============================================================================
# Configuration
# ============================================================================

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/app_db")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://root:example@localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "app_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")

# ============================================================================
# Database Adapter Initialization
# ============================================================================

logger.info("Initializing database adapters...")

# PostgreSQL adapter
postgres = PostgresAdapter(
    connection_string=POSTGRES_URL,
    min_size=10,
    max_size=20
)

# MongoDB adapter
mongodb = MongoDBAdapter(
    connection_string=MONGO_URL,
    database=MONGO_DB
)

# Redis adapter
redis = RedisAdapter(
    connection_string=REDIS_URL
)

# Register pools with pool manager
pool_manager = get_pool_manager()
# Note: Pools are registered after connection in startup event

logger.info("✓ Database adapters initialized")

# ============================================================================
# Repository Initialization
# ============================================================================

logger.info("Initializing repositories...")

# Core user repository
user_repository = UserRepository(
    postgres=postgres,
    mongodb=mongodb,
    redis=redis
)

logger.info("✓ Repositories initialized")

# ============================================================================
# Service Initialization
# ============================================================================

logger.info("Initializing services...")

# JWT provider
jwt_provider = JWTProvider()

# Auth service (authentication/authorization)
auth_service = AuthService(
    user_repository=user_repository,
    jwt_provider=jwt_provider
)

# User service (user CRUD operations)
user_service = UserService(
    user_repository=user_repository
)

# Domain services (for add-ons)
from core.services.cart import CartService
from core.services.product import ProductService
from core.services.order import OrderService
from core.services.payment import PaymentService

cart_service = CartService()
product_service = ProductService()
order_service = OrderService()
payment_service = PaymentService()

logger.info("✓ Services initialized")

# ============================================================================
# FastHTML Application
# ============================================================================

logger.info("Creating FastHTML application...")

app, rt = fast_app(
    hdrs=[
        *Theme.slate.headers(),
        Link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"
        ),
    ],
    live=ENVIRONMENT == "development"
)

# ============================================================================
# Dependency Injection (App State)
# ============================================================================

# Attach services to app state for access in routes and child apps
app.state.auth_service = auth_service
app.state.user_service = user_service
app.state.user_repository = user_repository
app.state.jwt_provider = jwt_provider

# Attach domain services for add-ons
app.state.cart_service = cart_service
app.state.product_service = product_service
app.state.order_service = order_service
app.state.payment_service = payment_service

# Attach adapters for child apps that need direct access
app.state.postgres = postgres
app.state.mongodb = mongodb
app.state.redis = redis

# Store demo mode flag
app.state.demo = DEMO_MODE

logger.info("✓ Services attached to app.state")
logger.info(f"  → Demo mode: {DEMO_MODE}")

# ============================================================================
# Middleware Configuration
# ============================================================================

logger.info("Applying middleware...")

# Security middlewares
try:
    # Order matters: most specific first, most general last
    app.add_middleware(SecurityMiddleware)      # Input sanitization & logging
    app.add_middleware(RateLimitMiddleware)     # Rate limiting (60 req/min per IP)
    app.add_middleware(SecurityHeaders)         # Security headers
    
    logger.info("✓ Security middlewares applied")
    logger.info("  → Input sanitization: enabled")
    logger.info("  → Rate limiting: 60 req/min per IP")
    logger.info("  → Security headers: enabled")
    logger.info("  → CSP: disabled (FastHTML inline styles)")
    logger.info("  → CSRF: disabled (needs HTMX token integration)")
    
except Exception as e:
    logger.warning(f"⚠️ Failed to apply security middlewares: {e}")

# Redis session middleware (for chat/real-time features)
if REDIS_URL and REDIS_URL != "redis://localhost:6379":
    try:
        app.add_middleware(
            RedisSessionMiddleware,
            redis_url=REDIS_URL,
            cookie_name="session_id",
            ttl_seconds=60 * 60 * 24 * 7,  # 7 days
            cookie_secure=ENVIRONMENT == "production",
            cookie_samesite="lax"
        )
        logger.info(f"✓ Redis session middleware applied")
    except Exception as e:
        logger.warning(f"⚠️ Failed to apply Redis session middleware: {e}")
else:
    logger.info("ℹ️  Redis session middleware skipped (Redis not configured)")

# ============================================================================
# Application Lifecycle
# ============================================================================
# Note: User context injection handled by middleware
# TODO: Implement proper before/after hooks if needed

@app.on_event("startup")
async def startup():
    """Initialize database connections and resources."""
    logger.info("Starting application...")
    
    try:
        # Connect adapters
        await postgres.connect()
        logger.info("✓ PostgreSQL connected")
        
        await mongodb.connect()
        logger.info("✓ MongoDB connected")
        
        await redis.connect()
        logger.info("✓ Redis connected")
        
        # Initialize session manager
        initialize_session_manager(postgres, mongodb, redis)
        logger.info("✓ Session manager initialized")
        
        # Register connection pools
        if hasattr(postgres, 'pool') and postgres.pool:
            pool_manager.register_pool("postgres", postgres.pool, None)
        if hasattr(mongodb, 'client') and mongodb.client:
            pool_manager.register_pool("mongodb", mongodb.client, None)
        if hasattr(redis, 'client') and redis.client:
            pool_manager.register_pool("redis", redis.client, None)
        
        logger.info("✓ Connection pools registered")
        logger.info("=" * 60)
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Clean up database connections and resources."""
    logger.info("Shutting down application...")
    
    try:
        # Close all connection pools
        await pool_manager.close_all()
        logger.info("✓ Connection pools closed")
        
        # Disconnect adapters
        await postgres.disconnect()
        logger.info("✓ PostgreSQL disconnected")
        
        await mongodb.disconnect()
        logger.info("✓ MongoDB disconnected")
        
        await redis.disconnect()
        logger.info("✓ Redis disconnected")
        
        logger.info("=" * 60)
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# ============================================================================
# Mount Core Routes
# ============================================================================

logger.info("Mounting core routes...")

try:
    router_main.to_app(app)
    router_auth.to_app(app)
    router_oauth.to_app(app)
    router_editor.to_app(app)
    router_admin_sites.to_app(app)
    router_admin_users.to_app(app)
    router_settings.to_app(app)
    router_profile.to_app(app)
    router_cart.to_app(app)

    logger.info("✓ Core routes mounted (main, auth, oauth, editor, admin_sites, admin_users, settings, profile, cart)")
except Exception as e:
    logger.error(f"Failed to mount core routes: {e}")

# ============================================================================
# Load and Mount Domain Add-ons
# ============================================================================

logger.info("Loading domain add-ons...")

# Load add-on manifests (registers roles, settings, components)
load_all_addons()

# Mount add-on routes
logger.info("Mounting domain add-on routes...")
addon_loader = get_addon_loader()

# TODO: Fix addon route registration - currently causing conflicts with mounted example apps
# Commenting out for now since we're using mounted example apps instead
logger.info("ℹ️  Addon route registration skipped (using mounted example apps)")

# ============================================================================
# Mount Example Applications
# ============================================================================

logger.info("Mounting example applications...")

# E-Shop Example
try:
    eshop_app = create_eshop_app(
        auth_service=auth_service,
        user_service=user_service,
        postgres=postgres,
        mongodb=mongodb,
        redis=redis,
        demo=DEMO_MODE
    )
    app.mount("/eshop-example", eshop_app)
    logger.info(f"✓ E-Shop example mounted at /eshop-example (demo={DEMO_MODE})")
except Exception as e:
    logger.error(f"Failed to mount e-shop example: {e}")
    logger.exception(e)

# LMS Example
try:
    lms_app = create_lms_app(
        auth_service=auth_service,
        user_service=user_service,
        postgres=postgres,
        mongodb=mongodb,
        redis=redis,
        demo=DEMO_MODE
    )
    app.mount("/lms-example", lms_app)
    logger.info(f"✓ LMS example mounted at /lms-example (demo={DEMO_MODE})")
except Exception as e:
    logger.error(f"Failed to mount LMS example: {e}")
    logger.exception(e)

# Social Example
try:
    social_app = create_social_app(
        auth_service=auth_service,
        user_service=user_service,
        postgres=postgres,
        mongodb=mongodb,
        redis=redis,
        demo=DEMO_MODE
    )
    app.mount("/social-example", social_app)
    logger.info(f"✓ Social example mounted at /social-example (demo={DEMO_MODE})")
except Exception as e:
    logger.error(f"Failed to mount social example: {e}")
    logger.exception(e)

# Streaming Example
try:
    streaming_app = create_streaming_app(
        auth_service=auth_service,
        user_service=user_service,
        postgres=postgres,
        mongodb=mongodb,
        redis=redis,
        demo=DEMO_MODE
    )
    app.mount("/streaming-example", streaming_app)
    logger.info(f"✓ Streaming example mounted at /streaming-example (demo={DEMO_MODE})")
except Exception as e:
    logger.error(f"Failed to mount streaming example: {e}")
    logger.exception(e)

# ============================================================================
# Startup Summary
# ============================================================================

logger.info("=" * 60)
logger.info("FastApp started successfully!")
logger.info("=" * 60)
logger.info("")
logger.info("Available routes:")
logger.info("  → / (Home)")
logger.info("  → /docs (Documentation)")
logger.info("  → /eshop-example (E-Commerce Demo)")
logger.info("  → /lms-example (Learning Management System)")
logger.info("  → /social-example (Social Network)")
logger.info("  → /streaming-example (Streaming Platform)")
logger.info("")
logger.info("Architecture:")
logger.info("  → Database: PostgreSQL + MongoDB + Redis")
logger.info("  → Pattern: Repository + Service Layer")
logger.info("  → Auth: JWT-based with session support")
logger.info("  → Security: Rate limiting, sanitization, headers")
logger.info("")
logger.info(f"Environment: {ENVIRONMENT}")
logger.info(f"Demo Mode: {DEMO_MODE}")
logger.info("=" * 60)

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    serve()