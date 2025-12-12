"""
Database Service - Unified multi-database access with state system integration

Provides simplified access to the multi-transactional database system.
Integrates with UserContext for user-aware operations and audit logging.
"""
from typing import Dict, List, Any, Optional
from core.db import (
    TransactionManager,
    transactional,
    transaction,
    PostgresAdapter,
    MongoDBAdapter,
    RedisAdapter
)
from core.services.auth.context import current_user_context, UserContext
from core.utils.logger import get_logger

logger = get_logger(__name__)


class DBService:
    """
    Unified database service for multi-database operations.
    
    Features:
    - Multi-database support (PostgreSQL, MongoDB, Redis)
    - Automatic transaction management
    - User context integration for audit trails
    - State-aware operations
    
    Usage:
        db = DBService()
        
        # Simple operations (auto-transaction)
        await db.insert("users", {"name": "John", "email": "john@example.com"})
        user = await db.find_one("users", {"email": "john@example.com"})
        
        # Complex operations (manual transaction)
        async with db.transaction() as tm:
            await db.insert("users", {...}, transaction_manager=tm)
            await db.insert("profiles", {...}, transaction_manager=tm)
            # Auto-commits on success, auto-rollbacks on error
    """
    
    def __init__(self):
        """Initialize database service with adapters."""
        self.postgres = PostgresAdapter()
        self.mongodb = MongoDBAdapter()
        self.redis = RedisAdapter()
        logger.info("DBService initialized with multi-database support")
    
    def _get_user_context(self) -> Optional[UserContext]:
        """Get current user context from state system."""
        try:
            return current_user_context.get(None)
        except Exception:
            return None
    
    def _enrich_with_audit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich data with audit fields from user context.
        
        Adds:
        - created_by: user_id
        - updated_by: user_id
        - created_at: timestamp (if not present)
        - updated_at: timestamp
        """
        user_context = self._get_user_context()
        
        enriched = data.copy()
        
        if user_context:
            # Add user tracking
            if 'created_by' not in enriched:
                enriched['created_by'] = user_context.user_id
            enriched['updated_by'] = user_context.user_id
            
            # Add metadata
            if 'metadata' not in enriched:
                enriched['metadata'] = {}
            enriched['metadata']['user_role'] = user_context.role
            enriched['metadata']['ip_address'] = user_context.ip_address
        
        return enriched
    
    # ========================================================================
    # Transaction Management
    # ========================================================================
    
    def transaction(self, timeout_seconds: int = 30):
        """
        Create a transaction context manager.
        
        Usage:
            async with db.transaction() as tm:
                await db.insert("users", {...}, transaction_manager=tm)
                await db.insert("profiles", {...}, transaction_manager=tm)
        """
        return transaction(timeout_seconds=timeout_seconds)
    
    # ========================================================================
    # PostgreSQL Operations (Relational Data)
    # ========================================================================
    
    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
        transaction_manager: Optional[TransactionManager] = None,
        audit: bool = True
    ) -> Dict[str, Any]:
        """
        Insert record into PostgreSQL table.
        
        Args:
            table: Table name
            data: Record data
            transaction_manager: Optional transaction manager
            audit: Whether to add audit fields (default True)
            
        Returns:
            Inserted record with ID
        """
        # Enrich with audit fields if enabled
        if audit:
            data = self._enrich_with_audit(data)
        
        if transaction_manager:
            return await transaction_manager.execute(
                self.postgres, "insert", table, data
            )
        
        async with TransactionManager() as tm:
            return await tm.execute(self.postgres, "insert", table, data)
    
    async def update(
        self,
        table: str,
        record_id: Any,
        data: Dict[str, Any],
        transaction_manager: Optional[TransactionManager] = None,
        audit: bool = True
    ) -> Dict[str, Any]:
        """
        Update record in PostgreSQL table.
        
        Args:
            table: Table name
            record_id: Record ID
            data: Updated data
            transaction_manager: Optional transaction manager
            audit: Whether to add audit fields (default True)
            
        Returns:
            Updated record
        """
        # Add updated_by from user context
        if audit:
            user_context = self._get_user_context()
            if user_context:
                data['updated_by'] = user_context.user_id
        
        if transaction_manager:
            return await transaction_manager.execute(
                self.postgres, "update", table, record_id, data
            )
        
        async with TransactionManager() as tm:
            return await tm.execute(self.postgres, "update", table, record_id, data)
    
    async def delete(
        self,
        table: str,
        record_id: Any,
        transaction_manager: Optional[TransactionManager] = None
    ) -> bool:
        """
        Delete record from PostgreSQL table.
        
        Args:
            table: Table name
            record_id: Record ID
            transaction_manager: Optional transaction manager
            
        Returns:
            True if deleted
        """
        if transaction_manager:
            return await transaction_manager.execute(
                self.postgres, "delete", table, record_id
            )
        
        async with TransactionManager() as tm:
            return await tm.execute(self.postgres, "delete", table, record_id)
    
    async def find_one(
        self,
        table: str,
        filters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find one record in PostgreSQL table.
        
        Args:
            table: Table name
            filters: Filter conditions
            
        Returns:
            Record or None
        """
        return await self.postgres.find_one(table, filters)
    
    async def find_many(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Find multiple records in PostgreSQL table.
        
        Args:
            table: Table name
            filters: Filter conditions
            limit: Maximum records to return
            offset: Number of records to skip
            
        Returns:
            List of records
        """
        return await self.postgres.find_many(table, filters, limit, offset)
    
    # ========================================================================
    # MongoDB Operations (Document Data)
    # ========================================================================
    
    async def insert_document(
        self,
        collection: str,
        document: Dict[str, Any],
        transaction_manager: Optional[TransactionManager] = None,
        audit: bool = True
    ) -> Dict[str, Any]:
        """
        Insert document into MongoDB collection.
        
        Args:
            collection: Collection name
            document: Document data
            transaction_manager: Optional transaction manager
            audit: Whether to add audit fields (default True)
            
        Returns:
            Inserted document with _id
        """
        # Enrich with audit fields if enabled
        if audit:
            document = self._enrich_with_audit(document)
        
        if transaction_manager:
            return await transaction_manager.execute(
                self.mongodb, "insert_one", collection, document
            )
        
        async with TransactionManager() as tm:
            return await tm.execute(self.mongodb, "insert_one", collection, document)
    
    async def find_document(
        self,
        collection: str,
        filters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find one document in MongoDB collection.
        
        Args:
            collection: Collection name
            filters: Filter conditions
            
        Returns:
            Document or None
        """
        return await self.mongodb.find_one(collection, filters)
    
    async def find_documents(
        self,
        collection: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents in MongoDB collection.
        
        Args:
            collection: Collection name
            filters: Filter conditions
            limit: Maximum documents to return
            skip: Number of documents to skip
            
        Returns:
            List of documents
        """
        return await self.mongodb.find(collection, filters, limit, skip)
    
    async def update_document(
        self,
        collection: str,
        filters: Dict[str, Any],
        update: Dict[str, Any],
        transaction_manager: Optional[TransactionManager] = None,
        audit: bool = True
    ) -> Dict[str, Any]:
        """
        Update document in MongoDB collection.
        
        Args:
            collection: Collection name
            filters: Filter conditions
            update: Update operations
            transaction_manager: Optional transaction manager
            audit: Whether to add audit fields (default True)
            
        Returns:
            Updated document
        """
        # Add updated_by from user context
        if audit:
            user_context = self._get_user_context()
            if user_context:
                if '$set' not in update:
                    update['$set'] = {}
                update['$set']['updated_by'] = user_context.user_id
        
        if transaction_manager:
            return await transaction_manager.execute(
                self.mongodb, "update_one", collection, filters, update
            )
        
        async with TransactionManager() as tm:
            return await tm.execute(self.mongodb, "update_one", collection, filters, update)
    
    async def delete_document(
        self,
        collection: str,
        filters: Dict[str, Any],
        transaction_manager: Optional[TransactionManager] = None
    ) -> bool:
        """
        Delete document from MongoDB collection.
        
        Args:
            collection: Collection name
            filters: Filter conditions
            transaction_manager: Optional transaction manager
            
        Returns:
            True if deleted
        """
        if transaction_manager:
            return await transaction_manager.execute(
                self.mongodb, "delete_one", collection, filters
            )
        
        async with TransactionManager() as tm:
            return await tm.execute(self.mongodb, "delete_one", collection, filters)
    
    # ========================================================================
    # Redis Operations (Cache)
    # ========================================================================
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        return await self.redis.get(key)
    
    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        transaction_manager: Optional[TransactionManager] = None
    ) -> bool:
        """
        Set value in Redis cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            transaction_manager: Optional transaction manager
            
        Returns:
            True if set successfully
        """
        if transaction_manager:
            return await transaction_manager.execute(
                self.redis, "set", key, value, ttl
            )
        
        async with TransactionManager() as tm:
            return await tm.execute(self.redis, "set", key, value, ttl)
    
    async def cache_delete(
        self,
        key: str,
        transaction_manager: Optional[TransactionManager] = None
    ) -> bool:
        """
        Delete value from Redis cache.
        
        Args:
            key: Cache key
            transaction_manager: Optional transaction manager
            
        Returns:
            True if deleted
        """
        if transaction_manager:
            return await transaction_manager.execute(
                self.redis, "delete", key
            )
        
        async with TransactionManager() as tm:
            return await tm.execute(self.redis, "delete", key)
    
    async def cache_exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        return await self.redis.exists(key)
    
    # ========================================================================
    # User-Aware Helper Methods
    # ========================================================================
    
    async def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data (checks both PostgreSQL and MongoDB).
        
        Args:
            user_id: User ID
            
        Returns:
            User data or None
        """
        # Try PostgreSQL first
        user = await self.find_one("users", {"id": user_id})
        if user:
            return user
        
        # Try MongoDB
        user = await self.find_document("users", {"_id": user_id})
        return user
    
    async def log_user_action(
        self,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log user action for audit trail.
        
        Args:
            action: Action performed (e.g., "create", "update", "delete")
            resource: Resource affected (e.g., "order", "course")
            details: Additional details
        """
        user_context = self._get_user_context()
        
        if not user_context:
            logger.warning("Cannot log action: no user context")
            return
        
        log_entry = {
            "user_id": user_context.user_id,
            "role": user_context.role,
            "action": action,
            "resource": resource,
            "details": details or {},
            "ip_address": user_context.ip_address,
            "user_agent": user_context.user_agent
        }
        
        # Log to MongoDB (audit logs)
        await self.insert_document("audit_logs", log_entry, audit=False)
        logger.info(f"Logged action: {user_context.user_id} {action} {resource}")


# Singleton instance
_db_service_instance: Optional[DBService] = None


def get_db_service() -> DBService:
    """
    Get singleton DBService instance.
    
    Usage:
        db = get_db_service()
        await db.insert("users", {...})
    """
    global _db_service_instance
    if _db_service_instance is None:
        _db_service_instance = DBService()
    return _db_service_instance
