"""
Backup Types and Data Structures

Defines backup types and information structures.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


class BackupType(Enum):
    """Types of backups"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    TRANSACTION_LOG = "transaction_log"


class BackupStatus(Enum):
    """Backup status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"


@dataclass
class BackupInfo:
    """Backup information"""
    backup_id: str
    backup_type: BackupType
    status: BackupStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    size_bytes: int = 0
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    compression: bool = False
    encryption: bool = False
    metadata: Dict[str, Any] = None
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get backup duration in seconds"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def size_mb(self) -> float:
        """Get backup size in MB"""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def is_complete(self) -> bool:
        """Check if backup is complete"""
        return self.status == BackupStatus.COMPLETED


@dataclass
class RestoreInfo:
    """Restore operation information"""
    restore_id: str
    backup_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    target_database: str = ""
    status: BackupStatus = BackupStatus.PENDING
    error_message: Optional[str] = None
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get restore duration in seconds"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class BackupConfig:
    """Backup configuration"""
    # Storage settings
    backup_dir: str = "/backups"
    s3_bucket: Optional[str] = None
    s3_region: str = "us-east-1"
    
    # Backup settings
    backup_type: BackupType = BackupType.FULL
    compression: bool = True
    encryption: bool = True
    parallel_jobs: int = 4
    
    # Retention settings
    retention_days: int = 30
    keep_weekly: int = 4
    keep_monthly: int = 12
    
    # Schedule settings
    full_backup_interval: str = "daily"  # daily, weekly, monthly
    incremental_interval: str = "hourly"
    
    # Notification settings
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_email: Optional[str] = None
