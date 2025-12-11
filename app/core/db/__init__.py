"""
Core Database Module

Provides database adapters, repositories, and transaction management.
"""
from core.db.transaction_manager import (
    TransactionManager,
    transactional,
    transaction
)
from core.db.session import (
    SessionManager,
    initialize_session_manager,
    get_session_manager
)
from core.db.connection_pool import (
    ConnectionPoolManager,
    PoolConfig,
    get_pool_manager
)

# Adapters
from core.db.adapters import (
    PostgresAdapter,
    MongoDBAdapter,
    RedisAdapter,
    DuckDBAdapter,
    MinioAdapter
)

# Repositories
from core.db.repositories import (
    BaseRepository,
    PostgresRepository,
    MongoRepository,
    UnitOfWork,
    UserRepository
)

__all__ = [
    # Transaction Management
    'TransactionManager',
    'transactional',
    'transaction',
    
    # Session Management
    'SessionManager',
    'initialize_session_manager',
    'get_session_manager',
    
    # Connection Pooling
    'ConnectionPoolManager',
    'PoolConfig',
    'get_pool_manager',
    
    # Adapters
    'PostgresAdapter',
    'MongoDBAdapter',
    'RedisAdapter',
    'DuckDBAdapter',
    'MinioAdapter',
    
    # Repositories
    'BaseRepository',
    'PostgresRepository',
    'MongoRepository',
    'UnitOfWork',
    'UserRepository',
]