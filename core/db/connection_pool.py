"""
Connection Pool Management

Provides connection pool configuration and monitoring.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from core.utils.logger import get_logger

logger = get_logger(__name__)


class PoolType(Enum):
    """Database pool types."""
    POSTGRES = "postgres"
    MONGODB = "mongodb"
    REDIS = "redis"


@dataclass
class PoolConfig:
    """Connection pool configuration."""
    min_size: int = 10
    max_size: int = 20
    max_idle_seconds: int = 300  # 5 minutes
    max_lifetime_seconds: int = 3600  # 1 hour
    connect_timeout_seconds: int = 10
    command_timeout_seconds: int = 60


@dataclass
class PoolStats:
    """Connection pool statistics."""
    pool_type: str
    current_size: int
    idle_count: int
    active_count: int
    waiting_count: int
    total_connections_created: int
    total_connections_closed: int


class ConnectionPoolManager:
    """
    Manages connection pools across all adapters.
    
    Provides monitoring and health check capabilities.
    """
    
    def __init__(self):
        """Initialize pool manager."""
        self.pools: Dict[str, Any] = {}
        self.configs: Dict[str, PoolConfig] = {}
        
    def register_pool(
        self,
        name: str,
        pool: Any,
        config: PoolConfig
    ):
        """
        Register a connection pool.
        
        Args:
            name: Pool name/identifier
            pool: Pool instance
            config: Pool configuration
        """
        self.pools[name] = pool
        self.configs[name] = config
        logger.info(f"Registered connection pool: {name}")
    
    async def get_pool_stats(self, name: str) -> Optional[PoolStats]:
        """
        Get statistics for a pool.
        
        Args:
            name: Pool name
            
        Returns:
            PoolStats or None if pool not found
        """
        pool = self.pools.get(name)
        if not pool:
            return None
        
        # Extract stats based on pool type
        if hasattr(pool, 'get_size'):
            # asyncpg pool (Postgres)
            return PoolStats(
                pool_type="postgres",
                current_size=pool.get_size(),
                idle_count=pool.get_idle_size(),
                active_count=pool.get_size() - pool.get_idle_size(),
                waiting_count=0,  # asyncpg doesn't expose this
                total_connections_created=0,
                total_connections_closed=0
            )
        
        # Return generic stats
        return PoolStats(
            pool_type="unknown",
            current_size=0,
            idle_count=0,
            active_count=0,
            waiting_count=0,
            total_connections_created=0,
            total_connections_closed=0
        )
    
    async def get_all_stats(self) -> Dict[str, PoolStats]:
        """
        Get statistics for all pools.
        
        Returns:
            Dict of pool name to stats
        """
        stats = {}
        for name in self.pools:
            pool_stats = await self.get_pool_stats(name)
            if pool_stats:
                stats[name] = pool_stats
        return stats
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all pools.
        
        Returns:
            Dict of pool name to health status
        """
        health = {}
        for name, pool in self.pools.items():
            try:
                # Basic health check - try to get stats
                stats = await self.get_pool_stats(name)
                health[name] = stats is not None
            except Exception as e:
                logger.error(f"Health check failed for pool {name}: {e}")
                health[name] = False
        
        return health
    
    async def close_all(self):
        """Close all connection pools."""
        for name, pool in self.pools.items():
            try:
                if hasattr(pool, 'close'):
                    await pool.close()
                logger.info(f"Closed connection pool: {name}")
            except Exception as e:
                logger.error(f"Error closing pool {name}: {e}")


# ============================================================================
# Global Pool Manager
# ============================================================================

_pool_manager: Optional[ConnectionPoolManager] = None


def get_pool_manager() -> ConnectionPoolManager:
    """
    Get global pool manager.
    
    Returns:
        ConnectionPoolManager instance
    """
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager()
    return _pool_manager


# ============================================================================
# Default Configurations
# ============================================================================

DEFAULT_POSTGRES_CONFIG = PoolConfig(
    min_size=10,
    max_size=20,
    max_idle_seconds=300,
    max_lifetime_seconds=3600,
    connect_timeout_seconds=10,
    command_timeout_seconds=60
)

DEFAULT_MONGODB_CONFIG = PoolConfig(
    min_size=10,
    max_size=100,
    max_idle_seconds=300,
    max_lifetime_seconds=3600,
    connect_timeout_seconds=10,
    command_timeout_seconds=60
)

DEFAULT_REDIS_CONFIG = PoolConfig(
    min_size=10,
    max_size=50,
    max_idle_seconds=300,
    max_lifetime_seconds=3600,
    connect_timeout_seconds=5,
    command_timeout_seconds=10
)