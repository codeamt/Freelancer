"""PostgreSQL Adapter - Handles structured relational data"""
from typing import Any, Dict, List, Optional
import asyncpg
from contextlib import asynccontextmanager
from core.utils.logger import get_logger

logger = get_logger(__name__)


class PostgresAdapter:
    """
    PostgreSQL adapter with connection pooling and transaction support.
    
    Use for: Structured data, ACID transactions, complex queries, referential integrity
    """
    
    def __init__(self, connection_string: str, min_size: int = 10, max_size: int = 20):
        self.connection_string = connection_string
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None
        self._transaction_sessions: Dict[str, asyncpg.Connection] = {}
        
    async def connect(self):
        """Initialize connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=60
            )
            logger.info(f"PostgreSQL pool created (size: {self.min_size}-{self.max_size})")
            
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool"""
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            yield conn
            
    # Transaction support
    async def prepare_transaction(self, transaction_id: str):
        """Phase 1: Prepare transaction (2PC)"""
        async with self.acquire() as conn:
            self._transaction_sessions[transaction_id] = conn
            await conn.execute(f"PREPARE TRANSACTION '{transaction_id}'")
            
    async def commit_transaction(self, transaction_id: str):
        """Phase 2: Commit prepared transaction"""
        conn = self._transaction_sessions.get(transaction_id)
        if conn:
            await conn.execute(f"COMMIT PREPARED '{transaction_id}'")
            del self._transaction_sessions[transaction_id]
            
    async def rollback_transaction(self, transaction_id: str):
        """Rollback prepared transaction"""
        conn = self._transaction_sessions.get(transaction_id)
        if conn:
            await conn.execute(f"ROLLBACK PREPARED '{transaction_id}'")
            del self._transaction_sessions[transaction_id]
            
    # CRUD operations
    async def execute(self, query: str, *args, transaction_id: Optional[str] = None):
        """Execute query"""
        if transaction_id and transaction_id in self._transaction_sessions:
            conn = self._transaction_sessions[transaction_id]
            return await conn.execute(query, *args)
        else:
            async with self.acquire() as conn:
                return await conn.execute(query, *args)
                
    async def fetch_one(self, query: str, *args) -> Optional[Dict]:
        """Fetch single row"""
        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
            
    async def fetch_many(self, query: str, *args) -> List[Dict]:
        """Fetch multiple rows"""
        async with self.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
            
    async def insert(self, table: str, data: Dict[str, Any], returning: str = "id") -> Any:
        """Insert row and return specified column"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(f'${i+1}' for i in range(len(data)))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING {returning}"
        
        async with self.acquire() as conn:
            result = await conn.fetchval(query, *data.values())
            return result
            
    async def update(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> int:
        """Update rows"""
        set_clause = ', '.join(f"{k} = ${i+1}" for i, k in enumerate(data.keys()))
        where_clause = ' AND '.join(
            f"{k} = ${i+len(data)+1}" for i, k in enumerate(where.keys())
        )
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        async with self.acquire() as conn:
            result = await conn.execute(query, *data.values(), *where.values())
            # Parse affected rows from result string like "UPDATE 5"
            return int(result.split()[-1]) if result else 0
            
    async def delete(self, table: str, where: Dict[str, Any]) -> int:
        """Delete rows"""
        where_clause = ' AND '.join(f"{k} = ${i+1}" for i, k in enumerate(where.keys()))
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        async with self.acquire() as conn:
            result = await conn.execute(query, *where.values())
            return int(result.split()[-1]) if result else 0