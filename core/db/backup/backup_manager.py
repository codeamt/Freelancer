"""
Backup Manager

Handles database backup operations.
"""

import os
import asyncio
import subprocess
import gzip
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from .backup_types import BackupType, BackupStatus, BackupInfo, BackupConfig
from core.utils.logger import get_logger

logger = get_logger(__name__)


class BackupManager:
    """Manages database backups"""
    
    def __init__(self, postgres_config, backup_config: BackupConfig = None):
        self.postgres_config = postgres_config
        self.config = backup_config or BackupConfig()
        self.backup_dir = Path(self.config.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self, backup_type: BackupType = None) -> BackupInfo:
        """
        Create a database backup
        
        Args:
            backup_type: Type of backup to create
            
        Returns:
            Backup information
        """
        backup_type = backup_type or self.config.backup_type
        backup_id = str(uuid.uuid4())
        
        backup_info = BackupInfo(
            backup_id=backup_id,
            backup_type=backup_type,
            status=BackupStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
            metadata={}
        )
        
        try:
            # Build pg_dump command
            cmd = self._build_backup_command(backup_id, backup_type)
            
            # Execute backup
            logger.info(f"Starting {backup_type.value} backup: {backup_id}")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy()
            )
            
            # Monitor progress
            while process.poll() is None:
                await asyncio.sleep(1)
            
            # Check result
            if process.returncode != 0:
                error = process.stderr.read().decode()
                raise Exception(f"Backup failed: {error}")
            
            # Get file info
            backup_file = self._get_backup_path(backup_id, backup_type)
            backup_info.file_path = str(backup_file)
            backup_info.size_bytes = backup_file.stat().st_size
            
            # Calculate checksum
            backup_info.checksum = self._calculate_checksum(backup_file)
            
            # Update status
            backup_info.status = BackupStatus.COMPLETED
            backup_info.completed_at = datetime.utcnow()
            
            logger.info(f"✓ Backup completed: {backup_id} ({backup_info.size_mb:.1f} MB)")
            
            # Upload to S3 if configured
            if self.config.s3_bucket:
                await self._upload_to_s3(backup_info)
            
            return backup_info
            
        except Exception as e:
            backup_info.status = BackupStatus.FAILED
            backup_info.completed_at = datetime.utcnow()
            backup_info.metadata['error'] = str(e)
            
            logger.error(f"✗ Backup failed: {backup_id} - {e}")
            raise
    
    def _build_backup_command(self, backup_id: str, backup_type: BackupType) -> List[str]:
        """Build pg_dump command"""
        cmd = [
            "pg_dump",
            f"--host={self.postgres_config.host}",
            f"--port={self.postgres_config.port}",
            f"--username={self.postgres_config.username}",
            f"--dbname={self.postgres_config.database}",
            "--no-password",
            "--verbose",
            "--format=custom",
            f"--jobs={self.config.parallel_jobs}"
        ]
        
        # Add compression if enabled
        if self.config.compression:
            cmd.extend(["--compress=9"])
        
        # Add file path
        backup_file = self._get_backup_path(backup_id, backup_type)
        cmd.extend([f"--file={backup_file}"])
        
        # Set password in environment
        os.environ['PGPASSWORD'] = self.postgres_config.password
        
        return cmd
    
    def _get_backup_path(self, backup_id: str, backup_type: BackupType) -> Path:
        """Get backup file path"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{backup_type.value}_{timestamp}_{backup_id}.backup"
        return self.backup_dir / filename
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of backup file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    async def _upload_to_s3(self, backup_info: BackupInfo):
        """Upload backup to S3"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            s3 = boto3.client('s3', region_name=self.config.s3_region)
            
            key = f"backups/{backup_info.backup_type.value}/{backup_info.backup_id}.backup"
            
            s3.upload_file(
                backup_info.file_path,
                self.config.s3_bucket,
                key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            backup_info.metadata['s3_key'] = key
            logger.info(f"✓ Backup uploaded to S3: {key}")
            
        except ImportError:
            logger.warning("boto3 not installed, skipping S3 upload")
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
    
    async def list_backups(self, backup_type: BackupType = None, 
                          limit: int = 50) -> List[BackupInfo]:
        """
        List available backups
        
        Args:
            backup_type: Filter by backup type
            limit: Maximum number to return
            
        Returns:
            List of backup information
        """
        backups = []
        
        # Scan backup directory
        for file_path in self.backup_dir.glob("*.backup"):
            try:
                # Extract backup info from filename
                parts = file_path.stem.split('_')
                if len(parts) < 3:
                    continue
                
                backup_type_str = parts[0]
                backup_id = parts[-1]
                
                if backup_type and backup_type_str != backup_type.value:
                    continue
                
                # Get file stats
                stat = file_path.stat()
                
                backup_info = BackupInfo(
                    backup_id=backup_id,
                    backup_type=BackupType(backup_type_str),
                    status=BackupStatus.COMPLETED,
                    started_at=datetime.fromtimestamp(stat.st_ctime),
                    file_path=str(file_path),
                    size_bytes=stat.st_size
                )
                
                backups.append(backup_info)
                
            except Exception as e:
                logger.warning(f"Failed to parse backup file {file_path}: {e}")
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda b: b.started_at, reverse=True)
        
        return backups[:limit]
    
    async def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup
        
        Args:
            backup_id: Backup ID to delete
            
        Returns:
            True if successful
        """
        try:
            # Find backup file
            for file_path in self.backup_dir.glob(f"*_{backup_id}.backup"):
                file_path.unlink()
                logger.info(f"✓ Deleted backup: {backup_id}")
                return True
            
            # Check S3 if configured
            if self.config.s3_bucket:
                try:
                    import boto3
                    s3 = boto3.client('s3', region_name=self.config.s3_region)
                    
                    # List and delete matching objects
                    response = s3.list_objects_v2(
                        Bucket=self.config.s3_bucket,
                        Prefix=f"backups/"
                    )
                    
                    for obj in response.get('Contents', []):
                        if backup_id in obj['Key']:
                            s3.delete_object(Bucket=self.config.s3_bucket, Key=obj['Key'])
                            logger.info(f"✓ Deleted S3 backup: {obj['Key']}")
                            return True
                            
                except ImportError:
                    pass
                except Exception as e:
                    logger.error(f"Failed to delete from S3: {e}")
            
            logger.warning(f"Backup not found: {backup_id}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False
    
    async def verify_backup(self, backup_id: str) -> bool:
        """
        Verify backup integrity
        
        Args:
            backup_id: Backup ID to verify
            
        Returns:
            True if backup is valid
        """
        try:
            # Find backup file
            backup_file = None
            for file_path in self.backup_dir.glob(f"*_{backup_id}.backup"):
                backup_file = file_path
                break
            
            if not backup_file:
                # Try S3
                if self.config.s3_bucket:
                    backup_file = await self._download_from_s3(backup_id)
                
                if not backup_file:
                    logger.error(f"Backup not found: {backup_id}")
                    return False
            
            # Verify with pg_restore --list
            cmd = [
                "pg_restore",
                "--list",
                str(backup_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Backup verification failed: {result.stderr}")
                return False
            
            # Calculate and verify checksum if stored
            # This would require storing checksums separately
            
            logger.info(f"✓ Backup verified: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify backup {backup_id}: {e}")
            return False
    
    async def _download_from_s3(self, backup_id: str) -> Optional[Path]:
        """Download backup from S3"""
        try:
            import boto3
            
            s3 = boto3.client('s3', region_name=self.config.s3_region)
            
            # Find the backup
            response = s3.list_objects_v2(
                Bucket=self.config.s3_bucket,
                Prefix=f"backups/"
            )
            
            for obj in response.get('Contents', []):
                if backup_id in obj['Key']:
                    # Download to temp file
                    temp_file = self.backup_dir / f"temp_{backup_id}.backup"
                    s3.download_file(self.config.s3_bucket, obj['Key'], temp_file)
                    return temp_file
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to download from S3: {e}")
            return None
    
    async def cleanup_old_backups(self) -> int:
        """
        Clean up old backups based on retention policy
        
        Returns:
            Number of backups deleted
        """
        deleted_count = 0
        cutoff_date = datetime.utcnow() - timedelta(days=self.config.retention_days)
        
        # Get all backups
        backups = await self.list_backups()
        
        # Group by type and date
        backup_groups = {}
        for backup in backups:
            date_key = backup.started_at.date()
            if backup.backup_type not in backup_groups:
                backup_groups[backup.backup_type] = {}
            if date_key not in backup_groups[backup.backup_type]:
                backup_groups[backup.backup_type][date_key] = []
            backup_groups[backup.backup_type][date_key].append(backup)
        
        # Delete old backups
        for backup_type, dates in backup_groups.items():
            for date, date_backups in dates.items():
                if date < cutoff_date:
                    # Keep only the newest backup for old dates
                    date_backups.sort(key=lambda b: b.started_at, reverse=True)
                    for backup in date_backups[1:]:
                        if await self.delete_backup(backup.backup_id):
                            deleted_count += 1
        
        logger.info(f"✓ Cleaned up {deleted_count} old backups")
        return deleted_count
    
    async def get_backup_statistics(self) -> Dict[str, Any]:
        """
        Get backup statistics
        
        Returns:
            Backup statistics
        """
        backups = await self.list_backups()
        
        if not backups:
            return {
                'total_backups': 0,
                'total_size_mb': 0,
                'oldest_backup': None,
                'newest_backup': None,
                'by_type': {}
            }
        
        total_size = sum(b.size_bytes for b in backups)
        
        # Group by type
        by_type = {}
        for backup in backups:
            if backup.backup_type not in by_type:
                by_type[backup.backup_type.value] = {
                    'count': 0,
                    'size_mb': 0
                }
            by_type[backup.backup_type.value]['count'] += 1
            by_type[backup.backup_type.value]['size_mb'] += backup.size_mb
        
        return {
            'total_backups': len(backups),
            'total_size_mb': total_size / (1024 * 1024),
            'oldest_backup': min(b.started_at for b in backups).isoformat(),
            'newest_backup': max(b.started_at for b in backups).isoformat(),
            'by_type': by_type
        }
