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
import asyncio
from core.utils.logger import get_logger

logger = get_logger(__name__)


class TransactionState(Enum):
    """Transaction states in 2PC protocol."""
    PENDING = "pending"
    PREPARED = "prepared"
    COMMITTED = "committed"
    ABORTED = "aborted"


@dataclass
class TransactionLog:
    """
    Transaction log entry for audit and recovery.
    
    Tracks all operations in a transaction for rollback capability.
    """
    transaction_id: str
    state: TransactionState
    participants: List[str] = field(default_factory=list)
    rollback_actions: List[Callable] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())


class TransactionManager:
    """
    Coordinates transactions across multiple databases.
    
    Implements Two-Phase Commit (2PC) protocol:
    1. Prepare phase: All participants prepare to commit
    2. Commit phase: All participants commit if prepare succeeded
    
    Usage:
        async with TransactionManager() as tm:
            # Postgres operations
            await tm.execute(postgres_adapter, "insert", "users", {...})
            
            # MongoDB operations
            await tm.execute(mongo_adapter, "insert_one", "profiles", {...})
            
            # Redis cache invalidation
            await tm.execute(redis_adapter, "delete", "cache_key")
            
            # Auto-commits on success, auto-rollback on error
    """
    
    def __init__(self, timeout_seconds: int = 30):
        """
        Initialize transaction manager.
        
        Args:
            timeout_seconds: Transaction timeout (default 30s)
        """
        self.transaction_id = str(uuid.uuid4())
        self.timeout = timeout_seconds
        self.log = TransactionLog(
            transaction_id=self.transaction_id,
            state=TransactionState.PENDING
        )
        self.adapters: Dict[str, Any] = {}
        self.operations: List[Dict] = []
        self._committed = False
        self._aborted = False
        
    async def __aenter__(self):
        """Start transaction."""
        logger.info(f"Transaction {self.transaction_id} started")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction."""
        if exc_type is not None:
            # Exception occurred, rollback
            await self.rollback()
            logger.error(
                f"Transaction {self.transaction_id} rolled back due to error: {exc_val}"
            )
            return False  # Re-raise exception
        
        # No exception, try to commit
        try:
            await self.commit()
            logger.info(f"Transaction {self.transaction_id} committed successfully")
        except Exception as e:
            # Commit failed, rollback
            await self.rollback()
            logger.error(f"Transaction {self.transaction_id} commit failed: {e}")
            raise
            
    async def execute(
        self,
        adapter,
        operation: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute operation and register for rollback if needed.
        
        Args:
            adapter: Database adapter instance
            operation: Operation name (e.g., "insert", "update", "delete")
            *args: Operation positional arguments
            **kwargs: Operation keyword arguments
            
        Returns:
            Operation result
            
        Raises:
            RuntimeError: If transaction already committed/aborted
        """
        if self._committed:
            raise RuntimeError("Cannot execute on committed transaction")
        if self._aborted:
            raise RuntimeError("Cannot execute on aborted transaction")
        
        adapter_name = adapter.__class__.__name__
        
        # Register adapter if new
        if adapter_name not in self.adapters:
            self.adapters[adapter_name] = adapter
            self.log.participants.append(adapter_name)
            logger.debug(f"Registered participant: {adapter_name}")
            
        # Execute operation
        try:
            result = await getattr(adapter, operation)(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Operation failed in transaction {self.transaction_id}: "
                f"{adapter_name}.{operation} - {e}"
            )
            raise
        
        # Register operation for logging
        self.operations.append({
            "adapter": adapter_name,
            "operation": operation,
            "args": args,
            "kwargs": kwargs,
            "result": result
        })
        
        # Register rollback action if adapter supports it
        rollback_method = f"rollback_{operation}"
        if hasattr(adapter, rollback_method):
            rollback_fn = getattr(adapter, rollback_method)
            self.log.rollback_actions.append(
                lambda r=result, a=args, k=kwargs: rollback_fn(r, *a, **k)
            )
            
        return result
        
    async def prepare(self):
        """
        Phase 1: Prepare all participants.
        
        Each participant must vote "yes" or "no" to commit.
        """
        self.log.state = TransactionState.PREPARED
        
        prepare_tasks = []
        for name, adapter in self.adapters.items():
            if hasattr(adapter, 'prepare_transaction'):
                task = adapter.prepare_transaction(self.transaction_id)
                prepare_tasks.append(task)
                logger.debug(f"Preparing {name} for transaction {self.transaction_id}")
        
        if prepare_tasks:
            try:
                # Wait for all participants to prepare
                await asyncio.wait_for(
                    asyncio.gather(*prepare_tasks),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                raise RuntimeError(
                    f"Transaction {self.transaction_id} prepare phase timed out"
                )
        
        logger.debug(f"All participants prepared for transaction {self.transaction_id}")
        
    async def commit(self):
        """
        Phase 2: Commit all participants.
        
        Only called if prepare phase succeeded for all participants.
        """
        if self._committed:
            logger.warning(f"Transaction {self.transaction_id} already committed")
            return
        
        if self._aborted:
            raise RuntimeError("Cannot commit aborted transaction")
        
        # Prepare phase
        await self.prepare()
        
        # Commit phase
        commit_tasks = []
        for name, adapter in self.adapters.items():
            if hasattr(adapter, 'commit_transaction'):
                task = adapter.commit_transaction(self.transaction_id)
                commit_tasks.append(task)
                logger.debug(f"Committing {name} for transaction {self.transaction_id}")
            elif hasattr(adapter, 'commit'):
                task = adapter.commit()
                commit_tasks.append(task)
        
        if commit_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*commit_tasks),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                raise RuntimeError(
                    f"Transaction {self.transaction_id} commit phase timed out"
                )
        
        self.log.state = TransactionState.COMMITTED
        self._committed = True
        
    async def rollback(self):
        """
        Rollback all operations.
        
        Executes rollback actions in reverse order (LIFO).
        """
        if self._aborted:
            logger.warning(f"Transaction {self.transaction_id} already aborted")
            return
        
        self.log.state = TransactionState.ABORTED
        self._aborted = True
        
        # Execute rollback actions in reverse order
        logger.info(
            f"Rolling back transaction {self.transaction_id} "
            f"({len(self.log.rollback_actions)} actions)"
        )
        
        for i, rollback_fn in enumerate(reversed(self.log.rollback_actions)):
            try:
                await rollback_fn()
            except Exception as e:
                logger.error(
                    f"Rollback action {i} failed for transaction "
                    f"{self.transaction_id}: {e}"
                )
                # Continue with other rollback actions
                
        # Rollback at adapter level
        rollback_tasks = []
        for name, adapter in self.adapters.items():
            if hasattr(adapter, 'rollback_transaction'):
                task = adapter.rollback_transaction(self.transaction_id)
                rollback_tasks.append(task)
            elif hasattr(adapter, 'rollback'):
                task = adapter.rollback()
                rollback_tasks.append(task)
        
        if rollback_tasks:
            try:
                await asyncio.gather(*rollback_tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Adapter rollback failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get transaction status.
        
        Returns:
            Dict with transaction metadata
        """
        return {
            "transaction_id": self.transaction_id,
            "state": self.log.state.value,
            "participants": self.log.participants,
            "operations_count": len(self.operations),
            "committed": self._committed,
            "aborted": self._aborted
        }


# ============================================================================
# Convenience Decorator
# ============================================================================

def transactional(func):
    """
    Decorator to wrap method in transaction.
    
    Automatically injects TransactionManager into kwargs.
    
    Usage:
        @transactional
        async def create_order(self, order_data, transaction_manager=None):
            # transaction_manager is auto-injected
            await transaction_manager.execute(...)
    """
    async def wrapper(*args, **kwargs):
        # Check if transaction_manager already provided
        if 'transaction_manager' in kwargs and kwargs['transaction_manager'] is not None:
            # Already in a transaction, use existing
            return await func(*args, **kwargs)
        
        # Create new transaction
        async with TransactionManager() as tm:
            kwargs['transaction_manager'] = tm
            return await func(*args, **kwargs)
    
    return wrapper


# ============================================================================
# Context Manager for Nested Transactions
# ============================================================================

@asynccontextmanager
async def transaction(timeout_seconds: int = 30):
    """
    Context manager for creating transactions.
    
    Usage:
        async with transaction() as tm:
            await tm.execute(adapter, "insert", ...)
    """
    tm = TransactionManager(timeout_seconds=timeout_seconds)
    async with tm:
        yield tm