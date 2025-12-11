"""
Unit of Work Pattern

Coordinates multiple repositories in a single transaction.
Ensures all changes are committed or rolled back together.
"""
from typing import Optional, Dict, Any
from core.db.transaction_manager import TransactionManager
from core.db.adapters.postgres_adapter import PostgresAdapter
from core.db.adapters.mongodb_adapter import MongoDBAdapter
from core.db.adapters.redis_adapter import RedisAdapter
from core.utils.logger import get_logger

logger = get_logger(__name__)


class UnitOfWork:
    """
    Unit of Work pattern implementation.
    
    Manages a business transaction that spans multiple repositories.
    All repositories share the same transaction context.
    
    Usage:
        async with UnitOfWork(postgres, mongodb, redis) as uow:
            # All repository operations use same transaction
            user_id = await uow.user_repo.create_user(...)
            order_id = await uow.order_repo.create_order(...)
            
            # Commit happens automatically on success
            # Rollback happens automatically on error
    """
    
    def __init__(
        self,
        postgres: Optional[PostgresAdapter] = None,
        mongodb: Optional[MongoDBAdapter] = None,
        redis: Optional[RedisAdapter] = None
    ):
        """
        Initialize unit of work.
        
        Args:
            postgres: PostgreSQL adapter
            mongodb: MongoDB adapter
            redis: Redis adapter
        """
        self.postgres = postgres
        self.mongodb = mongodb
        self.redis = redis
        self._transaction: Optional[TransactionManager] = None
        self._repositories: Dict[str, Any] = {}
        
    async def __aenter__(self):
        """Enter unit of work context."""
        # Create transaction manager
        self._transaction = TransactionManager()
        await self._transaction.__aenter__()
        
        logger.debug(f"Unit of work started with transaction {self._transaction.transaction_id}")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit unit of work context."""
        if self._transaction:
            result = await self._transaction.__aexit__(exc_type, exc_val, exc_tb)
            self._transaction = None
            return result
        
    def register_repository(self, name: str, repository: Any):
        """
        Register a repository with this unit of work.
        
        Args:
            name: Repository name
            repository: Repository instance
        """
        self._repositories[name] = repository
        
    def get_repository(self, name: str) -> Any:
        """
        Get registered repository.
        
        Args:
            name: Repository name
            
        Returns:
            Repository instance
        """
        return self._repositories.get(name)
    
    @property
    def transaction(self) -> TransactionManager:
        """Get current transaction manager."""
        if not self._transaction:
            raise RuntimeError("No active transaction")
        return self._transaction
    
    async def commit(self):
        """Explicitly commit transaction."""
        if self._transaction:
            await self._transaction.commit()
    
    async def rollback(self):
        """Explicitly rollback transaction."""
        if self._transaction:
            await self._transaction.rollback()