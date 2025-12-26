"""
Recovery Manager

Handles database recovery operations.
"""

import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .backup_types import BackupType, BackupStatus, RestoreInfo
from core.utils.logger import get_logger

logger = get_logger(__name__)


class RecoveryManager:
    """Manages database recovery operations"""
    
    def __init__(self, postgres_config, backup_manager):
        self.postgres_config = postgres_config
        self.backup_manager = backup_manager
    
    async def restore_database(self, backup_id: str, target_database: str = None,
                              clean: bool = True) -> RestoreInfo:
        """
        Restore database from backup
        
        Args:
            backup_id: Backup ID to restore from
            target_database: Target database name (default: same as source)
            clean: Drop existing database before restore
            
        Returns:
            Restore operation information
        """
        restore_id = str(uuid.uuid4())
        target_db = target_database or self.postgres_config.database
        
        restore_info = RestoreInfo(
            restore_id=restore_id,
            backup_id=backup_id,
            started_at=datetime.utcnow(),
            target_database=target_db,
            status=BackupStatus.IN_PROGRESS
        )
        
        try:
            # Verify backup exists
            backup_file = await self._get_backup_file(backup_id)
            if not backup_file:
                raise Exception(f"Backup not found: {backup_id}")
            
            # Verify backup integrity
            if not await self.backup_manager.verify_backup(backup_id):
                raise Exception(f"Backup verification failed: {backup_id}")
            
            # Drop existing database if requested
            if clean:
                await self._drop_database(target_db)
            
            # Create new database
            await self._create_database(target_db)
            
            # Restore from backup
            await self._restore_from_file(backup_file, target_db)
            
            # Update status
            restore_info.status = BackupStatus.COMPLETED
            restore_info.completed_at = datetime.utcnow()
            
            logger.info(f"✓ Database restored: {target_db} from backup {backup_id}")
            
            return restore_info
            
        except Exception as e:
            restore_info.status = BackupStatus.FAILED
            restore_info.completed_at = datetime.utcnow()
            restore_info.error_message = str(e)
            
            logger.error(f"✗ Restore failed: {backup_id} - {e}")
            raise
    
    async def _get_backup_file(self, backup_id: str) -> Optional[Path]:
        """Get backup file path"""
        # Check local storage
        for file_path in self.backup_manager.backup_dir.glob(f"*_{backup_id}.backup"):
            return file_path
        
        # Check S3 if configured
        if self.backup_manager.config.s3_bucket:
            return await self.backup_manager._download_from_s3(backup_id)
        
        return None
    
    async def _drop_database(self, database_name: str):
        """Drop existing database"""
        # Connect to postgres database to drop target database
        cmd = [
            "psql",
            f"--host={self.postgres_config.host}",
            f"--port={self.postgres_config.port}",
            f"--username={self.postgres_config.username}",
            "--dbname=postgres",
            "--no-password",
            "-c", f"DROP DATABASE IF EXISTS {database_name}"
        ]
        
        os.environ['PGPASSWORD'] = self.postgres_config.password
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to drop database: {result.stderr}")
    
    async def _create_database(self, database_name: str):
        """Create new database"""
        cmd = [
            "psql",
            f"--host={self.postgres_config.host}",
            f"--port={self.postgres_config.port}",
            f"--username={self.postgres_config.username}",
            "--dbname=postgres",
            "--no-password",
            "-c", f"CREATE DATABASE {database_name}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to create database: {result.stderr}")
    
    async def _restore_from_file(self, backup_file: Path, target_database: str):
        """Restore database from backup file"""
        cmd = [
            "pg_restore",
            f"--host={self.postgres_config.host}",
            f"--port={self.postgres_config.port}",
            f"--username={self.postgres_config.username}",
            f"--dbname={target_database}",
            "--no-password",
            "--verbose",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            str(backup_file)
        ]
        
        os.environ['PGPASSWORD'] = self.postgres_config.password
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor progress
        while process.poll() is None:
            await asyncio.sleep(1)
        
        if process.returncode != 0:
            error = process.stderr.read()
            raise Exception(f"Restore failed: {error}")
    
    async def point_in_time_recovery(self, target_time: datetime, 
                                   target_database: str = None) -> RestoreInfo:
        """
        Perform point-in-time recovery
        
        Args:
            target_time: Target recovery time
            target_database: Target database name
            
        Returns:
            Restore operation information
        """
        restore_id = str(uuid.uuid4())
        target_db = target_database or f"{self.postgres_config.database}_pitr_{restore_id[:8]}"
        
        restore_info = RestoreInfo(
            restore_id=restore_id,
            backup_id="pitr",
            started_at=datetime.utcnow(),
            target_database=target_db,
            status=BackupStatus.IN_PROGRESS
        )
        
        try:
            # This requires WAL archiving to be configured
            # For now, return an error
            raise Exception(
                "Point-in-time recovery requires WAL archiving to be configured. "
                "Please set up WAL archiving in PostgreSQL configuration."
            )
            
        except Exception as e:
            restore_info.status = BackupStatus.FAILED
            restore_info.completed_at = datetime.utcnow()
            restore_info.error_message = str(e)
            
            logger.error(f"✗ PITR failed: {e}")
            raise
    
    async def clone_database(self, source_database: str, 
                           target_database: str) -> RestoreInfo:
        """
        Clone a database
        
        Args:
            source_database: Source database name
            target_database: Target database name
            
        Returns:
            Restore operation information
        """
        restore_id = str(uuid.uuid4())
        
        restore_info = RestoreInfo(
            restore_id=restore_id,
            backup_id="clone",
            started_at=datetime.utcnow(),
            target_database=target_database,
            status=BackupStatus.IN_PROGRESS
        )
        
        try:
            # Create template from source
            cmd = [
                "createdb",
                f"--host={self.postgres_config.host}",
                f"--port={self.postgres_config.port}",
                f"--username={self.postgres_config.username}",
                f"--template={source_database}",
                target_database
            ]
            
            os.environ['PGPASSWORD'] = self.postgres_config.password
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                # Try alternative method
                await self._clone_via_dump(source_database, target_database)
            
            restore_info.status = BackupStatus.COMPLETED
            restore_info.completed_at = datetime.utcnow()
            
            logger.info(f"✓ Database cloned: {source_database} -> {target_database}")
            
            return restore_info
            
        except Exception as e:
            restore_info.status = BackupStatus.FAILED
            restore_info.completed_at = datetime.utcnow()
            restore_info.error_message = str(e)
            
            logger.error(f"✗ Clone failed: {e}")
            raise
    
    async def _clone_via_dump(self, source_database: str, target_database: str):
        """Clone database using pg_dump/pg_restore"""
        # Create temporary dump file
        temp_file = Path(f"/tmp/{source_database}_clone_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.dump")
        
        try:
            # Dump source database
            dump_cmd = [
                "pg_dump",
                f"--host={self.postgres_config.host}",
                f"--port={self.postgres_config.port}",
                f"--username={self.postgres_config.username}",
                f"--dbname={source_database}",
                "--no-password",
                "--format=custom",
                f"--file={temp_file}"
            ]
            
            os.environ['PGPASSWORD'] = self.postgres_config.password
            
            result = subprocess.run(dump_cmd, capture_output=True)
            if result.returncode != 0:
                raise Exception(f"Dump failed: {result.stderr.decode()}")
            
            # Create target database
            await self._create_database(target_database)
            
            # Restore to target
            await self._restore_from_file(temp_file, target_database)
            
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
    
    async def verify_restore(self, database_name: str) -> bool:
        """
        Verify restored database
        
        Args:
            database_name: Database to verify
            
        Returns:
            True if verification passes
        """
        try:
            # Connect and check basic functionality
            cmd = [
                "psql",
                f"--host={self.postgres_config.host}",
                f"--port={self.postgres_config.port}",
                f"--username={self.postgres_config.username}",
                f"--dbname={database_name}",
                "--no-password",
                "-c", "SELECT COUNT(*) FROM information_schema.tables"
            ]
            
            os.environ['PGPASSWORD'] = self.postgres_config.password
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Database verification failed: {result.stderr}")
                return False
            
            # Parse table count
            table_count = int(result.stdout.strip().split('\n')[-1])
            logger.info(f"✓ Database verified: {database_name} ({table_count} tables)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify database {database_name}: {e}")
            return False
    
    async def list_restores(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List recent restore operations
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of restore operations
        """
        # This would require storing restore history
        # For now, return empty list
        return []
    
    async def get_recovery_options(self, backup_id: str) -> Dict[str, Any]:
        """
        Get available recovery options for a backup
        
        Args:
            backup_id: Backup ID
            
        Returns:
            Recovery options
        """
        backup_info = None
        for backup in await self.backup_manager.list_backups():
            if backup.backup_id == backup_id:
                backup_info = backup
                break
        
        if not backup_info:
            raise Exception(f"Backup not found: {backup_id}")
        
        options = {
            'backup_id': backup_id,
            'backup_type': backup_info.backup_type.value,
            'backup_date': backup_info.started_at.isoformat(),
            'size_mb': backup_info.size_mb,
            'available_options': [
                {
                    'type': 'full_restore',
                    'description': 'Full database restore',
                    'requires_clean': True
                }
            ]
        }
        
        # Add PITR option if backup type supports it
        if backup_info.backup_type in [BackupType.FULL, BackupType.DIFFERENTIAL]:
            options['available_options'].append({
                'type': 'point_in_time',
                'description': 'Point-in-time recovery',
                'requires_wal': True
            })
        
        return options
