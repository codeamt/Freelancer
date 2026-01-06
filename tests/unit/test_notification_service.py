"""
Unit tests for Notification Service
"""

import pytest
from datetime import datetime
from core.services.notification_service import (
    NotificationService,
    Notification,
    NotificationType,
    NotificationPriority,
    NotificationStatus,
    NotificationCategory,
    EmailTemplate,
    get_notification_service,
)


class TestNotificationService:
    """Test suite for NotificationService"""
    
    def setup_method(self):
        """Setup test environment"""
        self.notification_service = NotificationService(max_queue_size=100)
    
    # ========================================================================
    # Notification Creation Tests
    # ========================================================================
    
    def test_create_notification(self):
        """Test creating a notification"""
        notification = self.notification_service.create_notification(
            user_id=1,
            notification_type=NotificationType.IN_APP,
            category=NotificationCategory.SYSTEM,
            title="Test Notification",
            message="This is a test message",
            priority=NotificationPriority.NORMAL,
        )
        
        assert notification is not None
        assert notification.user_id == 1
        assert notification.type == NotificationType.IN_APP
        assert notification.category == NotificationCategory.SYSTEM
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test message"
        assert notification.priority == NotificationPriority.NORMAL
        assert notification.status == NotificationStatus.PENDING
        assert notification.created_at is not None
    
    def test_create_notification_with_expiration(self):
        """Test creating notification with expiration"""
        notification = self.notification_service.create_notification(
            user_id=1,
            notification_type=NotificationType.IN_APP,
            category=NotificationCategory.SYSTEM,
            title="Test",
            message="Test",
            expires_in_days=7,
        )
        
        assert notification.expires_at is not None
    
    def test_create_notification_with_data(self):
        """Test creating notification with additional data"""
        data = {"link": "/profile", "action": "view"}
        
        notification = self.notification_service.create_notification(
            user_id=1,
            notification_type=NotificationType.IN_APP,
            category=NotificationCategory.SYSTEM,
            title="Test",
            message="Test",
            data=data,
        )
        
        assert notification.data == data
    
    # ========================================================================
    # Email Notification Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_send_email_basic(self):
        """Test sending basic email"""
        notification_id = await self.notification_service.send_email(
            user_id=1,
            to_email="test@example.com",
            subject="Test Email",
            body_html="<p>Test body</p>",
            body_text="Test body",
        )
        
        assert notification_id is not None
        
        # Verify notification was created
        notification = self.notification_service.notifications[notification_id]
        assert notification.type == NotificationType.EMAIL
        assert notification.status == NotificationStatus.QUEUED
    
    @pytest.mark.asyncio
    async def test_send_email_with_template(self):
        """Test sending email with template"""
        notification_id = await self.notification_service.send_email(
            user_id=1,
            to_email="test@example.com",
            subject="",
            body_html="",
            template_id="welcome",
            template_vars={"app_name": "TestApp", "user_name": "John"},
        )
        
        assert notification_id is not None
        
        notification = self.notification_service.notifications[notification_id]
        assert "TestApp" in notification.title
        assert "John" in notification.message
    
    @pytest.mark.asyncio
    async def test_send_transactional_email(self):
        """Test sending transactional email"""
        notification_id = await self.notification_service.send_transactional_email(
            user_id=1,
            to_email="test@example.com",
            template_id="password_reset",
            template_vars={"reset_link": "https://example.com/reset"},
        )
        
        assert notification_id is not None
        
        notification = self.notification_service.notifications[notification_id]
        assert notification.priority == NotificationPriority.HIGH
    
    # ========================================================================
    # In-App Notification Tests
    # ========================================================================
    
    def test_send_in_app_notification(self):
        """Test sending in-app notification"""
        notification_id = self.notification_service.send_in_app_notification(
            user_id=1,
            title="New Message",
            message="You have a new message from John",
            category=NotificationCategory.SOCIAL,
        )
        
        assert notification_id is not None
        
        notification = self.notification_service.notifications[notification_id]
        assert notification.type == NotificationType.IN_APP
        assert notification.status == NotificationStatus.SENT
        assert notification.sent_at is not None
    
    def test_get_user_notifications(self):
        """Test getting user notifications"""
        # Create multiple notifications
        for i in range(5):
            self.notification_service.send_in_app_notification(
                user_id=1,
                title=f"Notification {i}",
                message=f"Message {i}",
            )
        
        # Get notifications
        notifications = self.notification_service.get_user_notifications(user_id=1)
        
        assert len(notifications) == 5
        # Should be sorted by created_at (newest first)
        assert notifications[0].title == "Notification 4"
    
    def test_get_user_notifications_unread_only(self):
        """Test getting only unread notifications"""
        # Create notifications
        n1_id = self.notification_service.send_in_app_notification(
            user_id=1, title="N1", message="M1"
        )
        n2_id = self.notification_service.send_in_app_notification(
            user_id=1, title="N2", message="M2"
        )
        
        # Mark one as read
        self.notification_service.mark_as_read(n1_id)
        
        # Get unread only
        unread = self.notification_service.get_user_notifications(
            user_id=1, unread_only=True
        )
        
        assert len(unread) == 1
        assert unread[0].id == n2_id
    
    def test_get_user_notifications_by_category(self):
        """Test filtering notifications by category"""
        # Create notifications with different categories
        self.notification_service.send_in_app_notification(
            user_id=1, title="System", message="M1",
            category=NotificationCategory.SYSTEM
        )
        self.notification_service.send_in_app_notification(
            user_id=1, title="Social", message="M2",
            category=NotificationCategory.SOCIAL
        )
        
        # Filter by category
        system_notifs = self.notification_service.get_user_notifications(
            user_id=1, category=NotificationCategory.SYSTEM
        )
        
        assert len(system_notifs) == 1
        assert system_notifs[0].category == NotificationCategory.SYSTEM
    
    def test_get_unread_count(self):
        """Test getting unread notification count"""
        # Create notifications
        n1_id = self.notification_service.send_in_app_notification(
            user_id=1, title="N1", message="M1"
        )
        self.notification_service.send_in_app_notification(
            user_id=1, title="N2", message="M2"
        )
        self.notification_service.send_in_app_notification(
            user_id=1, title="N3", message="M3"
        )
        
        # Initially all unread
        assert self.notification_service.get_unread_count(1) == 3
        
        # Mark one as read
        self.notification_service.mark_as_read(n1_id)
        assert self.notification_service.get_unread_count(1) == 2
    
    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification_id = self.notification_service.send_in_app_notification(
            user_id=1, title="Test", message="Test"
        )
        
        success = self.notification_service.mark_as_read(notification_id)
        
        assert success is True
        
        notification = self.notification_service.notifications[notification_id]
        assert notification.status == NotificationStatus.READ
        assert notification.read_at is not None
    
    def test_mark_as_read_invalid_id(self):
        """Test marking non-existent notification as read"""
        success = self.notification_service.mark_as_read("invalid_id")
        assert success is False
    
    def test_mark_all_as_read(self):
        """Test marking all notifications as read"""
        # Create multiple notifications
        for i in range(3):
            self.notification_service.send_in_app_notification(
                user_id=1, title=f"N{i}", message=f"M{i}"
            )
        
        count = self.notification_service.mark_all_as_read(1)
        
        assert count == 3
        assert self.notification_service.get_unread_count(1) == 0
    
    def test_delete_notification(self):
        """Test deleting notification"""
        notification_id = self.notification_service.send_in_app_notification(
            user_id=1, title="Test", message="Test"
        )
        
        success = self.notification_service.delete_notification(notification_id)
        
        assert success is True
        assert notification_id not in self.notification_service.notifications
    
    # ========================================================================
    # Batch Operations Tests
    # ========================================================================
    
    def test_send_bulk_notification(self):
        """Test sending bulk notifications"""
        user_ids = [1, 2, 3, 4, 5]
        
        notification_ids = self.notification_service.send_bulk_notification(
            user_ids=user_ids,
            title="Announcement",
            message="System maintenance scheduled",
            category=NotificationCategory.SYSTEM,
        )
        
        assert len(notification_ids) == 5
        
        # Verify each user received notification
        for user_id in user_ids:
            user_notifs = self.notification_service.get_user_notifications(user_id)
            assert len(user_notifs) == 1
            assert user_notifs[0].title == "Announcement"
    
    # ========================================================================
    # Template Management Tests
    # ========================================================================
    
    def test_add_template(self):
        """Test adding email template"""
        success = self.notification_service.add_template(
            template_id="custom_template",
            subject="Custom Subject {var1}",
            body_html="<p>Hello {var1}</p>",
            body_text="Hello {var1}",
            variables=["var1"],
        )
        
        assert success is True
        
        template = self.notification_service.get_template("custom_template")
        assert template is not None
        assert template.template_id == "custom_template"
    
    def test_get_template(self):
        """Test getting template"""
        template = self.notification_service.get_template("welcome")
        
        assert template is not None
        assert template.template_id == "welcome"
        assert "app_name" in template.variables
    
    def test_get_template_not_found(self):
        """Test getting non-existent template"""
        template = self.notification_service.get_template("nonexistent")
        assert template is None
    
    def test_list_templates(self):
        """Test listing all templates"""
        templates = self.notification_service.list_templates()
        
        assert isinstance(templates, list)
        assert "welcome" in templates
        assert "password_reset" in templates
        assert "email_verification" in templates
    
    # ========================================================================
    # Queue Management Tests
    # ========================================================================
    
    def test_get_queue_size(self):
        """Test getting queue size"""
        initial_size = self.notification_service.get_queue_size()
        
        # Create notification (adds to queue)
        self.notification_service.create_notification(
            user_id=1,
            notification_type=NotificationType.EMAIL,
            category=NotificationCategory.TRANSACTIONAL,
            title="Test",
            message="Test",
        )
        
        new_size = self.notification_service.get_queue_size()
        assert new_size == initial_size + 1
    
    def test_get_pending_notifications(self):
        """Test getting pending notifications"""
        # Create pending notifications
        for i in range(3):
            self.notification_service.create_notification(
                user_id=1,
                notification_type=NotificationType.EMAIL,
                category=NotificationCategory.TRANSACTIONAL,
                title=f"Test {i}",
                message=f"Message {i}",
            )
        
        pending = self.notification_service.get_pending_notifications()
        
        assert len(pending) >= 3
        assert all(n.status == NotificationStatus.PENDING for n in pending)
    
    def test_process_queue(self):
        """Test processing notification queue"""
        # Create notifications
        for i in range(5):
            self.notification_service.create_notification(
                user_id=1,
                notification_type=NotificationType.EMAIL,
                category=NotificationCategory.TRANSACTIONAL,
                title=f"Test {i}",
                message=f"Message {i}",
            )
        
        initial_queue_size = self.notification_service.get_queue_size()
        
        # Process queue
        processed = self.notification_service.process_queue(batch_size=3)
        
        assert processed == 3
        assert self.notification_service.get_queue_size() == initial_queue_size - 3
    
    # ========================================================================
    # Statistics Tests
    # ========================================================================
    
    def test_get_notification_stats(self):
        """Test getting notification statistics"""
        # Create various notifications
        self.notification_service.send_in_app_notification(
            user_id=1, title="N1", message="M1",
            category=NotificationCategory.SYSTEM
        )
        self.notification_service.send_in_app_notification(
            user_id=1, title="N2", message="M2",
            category=NotificationCategory.SOCIAL
        )
        
        stats = self.notification_service.get_notification_stats()
        
        assert stats["total"] >= 2
        assert "by_type" in stats
        assert "by_status" in stats
        assert "by_category" in stats
        assert "by_priority" in stats
    
    def test_get_notification_stats_for_user(self):
        """Test getting statistics for specific user"""
        # Create notifications for different users
        self.notification_service.send_in_app_notification(
            user_id=1, title="N1", message="M1"
        )
        self.notification_service.send_in_app_notification(
            user_id=2, title="N2", message="M2"
        )
        
        user1_stats = self.notification_service.get_notification_stats(user_id=1)
        
        assert user1_stats["total"] == 1


