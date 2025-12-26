"""
Migration Manager

Handles database schema migrations.
"""

import os
import importlib
import inspect
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import asyncio

from .migration import Migration
from ..adapters.postgres_adapter import PostgresAdapter
from ...utils.logger import get_logger

logger = get_logger(__name__)


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, postgres: PostgresAdapter, migrations_dir: str = None):
        self.postgres = postgres
        self.migrations_dir = migrations_dir or Path(__file__).parent.parent.parent / "migrations"
        self.migrations: Dict[str, Migration] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize migration system"""
        if self._initialized:
            return
        
        # Create migrations table if it doesn't exist
        await self._create_migrations_table()
        
        # Load all migrations
        await self._load_migrations()
        
        self._initialized = True
        logger.info("Migration system initialized")
    
    async def _create_migrations_table(self):
        """Create the schema_migrations table"""
        async with self.postgres.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(20) PRIMARY KEY,
                    description TEXT NOT NULL,
                    author VARCHAR(255),
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    execution_time_ms INTEGER,
                    checksum VARCHAR(64)
                )
            """)
            
            # Create index for faster queries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at 
                ON schema_migrations(applied_at)
            """)
    
    async def _load_migrations(self):
        """Load all migration files"""
        self.migrations = {}
        
        # Load from Python files
        migrations_path = Path(self.migrations_dir)
        if migrations_path.exists():
            for file_path in migrations_path.glob("*.py"):
                if file_path.name.startswith("__"):
                    continue
                
                module_name = file_path.stem
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find migration classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Migration) and obj != Migration:
                        migration = obj()
                        self.migrations[migration.version] = migration
                        logger.debug(f"Loaded migration {migration.version}: {migration.description}")
        
        logger.info(f"Loaded {len(self.migrations)} migrations")
    
    async def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        await self.initialize()
        
        # Get applied migrations
        async with self.postgres.acquire() as conn:
            result = await conn.fetch(
                "SELECT version FROM schema_migrations ORDER BY version"
            )
            applied_versions = {row['version'] for row in result}
        
        # Filter pending migrations
        pending = []
        for version in sorted(self.migrations.keys()):
            if version not in applied_versions:
                migration = self.migrations[version]
                
                # Check dependencies
                if self._check_dependencies(migration, applied_versions):
                    pending.append(migration)
                else:
                    logger.warning(f"Skipping migration {version} due to unmet dependencies")
        
        return pending
    
    def _check_dependencies(self, migration: Migration, applied_versions: set) -> bool:
        """Check if all dependencies are satisfied"""
        for dep in migration.dependencies:
            if dep not in applied_versions:
                return False
        return True
    
    async def migrate(self, target_version: str = None) -> bool:
        """
        Run all pending migrations up to target_version.
        
        Args:
            target_version: Stop at this version (None for all pending)
            
        Returns:
            True if successful, False otherwise
        """
        await self.initialize()
        
        pending = await self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return True
        
        if target_version:
            pending = [m for m in pending if m.version <= target_version]
        
        logger.info(f"Running {len(pending)} migrations...")
        
        for migration in pending:
            success = await self._run_migration(migration)
            if not success:
                logger.error(f"Migration {migration.version} failed")
                return False
        
        logger.info("All migrations completed successfully")
        return True
    
    async def _run_migration(self, migration: Migration) -> bool:
        """Run a single migration"""
        logger.info(f"Running migration {migration.version}: {migration.description}")
        
        start_time = datetime.utcnow()
        
        try:
            async with self.postgres.acquire() as conn:
                # Start transaction
                async with conn.transaction():
                    # Pre-check
                    if not await migration.pre_check(conn):
                        logger.error(f"Pre-check failed for migration {migration.version}")
                        return False
                    
                    # Run migration
                    await migration.up(conn)
                    
                    # Record migration
                    end_time = datetime.utcnow()
                    execution_time = int((end_time - start_time).total_seconds() * 1000)
                    
                    await conn.execute(
                        """
                        INSERT INTO schema_migrations 
                        (version, description, author, applied_at, execution_time_ms)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        migration.version,
                        migration.description,
                        migration.author,
                        start_time,
                        execution_time
                    )
                    
                    # Post-check
                    if not await migration.post_check(conn):
                        logger.error(f"Post-check failed for migration {migration.version}")
                        await conn.rollback()
                        return False
            
            logger.info(f"Migration {migration.version} completed in {execution_time}ms")
            return True
            
        except Exception as e:
            logger.error(f"Migration {migration.version} failed: {e}")
            return False
    
    async def rollback(self, target_version: str) -> bool:
        """
        Rollback to target_version.
        
        Args:
            target_version: Rollback to this version
            
        Returns:
            True if successful, False otherwise
        """
        await self.initialize()
        
        # Get migrations to rollback
        async with self.postgres.acquire() as conn:
            result = await conn.fetch(
                """
                SELECT version 
                FROM schema_migrations 
                WHERE version > $1 
                ORDER BY version DESC
                """,
                target_version
            )
        
        versions_to_rollback = [row['version'] for row in result]
        
        if not versions_to_rollback:
            logger.info("No migrations to rollback")
            return True
        
        logger.info(f"Rolling back {len(versions_to_rollback)} migrations...")
        
        for version in versions_to_rollback:
            if version in self.migrations:
                success = await self._rollback_migration(self.migrations[version])
                if not success:
                    logger.error(f"Rollback failed for migration {version}")
                    return False
            else:
                logger.warning(f"Migration {version} not found for rollback")
        
        logger.info("Rollback completed successfully")
        return True
    
    async def _rollback_migration(self, migration: Migration) -> bool:
        """Rollback a single migration"""
        logger.info(f"Rolling back migration {migration.version}: {migration.description}")
        
        try:
            async with self.postgres.acquire() as conn:
                async with conn.transaction():
                    # Run rollback
                    await migration.down(conn)
                    
                    # Remove from migrations table
                    await conn.execute(
                        "DELETE FROM schema_migrations WHERE version = $1",
                        migration.version
                    )
            
            logger.info(f"Rollback {migration.version} completed")
            return True
            
        except Exception as e:
            logger.error(f"Rollback {migration.version} failed: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get migration status"""
        await self.initialize()
        
        # Get applied migrations
        async with self.postgres.acquire() as conn:
            result = await conn.fetch(
                """
                SELECT version, description, author, applied_at, execution_time_ms
                FROM schema_migrations 
                ORDER BY version
                """
            )
        
        applied = [dict(row) for row in result]
        applied_versions = {row['version'] for row in applied}
        
        # Get pending migrations
        pending = []
        for version in sorted(self.migrations.keys()):
            if version not in applied_versions:
                migration = self.migrations[version]
                pending.append({
                    'version': version,
                    'description': migration.description,
                    'author': migration.author,
                    'dependencies': migration.dependencies
                })
        
        return {
            'applied': applied,
            'pending': pending,
            'current_version': applied[-1]['version'] if applied else None,
            'total_applied': len(applied),
            'total_pending': len(pending)
        }
    
    async def create_migration(self, description: str, author: str = None) -> str:
        """
        Create a new migration file.
        
        Args:
            description: Migration description
            author: Migration author
            
        Returns:
            Path to created migration file
        """
        # Generate version from timestamp
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sanitize description for filename
        filename = f"{version}_{description.lower().replace(' ', '_').replace('-', '_')}.py"
        filepath = Path(self.migrations_dir) / filename
        
        # Ensure migrations directory exists
        Path(self.migrations_dir).mkdir(exist_ok=True)
        
        # Create migration file template
        template = f'''"""
Migration: {description}

Created: {datetime.now().isoformat()}
Author: {author or "Unknown"}
"""

from core.db.migrations import Migration


class Migration_{version.replace('-', '_')}(Migration):
    version = "{version}"
    description = "{description}"
    author = "{author or 'Unknown'}"
    dependencies = []  # Add dependency versions here
    
    async def up(self, connection):
        """Apply the migration"""
        # Add your migration SQL here
        pass
    
    async def down(self, connection):
        """Rollback the migration"""
        # Add your rollback SQL here
        pass
'''
        
        # Write file
        with open(filepath, 'w') as f:
            f.write(template)
        
        logger.info(f"Created migration file: {filepath}")
        return str(filepath)
