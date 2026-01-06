from fasthtml.common import *
from monsterui.all import *

import os
import secrets
from core.db.config import configure_database
from core.db.adapters.postgres_adapter import PostgresAdapter
from core.utils.security import initialize_encryption
from core.utils.logger import get_logger

from core.db.adapters import PostgresAdapter, MongoDBAdapter, RedisAdapter
from core.db.repositories import UserRepository
from core.db import initialize_session_manager, get_pool_manager
from dotenv import load_dotenv
from core.db.config import configure_database

from core.middleware.redis_session import RedisSessionMiddleware
from core.config.validation import validate_config
from core.integrations.registry import validate_integrations


def create_app(*, demo: bool) -> tuple[FastHTML, dict]:
    load_dotenv('app.config.env')

    logger = get_logger(__name__)

    # Configure database
    db_config = configure_database()
    
    # Initialize encryption
    initialize_encryption()
    logger.info("✓ Encryption service initialized")
    
    # Validate integrations
    integration_validation = validate_integrations()
    valid_integrations = [name for name, result in integration_validation.items() if result['valid']]
    invalid_integrations = [name for name, result in integration_validation.items() if not result['valid']]
    
    if valid_integrations:
        logger.info(f"✓ Validated integrations: {', '.join(valid_integrations)}")
    
    if invalid_integrations:
        logger.warning(f"⚠ Invalid integrations: {', '.join(invalid_integrations)}")
        for name in invalid_integrations:
            errors = integration_validation[name]['errors']
            logger.warning(f"  {name}: {', '.join(errors)}")
    
    mongo_url = os.getenv("MONGO_URL", "mongodb://root:example@localhost:27017")
    mongo_db = os.getenv("MONGO_DB", "app_db")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    environment = os.getenv("ENVIRONMENT", "development")

    if environment != "production":
        if not os.getenv("JWT_SECRET"):
            os.environ["JWT_SECRET"] = secrets.token_hex(32)
        if not os.getenv("APP_MEDIA_KEY"):
            os.environ["APP_MEDIA_KEY"] = secrets.token_hex(32)

    validate_config()

    if os.getenv("RESET_COOKIE_CONSENT_ON_RESTART", "").lower() in {"1", "true", "yes"}:
        os.environ["COOKIE_CONSENT_RESET_TOKEN"] = secrets.token_hex(8)

    logger.info("Initializing database adapters...")

    # Initialize PostgreSQL with configuration
    postgres = PostgresAdapter()  # Will use config defaults
    
    # Initialize read replica adapter if configured
    postgres_readonly = None
    if db_config.read_replica_host:
        postgres_readonly = PostgresAdapter(read_only=True)
        logger.info("✓ Read replica adapter configured")
    
    mongodb = MongoDBAdapter(connection_string=mongo_url, database=mongo_db)
    redis = RedisAdapter(connection_string=redis_url)

    pool_manager = get_pool_manager()

    logger.info("✓ Database adapters initialized")

    logger.info("Initializing repositories...")

    user_repository = UserRepository(postgres=postgres, mongodb=mongodb, redis=redis)

    logger.info("✓ Repositories initialized")

    logger.info("Initializing services...")

    from core.services.auth import AuthService, UserService
    from core.services.auth.providers.jwt import JWTProvider

    jwt_provider = JWTProvider()

    auth_service = AuthService(user_repository=user_repository, jwt_provider=jwt_provider)
    user_service = UserService(user_repository=user_repository)

    from core.services.cart_service import CartService
    from core.services.product_service import ProductService
    from core.services.order_service import OrderService
    from core.services.payment_service import PaymentService
    from core.services.audit_service import get_audit_service
    from core.services.user_profile_service import UserProfileService
    from core.services.notification_service import get_notification_service

    cart_service = CartService()
    product_service = ProductService()
    order_service = OrderService()
    payment_service = PaymentService()
    audit_service = get_audit_service()
    profile_service = UserProfileService(user_service)
    notification_service = get_notification_service()

    logger.info("✓ Services initialized")

    logger.info("Creating FastHTML application...")

    app, rt = fast_app(
        hdrs=[
            *Theme.slate.headers(),
            Link(
                rel="stylesheet",
                href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css",
            ),
        ],
        live=environment == "development",
        static_path="app/core/static",
    )

    app.static_route(ext='.js', prefix='/static/js/', static_path='app/core/static/js')
    app.static_route(ext='.css', prefix='/static/css/', static_path='app/core/static/css')

    app.state.auth_service = auth_service
    app.state.user_service = user_service
    app.state.user_repository = user_repository
    app.state.jwt_provider = jwt_provider

    app.state.cart_service = cart_service
    app.state.product_service = product_service
    app.state.order_service = order_service
    app.state.payment_service = payment_service
    app.state.audit_service = audit_service
    app.state.profile_service = profile_service
    app.state.notification_service = notification_service

    app.state.postgres = postgres
    app.state.mongodb = mongodb
    app.state.redis = redis

    app.state.demo = demo
    app.state.environment = environment

    logger.info("✓ Services attached to app.state")
    logger.info(f"  → Demo mode: {demo}")

    logger.info("Applying security middleware...")

    try:
        from core.middleware.auth_context import AuthContextMiddleware
        from core.middleware.security import SecurityMiddleware

        app.add_middleware(AuthContextMiddleware)
        app.add_middleware(SecurityMiddleware)

        logger.info("✓ Security middleware applied")
        logger.info("  → Auth endpoint rate limiting: enabled")
        logger.info("  → Smart input sanitization: enabled")
        logger.info("  → CSS/MonsterUI: preserved")
        logger.info("  → Dangerous input sanitized")
        logger.info("  → Field-aware protection")
        logger.info("  → CSP policy: enabled (CSS-friendly)")
        logger.info("  → XSS protection: enabled")
        logger.info("  → Security headers: comprehensive")
    except Exception as e:
        logger.warning(f"⚠️ Failed to apply smart security middleware: {e}")

    if redis_url:
        try:
            app.add_middleware(
                RedisSessionMiddleware,
                redis_url=redis_url,
                cookie_name="session_id",
                ttl_seconds=60 * 60 * 24 * 7,
                cookie_secure=environment == "production",
                cookie_samesite="lax",
            )
            logger.info("✓ Redis session middleware applied")
        except Exception as e:
            logger.warning(f"⚠️ Failed to apply Redis session middleware: {e}")
            # Fallback to cookie session
            from core.middleware.cookie_session import CookieSessionMiddleware
            app.add_middleware(
                CookieSessionMiddleware,
                cookie_name="session",
                cookie_secure=environment == "production",
                cookie_samesite="lax",
            )
            logger.info("✓ Cookie session middleware applied (fallback)")
    else:
        # Use cookie session when Redis is not configured
        from core.middleware.cookie_session import CookieSessionMiddleware
        app.add_middleware(
            CookieSessionMiddleware,
            cookie_name="session",
            cookie_secure=environment == "production",
            cookie_samesite="lax",
        )
        logger.info("✓ Cookie session middleware applied")

    @app.on_event("startup")
    async def startup():
        logger.info("Starting application...")

        try:
            await postgres.connect()
            logger.info("✓ PostgreSQL connected")

            await mongodb.connect()
            logger.info("✓ MongoDB connected")

            await redis.connect()
            logger.info("✓ Redis connected")

            initialize_session_manager(postgres, mongodb, redis)
            logger.info("✓ Session manager initialized")

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
        logger.info("Shutting down application...")

        try:
            await pool_manager.close_all()
            logger.info("✓ Connection pools closed")

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

    services = {
        "auth_service": auth_service,
        "user_service": user_service,
        "user_repository": user_repository,
        "jwt_provider": jwt_provider,
        "cart_service": cart_service,
        "product_service": product_service,
        "order_service": order_service,
        "payment_service": payment_service,
        "postgres": postgres,
        "mongodb": mongodb,
        "redis": redis,
    }

    return app, services
