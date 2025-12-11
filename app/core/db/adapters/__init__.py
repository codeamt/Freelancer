"""
Database Adapters Module

Provides adapters for different database systems.
"""
from core.db.adapters.postgres_adapter import PostgresAdapter
from core.db.adapters.mongodb_adapter import MongoDBAdapter
from core.db.adapters.redis_adapter import RedisAdapter
from core.db.adapters.duckdb_adapter import DuckDBAdapter
from core.db.adapters.minio_adapter import MinioAdapter

__all__ = [
    'PostgresAdapter',
    'MongoDBAdapter',
    'RedisAdapter',
    'DuckDBAdapter',
    'MinioAdapter',
]