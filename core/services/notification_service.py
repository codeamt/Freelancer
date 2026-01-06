"""
Notification Service

Provides unified notification system for email, in-app, and push notifications.
Supports templates, queuing, delivery tracking, and user preferences.
"""

import os
import json
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict
from collections import deque

from core.utils.logger import get_logger
from core.services.audit_service import get_audit_service, AuditEventType

logger = get_logger(__name__)


class NotificationType(Enum):
    """Types of notifications"""
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"
    SMS = "sms"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(Enum):
    """Notification delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"
    ARCHIVED = "archived"


class NotificationCategory(Enum):
    """Notification categories"""
    SYSTEM = "system"
    ACCOUNT = "account"
    SECURITY = "security"
    MARKETING = "marketing"
    TRANSACTIONAL = "transactional"
    SOCIAL = "social"
    PRODUCT = "product"
    PAYMENT = "payment"


@dataclass
class Notification:
    """Notification data structure"""
    id: str
    user_id: int
    type: NotificationType
    category: NotificationCategory
    priority: NotificationPriority
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: Optional[str] = None
    sent_at: Optional[str] = None
    read_at: Optional[str] = None
    expires_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "category": self.category.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "status": self.status.value,
        }
        
        if self.data:
            result["data"] = self.data
        if self.created_at:
            result["created_at"] = self.created_at
        if self.sent_at:
            result["sent_at"] = self.sent_at
        if self.read_at:
            result["read_at"] = self.read_at
        if self.expires_at:
            result["expires_at"] = self.expires_at
        
        return result


@dataclass
class EmailTemplate:
    """Email template data structure"""
    template_id: str
    subject: str
    body_html: str
    body_text: str
    variables: List[str]


class NotificationService:
    """
    Unified notification service.
    
    Features:
    - Email notifications (transactional)
    - In-app notification system
    - Notification preferences management
    - Notification delivery queue
    - Template system
    - Delivery tracking
    """
    
    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize notification service.
        
        Args:
            max_queue_size: Maximum size of notification queue
        """
        self.max_queue_size = max_queue_size
        self.notification_queue = deque(maxlen=max_queue_size)
        self.notifications: Dict[str, Notification] = {}
        self.templates: Dict[str, EmailTemplate] = {}
        self.audit = get_audit_service()
        
        # Load default templates
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default email templates"""
        # Welcome email
        self.templates["welcome"] = EmailTemplate(
            template_id="welcome",
            subject="Welcome to {app_name}!",
            body_html="<h1>Welcome {user_name}!</h1><p>Thanks for joining us.</p>",
            body_text="Welcome {user_name}! Thanks for joining us.",
            variables=["app_name", "user_name"]
        )
        
        # Password reset
        self.templates["password_reset"] = EmailTemplate(
            template_id="password_reset",
            subject="Reset Your Password",
            body_html="<h1>Password Reset</h1><p>Click here to reset: {reset_link}</p>",
            body_text="Password Reset: {reset_link}",
            variables=["reset_link"]
        )
        
        # Email verification
        self.templates["email_verification"] = EmailTemplate(
            template_id="email_verification",
            subject="Verify Your Email",
            body_html="<h1>Verify Email</h1><p>Click here: {verification_link}</p>",
            body_text="Verify your email: {verification_link}",
            variables=["verification_link"]
        )
    
    # ========================================================================
    # Notification Creation
    # ========================================================================
    
    def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        category: NotificationCategory,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        expires_in_days: Optional[int] = None,
    ) -> Notification:
        """
        Create a notification.
        
        Args:
            user_id: Target user ID
            notification_type: Type of notification
            category: Notification category
            title: Notification title
            message: Notification message
            priority: Priority level
            data: Additional data
            expires_in_days: Days until notification expires
            
        Returns:
            Created notification
        """
        import uuid
        
        notification_id = str(uuid.uuid4())
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            from datetime import timedelta
            expires_at = (datetime.now(timezone.utc) + timedelta(days=expires_in_days)).isoformat()
        
        notification = Notification(
            id=notification_id,
            user_id=user_id,
            type=notification_type,
            category=category,
            priority=priority,
            title=title,
            message=message,
            data=data,
            status=NotificationStatus.PENDING,
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=expires_at,
        )
        
        # Store notification
        self.notifications[notification_id] = notification
        
        # Add to queue for processing
        self.notification_queue.append(notification)
        
        logger.info(f"Notification created: {notification_id} for user {user_id}")
        
        return notification
    
    # ========================================================================
    # Email Notifications
    # ========================================================================
    
    async def send_email(
        self,
        user_id: int,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        template_id: Optional[str] = None,
        template_vars: Optional[Dict[str, str]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
    ) -> Optional[str]:
        """
        Send email notification.
        
        Args:
            user_id: User ID
            to_email: Recipient email
            subject: Email subject
            body_html: HTML body
            body_text: Plain text body
            template_id: Optional template ID
            template_vars: Template variables
            priority: Priority level
            
        Returns:
            Notification ID or None
        """
        try:
            # Use template if provided
            if template_id and template_id in self.templates:
                template = self.templates[template_id]
                
                # Replace variables
                if template_vars:
                    subject = template.subject.format(**template_vars)
                    body_html = template.body_html.format(**template_vars)
                    body_text = template.body_text.format(**template_vars)
                else:
                    subject = template.subject
                    body_html = template.body_html
                    body_text = template.body_text
            
            # Create notification
            notification = self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.EMAIL,
                category=NotificationCategory.TRANSACTIONAL,
                title=subject,
                message=body_text or body_html[:200],
                priority=priority,
                data={
                    "to_email": to_email,
                    "subject": subject,
                    "body_html": body_html,
                    "body_text": body_text,
                },
            )
            
            # In production, this would integrate with email service (SendGrid, SES, etc.)
            # For now, we'll mark as queued
            notification.status = NotificationStatus.QUEUED
            
            logger.info(f"Email notification queued for {to_email}")
            
            return notification.id
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return None
    
    async def send_transactional_email(
        self,
        user_id: int,
        to_email: str,
        template_id: str,
        template_vars: Dict[str, str],
    ) -> Optional[str]:
        """
        Send transactional email using template.
        
        Args:
            user_id: User ID
            to_email: Recipient email
            template_id: Template ID
            template_vars: Template variables
            
        Returns:
            Notification ID or None
        """
        return await self.send_email(
            user_id=user_id,
            to_email=to_email,
            subject="",  # Will be filled by template
            body_html="",  # Will be filled by template
            template_id=template_id,
            template_vars=template_vars,
            priority=NotificationPriority.HIGH,
        )
    
    # ========================================================================
    # In-App Notifications
    # ========================================================================
    
    def send_in_app_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        expires_in_days: int = 30,
    ) -> str:
        """
        Send in-app notification.
        
        Args:
            user_id: User ID
            title: Notification title
            message: Notification message
            category: Notification category
            priority: Priority level
            data: Additional data (links, actions, etc.)
            expires_in_days: Days until notification expires
            
        Returns:
            Notification ID
        """
        notification = self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.IN_APP,
            category=category,
            title=title,
            message=message,
            priority=priority,
            data=data,
            expires_in_days=expires_in_days,
        )
        
        # Mark as sent immediately for in-app notifications
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"In-app notification sent to user {user_id}")
        
        return notification.id
    
    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        category: Optional[NotificationCategory] = None,
    ) -> List[Notification]:
        """
        Get user's in-app notifications.
        
        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum number to return
            category: Filter by category
            
        Returns:
            List of notifications
        """
        notifications = [
            n for n in self.notifications.values()
            if n.user_id == user_id and n.type == NotificationType.IN_APP
        ]
        
        # Filter by read status
        if unread_only:
            notifications = [n for n in notifications if n.status != NotificationStatus.READ]
        
        # Filter by category
        if category:
            notifications = [n for n in notifications if n.category == category]
        
        # Sort by created_at (newest first)
        notifications.sort(key=lambda n: n.created_at or "", reverse=True)
        
        return notifications[:limit]
    
    def get_unread_count(self, user_id: int) -> int:
        """
        Get count of unread notifications.
        
        Args:
            user_id: User ID
            
        Returns:
            Count of unread notifications
        """
        return len([
            n for n in self.notifications.values()
            if n.user_id == user_id 
            and n.type == NotificationType.IN_APP
            and n.status != NotificationStatus.READ
        ])
    
    def mark_as_read(self, notification_id: str) -> bool:
        """
        Mark notification as read.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            True if successful
        """
        if notification_id not in self.notifications:
            return False
        
        notification = self.notifications[notification_id]
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Notification {notification_id} marked as read")
        
        return True
    
    def mark_all_as_read(self, user_id: int) -> int:
        """
        Mark all user notifications as read.
        
        Args:
            user_id: User ID
            
        Returns:
            Count of notifications marked as read
        """
        count = 0
        
        for notification in self.notifications.values():
            if (notification.user_id == user_id 
                and notification.type == NotificationType.IN_APP
                and notification.status != NotificationStatus.READ):
                notification.status = NotificationStatus.READ
                notification.read_at = datetime.now(timezone.utc).isoformat()
                count += 1
        
        logger.info(f"Marked {count} notifications as read for user {user_id}")
        
        return count
    
    def delete_notification(self, notification_id: str) -> bool:
        """
        Delete notification.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            True if successful
        """
        if notification_id in self.notifications:
            del self.notifications[notification_id]
            logger.info(f"Notification {notification_id} deleted")
            return True
        
        return False
    
    # ========================================================================
    # Notification Preferences
    # ========================================================================
    
    async def check_user_preferences(
        self,
        user_id: int,
        notification_type: NotificationType,
        category: NotificationCategory,
    ) -> bool:
        """
        Check if user wants to receive this type of notification.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            category: Notification category
            
        Returns:
            True if user wants to receive this notification
        """
        # This would integrate with UserProfileService preferences
        # For now, return True (user wants all notifications)
        
        # Example logic:
        # - Check if email_notifications is enabled for email type
        # - Check if marketing_emails is enabled for marketing category
        # - Check if push_notifications is enabled for push type
        
        return True
    
    # ========================================================================
    # Batch Operations
    # ========================================================================
    
    def send_bulk_notification(
        self,
        user_ids: List[int],
        title: str,
        message: str,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        notification_type: NotificationType = NotificationType.IN_APP,
    ) -> List[str]:
        """
        Send notification to multiple users.
        
        Args:
            user_ids: List of user IDs
            title: Notification title
            message: Notification message
            category: Notification category
            notification_type: Type of notification
            
        Returns:
            List of notification IDs
        """
        notification_ids = []
        
        for user_id in user_ids:
            if notification_type == NotificationType.IN_APP:
                notification_id = self.send_in_app_notification(
                    user_id=user_id,
                    title=title,
                    message=message,
                    category=category,
                )
                notification_ids.append(notification_id)
        
        logger.info(f"Bulk notification sent to {len(user_ids)} users")
        
        return notification_ids
    
    # ========================================================================
    # Template Management
    # ========================================================================
    
    def add_template(
        self,
        template_id: str,
        subject: str,
        body_html: str,
        body_text: str,
        variables: List[str],
    ) -> bool:
        """
        Add email template.
        
        Args:
            template_id: Unique template ID
            subject: Email subject (can include {variables})
            body_html: HTML body (can include {variables})
            body_text: Plain text body (can include {variables})
            variables: List of variable names
            
        Returns:
            True if successful
        """
        try:
            self.templates[template_id] = EmailTemplate(
                template_id=template_id,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                variables=variables,
            )
            
            logger.info(f"Template {template_id} added")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add template {template_id}: {e}")
            return False
    
    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get email template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[str]:
        """List all template IDs"""
        return list(self.templates.keys())
    
    # ========================================================================
    # Queue Management
    # ========================================================================
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return len(self.notification_queue)
    
    def get_pending_notifications(self, limit: int = 100) -> List[Notification]:
        """
        Get pending notifications from queue.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of pending notifications
        """
        pending = [
            n for n in self.notification_queue
            if n.status == NotificationStatus.PENDING
        ]
        
        return pending[:limit]
    
    def process_queue(self, batch_size: int = 10) -> int:
        """
        Process notification queue.
        
        Args:
            batch_size: Number of notifications to process
            
        Returns:
            Number of notifications processed
        """
        processed = 0
        
        for _ in range(min(batch_size, len(self.notification_queue))):
            if not self.notification_queue:
                break
            
            notification = self.notification_queue.popleft()
            
            # Process based on type
            if notification.type == NotificationType.EMAIL:
                # In production, send via email service
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now(timezone.utc).isoformat()
                processed += 1
            
            elif notification.type == NotificationType.IN_APP:
                # Already handled in send_in_app_notification
                processed += 1
        
        if processed > 0:
            logger.info(f"Processed {processed} notifications from queue")
        
        return processed
    
    # ========================================================================
    # Statistics
    # ========================================================================
    
    def get_notification_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get notification statistics.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            Statistics dictionary
        """
        notifications = list(self.notifications.values())
        
        if user_id:
            notifications = [n for n in notifications if n.user_id == user_id]
        
        stats = {
            "total": len(notifications),
            "by_type": {},
            "by_status": {},
            "by_category": {},
            "by_priority": {},
        }
        
        for notification in notifications:
            # Count by type
            type_key = notification.type.value
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
            
            # Count by status
            status_key = notification.status.value
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1
            
            # Count by category
            category_key = notification.category.value
            stats["by_category"][category_key] = stats["by_category"].get(category_key, 0) + 1
            
            # Count by priority
            priority_key = notification.priority.value
            stats["by_priority"][priority_key] = stats["by_priority"].get(priority_key, 0) + 1
        
        return stats


# Global instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get global notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
