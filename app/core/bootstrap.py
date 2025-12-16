from fasthtml.common import *
from monsterui.all import *

import os
import secrets
from dotenv import load_dotenv

from core.config.validation import validate_config
from core.utils.logger import get_logger

from core.db.adapters import PostgresAdapter, MongoDBAdapter, RedisAdapter
from core.db.repositories import UserRepository
from core.db import initialize_session_manager, get_pool_manager

from core.services.auth import AuthService, UserService
from core.services.auth.providers.jwt import JWTProvider

from core.middleware.security import SecurityHeaders, RateLimitMiddleware, SecurityMiddleware
from core.middleware import RedisSessionMiddleware


def create_app(*, demo: bool) -> tuple[FastHTML, dict]:
    load_dotenv('app.config.env')
    validate_config()

    logger = get_logger(__name__)

    postgres_url = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/app_db")
    mongo_url = os.getenv("MONGO_URL", "mongodb://root:example@localhost:27017")
    mongo_db = os.getenv("MONGO_DB", "app_db")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    environment = os.getenv("ENVIRONMENT", "development")

    if os.getenv("RESET_COOKIE_CONSENT_ON_RESTART", "").lower() in {"1", "true", "yes"}:
        os.environ["COOKIE_CONSENT_RESET_TOKEN"] = secrets.token_hex(8)

    logger.info("Initializing database adapters...")

    postgres = PostgresAdapter(connection_string=postgres_url, min_size=10, max_size=20)
    mongodb = MongoDBAdapter(connection_string=mongo_url, database=mongo_db)
    redis = RedisAdapter(connection_string=redis_url)

    pool_manager = get_pool_manager()

    logger.info("✓ Database adapters initialized")

    logger.info("Initializing repositories...")

    user_repository = UserRepository(postgres=postgres, mongodb=mongodb, redis=redis)

    logger.info("✓ Repositories initialized")

    logger.info("Initializing services...")

    jwt_provider = JWTProvider()

    auth_service = AuthService(user_repository=user_repository, jwt_provider=jwt_provider)
    user_service = UserService(user_repository=user_repository)

    from core.services.cart import CartService
    from core.services.product import ProductService
    from core.services.order import OrderService
    from core.services.payment import PaymentService

    cart_service = CartService()
    product_service = ProductService()
    order_service = OrderService()
    payment_service = PaymentService()

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
        static_path="app/core/ui/static",
    )

    app.static_route(ext='.js', prefix='/static/js/', static_path='app/core/ui/static/js')
    app.static_route(ext='.css', prefix='/static/css/', static_path='app/core/ui/static/css')

    app.state.auth_service = auth_service
    app.state.user_service = user_service
    app.state.user_repository = user_repository
    app.state.jwt_provider = jwt_provider

    app.state.cart_service = cart_service
    app.state.product_service = product_service
    app.state.order_service = order_service
    app.state.payment_service = payment_service

    app.state.postgres = postgres
    app.state.mongodb = mongodb
    app.state.redis = redis

    app.state.demo = demo
    app.state.environment = environment

    logger.info("✓ Services attached to app.state")
    logger.info(f"  → Demo mode: {demo}")

    logger.info("Applying middleware...")

    try:
        app.add_middleware(SecurityMiddleware)
        app.add_middleware(RateLimitMiddleware)
        app.add_middleware(SecurityHeaders)

        logger.info("✓ Security middlewares applied")
        logger.info("  → Input sanitization: enabled")
        logger.info("  → Rate limiting: 60 req/min per IP")
        logger.info("  → Security headers: enabled")
        logger.info("  → CSP: disabled (FastHTML inline styles)")
        logger.info("  → CSRF: disabled (needs HTMX token integration)")
    except Exception as e:
        logger.warning(f"⚠️ Failed to apply security middlewares: {e}")

    if redis_url and redis_url != "redis://localhost:6379":
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
    else:
        logger.info("ℹ️  Redis session middleware skipped (Redis not configured)")

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
