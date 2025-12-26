#!/usr/bin/env python3
"""
Database Migration CLI

Usage:
    python scripts/manage_migrations.py status
    python scripts/manage_migrations.py migrate
    python scripts/manage_migrations.py rollback <version>
    python scripts/manage_migrations.py create "<description>"
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv('app.config.env')

from core.db.config import configure_database
from core.db.adapters.postgres_adapter import PostgresAdapter
from core.db.migrations import MigrationManager
from core.utils.logger import get_logger

logger = get_logger(__name__)


async def main():
    """Main CLI function"""
    if len(sys.argv) < 2:
        print("Usage: python manage_migrations.py <command> [args]")
        print("\nCommands:")
        print("  status                    Show migration status")
        print("  migrate [version]         Run pending migrations")
        print("  rollback <version>        Rollback to version")
        print("  create <description>      Create new migration")
        print("\nExamples:")
        print("  python manage_migrations.py status")
        print("  python manage_migrations.py migrate")
        print("  python manage_migrations.py rollback 20231201_120000")
        print('  python manage_migrations.py create "Add user preferences table"')
        return
    
    command = sys.argv[1]
    
    # Configure database
    try:
        configure_database()
    except Exception as e:
        print(f"Database configuration error: {e}")
        print("Please check your environment variables or app.config.env file")
        return
    
    # Initialize database connection
    postgres = PostgresAdapter()
    await postgres.connect()
    
    # Initialize migration manager
    migrations_dir = Path(__file__).parent.parent / "migrations"
    manager = MigrationManager(postgres, str(migrations_dir))
    
    try:
        if command == "status":
            await show_status(manager)
        elif command == "migrate":
            version = sys.argv[2] if len(sys.argv) > 2 else None
            await run_migrations(manager, version)
        elif command == "rollback":
            if len(sys.argv) < 3:
                print("Error: Rollback requires a version")
                print("Usage: python manage_migrations.py rollback <version>")
                return
            version = sys.argv[2]
            await rollback_migrations(manager, version)
        elif command == "create":
            if len(sys.argv) < 3:
                print("Error: Create requires a description")
                print('Usage: python manage_migrations.py create "<description>"')
                return
            description = " ".join(sys.argv[2:])
            author = os.getenv("USER", "Unknown")
            await create_migration(manager, description, author)
        else:
            print(f"Unknown command: {command}")
    finally:
        await postgres.disconnect()


async def show_status(manager: MigrationManager):
    """Show migration status"""
    status = await manager.get_status()
    
    print("\n=== Migration Status ===")
    print(f"Current version: {status['current_version'] or 'None'}")
    print(f"Applied migrations: {status['total_applied']}")
    print(f"Pending migrations: {status['total_pending']}")
    
    if status['applied']:
        print("\nApplied migrations:")
        for mig in status['applied']:
            print(f"  ✓ {mig['version']}: {mig['description']}")
            if mig['author']:
                print(f"    Author: {mig['author']}")
            print(f"    Applied: {mig['applied_at']}")
            if mig['execution_time_ms']:
                print(f"    Duration: {mig['execution_time_ms']}ms")
    
    if status['pending']:
        print("\nPending migrations:")
        for mig in status['pending']:
            print(f"  ○ {mig['version']}: {mig['description']}")
            if mig['author']:
                print(f"    Author: {mig['author']}")
            if mig['dependencies']:
                print(f"    Dependencies: {', '.join(mig['dependencies'])}")
    
    print()


async def run_migrations(manager: MigrationManager, target_version: str = None):
    """Run migrations"""
    if target_version:
        print(f"\nRunning migrations up to version {target_version}...")
    else:
        print("\nRunning all pending migrations...")
    
    success = await manager.migrate(target_version)
    
    if success:
        print("✓ Migrations completed successfully")
    else:
        print("✗ Migration failed")
        sys.exit(1)


async def rollback_migrations(manager: MigrationManager, version: str):
    """Rollback migrations"""
    print(f"\nRolling back to version {version}...")
    
    success = await manager.rollback(version)
    
    if success:
        print("✓ Rollback completed successfully")
    else:
        print("✗ Rollback failed")
        sys.exit(1)


async def create_migration(manager: MigrationManager, description: str, author: str):
    """Create new migration"""
    print(f"\nCreating migration: {description}")
    
    filepath = await manager.create_migration(description, author)
    
    print(f"✓ Migration created: {filepath}")
    print("\nEdit the file to add your migration logic, then run:")
    print("  python manage_migrations.py migrate")


if __name__ == "__main__":
    asyncio.run(main())
