"""
Multi-Database Transaction Coordinator

Handles ACID transactions across PostgreSQL, MongoDB, and other databases.
Uses Two-Phase Commit (2PC) pattern for distributed transactions.
"""
from typing import Dict, List, Callable, Any, Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
import uuid
from core.utils.logger import get_logger

logger = get_logger(__name__)


class TransactionState(Enum):
    PENDING = "pending"
    PREPARED = "prepared"
    COMMITTED = "committed"
    ABORTED = "aborted"


@dataclass
class TransactionLog:
    """Transaction log entry for audit and recovery"""
    transaction_id: str
    state: TransactionState
    participants: List[str] = field(default_factory=list)
    rollback_actions: List[Callable] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TransactionManager:
    """
    Coordinates transactions across multiple databases.
    
    Usage:
        async with TransactionManager() as tm:
            # Postgres operations
            await tm.execute(postgres_adapter, "INSERT INTO products ...")
            
            # MongoDB operations
            await tm.execute(mongo_adapter, "insert_one", collection, data)
            
            # Redis cache invalidation
            await tm.execute(redis_adapter, "delete", cache_key)
            
            # Auto-commits on success, auto-rollback on error
    """
    
    def __init__(self):
        self.transaction_id = str(uuid.uuid4())
        self.log = TransactionLog(
            transaction_id=self.transaction_id,
            state=TransactionState.PENDING
        )
        self.adapters: Dict[str, Any] = {}
        self.operations: List[Dict] = []
        
    async def __aenter__(self):
        """Start transaction"""
        logger.info(f"Starting transaction {self.transaction_id}")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction"""
        if exc_type is not None:
            await self.rollback()
            logger.error(f"Transaction {self.transaction_id} rolled back: {exc_val}")
            return False
        
        try:
            await self.commit()
            logger.info(f"Transaction {self.transaction_id} committed")
        except Exception as e:
            await self.rollback()
            logger.error(f"Commit failed, rolled back: {e}")
            raise
            
    async def execute(self, adapter, operation: str, *args, **kwargs):
        """
        Execute operation and register for rollback if needed.
        
        Args:
            adapter: Database adapter instance
            operation: Operation name (e.g., "insert", "update", "delete")
            *args, **kwargs: Operation parameters
        """
        adapter_name = adapter.__class__.__name__
        
        # Register adapter
        if adapter_name not in self.adapters:
            self.adapters[adapter_name] = adapter
            self.log.participants.append(adapter_name)
            
        # Execute operation
        result = await getattr(adapter, operation)(*args, **kwargs)
        
        # Register operation for logging
        self.operations.append({
            "adapter": adapter_name,
            "operation": operation,
            "args": args,
            "kwargs": kwargs,
            "result": result
        })
        
        # Register rollback action if available
        if hasattr(adapter, f"rollback_{operation}"):
            rollback_fn = getattr(adapter, f"rollback_{operation}")
            self.log.rollback_actions.append(
                lambda: rollback_fn(result, *args, **kwargs)
            )
            
        return result
        
    async def prepare(self):
        """Phase 1: Prepare all participants"""
        self.log.state = TransactionState.PREPARED
        
        for name, adapter in self.adapters.items():
            if hasattr(adapter, 'prepare_transaction'):
                await adapter.prepare_transaction(self.transaction_id)
                
    async def commit(self):
        """Phase 2: Commit all participants"""
        await self.prepare()
        
        for name, adapter in self.adapters.items():
            if hasattr(adapter, 'commit_transaction'):
                await adapter.commit_transaction(self.transaction_id)
            elif hasattr(adapter, 'commit'):
                await adapter.commit()
                
        self.log.state = TransactionState.COMMITTED
        
    async def rollback(self):
        """Rollback all operations"""
        self.log.state = TransactionState.ABORTED
        
        # Execute rollback actions in reverse order
        for rollback_fn in reversed(self.log.rollback_actions):
            try:
                await rollback_fn()
            except Exception as e:
                logger.error(f"Rollback action failed: {e}")
                
        # Rollback at adapter level
        for name, adapter in self.adapters.items():
            if hasattr(adapter, 'rollback_transaction'):
                await adapter.rollback_transaction(self.transaction_id)
            elif hasattr(adapter, 'rollback'):
                await adapter.rollback()


# Convenience decorator for transactional methods
def transactional(func):
    """
    Decorator to wrap method in transaction.
    
    Usage:
        @transactional
        async def create_order(self, order_data):
            # All operations auto-wrapped in transaction
            pass
    """
    async def wrapper(*args, **kwargs):
        async with TransactionManager() as tm:
            # Inject transaction manager into kwargs
            kwargs['transaction_manager'] = tm
            return await func(*args, **kwargs)
    return wrapper