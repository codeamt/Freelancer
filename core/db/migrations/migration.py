"""
Base Migration Class

All migrations should inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio


class Migration(ABC):
    """Base class for database migrations"""
    
    # Migration metadata
    version: str = None  # Format: YYYYMMDD_HHMMSS (e.g., 20231226_143000)
    description: str = None
    author: str = None
    dependencies: List[str] = None  # List of version strings this migration depends on
    
    def __init__(self):
        if not self.version:
            raise ValueError("Migration must have a version")
        if not self.description:
            raise ValueError("Migration must have a description")
        if not self.dependencies:
            self.dependencies = []
    
    @abstractmethod
    async def up(self, connection) -> None:
        """
        Apply the migration.
        
        Args:
            connection: Database connection to execute migration
        """
        pass
    
    @abstractmethod
    async def down(self, connection) -> None:
        """
        Rollback the migration.
        
        Args:
            connection: Database connection to execute rollback
        """
        pass
    
    async def pre_check(self, connection) -> bool:
        """
        Check if migration can be safely applied.
        
        Returns:
            True if migration can proceed, False otherwise
        """
        return True
    
    async def post_check(self, connection) -> bool:
        """
        Verify migration was applied successfully.
        
        Returns:
            True if migration succeeded, False otherwise
        """
        return True
    
    def get_sql_statements(self) -> Dict[str, List[str]]:
        """
        Get SQL statements for documentation purposes.
        
        Returns:
            Dict with 'up' and 'down' keys containing lists of SQL statements
        """
        return {
            'up': [],
            'down': []
        }


class SQLMigration(Migration):
    """Migration that executes raw SQL statements"""
    
    def __init__(self, up_sql: str, down_sql: str, **kwargs):
        super().__init__(**kwargs)
        self.up_sql = up_sql.strip()
        self.down_sql = down_sql.strip()
    
    async def up(self, connection) -> None:
        """Execute up SQL statements"""
        statements = [s.strip() for s in self.up_sql.split(';') if s.strip()]
        for statement in statements:
            await connection.execute(statement)
    
    async def down(self, connection) -> None:
        """Execute down SQL statements"""
        statements = [s.strip() for s in self.down_sql.split(';') if s.strip()]
        for statement in statements:
            await connection.execute(statement)
    
    def get_sql_statements(self) -> Dict[str, List[str]]:
        """Return the SQL statements"""
        return {
            'up': [s.strip() for s in self.up_sql.split(';') if s.strip()],
            'down': [s.strip() for s in self.down_sql.split(';') if s.strip()]
        }


class PythonMigration(Migration):
    """Migration that executes Python code"""
    
    def __init__(self, up_func=None, down_func=None, **kwargs):
        super().__init__(**kwargs)
        if up_func:
            self.up = up_func
        if down_func:
            self.down = down_func


# Migration decorator for easy creation
def migration(version: str, description: str, author: str = None, dependencies: List[str] = None):
    """Decorator to create migrations from functions"""
    def decorator(up_func):
        class DecoratedMigration(PythonMigration):
            version = version
            description = description
            author = author
            dependencies = dependencies or []
            
            async def up(self, connection):
                await up_func(connection)
        
        return DecoratedMigration()
    return decorator
