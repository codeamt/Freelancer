"""
Tests for database configuration
"""

import pytest
import os
from unittest.mock import patch
from core.db.config import DatabaseConfig, configure_database


class TestDatabaseConfig:
    """Test database configuration"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = DatabaseConfig()
        
        assert config.port == 5432
        assert config.min_size == 10
        assert config.max_size == 20
        assert config.max_queries == 50000
        assert config.command_timeout == 60
        assert config.statement_timeout == 30000
        assert config.ssl_mode == "prefer"
    
    def test_environment_override(self):
        """Test environment variable overrides"""
        with patch.dict(os.environ, {
            'DB_HOST': 'test-host',
            'DB_PORT': '5433',
            'DB_NAME': 'test_db',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_password',
            'DB_POOL_MIN': '5',
            'DB_POOL_MAX': '15',
            'DB_COMMAND_TIMEOUT': '120'
        }):
            config = DatabaseConfig()
            
            assert config.host == 'test-host'
            assert config.port == 5433
            assert config.database == 'test_db'
            assert config.username == 'test_user'
            assert config.password == 'test_password'
            assert config.min_size == 5
            assert config.max_size == 15
            assert config.command_timeout == 120
    
    def test_postgres_url_override(self):
        """Test POSTGRES_URL takes precedence"""
        with patch.dict(os.environ, {
            'POSTGRES_URL': 'postgresql://user:pass@host:port/dbname',
            'DB_HOST': 'should-not-use'
        }):
            config = DatabaseConfig()
            
            assert config.connection_string == 'postgresql://user:pass@host:port/dbname'
    
    def test_build_connection_string(self):
        """Test connection string building"""
        # Create config with direct values
        config = DatabaseConfig()
        config.host = 'localhost'
        config.port = 5432
        config.database = 'test_db'
        config.username = 'user'
        config.password = 'pass'
        
        # Build connection string manually
        connection_string = config._build_connection_string()
        
        expected = 'postgresql://user:pass@localhost:5432/test_db?sslmode=prefer'
        assert connection_string == expected
    
    def test_build_connection_string_with_ssl(self):
        """Test connection string with SSL parameters"""
        config = DatabaseConfig()
        config.host = 'localhost'
        config.port = 5432
        config.database = 'test_db'
        config.username = 'user'
        config.password = 'pass'
        config.ssl_mode = 'require'
        
        # Build connection string manually
        connection_string = config._build_connection_string()
        
        expected = 'postgresql://user:pass@localhost:5432/test_db?sslmode=require'
        assert connection_string == expected
    
    def test_read_replica_configuration(self):
        """Test read replica configuration"""
        config = DatabaseConfig()
        config.username = 'postgres'
        config.password = 'postgres'
        config.read_replica_host = 'replica-host'
        config.read_replica_port = 5433
        config.read_replica_database = 'replica_db'
        
        replica_string = config.get_read_replica_string()
        expected = 'postgresql://postgres:postgres@replica-host:5433/replica_db?sslmode=prefer'
        assert replica_string == expected
    
    def test_pool_configuration(self):
        """Test pool configuration dictionary"""
        config = DatabaseConfig()
        config.min_size = 5
        config.max_size = 10
        config.command_timeout = 30
        
        pool_config = config.get_pool_config()
        
        assert pool_config['min_size'] == 5
        assert pool_config['max_size'] == 10
        assert pool_config['command_timeout'] == 30
        assert 'server_settings' in pool_config
    
    def test_validation_success(self):
        """Test successful validation"""
        config = DatabaseConfig()
        config.connection_string = 'postgresql://user:pass@host:5432/db'
        
        assert config.validate() == True
    
    def test_validation_failure_missing_host(self):
        """Test validation failure with missing host"""
        config = DatabaseConfig()
        config.host = None
        config.connection_string = None
        
        assert config.validate() == False
    
    def test_validation_failure_invalid_pool_size(self):
        """Test validation failure with invalid pool size"""
        config = DatabaseConfig()
        config.connection_string = 'postgresql://user:pass@host:5432/db'
        config.min_size = 10
        config.max_size = 5  # Less than min_size
        
        assert config.validate() == False
    
    @patch('core.db.config.logger')
    def test_log_config(self, mock_logger):
        """Test configuration logging"""
        config = DatabaseConfig()
        config.connection_string = 'postgresql://user@host:5432/db'
        
        config.log_config()
        
        # Check that logger.info was called
        assert mock_logger.info.called
    
    def test_configure_database(self):
        """Test global database configuration"""
        config = configure_database()
        
        assert isinstance(config, DatabaseConfig)
        assert config.validate() == True
