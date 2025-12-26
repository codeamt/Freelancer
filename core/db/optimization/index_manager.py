"""
Index Manager

Manages database indexes for optimal query performance.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

from core.utils.logger import get_logger

logger = get_logger(__name__)


class IndexType(Enum):
    """Supported index types"""
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    BRIN = "brin"
    PARTIAL = "partial"


@dataclass
class IndexDefinition:
    """Index definition"""
    name: str
    table: str
    columns: List[str]
    index_type: IndexType
    unique: bool = False
    partial_condition: Optional[str] = None
    include_columns: Optional[List[str]] = None
    
    def get_create_sql(self) -> str:
        """Generate CREATE INDEX SQL"""
        cols = ", ".join(self.columns)
        
        sql = f"CREATE "
        
        if self.unique:
            sql += "UNIQUE "
        
        sql += f"INDEX {self.name} ON {self.table} USING {self.index_type.value} ({cols}"
        
        if self.include_columns:
            sql += f") INCLUDE ({', '.join(self.include_columns)})"
        else:
            sql += ")"
        
        if self.partial_condition:
            sql += f" WHERE {self.partial_condition}"
        
        return sql


class IndexManager:
    """Manages database indexes"""
    
    def __init__(self, postgres_adapter):
        self.postgres = postgres_adapter
        self._index_cache: Dict[str, IndexDefinition] = {}
    
    async def create_index(self, index_def: IndexDefinition, concurrent: bool = True) -> bool:
        """
        Create a new index
        
        Args:
            index_def: Index definition
            concurrent: Create index concurrently (no locking)
            
        Returns:
            True if successful
        """
        try:
            sql = index_def.get_create_sql()
            
            if concurrent:
                sql = sql.replace("CREATE INDEX", "CREATE INDEX CONCURRENTLY")
            
            logger.info(f"Creating index: {index_def.name}")
            await self.postgres.execute(sql)
            
            # Cache the index definition
            self._index_cache[index_def.name] = index_def
            
            logger.info(f"✓ Index {index_def.name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index {index_def.name}: {e}")
            return False
    
    async def drop_index(self, index_name: str, concurrent: bool = True) -> bool:
        """
        Drop an index
        
        Args:
            index_name: Name of index to drop
            concurrent: Drop index concurrently
            
        Returns:
            True if successful
        """
        try:
            sql = f"DROP INDEX "
            if concurrent:
                sql += "CONCURRENTLY "
            sql += f"{index_name}"
            
            logger.info(f"Dropping index: {index_name}")
            await self.postgres.execute(sql)
            
            # Remove from cache
            if index_name in self._index_cache:
                del self._index_cache[index_name]
            
            logger.info(f"✓ Index {index_name} dropped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop index {index_name}: {e}")
            return False
    
    async def get_table_indexes(self, table: str) -> List[Dict[str, Any]]:
        """
        Get all indexes for a table
        
        Args:
            table: Table name
            
        Returns:
            List of index information
        """
        query = """
            SELECT 
                indexname as name,
                indexdef as definition
            FROM pg_indexes 
            WHERE tablename = $1 AND schemaname = 'public'
            ORDER BY indexname
        """
        
        results = await self.postgres.fetch_all(query, table)
        
        indexes = []
        for row in results:
            indexes.append({
                'name': row['name'],
                'definition': row['definition']
            })
        
        return indexes
    
    async def get_index_usage(self) -> List[Dict[str, Any]]:
        """
        Get index usage statistics
        
        Returns:
            List of index usage information
        """
        query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan as scan_count,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched,
                pg_size_pretty(pg_relation_size(indexrelid)) as size
            FROM pg_stat_user_indexes 
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC
        """
        
        results = await self.postgres.fetch_all(query)
        
        usage = []
        for row in results:
            usage.append({
                'schema': row['schemaname'],
                'table': row['tablename'],
                'index': row['indexname'],
                'scan_count': row['scan_count'],
                'tuples_read': row['tuples_read'],
                'tuples_fetched': row['tuples_fetched'],
                'size': row['size']
            })
        
        return usage
    
    async def rebuild_index(self, index_name: str) -> bool:
        """
        Rebuild an index (useful for fragmented indexes)
        
        Args:
            index_name: Name of index to rebuild
            
        Returns:
            True if successful
        """
        try:
            # Get index definition
            query = """
                SELECT indexdef 
                FROM pg_indexes 
                WHERE indexname = $1 AND schemaname = 'public'
            """
            
            result = await self.postgres.fetch_one(query, index_name)
            
            if not result:
                logger.error(f"Index {index_name} not found")
                return False
            
            # Drop and recreate
            await self.drop_index(index_name, concurrent=False)
            await self.postgres.execute(result['indexdef'])
            
            logger.info(f"✓ Index {index_name} rebuilt successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rebuild index {index_name}: {e}")
            return False
    
    async def analyze_index(self, index_name: str) -> Dict[str, Any]:
        """
        Analyze an index for optimization opportunities
        
        Args:
            index_name: Name of index
            
        Returns:
            Index analysis
        """
        # Get index statistics
        query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexrelid)) as size_bytes
            FROM pg_stat_user_indexes 
            WHERE indexname = $1 AND schemaname = 'public'
        """
        
        result = await self.postgres.fetch_one(query, index_name)
        
        if not result:
            return {'error': 'Index not found'}
        
        # Calculate efficiency
        efficiency = 0
        if result['idx_tup_read'] > 0:
            efficiency = result['idx_tup_fetch'] / result['idx_tup_read']
        
        analysis = {
            'index_name': index_name,
            'table': result['tablename'],
            'scan_count': result['idx_scan'],
            'tuples_read': result['idx_tup_read'],
            'tuples_fetched': result['idx_tup_fetch'],
            'efficiency': efficiency,
            'size': result['size_bytes'],
            'recommendations': []
        }
        
        # Generate recommendations
        if result['idx_scan'] == 0:
            analysis['recommendations'].append(
                "Index is never used - consider dropping it"
            )
        elif result['idx_scan'] < 10:
            analysis['recommendations'].append(
                "Index is rarely used - verify if still needed"
            )
        
        if efficiency < 0.5:
            analysis['recommendations'].append(
                "Low efficiency - consider reviewing index columns"
            )
        
        return analysis
    
    async def create_optimal_indexes(self) -> List[str]:
        """
        Create recommended indexes for optimal performance
        
        Returns:
            List of created index names
        """
        created = []
        
        # Define optimal indexes
        optimal_indexes = [
            # Users table
            IndexDefinition(
                name="idx_users_email_active",
                table="users",
                columns=["email", "is_active"],
                index_type=IndexType.BTREE
            ),
            IndexDefinition(
                name="idx_users_role_created",
                table="users",
                columns=["role", "created_at"],
                index_type=IndexType.BTREE
            ),
            IndexDefinition(
                name="idx_users_verified",
                table="users",
                columns=["is_verified", "created_at"],
                index_type=IndexType.BTREE,
                partial_condition="is_verified = true"
            ),
            
            # Devices table
            IndexDefinition(
                name="idx_devices_user_last_seen",
                table="devices",
                columns=["user_id", "last_seen_at DESC"],
                index_type=IndexType.BTREE
            ),
            IndexDefinition(
                name="idx_devices_active_trusted",
                table="devices",
                columns=["is_active", "is_trusted"],
                index_type=IndexType.BTREE
            ),
            
            # Refresh tokens table
            IndexDefinition(
                name="idx_refresh_tokens_user_expires",
                table="refresh_tokens",
                columns=["user_id", "expires_at"],
                index_type=IndexType.BTREE
            ),
            IndexDefinition(
                name="idx_refresh_tokens_expired_cleanup",
                table="refresh_tokens",
                columns=["expires_at", "is_active"],
                index_type=IndexType.BTREE,
                partial_condition="expires_at < NOW() OR is_active = false"
            ),
            
            # User sessions table
            IndexDefinition(
                name="idx_sessions_user_expires",
                table="user_sessions",
                columns=["user_id", "expires_at"],
                index_type=IndexType.BTREE
            ),
            IndexDefinition(
                name="idx_sessions_expired",
                table="user_sessions",
                columns=["expires_at"],
                index_type=IndexType.BTREE,
                partial_condition="expires_at < NOW()"
            ),
            
            # Sites table
            IndexDefinition(
                name="idx_sites_owner_created",
                table="sites",
                columns=["owner_id", "created_at DESC"],
                index_type=IndexType.BTREE
            ),
            IndexDefinition(
                name="idx_sites_settings_gin",
                table="sites",
                columns=["settings"],
                index_type=IndexType.GIN
            )
        ]
        
        # Create indexes
        for index_def in optimal_indexes:
            # Check if index exists
            existing = await self.get_table_indexes(index_def.table)
            exists = any(idx['name'] == index_def.name for idx in existing)
            
            if not exists:
                if await self.create_index(index_def):
                    created.append(index_def.name)
                    # Small delay between concurrent index creations
                    await asyncio.sleep(0.1)
        
        return created
    
    async def get_index_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get index recommendations based on query patterns
        
        Returns:
            List of index recommendations
        """
        recommendations = []
        
        # Analyze missing indexes
        query = """
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats 
            WHERE schemaname = 'public'
            AND tablename IN ('users', 'devices', 'refresh_tokens', 'sites')
            ORDER BY tablename, n_distinct DESC
        """
        
        results = await self.postgres.fetch_all(query)
        
        # Group by table
        table_stats = {}
        for row in results:
            table = row['tablename']
            if table not in table_stats:
                table_stats[table] = []
            table_stats[table].append({
                'column': row['attname'],
                'distinct': row['n_distinct'],
                'correlation': row['correlation']
            })
        
        # Generate recommendations
        for table, stats in table_stats.items():
            if table == 'users':
                if any(s['column'] == 'first_name' for s in stats):
                    recommendations.append({
                        'table': 'users',
                        'columns': ['first_name', 'last_name'],
                        'reason': 'Name search queries',
                        'impact': 'Medium',
                        'estimated_queries': 50
                    })
            
            elif table == 'devices':
                if any(s['column'] == 'ip_address' for s in stats):
                    recommendations.append({
                        'table': 'devices',
                        'columns': ['ip_address', 'user_id'],
                        'reason': 'Security audit queries',
                        'impact': 'High',
                        'estimated_queries': 100
                    })
        
        return recommendations
