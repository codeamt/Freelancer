"""
Read Replica Router

Routes database operations between primary and read replicas.
"""

import random
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import asyncio

from core.db.adapters.postgres_adapter import PostgresAdapter
from core.db.config import DatabaseConfig
from core.utils.logger import get_logger

logger = get_logger(__name__)


class ReplicaType(Enum):
    """Replica types"""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"


@dataclass
class ReplicaInfo:
    """Replica information"""
    id: str
    host: str
    port: int
    database: str
    username: str
    password: str
    replica_type: ReplicaType
    weight: int = 1
    is_healthy: bool = True
    last_check: float = 0
    lag_seconds: float = 0
    connection_pool: Optional[PostgresAdapter] = None


class ReadReplicaRouter:
    """Routes queries to appropriate database replicas"""
    
    def __init__(self, primary_config: DatabaseConfig):
        self.primary_config = primary_config
        self.replicas: List[ReplicaInfo] = []
        self.primary_adapter: Optional[PostgresAdapter] = None
        self.health_check_interval = 30  # seconds
        self.health_check_task: Optional[asyncio.Task] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the router and connections"""
        if self._initialized:
            return
        
        # Initialize primary connection
        self.primary_adapter = PostgresAdapter(self.primary_config)
        
        # Initialize replica connections
        for replica in self.replicas:
            replica_config = DatabaseConfig(
                host=replica.host,
                port=replica.port,
                database=replica.database,
                username=replica.username,
                password=replica.password
            )
            replica.connection_pool = PostgresAdapter(replica_config)
        
        # Start health checks
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        self._initialized = True
        logger.info(f"Read replica router initialized with {len(self.replicas)} replicas")
    
    async def close(self):
        """Close all connections"""
        if self.primary_adapter:
            await self.primary_adapter.close()
        
        for replica in self.replicas:
            if replica.connection_pool:
                await replica.connection_pool.close()
        
        if self.health_check_task:
            self.health_check_task.cancel()
        
        self._initialized = False
    
    def add_replica(self, replica: ReplicaInfo):
        """
        Add a read replica
        
        Args:
            replica: Replica configuration
        """
        self.replicas.append(replica)
        logger.info(f"Added replica: {replica.id} ({replica.host}:{replica.port})")
    
    def remove_replica(self, replica_id: str):
        """
        Remove a read replica
        
        Args:
            replica_id: Replica ID to remove
        """
        self.replicas = [r for r in self.replicas if r.id != replica_id]
        logger.info(f"Removed replica: {replica_id}")
    
    def get_primary(self) -> PostgresAdapter:
        """Get primary database adapter"""
        if not self._initialized:
            raise RuntimeError("Router not initialized")
        
        if not self.primary_adapter:
            raise RuntimeError("Primary adapter not available")
        
        return self.primary_adapter
    
    def get_read_replica(self) -> Optional[PostgresAdapter]:
        """
        Get a healthy read replica using weighted round-robin
        
        Returns:
            Read replica adapter or None if none available
        """
        if not self._initialized:
            return None
        
        # Get healthy replicas
        healthy_replicas = [r for r in self.replicas 
                          if r.is_healthy and r.replica_type == ReplicaType.READ_ONLY]
        
        if not healthy_replicas:
            logger.warning("No healthy read replicas available")
            return None
        
        # Weighted selection
        total_weight = sum(r.weight for r in healthy_replicas)
        if total_weight == 0:
            return None
        
        rand = random.uniform(0, total_weight)
        current_weight = 0
        
        for replica in healthy_replicas:
            current_weight += replica.weight
            if rand <= current_weight:
                return replica.connection_pool
        
        # Fallback to first healthy replica
        return healthy_replicas[0].connection_pool
    
    def get_all_replicas(self) -> List[PostgresAdapter]:
        """Get all healthy replica adapters"""
        if not self._initialized:
            return []
        
        adapters = []
        for replica in self.replicas:
            if replica.is_healthy and replica.connection_pool:
                adapters.append(replica.connection_pool)
        
        return adapters
    
    async def execute_read(self, query: str, *args, **kwargs) -> Any:
        """
        Execute a read query on a replica
        
        Args:
            query: SQL query
            *args: Query parameters
            **kwargs: Additional options
            
        Returns:
            Query result
        """
        adapter = self.get_read_replica()
        if adapter:
            return await adapter.execute(query, *args, **kwargs)
        else:
            # Fallback to primary
            logger.warning("Falling back to primary for read query")
            return await self.primary_adapter.execute(query, *args, **kwargs)
    
    async def execute_write(self, query: str, *args, **kwargs) -> Any:
        """
        Execute a write query on primary
        
        Args:
            query: SQL query
            *args: Query parameters
            **kwargs: Additional options
            
        Returns:
            Query result
        """
        return await self.primary_adapter.execute(query, *args, **kwargs)
    
    async def fetch_one_read(self, query: str, *args, **kwargs) -> Optional[Dict]:
        """
        Fetch one row from replica
        
        Args:
            query: SQL query
            *args: Query parameters
            **kwargs: Additional options
            
        Returns:
            Row data or None
        """
        adapter = self.get_read_replica()
        if adapter:
            return await adapter.fetch_one(query, *args, **kwargs)
        else:
            # Fallback to primary
            logger.warning("Falling back to primary for read query")
            return await self.primary_adapter.fetch_one(query, *args, **kwargs)
    
    async def fetch_all_read(self, query: str, *args, **kwargs) -> List[Dict]:
        """
        Fetch all rows from replica
        
        Args:
            query: SQL query
            *args: Query parameters
            **kwargs: Additional options
            
        Returns:
            List of rows
        """
        adapter = self.get_read_replica()
        if adapter:
            return await adapter.fetch_all(query, *args, **kwargs)
        else:
            # Fallback to primary
            logger.warning("Falling back to primary for read query")
            return await self.primary_adapter.fetch_all(query, *args, **kwargs)
    
    async def _health_check_loop(self):
        """Run periodic health checks"""
        while self._initialized:
            try:
                await self._check_replica_health()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)
    
    async def _check_replica_health(self):
        """Check health of all replicas"""
        for replica in self.replicas:
            try:
                if not replica.connection_pool:
                    continue
                
                # Simple health check
                start_time = time.time()
                result = await replica.connection_pool.fetch_one("SELECT 1")
                response_time = time.time() - start_time
                
                # Check replication lag
                lag = await self._get_replication_lag(replica)
                
                # Update health status
                replica.is_healthy = (
                    result is not None and
                    response_time < 5.0 and  # 5 second threshold
                    lag < 60  # 60 second lag threshold
                )
                replica.last_check = time.time()
                replica.lag_seconds = lag
                
                if not replica.is_healthy:
                    logger.warning(f"Replica {replica.id} is unhealthy (lag: {lag}s, response: {response_time:.2f}s)")
                
            except Exception as e:
                replica.is_healthy = False
                logger.error(f"Health check failed for replica {replica.id}: {e}")
    
    async def _get_replication_lag(self, replica: ReplicaInfo) -> float:
        """Get replication lag in seconds"""
        try:
            # Query pg_last_xact_replay_timestamp
            result = await replica.connection_pool.fetch_one(
                "SELECT EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp())) as lag"
            )
            
            return result.get('lag', 0) if result else 0
            
        except Exception:
            # If query fails, assume high lag
            return 999999
    
    def get_replica_stats(self) -> Dict[str, Any]:
        """Get replica statistics"""
        stats = {
            'total_replicas': len(self.replicas),
            'healthy_replicas': len([r for r in self.replicas if r.is_healthy]),
            'unhealthy_replicas': len([r for r in self.replicas if not r.is_healthy]),
            'replicas': []
        }
        
        for replica in self.replicas:
            stats['replicas'].append({
                'id': replica.id,
                'host': replica.host,
                'port': replica.port,
                'type': replica.replica_type.value,
                'weight': replica.weight,
                'healthy': replica.is_healthy,
                'lag_seconds': replica.lag_seconds,
                'last_check': replica.last_check
            })
        
        return stats
    
    def set_replica_weight(self, replica_id: str, weight: int):
        """
        Set weight for a replica
        
        Args:
            replica_id: Replica ID
            weight: Weight (higher = more traffic)
        """
        for replica in self.replicas:
            if replica.id == replica_id:
                replica.weight = weight
                logger.info(f"Set weight for replica {replica_id}: {weight}")
                return
        
        logger.warning(f"Replica not found: {replica_id}")
    
    async def promote_replica(self, replica_id: str) -> bool:
        """
        Promote a replica to primary
        
        Args:
            replica_id: Replica to promote
            
        Returns:
            True if successful
        """
        replica = next((r for r in self.replicas if r.id == replica_id), None)
        
        if not replica:
            logger.error(f"Replica not found: {replica_id}")
            return False
        
        try:
            # Stop replication
            await replica.connection_pool.execute("SELECT pg_promote()")
            
            # Update configuration
            self.primary_config.host = replica.host
            self.primary_config.port = replica.port
            
            # Reinitialize
            await self.close()
            await self.initialize()
            
            logger.info(f"Promoted replica {replica_id} to primary")
            return True
            
        except Exception as e:
            logger.error(f"Failed to promote replica {replica_id}: {e}")
            return False
