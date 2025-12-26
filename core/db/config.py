"""
Database Configuration Module

Handles database connection pooling, configuration, and optimization settings.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    
    # Connection settings - no defaults for sensitive data
    host: str = None
    port: int = 5432
    database: str = None
    username: str = None
    password: str = None
    
    # Pool settings
    min_size: int = 10
    max_size: int = 20
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0  # 5 minutes
    
    # Connection settings
    command_timeout: int = 60
    statement_timeout: int = 30000  # 30 seconds
    idle_timeout: float = 300.0  # 5 minutes
    
    # SSL settings
    ssl_mode: str = "prefer"
    ssl_cert_file: Optional[str] = None
    ssl_key_file: Optional[str] = None
    ssl_ca_file: Optional[str] = None
    
    # Performance settings
    server_settings: Dict[str, Any] = None
    
    # Read replica settings
    read_replica_host: Optional[str] = None
    read_replica_port: int = 5432
    read_replica_database: Optional[str] = None
    
    # Connection string
    connection_string: Optional[str] = None
    
    def __post_init__(self):
        """Initialize defaults and validate configuration"""
        if self.server_settings is None:
            self.server_settings = {
                "application_name": "fastapp",
                "jit": "off",  # Disable JIT for smaller queries
                "max_parallel_workers_per_gather": "2",
                "timezone": "UTC"
            }
        
        # Override with environment variables
        self._load_from_env()
        
        # Build connection string if not provided
        if not self.connection_string:
            self.connection_string = self._build_connection_string()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Connection settings - required fields
        self.host = os.getenv("DB_HOST", self.host)
        self.port = int(os.getenv("DB_PORT", str(self.port)))
        self.database = os.getenv("DB_NAME", self.database)
        self.username = os.getenv("DB_USER", self.username)
        self.password = os.getenv("DB_PASSWORD", self.password)
        
        # Also check for legacy POSTGRES_URL
        if not self.host and not self.connection_string:
            postgres_url = os.getenv("POSTGRES_URL")
            if postgres_url:
                self.connection_string = postgres_url
                return  # Skip other config if URL is provided
        
        # Pool settings
        self.min_size = int(os.getenv("DB_POOL_MIN", self.min_size))
        self.max_size = int(os.getenv("DB_POOL_MAX", self.max_size))
        self.max_queries = int(os.getenv("DB_MAX_QUERIES", self.max_queries))
        self.max_inactive_connection_lifetime = float(
            os.getenv("DB_MAX_INACTIVE_LIFETIME", self.max_inactive_connection_lifetime)
        )
        
        # Timeouts
        self.command_timeout = int(os.getenv("DB_COMMAND_TIMEOUT", self.command_timeout))
        self.statement_timeout = int(os.getenv("DB_STATEMENT_TIMEOUT", self.statement_timeout))
        self.idle_timeout = float(os.getenv("DB_IDLE_TIMEOUT", self.idle_timeout))
        
        # SSL settings
        self.ssl_mode = os.getenv("DB_SSL_MODE", self.ssl_mode)
        self.ssl_cert_file = os.getenv("DB_SSL_CERT", self.ssl_cert_file)
        self.ssl_key_file = os.getenv("DB_SSL_KEY", self.ssl_key_file)
        self.ssl_ca_file = os.getenv("DB_SSL_CA", self.ssl_ca_file)
        
        # Read replica
        self.read_replica_host = os.getenv("DB_READ_REPLICA_HOST", self.read_replica_host)
        self.read_replica_port = int(os.getenv("DB_READ_REPLICA_PORT", self.read_replica_port))
        self.read_replica_database = os.getenv("DB_READ_REPLICA_DB", self.read_replica_database or self.database)
        
        # Override connection string if provided
        self.connection_string = os.getenv("POSTGRES_URL", self.connection_string)
    
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string"""
        base = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        
        # Add SSL parameters
        params = []
        if self.ssl_mode:
            params.append(f"sslmode={self.ssl_mode}")
        if self.ssl_cert_file:
            params.append(f"sslcert={self.ssl_cert_file}")
        if self.ssl_key_file:
            params.append(f"sslkey={self.ssl_key_file}")
        if self.ssl_ca_file:
            params.append(f"sslrootcert={self.ssl_ca_file}")
        
        if params:
            base += "?" + "&".join(params)
        
        return base
    
    def get_read_replica_string(self) -> Optional[str]:
        """Get read replica connection string"""
        if not self.read_replica_host:
            return None
        
        replica = f"postgresql://{self.username}:{self.password}@{self.read_replica_host}:{self.read_replica_port}/{self.read_replica_database}"
        
        # Add SSL parameters
        params = []
        if self.ssl_mode:
            params.append(f"sslmode={self.ssl_mode}")
        
        if params:
            replica += "?" + "&".join(params)
        
        return replica
    
    def get_pool_config(self) -> Dict[str, Any]:
        """Get connection pool configuration"""
        return {
            "min_size": self.min_size,
            "max_size": self.max_size,
            "max_queries": self.max_queries,
            "max_inactive_connection_lifetime": self.max_inactive_connection_lifetime,
            "command_timeout": self.command_timeout,
            "server_settings": self.server_settings
        }
    
    def validate(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check if connection string is provided
        if not self.connection_string:
            # If no connection string, require individual components
            if not self.host:
                errors.append("Database host is required (DB_HOST)")
            if not self.database:
                errors.append("Database name is required (DB_NAME)")
            if not self.username:
                errors.append("Database username is required (DB_USER)")
            if not self.password:
                errors.append("Database password is required (DB_PASSWORD)")
        
        if self.min_size < 1:
            errors.append("Pool min_size must be at least 1")
        if self.max_size < self.min_size:
            errors.append("Pool max_size must be >= min_size")
        if self.command_timeout < 1:
            errors.append("Command timeout must be positive")
        
        if errors:
            for error in errors:
                logger.error(f"Database config error: {error}")
            return False
        
        return True
    
    def log_config(self):
        """Log configuration (without sensitive data)"""
        logger.info("Database Configuration:")
        if self.connection_string:
            # Log only the host and database from connection string
            try:
                import re
                match = re.match(r'postgresql://[^@]+@([^:]+):\d+/([^?]+)', self.connection_string)
                if match:
                    logger.info(f"  Host: {match.group(1)}")
                    logger.info(f"  Database: {match.group(2)}")
                else:
                    logger.info("  Connection: [CONFIGURED]")
            except:
                logger.info("  Connection: [CONFIGURED]")
        else:
            logger.info(f"  Host: {self.host}:{self.port}")
            logger.info(f"  Database: {self.database}")
            logger.info(f"  User: {self.username}")
        logger.info(f"  Pool Size: {self.min_size}-{self.max_size}")
        logger.info(f"  Command Timeout: {self.command_timeout}s")
        logger.info(f"  SSL Mode: {self.ssl_mode}")
        if self.read_replica_host:
            logger.info(f"  Read Replica: {self.read_replica_host}:{self.read_replica_port}")


# Global configuration instance
db_config = DatabaseConfig()


def get_database_config() -> DatabaseConfig:
    """Get the global database configuration"""
    return db_config


def configure_database(config: Optional[DatabaseConfig] = None) -> DatabaseConfig:
    """Configure database settings"""
    global db_config
    
    if config:
        db_config = config
    else:
        db_config = DatabaseConfig()
    
    # Validate configuration
    if not db_config.validate():
        raise ValueError("Invalid database configuration")
    
    # Log configuration
    db_config.log_config()
    
    return db_config