class TestNotification:
    """Test Notification data structure"""
    
    def test_notification_creation(self):
        """Test creating notification"""
        notification = Notification(
            id="test_id",
            user_id=1,
            type=NotificationType.IN_APP,
            category=NotificationCategory.SYSTEM,
            priority=NotificationPriority.NORMAL,
            title="Test",
            message="Test message",
        )
        
        assert notification.id == "test_id"
        assert notification.user_id == 1
        assert notification.type == NotificationType.IN_APP
        assert notification.status == NotificationStatus.PENDING
    
    def test_notification_to_dict(self):
        """Test converting notification to dict"""
        notification = Notification(
            id="test_id",
            user_id=1,
            type=NotificationType.IN_APP,
            category=NotificationCategory.SYSTEM,
            priority=NotificationPriority.NORMAL,
            title="Test",
            message="Test message",
            data={"key": "value"},
        )
        
        notif_dict = notification.to_dict()
        
        assert isinstance(notif_dict, dict)
        assert notif_dict["id"] == "test_id"
        assert notif_dict["user_id"] == 1
        assert notif_dict["type"] == "in_app"
        assert notif_dict["data"] == {"key": "value"}


class TestEmailTemplate:
    """Test EmailTemplate data structure"""
    
    def test_email_template_creation(self):
        """Test creating email template"""
        template = EmailTemplate(
            template_id="test",
            subject="Test Subject {var1}",
            body_html="<p>{var1}</p>",
            body_text="{var1}",
            variables=["var1"],
        )
        
        assert template.template_id == "test"
        assert template.subject == "Test Subject {var1}"
        assert "var1" in template.variables


