"""
Backup Scheduler

Automates backup scheduling and management.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from .backup_manager import BackupManager
from .backup_types import BackupType, BackupConfig
from core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScheduleConfig:
    """Backup schedule configuration"""
    backup_type: BackupType
    interval: str  # cron-style or "hourly", "daily", "weekly", "monthly"
    retention_days: int
    enabled: bool = True


class BackupScheduler:
    """Schedules and manages automated backups"""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.schedules: Dict[str, ScheduleConfig] = {}
        self.running = False
        self.tasks: List[asyncio.Task] = []
    
    def add_schedule(self, name: str, config: ScheduleConfig):
        """
        Add a backup schedule
        
        Args:
            name: Schedule name
            config: Schedule configuration
        """
        self.schedules[name] = config
        logger.info(f"Added backup schedule: {name} ({config.interval})")
    
    def remove_schedule(self, name: str):
        """
        Remove a backup schedule
        
        Args:
            name: Schedule name
        """
        if name in self.schedules:
            del self.schedules[name]
            logger.info(f"Removed backup schedule: {name}")
    
    async def start(self):
        """Start the backup scheduler"""
        if self.running:
            logger.warning("Backup scheduler already running")
            return
        
        self.running = True
        logger.info("Starting backup scheduler")
        
        # Create tasks for each schedule
        for name, config in self.schedules.items():
            if config.enabled:
                task = asyncio.create_task(self._run_schedule(name, config))
                self.tasks.append(task)
        
        # Add cleanup task
        cleanup_task = asyncio.create_task(self._run_cleanup())
        self.tasks.append(cleanup_task)
    
    async def stop(self):
        """Stop the backup scheduler"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping backup scheduler")
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
    
    async def _run_schedule(self, name: str, config: ScheduleConfig):
        """Run a specific backup schedule"""
        while self.running:
            try:
                # Calculate next run time
                next_run = self._get_next_run_time(config.interval)
                
                logger.info(f"Next {name} backup at: {next_run}")
                
                # Wait until next run time
                now = datetime.utcnow()
                if next_run > now:
                    sleep_seconds = (next_run - now).total_seconds()
                    await asyncio.sleep(sleep_seconds)
                
                if not self.running:
                    break
                
                # Execute backup
                logger.info(f"Executing scheduled backup: {name}")
                backup_info = await self.backup_manager.create_backup(config.backup_type)
                
                # Send notification if configured
                if self.backup_manager.config.notify_on_success:
                    await self._send_notification(
                        f"Backup completed: {name}",
                        f"Backup {backup_info.backup_id} completed successfully\n"
                        f"Size: {backup_info.size_mb:.1f} MB\n"
                        f"Duration: {backup_info.duration_seconds:.1f} seconds"
                    )
                
            except Exception as e:
                logger.error(f"Scheduled backup failed: {name} - {e}")
                
                # Send error notification
                if self.backup_manager.config.notify_on_failure:
                    await self._send_notification(
                        f"Backup failed: {name}",
                        f"Error: {str(e)}"
                    )
                
                # Wait before retry
                await asyncio.sleep(300)  # 5 minutes
    
    async def _run_cleanup(self):
        """Run periodic cleanup of old backups"""
        while self.running:
            try:
                # Run cleanup daily at 2 AM
                now = datetime.utcnow()
                next_cleanup = now.replace(hour=2, minute=0, second=0, microsecond=0)
                
                if next_cleanup <= now:
                    next_cleanup += timedelta(days=1)
                
                sleep_seconds = (next_cleanup - now).total_seconds()
                await asyncio.sleep(sleep_seconds)
                
                if not self.running:
                    break
                
                # Run cleanup
                deleted_count = await self.backup_manager.cleanup_old_backups()
                logger.info(f"Cleanup completed: {deleted_count} backups deleted")
                
            except Exception as e:
                logger.error(f"Backup cleanup failed: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    def _get_next_run_time(self, interval: str) -> datetime:
        """Calculate next run time based on interval"""
        now = datetime.utcnow()
        
        if interval == "hourly":
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        elif interval == "daily":
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        elif interval == "weekly":
            days_until_sunday = (6 - now.weekday()) % 7
            next_sunday = now + timedelta(days=days_until_sunday)
            return next_sunday.replace(hour=0, minute=0, second=0, microsecond=0)
        
        elif interval == "monthly":
            # First day of next month
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            return next_month.replace(hour=0, minute=0, second=0, microsecond=0)
        
        else:
            # For cron expressions, would need cron parser
            # For now, default to daily
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    async def _send_notification(self, subject: str, message: str):
        """Send backup notification"""
        # This would integrate with email/SMS/notification system
        if self.backup_manager.config.notification_email:
            logger.info(f"Notification: {subject}\n{message}")
            # TODO: Implement actual email sending
    
    def get_schedule_status(self) -> Dict[str, any]:
        """Get current schedule status"""
        return {
            'running': self.running,
            'active_schedules': len([s for s in self.schedules.values() if s.enabled]),
            'total_schedules': len(self.schedules),
            'schedules': {
                name: {
                    'type': config.backup_type.value,
                    'interval': config.interval,
                    'enabled': config.enabled,
                    'retention_days': config.retention_days
                }
                for name, config in self.schedules.items()
            }
        }
    
    def create_default_schedules(self):
        """Create default backup schedules"""
        # Daily full backup
        self.add_schedule("daily_full", ScheduleConfig(
            backup_type=BackupType.FULL,
            interval="daily",
            retention_days=7,
            enabled=True
        ))
        
        # Hourly incremental backup
        self.add_schedule("hourly_incremental", ScheduleConfig(
            backup_type=BackupType.INCREMENTAL,
            interval="hourly",
            retention_days=1,
            enabled=True
        ))
        
        # Weekly full backup with longer retention
        self.add_schedule("weekly_full", ScheduleConfig(
            backup_type=BackupType.FULL,
            interval="weekly",
            retention_days=30,
            enabled=True
        ))
