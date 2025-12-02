"""Base Notification Service - Abstract Base Class"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class NotificationType(Enum):
    """Types of notifications"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationChannel(Enum):
    """Notification delivery channels"""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class BaseNotificationService(ABC):
    """
    Abstract base class for notification services.
    Add-ons can extend this to implement custom notification logic
    with different channels, formats, and user preferences.
    """

    @abstractmethod
    async def send_notification(
        self,
        user_id: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        channels: Optional[List[NotificationChannel]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None
    ) -> bool:
        """
        Send a notification to a user.
        
        Args:
            user_id: User ID to send notification to
            message: Notification message
            notification_type: Type of notification
            channels: List of channels to use (defaults to user preferences)
            metadata: Optional metadata
            action_url: Optional URL for notification action
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass

    @abstractmethod
    async def send_bulk_notification(
        self,
        user_ids: List[str],
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        channels: Optional[List[NotificationChannel]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        Send a notification to multiple users.
        
        Args:
            user_ids: List of user IDs
            message: Notification message
            notification_type: Type of notification
            channels: List of channels to use
            metadata: Optional metadata
            
        Returns:
            Dict with 'sent' and 'failed' counts
        """
        pass

    @abstractmethod
    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum number of results
            skip: Number to skip (pagination)
            
        Returns:
            List of notification dicts
        """
        pass

    @abstractmethod
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for verification)
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications marked as read
        """
        pass

    @abstractmethod
    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for verification)
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Count of unread notifications
        """
        pass

    @abstractmethod
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get notification preferences for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict of user notification preferences
        """
        pass

    @abstractmethod
    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Update notification preferences for a user.
        
        Args:
            user_id: User ID
            preferences: New preferences dict
            
        Returns:
            True if successful, False otherwise
        """
        pass

    # Helper methods for specific notification types
    async def send_success_notification(
        self,
        user_id: str,
        message: str,
        action_url: Optional[str] = None
    ) -> bool:
        """Send a success notification."""
        return await self.send_notification(
            user_id,
            message,
            NotificationType.SUCCESS,
            action_url=action_url
        )

    async def send_error_notification(
        self,
        user_id: str,
        message: str,
        action_url: Optional[str] = None
    ) -> bool:
        """Send an error notification."""
        return await self.send_notification(
            user_id,
            message,
            NotificationType.ERROR,
            action_url=action_url
        )

    async def send_warning_notification(
        self,
        user_id: str,
        message: str,
        action_url: Optional[str] = None
    ) -> bool:
        """Send a warning notification."""
        return await self.send_notification(
            user_id,
            message,
            NotificationType.WARNING,
            action_url=action_url
        )

    @abstractmethod
    def format_notification(
        self,
        message: str,
        notification_type: NotificationType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format a notification for storage/delivery.
        Add-ons can customize the notification format.
        
        Args:
            message: Notification message
            notification_type: Type of notification
            metadata: Optional metadata
            
        Returns:
            Formatted notification dict
        """
        pass
