# app/core/db/repositories/base_repository.py
"""
Base Repository - Abstract foundation for all repositories

Provides common CRUD patterns and transaction support.
All domain repositories should extend this.
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any, Type
from datetime import datetime
from core.db.transaction_manager import TransactionManager
from core.db.adapters.postgres_adapter import PostgresAdapter
from core.db.adapters.mongodb_adapter import MongoDBAdapter
from core.db.adapters.redis_adapter import RedisAdapter
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Generic type for model/entity
T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository providing common patterns.
    
    Repositories coordinate data access across multiple databases
    while maintaining transactional consistency.
    
    Subclasses must implement:
    - get_entity_name(): Entity name for logging/keys
    - get_primary_key_field(): Primary key field name
    - to_dict(): Convert entity to dict
    - from_dict(): Convert dict to entity
    """
    
    def __init__(
        self,
        postgres: Optional[PostgresAdapter] = None,
        mongodb: Optional[MongoDBAdapter] = None,
        redis: Optional[RedisAdapter] = None
    ):
        """
        Initialize repository with database adapters.
        
        Args:
            postgres: PostgreSQL adapter for structured data
            mongodb: MongoDB adapter for document data
            redis: Redis adapter for caching
        """
        self.postgres = postgres
        self.mongodb = mongodb
        self.redis = redis
        
        # Validate that at least one adapter is provided
        if not any([postgres, mongodb]):
            raise ValueError(
                f"{self.__class__.__name__} requires at least Postgres or MongoDB"
            )
    
    # ========================================================================
    # Abstract Methods - Subclasses MUST implement
    # ========================================================================
    
    @abstractmethod
    def get_entity_name(self) -> str:
        """
        Get entity name for logging and cache keys.
        
        Returns:
            Entity name (e.g., "user", "product", "order")
        """
        pass
    
    @abstractmethod
    def get_primary_key_field(self) -> str:
        """
        Get primary key field name.
        
        Returns:
            Primary key field (e.g., "id", "user_id")
        """
        pass
    
    @abstractmethod
    def to_dict(self, entity: T) -> Dict[str, Any]:
        """
        Convert entity to dictionary.
        
        Args:
            entity: Entity instance
            
        Returns:
            Dictionary representation
        """
        pass
    
    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> T:
        """
        Convert dictionary to entity.
        
        Args:
            data: Dictionary data
            
        Returns:
            Entity instance
        """
        pass
    
    # ========================================================================
    # Cache Management (Redis)
    # ========================================================================
    
    def _get_cache_key(self, identifier: Any, prefix: str = None) -> str:
        """
        Generate cache key.
        
        Args:
            identifier: Entity identifier
            prefix: Optional prefix (default: primary key field)
            
        Returns:
            Cache key string
        """
        entity_name = self.get_entity_name()
        prefix = prefix or self.get_primary_key_field()
        return f"{entity_name}:{prefix}:{identifier}"
    
    async def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get from cache if Redis is available."""
        if not self.redis:
            return None
        
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.warning(f"Cache read error for {key}: {e}")
            return None
    
    async def _set_cache(
        self,
        key: str,
        value: Dict,
        ttl_seconds: int = 300
    ):
        """Set cache if Redis is available."""
        if not self.redis:
            return
        
        try:
            await self.redis.setex(key, ttl_seconds, value)
        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")
    
    async def _invalidate_cache(self, *keys: str):
        """Invalidate multiple cache keys."""
        if not self.redis:
            return
        
        try:
            for key in keys:
                await self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
    
    async def _invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        if not self.redis:
            return
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache pattern invalidation error: {e}")
    
    # ========================================================================
    # Common CRUD Operations (Can be overridden)
    # ========================================================================
    
    async def get_by_id(
        self,
        entity_id: Any,
        use_cache: bool = True
    ) -> Optional[T]:
        """
        Get entity by primary key.
        
        Args:
            entity_id: Entity ID
            use_cache: Whether to use cache
            
        Returns:
            Entity instance or None
        """
        entity_name = self.get_entity_name()
        pk_field = self.get_primary_key_field()
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(entity_id)
            cached = await self._get_from_cache(cache_key)
            if cached:
                logger.debug(f"Cache hit for {entity_name} {entity_id}")
                return self.from_dict(cached)
        
        # Not in cache, fetch from database
        data = await self._fetch_by_id(entity_id)
        
        if not data:
            return None
        
        # Cache result
        if use_cache:
            cache_key = self._get_cache_key(entity_id)
            await self._set_cache(cache_key, data)
        
        return self.from_dict(data)
    
    @abstractmethod
    async def _fetch_by_id(self, entity_id: Any) -> Optional[Dict]:
        """
        Fetch entity data by ID from database.
        
        Subclasses implement the actual database query.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity data dict or None
        """
        pass
    
    async def exists(self, entity_id: Any) -> bool:
        """
        Check if entity exists.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            True if exists
        """
        entity = await self.get_by_id(entity_id, use_cache=True)
        return entity is not None
    
    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False
    ) -> List[T]:
        """
        List entities with pagination and filtering.
        
        Args:
            limit: Max results
            offset: Pagination offset
            filters: Optional filter dict
            sort_by: Optional sort field
            sort_desc: Sort descending
            
        Returns:
            List of entities
        """
        data_list = await self._fetch_list(
            limit=limit,
            offset=offset,
            filters=filters,
            sort_by=sort_by,
            sort_desc=sort_desc
        )
        
        return [self.from_dict(data) for data in data_list]
    
    @abstractmethod
    async def _fetch_list(
        self,
        limit: int,
        offset: int,
        filters: Optional[Dict[str, Any]],
        sort_by: Optional[str],
        sort_desc: bool
    ) -> List[Dict]:
        """
        Fetch list of entities from database.
        
        Subclasses implement the actual database query.
        
        Args:
            limit: Max results
            offset: Pagination offset
            filters: Optional filter dict
            sort_by: Optional sort field
            sort_desc: Sort descending
            
        Returns:
            List of entity data dicts
        """
        pass
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities.
        
        Args:
            filters: Optional filter dict
            
        Returns:
            Count
        """
        return await self._count(filters)
    
    @abstractmethod
    async def _count(self, filters: Optional[Dict[str, Any]]) -> int:
        """
        Count entities in database.
        
        Subclasses implement the actual database query.
        
        Args:
            filters: Optional filter dict
            
        Returns:
            Count
        """
        pass
    
    # ========================================================================
    # Transaction Support
    # ========================================================================
    
    async def execute_in_transaction(
        self,
        transaction_manager: TransactionManager,
        adapter: Any,
        operation: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute operation within transaction.
        
        Wrapper around transaction manager for convenience.
        
        Args:
            transaction_manager: Transaction manager instance
            adapter: Database adapter
            operation: Operation name
            *args, **kwargs: Operation arguments
            
        Returns:
            Operation result
        """
        return await transaction_manager.execute(
            adapter,
            operation,
            *args,
            **kwargs
        )
    
    # ========================================================================
    # Audit/Logging Helpers
    # ========================================================================
    
    def _add_timestamps(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add created_at and updated_at timestamps.
        
        Args:
            data: Entity data
            
        Returns:
            Data with timestamps
        """
        now = datetime.utcnow()
        data['created_at'] = now
        data['updated_at'] = now
        return data
    
    def _update_timestamp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update updated_at timestamp.
        
        Args:
            data: Entity data
            
        Returns:
            Data with updated timestamp
        """
        data['updated_at'] = datetime.utcnow()
        return data
    
    def _log_operation(
        self,
        operation: str,
        entity_id: Any,
        details: Optional[str] = None
    ):
        """
        Log repository operation.
        
        Args:
            operation: Operation name (create, update, delete, etc.)
            entity_id: Entity ID
            details: Optional details
        """
        entity_name = self.get_entity_name()
        msg = f"{operation.upper()} {entity_name} {entity_id}"
        if details:
            msg += f" - {details}"
        logger.info(msg)
    
    # ========================================================================
    # Validation Helpers
    # ========================================================================
    
    def _validate_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: List[str]
    ):
        """
        Validate that required fields are present.
        
        Args:
            data: Data dict
            required_fields: List of required field names
            
        Raises:
            ValueError: If required field is missing
        """
        missing = [f for f in required_fields if f not in data or data[f] is None]
        if missing:
            entity_name = self.get_entity_name()
            raise ValueError(
                f"{entity_name} missing required fields: {', '.join(missing)}"
            )


class PostgresRepository(BaseRepository[T]):
    """
    Base repository for Postgres-primary entities.
    
    Use when entity data primarily lives in Postgres
    with optional MongoDB/Redis support.
    """
    
    def __init__(
        self,
        postgres: PostgresAdapter,
        mongodb: Optional[MongoDBAdapter] = None,
        redis: Optional[RedisAdapter] = None
    ):
        if not postgres:
            raise ValueError("PostgresRepository requires postgres adapter")
        super().__init__(postgres, mongodb, redis)
    
    @abstractmethod
    def get_table_name(self) -> str:
        """Get Postgres table name."""
        pass
    
    async def _fetch_by_id(self, entity_id: Any) -> Optional[Dict]:
        """Fetch from Postgres by ID."""
        table = self.get_table_name()
        pk_field = self.get_primary_key_field()
        
        query = f"SELECT * FROM {table} WHERE {pk_field} = $1"
        return await self.postgres.fetch_one(query, entity_id)
    
    async def _fetch_list(
        self,
        limit: int,
        offset: int,
        filters: Optional[Dict[str, Any]],
        sort_by: Optional[str],
        sort_desc: bool
    ) -> List[Dict]:
        """Fetch list from Postgres."""
        table = self.get_table_name()
        
        # Build query
        query = f"SELECT * FROM {table}"
        params = []
        
        # Add filters
        if filters:
            where_clauses = []
            for i, (key, value) in enumerate(filters.items(), start=1):
                where_clauses.append(f"{key} = ${i}")
                params.append(value)
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        # Add sorting
        if sort_by:
            direction = "DESC" if sort_desc else "ASC"
            query += f" ORDER BY {sort_by} {direction}"
        
        # Add pagination
        query += f" LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])
        
        return await self.postgres.fetch_many(query, *params)
    
    async def _count(self, filters: Optional[Dict[str, Any]]) -> int:
        """Count in Postgres."""
        table = self.get_table_name()
        
        query = f"SELECT COUNT(*) FROM {table}"
        params = []
        
        if filters:
            where_clauses = []
            for i, (key, value) in enumerate(filters.items(), start=1):
                where_clauses.append(f"{key} = ${i}")
                params.append(value)
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        result = await self.postgres.fetch_one(query, *params)
        return result['count'] if result else 0


class MongoRepository(BaseRepository[T]):
    """
    Base repository for MongoDB-primary entities.
    
    Use when entity data primarily lives in MongoDB
    with optional Postgres/Redis support.
    """
    
    def __init__(
        self,
        mongodb: MongoDBAdapter,
        postgres: Optional[PostgresAdapter] = None,
        redis: Optional[RedisAdapter] = None
    ):
        if not mongodb:
            raise ValueError("MongoRepository requires mongodb adapter")
        super().__init__(postgres, mongodb, redis)
    
    @abstractmethod
    def get_collection_name(self) -> str:
        """Get MongoDB collection name."""
        pass
    
    async def _fetch_by_id(self, entity_id: Any) -> Optional[Dict]:
        """Fetch from MongoDB by ID."""
        collection = self.get_collection_name()
        pk_field = self.get_primary_key_field()
        
        return await self.mongodb.find_one(
            collection,
            {pk_field: entity_id}
        )
    
    async def _fetch_list(
        self,
        limit: int,
        offset: int,
        filters: Optional[Dict[str, Any]],
        sort_by: Optional[str],
        sort_desc: bool
    ) -> List[Dict]:
        """Fetch list from MongoDB."""
        collection = self.get_collection_name()
        
        filter_query = filters or {}
        sort = [(sort_by, -1 if sort_desc else 1)] if sort_by else None
        
        return await self.mongodb.find_many(
            collection,
            filter_query,
            limit=limit,
            skip=offset,
            sort=sort
        )
    
    async def _count(self, filters: Optional[Dict[str, Any]]) -> int:
        """Count in MongoDB."""
        collection = self.get_collection_name()
        filter_query = filters or {}
        
        return await self.mongodb.count(collection, filter_query)