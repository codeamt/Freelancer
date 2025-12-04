# app/add_ons/services/duckdb/repository.py
from core.db.interfaces.base_repository import BaseRepository
import duckdb
from typing import Dict, List, Any, Optional, AsyncIterator
from pathlib import Path

class DuckDBRepository(BaseRepository):
    """DuckDB implementation for analytical queries"""
    def __init__(self, db_path: str = "/var/lib/duckdb/main.db"):
        self.conn = duckdb.connect(db_path)
        self.conn.execute("INSTALL 'httpfs'; LOAD 'httpfs';")
        
    async def get(self, id: str) -> Optional[Dict]:
        return self.conn.execute(
            f"SELECT * FROM entities WHERE id = '{id}'"
        ).fetchone()

    async def query(self, sql: str, params: Dict = None) -> List[Dict]:
        """Execute raw analytical queries"""
        if params:
            return self.conn.execute(sql, params).fetchdf().to_dict('records')
        return self.conn.execute(sql).fetchdf().to_dict('records')

    async def load_csv(self, path: str, table_name: str):
        """Load CSV data into DuckDB"""
        self.conn.execute(
            f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv('{path}')"
        )

    async def stream_all(self, table: str = "entities", batch_size: int = 1000) -> AsyncIterator[Dict]:
        """Stream table contents efficiently with configurable batch size
        
        Args:
            table: Name of table to stream (must be alphanumeric)
            batch_size: Number of rows per batch (default: 1000)
            
        Yields:
            Dict: Row data as dictionaries
        """
        # Validate table name to prevent SQL injection
        if not table.isidentifier():
            raise ValueError(f"Invalid table name: {table}")
            
        query = f"SELECT * FROM {table}"
        result = self.conn.cursor().execute(query)
        columns = [desc[0] for desc in result.description]
        
        while True:
            batch = result.fetchmany(batch_size)
            if not batch:
                break
                
            # Convert to dict with column names and yield each row
            for row in batch:
                yield dict(zip(columns, row))