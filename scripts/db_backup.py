#!/usr/bin/env python3
"""
Database Backup CLI Tool

Provides commands for database backup and recovery.
"""

import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(PROJECT_ROOT))

from core.db.config import configure_database
from core.db.backup import BackupManager, RecoveryManager, BackupScheduler, BackupType
from core.utils.logger import get_logger

logger = get_logger(__name__)


class BackupCLI:
    """Backup CLI tool"""
    
    def __init__(self):
        self.config = configure_database()
        self.backup_manager = BackupManager(self.config)
        self.recovery_manager = RecoveryManager(self.config, self.backup_manager)
        self.scheduler = BackupScheduler(self.backup_manager)
    
    async def create_backup(self, backup_type: str = "full"):
        """Create a backup"""
        print(f"\n🔄 Creating {backup_type} backup...")
        
        backup_type_enum = BackupType(backup_type)
        backup_info = await self.backup_manager.create_backup(backup_type_enum)
        
        if backup_info.is_complete:
            print(f"✅ Backup completed successfully!")
            print(f"   ID: {backup_info.backup_id}")
            print(f"   Size: {backup_info.size_mb:.1f} MB")
            print(f"   Duration: {backup_info.duration_seconds:.1f} seconds")
            print(f"   File: {backup_info.file_path}")
        else:
            print(f"❌ Backup failed!")
            sys.exit(1)
    
    async def list_backups(self, backup_type: str = None, limit: int = 20):
        """List backups"""
        print("\n📋 Database Backups")
        print("=" * 80)
        
        backup_type_enum = BackupType(backup_type) if backup_type else None
        backups = await self.backup_manager.list_backups(backup_type_enum, limit)
        
        if not backups:
            print("No backups found")
            return
        
        print(f"{'ID':<36} {'Type':<12} {'Size':<10} {'Created':<20}")
        print("-" * 80)
        
        for backup in backups:
            print(f"{backup.backup_id:<36} {backup.backup_type.value:<12} "
                  f"{backup.size_mb:<10.1f} {backup.started_at.strftime('%Y-%m-%d %H:%M:%S'):<20}")
    
    async def restore_backup(self, backup_id: str, target_db: str = None, clean: bool = True):
        """Restore from backup"""
        print(f"\n🔄 Restoring backup {backup_id}...")
        
        if target_db:
            print(f"Target database: {target_db}")
        
        if clean:
            print("⚠️  This will drop the existing target database!")
            response = input("Continue? (y/N): ")
            if response.lower() != 'y':
                print("Cancelled")
                return
        
        try:
            restore_info = await self.recovery_manager.restore_database(
                backup_id, target_db, clean
            )
            
            if restore_info.status.value == "completed":
                print(f"✅ Restore completed successfully!")
                print(f"   Database: {restore_info.target_database}")
                print(f"   Duration: {restore_info.duration_seconds:.1f} seconds")
                
                # Verify restore
                if await self.recovery_manager.verify_restore(restore_info.target_database):
                    print("✅ Restore verification passed")
                else:
                    print("⚠️  Restore verification failed")
            else:
                print(f"❌ Restore failed: {restore_info.error_message}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            sys.exit(1)
    
    async def delete_backup(self, backup_id: str):
        """Delete a backup"""
        print(f"\n🗑️  Deleting backup {backup_id}...")
        
        response = input("Are you sure? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled")
            return
        
        if await self.backup_manager.delete_backup(backup_id):
            print("✅ Backup deleted")
        else:
            print("❌ Failed to delete backup")
            sys.exit(1)
    
    async def verify_backup(self, backup_id: str):
        """Verify backup integrity"""
        print(f"\n🔍 Verifying backup {backup_id}...")
        
        if await self.backup_manager.verify_backup(backup_id):
            print("✅ Backup is valid")
        else:
            print("❌ Backup verification failed")
            sys.exit(1)
    
    async def cleanup_backups(self):
        """Clean up old backups"""
        print("\n🧹 Cleaning up old backups...")
        
        deleted_count = await self.backup_manager.cleanup_old_backups()
        print(f"✅ Deleted {deleted_count} old backups")
    
    async def show_stats(self):
        """Show backup statistics"""
        print("\n📊 Backup Statistics")
        print("=" * 40)
        
        stats = await self.backup_manager.get_backup_statistics()
        
        print(f"Total backups: {stats['total_backups']}")
        print(f"Total size: {stats['total_size_mb']:.1f} MB")
        
        if stats['oldest_backup']:
            print(f"Oldest: {stats['oldest_backup']}")
        if stats['newest_backup']:
            print(f"Newest: {stats['newest_backup']}")
        
        print("\nBy type:")
        for backup_type, type_stats in stats['by_type'].items():
            print(f"  {backup_type}: {type_stats['count']} backups, "
                  f"{type_stats['size_mb']:.1f} MB")
    
    async def clone_database(self, source: str, target: str):
        """Clone a database"""
        print(f"\n🔄 Cloning database {source} to {target}...")
        
        try:
            restore_info = await self.recovery_manager.clone_database(source, target)
            
            if restore_info.status.value == "completed":
                print(f"✅ Clone completed successfully!")
                print(f"   Database: {restore_info.target_database}")
                print(f"   Duration: {restore_info.duration_seconds:.1f} seconds")
            else:
                print(f"❌ Clone failed: {restore_info.error_message}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Clone failed: {e}")
            sys.exit(1)
    
    async def start_scheduler(self):
        """Start backup scheduler"""
        print("\n⏰ Starting backup scheduler...")
        
        # Create default schedules
        self.scheduler.create_default_schedules()
        
        # Show schedule status
        status = self.scheduler.get_schedule_status()
        print(f"Active schedules: {status['active_schedules']}")
        
        for name, config in status['schedules'].items():
            print(f"  - {name}: {config['interval']} ({config['backup_type']})")
        
        print("\nScheduler is running. Press Ctrl+C to stop...")
        
        try:
            await self.scheduler.start()
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping scheduler...")
            await self.scheduler.stop()
            print("✅ Scheduler stopped")
    
    async def close(self):
        """Close connections"""
        # Nothing to close for now
        pass


async def main():
    parser = argparse.ArgumentParser(description="Database Backup Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create backup
    create_parser = subparsers.add_parser('create', help='Create a backup')
    create_parser.add_argument('--type', choices=['full', 'incremental', 'differential'],
                             default='full', help='Backup type')
    
    # List backups
    list_parser = subparsers.add_parser('list', help='List backups')
    list_parser.add_argument('--type', choices=['full', 'incremental', 'differential'],
                            help='Filter by type')
    list_parser.add_argument('--limit', type=int, default=20, help='Max number to show')
    
    # Restore backup
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_id', help='Backup ID to restore')
    restore_parser.add_argument('--target', help='Target database name')
    restore_parser.add_argument('--no-clean', action='store_true',
                               help='Do not drop existing database')
    
    # Delete backup
    delete_parser = subparsers.add_parser('delete', help='Delete a backup')
    delete_parser.add_argument('backup_id', help='Backup ID to delete')
    
    # Verify backup
    verify_parser = subparsers.add_parser('verify', help='Verify backup integrity')
    verify_parser.add_argument('backup_id', help='Backup ID to verify')
    
    # Cleanup
    subparsers.add_parser('cleanup', help='Clean up old backups')
    
    # Statistics
    subparsers.add_parser('stats', help='Show backup statistics')
    
    # Clone database
    clone_parser = subparsers.add_parser('clone', help='Clone a database')
    clone_parser.add_argument('source', help='Source database')
    clone_parser.add_argument('target', help='Target database')
    
    # Scheduler
    subparsers.add_parser('schedule', help='Start backup scheduler')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = BackupCLI()
    
    try:
        if args.command == 'create':
            await cli.create_backup(args.type)
        
        elif args.command == 'list':
            await cli.list_backups(args.type, args.limit)
        
        elif args.command == 'restore':
            await cli.restore_backup(args.backup_id, args.target, not args.no_clean)
        
        elif args.command == 'delete':
            await cli.delete_backup(args.backup_id)
        
        elif args.command == 'verify':
            await cli.verify_backup(args.backup_id)
        
        elif args.command == 'cleanup':
            await cli.cleanup_backups()
        
        elif args.command == 'stats':
            await cli.show_stats()
        
        elif args.command == 'clone':
            await cli.clone_database(args.source, args.target)
        
        elif args.command == 'schedule':
            await cli.start_scheduler()
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        await cli.close()


if __name__ == "__main__":
    asyncio.run(main())