class TestNotificationEnums:
    """Test notification enums"""
    
    def test_notification_type_values(self):
        """Test notification type enum values"""
        assert NotificationType.EMAIL.value == "email"
        assert NotificationType.IN_APP.value == "in_app"
        assert NotificationType.PUSH.value == "push"
        assert NotificationType.SMS.value == "sms"
    
    def test_notification_priority_values(self):
        """Test notification priority enum values"""
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.NORMAL.value == "normal"
        assert NotificationPriority.HIGH.value == "high"
        assert NotificationPriority.URGENT.value == "urgent"
    
    def test_notification_status_values(self):
        """Test notification status enum values"""
        assert NotificationStatus.PENDING.value == "pending"
        assert NotificationStatus.QUEUED.value == "queued"
        assert NotificationStatus.SENT.value == "sent"
        assert NotificationStatus.DELIVERED.value == "delivered"
        assert NotificationStatus.FAILED.value == "failed"
        assert NotificationStatus.READ.value == "read"
        assert NotificationStatus.ARCHIVED.value == "archived"
    
    def test_notification_category_values(self):
        """Test notification category enum values"""
        assert NotificationCategory.SYSTEM.value == "system"
        assert NotificationCategory.ACCOUNT.value == "account"
        assert NotificationCategory.SECURITY.value == "security"
        assert NotificationCategory.MARKETING.value == "marketing"
        assert NotificationCategory.TRANSACTIONAL.value == "transactional"
        assert NotificationCategory.SOCIAL.value == "social"
        assert NotificationCategory.PRODUCT.value == "product"
        assert NotificationCategory.PAYMENT.value == "payment"


class TestGlobalNotificationService:
    """Test global notification service instance"""
    
    def test_get_notification_service(self):
        """Test getting global notification service"""
        service1 = get_notification_service()
        service2 = get_notification_service()
        
        # Should return same instance
        assert service1 is service2
    
    def test_global_service_persistence(self):
        """Test that global service persists data"""
        service = get_notification_service()
        
        # Create notification
        notification_id = service.send_in_app_notification(
            user_id=1, title="Test", message="Test"
        )
        
        # Get service again
        service2 = get_notification_service()
        
        # Should have same notification
        assert notification_id in service2.notifications


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
