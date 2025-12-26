"""
Tests for database migration system
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from core.db.migrations import Migration, SQLMigration, PythonMigration
from core.db.migrations.migration_manager import MigrationManager


class TestMigration:
    """Test base migration class"""
    
    def test_migration_requires_version(self):
        """Test that migration must have version"""
        with pytest.raises(ValueError, match="Migration must have a version"):
            class BadMigration(Migration):
                description = "Test migration"
            
            BadMigration()
    
    def test_migration_requires_description(self):
        """Test that migration must have description"""
        with pytest.raises(ValueError, match="Migration must have a description"):
            class BadMigration(Migration):
                version = "20231201_120000"
            
            BadMigration()
    
    def test_migration_initialization(self):
        """Test successful migration initialization"""
        class TestMigration(Migration):
            version = "20231201_120000"
            description = "Test migration"
        
        migration = TestMigration()
        assert migration.version == "20231201_120000"
        assert migration.description == "Test migration"
        assert migration.dependencies == []
    
    async def test_migration_pre_check_default(self):
        """Test default pre_check returns True"""
        class TestMigration(Migration):
            version = "20231201_120000"
            description = "Test migration"
        
        migration = TestMigration()
        assert await migration.pre_check(None) == True
    
    async def test_migration_post_check_default(self):
        """Test default post_check returns True"""
        class TestMigration(Migration):
            version = "20231201_120000"
            description = "Test migration"
        
        migration = TestMigration()
        assert await migration.post_check(None) == True


class TestSQLMigration:
    """Test SQL migration class"""
    
    def test_sql_migration_initialization(self):
        """Test SQL migration initialization"""
        up_sql = "CREATE TABLE test (id SERIAL PRIMARY KEY);"
        down_sql = "DROP TABLE test;"
        
        migration = SQLMigration(
            up_sql=up_sql,
            down_sql=down_sql,
            version="20231201_120000",
            description="Create test table"
        )
        
        assert migration.up_sql == up_sql
        assert migration.down_sql == down_sql
        assert migration.version == "20231201_120000"
        assert migration.description == "Create test table"
    
    async def test_sql_migration_up(self):
        """Test SQL migration up execution"""
        up_sql = "CREATE TABLE test (id SERIAL PRIMARY KEY);"
        down_sql = "DROP TABLE test;"
        
        migration = SQLMigration(
            up_sql=up_sql,
            down_sql=down_sql,
            version="20231201_120000",
            description="Create test table"
        )
        
        mock_conn = AsyncMock()
        await migration.up(mock_conn)
        
        # Verify execute was called
        mock_conn.execute.assert_called_once_with(up_sql)
    
    async def test_sql_migration_down(self):
        """Test SQL migration down execution"""
        up_sql = "CREATE TABLE test (id SERIAL PRIMARY KEY);"
        down_sql = "DROP TABLE test;"
        
        migration = SQLMigration(
            up_sql=up_sql,
            down_sql=down_sql,
            version="20231201_120000",
            description="Create test table"
        )
        
        mock_conn = AsyncMock()
        await migration.down(mock_conn)
        
        # Verify execute was called
        mock_conn.execute.assert_called_once_with(down_sql)
    
    def test_sql_migration_get_statements(self):
        """Test getting SQL statements"""
        up_sql = "CREATE TABLE test (id SERIAL PRIMARY KEY);"
        down_sql = "DROP TABLE test;"
        
        migration = SQLMigration(
            up_sql=up_sql,
            down_sql=down_sql,
            version="20231201_120000",
            description="Create test table"
        )
        
        statements = migration.get_sql_statements()
        
        assert statements['up'] == [up_sql]
        assert statements['down'] == [down_sql]


class TestPythonMigration:
    """Test Python migration class"""
    
    async def test_python_migration_with_functions(self):
        """Test Python migration with custom functions"""
        up_called = False
        down_called = False
        
        async def up_func(conn):
            nonlocal up_called
            up_called = True
        
        async def down_func(conn):
            nonlocal down_called
            down_called = True
        
        migration = PythonMigration(
            up_func=up_func,
            down_func=down_func,
            version="20231201_120000",
            description="Test Python migration"
        )
        
        await migration.up(None)
        assert up_called
        
        await migration.down(None)
        assert down_called


class TestMigrationManager:
    """Test migration manager"""
    
    @pytest.fixture
    def mock_postgres(self):
        """Create mock PostgreSQL adapter"""
        postgres = MagicMock()
        postgres.acquire = AsyncMock()
        return postgres
    
    @pytest.fixture
    def migration_manager(self, mock_postgres):
        """Create migration manager with mock postgres"""
        return MigrationManager(mock_postgres)
    
    async def test_initialize_creates_migrations_table(self, migration_manager, mock_postgres):
        """Test initialization creates migrations table"""
        mock_conn = AsyncMock()
        mock_postgres.acquire.return_value.__aenter__.return_value = mock_conn
        
        await migration_manager.initialize()
        
        # Verify table creation
        assert mock_conn.execute.call_count >= 2  # Table and index creation
    
    async def test_get_pending_migrations(self, migration_manager, mock_postgres):
        """Test getting pending migrations"""
        # Mock applied migrations
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {'version': '20231201_110000'},
            {'version': '20231201_120000'}
        ]
        mock_postgres.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Add test migrations
        class TestMigration1(Migration):
            version = "20231201_110000"
            description = "Test 1"
        
        class TestMigration2(Migration):
            version = "20231201_120000"
            description = "Test 2"
        
        class TestMigration3(Migration):
            version = "20231201_130000"
            description = "Test 3"
        
        migration_manager.migrations = {
            "20231201_110000": TestMigration1(),
            "20231201_120000": TestMigration2(),
            "20231201_130000": TestMigration3()
        }
        
        pending = await migration_manager.get_pending_migrations()
        
        assert len(pending) == 1
        assert pending[0].version == "20231201_130000"
    
    async def test_migrate_success(self, migration_manager, mock_postgres):
        """Test successful migration"""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []  # No applied migrations
        mock_postgres.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Add test migration
        class TestMigration(Migration):
            version = "20231201_120000"
            description = "Test migration"
            
            async def up(self, conn):
                pass
        
        migration_manager.migrations = {"20231201_120000": TestMigration()}
        
        success = await migration_manager.migrate()
        
        assert success == True
    
    async def test_rollback_success(self, migration_manager, mock_postgres):
        """Test successful rollback"""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {'version': '20231201_130000'},
            {'version': '20231201_140000'}
        ]
        mock_postgres.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Add test migrations
        class TestMigration1(Migration):
            version = "20231201_130000"
            description = "Test 1"
            async def down(self, conn): pass
        
        class TestMigration2(Migration):
            version = "20231201_140000"
            description = "Test 2"
            async def down(self, conn): pass
        
        migration_manager.migrations = {
            "20231201_130000": TestMigration1(),
            "20231201_140000": TestMigration2()
        }
        
        success = await migration_manager.rollback("20231201_120000")
        
        assert success == True
    
    async def test_get_status(self, migration_manager, mock_postgres):
        """Test getting migration status"""
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {
                'version': '20231201_120000',
                'description': 'Test migration',
                'author': 'Test',
                'applied_at': datetime.now(),
                'execution_time_ms': 100
            }
        ]
        mock_postgres.acquire.return_value.__aenter__.return_value = mock_conn
        
        status = await migration_manager.get_status()
        
        assert status['total_applied'] == 1
        assert status['current_version'] == '20231201_120000'
        assert len(status['applied']) == 1
    
    async def test_create_migration_file(self, migration_manager, tmp_path):
        """Test creating migration file"""
        migration_manager.migrations_dir = str(tmp_path)
        
        filepath = await migration_manager.create_migration(
            description="Create test table",
            author="Test Author"
        )
        
        assert filepath.endswith(".py")
        assert "20231226" in filepath  # Date should be in filename
        assert "create_test_table" in filepath
        
        # Check file contents
        with open(filepath, 'r') as f:
            content = f.read()
            assert "Create test table" in content
            assert "Test Author" in content
            assert "version = " in content
