"""DuckDB Adapter - Handles analytical queries and data warehousing"""
from typing import Any, Dict, List, Optional
import duckdb
from contextlib import asynccontextmanager
from core.utils.logger import get_logger

logger = get_logger(__name__)


class DuckDBAdapter:
    """
    DuckDB adapter for analytical queries and OLAP workloads.
    
    Use for: Analytics, data warehousing, aggregations, reporting, batch processing
    """
    
    def __init__(self, database_path: str = ":memory:", read_only: bool = False):
        self.database_path = database_path
        self.read_only = read_only
        self.connection: Optional[duckdb.DuckDBPyConnection] = None
        
    async def connect(self):
        """Connect to DuckDB"""
        if not self.connection:
            self.connection = duckdb.connect(
                database=self.database_path,
                read_only=self.read_only
            )
            logger.info(f"DuckDB connected: {self.database_path}")
            
    async def disconnect(self):
        """Close DuckDB connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            
    @asynccontextmanager
    async def cursor(self):
        """Get cursor for queries"""
        if not self.connection:
            await self.connect()
        cursor = self.connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
            
    async def execute(self, query: str, parameters: Optional[tuple] = None) -> Any:
        """Execute query"""
        async with self.cursor() as cursor:
            if parameters:
                return cursor.execute(query, parameters)
            return cursor.execute(query)
            
    async def fetch_one(self, query: str, parameters: Optional[tuple] = None) -> Optional[Dict]:
        """Fetch single row"""
        async with self.cursor() as cursor:
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
            
    async def fetch_many(
        self, 
        query: str, 
        parameters: Optional[tuple] = None,
        size: Optional[int] = None
    ) -> List[Dict]:
        """Fetch multiple rows"""
        async with self.cursor() as cursor:
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            
            if size:
                rows = cursor.fetchmany(size)
            else:
                rows = cursor.fetchall()
                
            if rows:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
            
    async def fetch_df(self, query: str, parameters: Optional[tuple] = None):
        """Fetch results as pandas DataFrame"""
        async with self.cursor() as cursor:
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            return cursor.df()
            
    async def insert_df(self, table: str, df, if_exists: str = "append"):
        """Insert pandas DataFrame into table"""
        if not self.connection:
            await self.connect()
        self.connection.register('temp_df', df)
        
        if if_exists == "replace":
            await self.execute(f"DROP TABLE IF EXISTS {table}")
            
        await self.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM temp_df")
        self.connection.unregister('temp_df')
        
    async def create_table(self, table: str, schema: str):
        """Create table with schema"""
        query = f"CREATE TABLE IF NOT EXISTS {table} ({schema})"
        await self.execute(query)
        
    async def drop_table(self, table: str):
        """Drop table"""
        await self.execute(f"DROP TABLE IF EXISTS {table}")
        
    async def table_exists(self, table: str) -> bool:
        """Check if table exists"""
        result = await self.fetch_one(
            "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_name = ?",
            (table,)
        )
        return result and result['count'] > 0
        
    async def load_csv(self, table: str, file_path: str, **kwargs):
        """Load CSV file into table"""
        options = ', '.join(f"{k}={v}" for k, v in kwargs.items())
        query = f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto('{file_path}'{', ' + options if options else ''})"
        await self.execute(query)
        
    async def load_parquet(self, table: str, file_path: str):
        """Load Parquet file into table"""
        query = f"CREATE TABLE {table} AS SELECT * FROM read_parquet('{file_path}')"
        await self.execute(query)
        
    async def export_csv(self, query: str, file_path: str):
        """Export query results to CSV"""
        export_query = f"COPY ({query}) TO '{file_path}' (HEADER, DELIMITER ',')"
        await self.execute(export_query)
        
    async def export_parquet(self, query: str, file_path: str):
        """Export query results to Parquet"""
        export_query = f"COPY ({query}) TO '{file_path}' (FORMAT PARQUET)"
        await self.execute(export_query)
        
    async def vacuum(self):
        """Optimize database"""
        await self.execute("VACUUM")
        
    async def analyze(self, table: Optional[str] = None):
        """Update statistics"""
        if table:
            await self.execute(f"ANALYZE {table}")
        else:
            await self.execute("ANALYZE")
            
    # Transaction support
    async def prepare_transaction(self, transaction_id: str):
        """Begin transaction"""
        await self.execute("BEGIN TRANSACTION")
        
    async def commit_transaction(self, transaction_id: str):
        """Commit transaction"""
        await self.execute("COMMIT")
        
    async def rollback_transaction(self, transaction_id: str):
        """Rollback transaction"""
        await self.execute("ROLLBACK")