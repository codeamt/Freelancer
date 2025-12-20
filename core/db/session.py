"""
Database Session Management

Provides session factories for different databases.
Handles connection lifecycle and session context.
"""
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from core.db.adapters.postgres_adapter import PostgresAdapter
from core.db.adapters.mongodb_adapter import MongoDBAdapter
from core.db.adapters.redis_adapter import RedisAdapter
from core.utils.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """
    Manages database sessions across adapters.
    
    Provides context managers for acquiring database connections.
    """
    
    def __init__(
        self,
        postgres: Optional[PostgresAdapter] = None,
        mongodb: Optional[MongoDBAdapter] = None,
        redis: Optional[RedisAdapter] = None
    ):
        """
        Initialize session manager.
        
        Args:
            postgres: PostgreSQL adapter
            mongodb: MongoDB adapter
            redis: Redis adapter
        """
        self.postgres = postgres
        self.mongodb = mongodb
        self.redis = redis
        
    @asynccontextmanager
    async def postgres_session(self) -> AsyncGenerator:
        """
        Get PostgreSQL session (connection).
        
        Usage:
            async with session_manager.postgres_session() as conn:
                await conn.execute("SELECT * FROM users")
        
        Yields:
            PostgreSQL connection
        """
        if not self.postgres:
            raise RuntimeError("PostgreSQL adapter not configured")
        
        async with self.postgres.acquire() as conn:
            yield conn
    
    @asynccontextmanager
    async def mongodb_session(self) -> AsyncGenerator:
        """
        Get MongoDB session.
        
        Usage:
            async with session_manager.mongodb_session() as session:
                await db.collection.find_one({}, session=session)
        
        Yields:
            MongoDB session
        """
        if not self.mongodb:
            raise RuntimeError("MongoDB adapter not configured")
        
        if not self.mongodb.client:
            await self.mongodb.connect()
        
        session = await self.mongodb.client.start_session()
        try:
            yield session
        finally:
            await session.end_session()
    
    async def get_redis_client(self):
        """
        Get Redis client.
        
        Returns:
            Redis client instance
        """
        if not self.redis:
            raise RuntimeError("Redis adapter not configured")
        
        if not self.redis.client:
            await self.redis.connect()
        
        return self.redis.client
    
    async def close_all(self):
        """Close all database connections."""
        if self.postgres:
            await self.postgres.disconnect()
        if self.mongodb:
            await self.mongodb.disconnect()
        if self.redis:
            await self.redis.disconnect()
        
        logger.info("All database sessions closed")


# ============================================================================
# Global Session Manager (Singleton)
# ============================================================================

_session_manager: Optional[SessionManager] = None


def initialize_session_manager(
    postgres: Optional[PostgresAdapter] = None,
    mongodb: Optional[MongoDBAdapter] = None,
    redis: Optional[RedisAdapter] = None
):
    """
    Initialize global session manager.
    
    Args:
        postgres: PostgreSQL adapter
        mongodb: MongoDB adapter
        redis: Redis adapter
    """
    global _session_manager
    _session_manager = SessionManager(postgres, mongodb, redis)
    logger.info("Session manager initialized")


def get_session_manager() -> SessionManager:
    """
    Get global session manager.
    
    Returns:
        SessionManager instance
        
    Raises:
        RuntimeError: If not initialized
    """
    if _session_manager is None:
        raise RuntimeError(
            "Session manager not initialized. "
            "Call initialize_session_manager() first."
        )
    return _session_manager