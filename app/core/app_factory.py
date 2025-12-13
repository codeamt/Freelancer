"""
Application Factory

Provides a factory function for creating FastHTML applications with configurable
demo mode. This allows both the main app and example apps to be created with
consistent configuration.
"""
from fasthtml.common import *
from monsterui.all import *
import os
from typing import Optional, Callable
from dotenv import load_dotenv

from core.utils.logger import get_logger
from core.db.adapters import PostgresAdapter, MongoDBAdapter, RedisAdapter
from core.services.auth import AuthService, UserService
from core.services.auth.providers.jwt import JWTProvider
from core.db.repositories import UserRepository

logger = get_logger(__name__)


def create_app(
    demo: bool = False,
    theme: Optional[object] = None,
    environment: Optional[str] = None,
    postgres_url: Optional[str] = None,
    mongo_url: Optional[str] = None,
    redis_url: Optional[str] = None,
    setup_routes: Optional[Callable] = None,
    **kwargs
) -> tuple[FastHTML, dict]:
    """
    Create a FastHTML application with optional demo mode.
    
    Args:
        demo: Whether to run in demo mode (uses mock data, limited features)
        theme: MonsterUI theme to use (defaults to Theme.slate)
        environment: Environment name (development/production)
        postgres_url: PostgreSQL connection string
        mongo_url: MongoDB connection string
        redis_url: Redis connection string
        setup_routes: Optional callback to setup routes after app creation
        **kwargs: Additional arguments passed to fast_app
        
    Returns:
        Tuple of (app, services_dict) where services_dict contains initialized services
    """
    logger.info(f"Creating app (demo={demo})...")
    
    # Load environment if not already loaded
    if not os.getenv("ENVIRONMENT"):
        load_dotenv('app.config.env')
    
    # Use environment variables or provided values
    environment = environment or os.getenv("ENVIRONMENT", "development")
    postgres_url = postgres_url or os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/app_db")
    mongo_url = mongo_url or os.getenv("MONGO_URL", "mongodb://root:example@localhost:27017")
    redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Use default theme if not provided
    if theme is None:
        theme = Theme.slate
    
    # Create FastHTML app
    app, rt = fast_app(
        hdrs=[
            *theme.headers(),
            Link(
                rel="stylesheet",
                href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"
            ),
        ],
        live=environment == "development",
        **kwargs
    )
    
    # Initialize database adapters
    logger.info("Initializing database adapters...")
    
    postgres = PostgresAdapter(
        connection_string=postgres_url,
        min_size=10 if not demo else 2,
        max_size=20 if not demo else 5
    )
    
    mongodb = MongoDBAdapter(
        connection_string=mongo_url,
        database=os.getenv("MONGO_DB", "app_db")
    )
    
    redis = RedisAdapter(
        connection_string=redis_url
    )
    
    logger.info("✓ Database adapters initialized")
    
    # Initialize repositories
    logger.info("Initializing repositories...")
    
    user_repository = UserRepository(
        postgres=postgres,
        mongodb=mongodb,
        redis=redis
    )
    
    logger.info("✓ Repositories initialized")
    
    # Initialize services
    logger.info("Initializing services...")
    
    jwt_provider = JWTProvider()
    
    auth_service = AuthService(
        user_repository=user_repository,
        jwt_provider=jwt_provider
    )
    
    user_service = UserService(
        user_repository=user_repository
    )
    
    logger.info("✓ Services initialized")
    
    # Attach services to app state
    app.state.auth_service = auth_service
    app.state.user_service = user_service
    app.state.user_repository = user_repository
    app.state.jwt_provider = jwt_provider
    app.state.postgres = postgres
    app.state.mongodb = mongodb
    app.state.redis = redis
    app.state.demo = demo
    app.state.environment = environment
    
    logger.info("✓ Services attached to app.state")
    
    # Setup lifecycle events
    @app.on_event("startup")
    async def startup():
        """Initialize database connections."""
        logger.info(f"Starting application (demo={demo})...")
        
        try:
            await postgres.connect()
            logger.info("✓ PostgreSQL connected")
            
            await mongodb.connect()
            logger.info("✓ MongoDB connected")
            
            await redis.connect()
            logger.info("✓ Redis connected")
            
            logger.info("=" * 60)
            logger.info("Application startup complete")
            
        except Exception as e:
            logger.error(f"Startup failed: {e}")
            raise
    
    @app.on_event("shutdown")
    async def shutdown():
        """Clean up database connections."""
        logger.info("Shutting down application...")
        
        try:
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
    
    # Call setup_routes callback if provided
    if setup_routes:
        setup_routes(app, rt)
    
    # Return app and services dict
    services = {
        "auth_service": auth_service,
        "user_service": user_service,
        "user_repository": user_repository,
        "jwt_provider": jwt_provider,
        "postgres": postgres,
        "mongodb": mongodb,
        "redis": redis,
    }
    
    logger.info(f"✓ App created (demo={demo})")
    
    return app, services
