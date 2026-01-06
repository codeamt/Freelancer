"""
Unit tests for Audit Logging Service
"""

import pytest
from datetime import datetime
from core.services.audit_service import (
    AuditService,
    AuditEventType,
    AuditSeverity,
    get_audit_service,
    log_audit_event,
)


class TestAuditService:
    """Test suite for AuditService"""
    
    def setup_method(self):
        """Setup test environment"""
        self.audit_service = AuditService()
    
    def test_audit_service_initialization(self):
        """Test audit service initializes correctly"""
        assert self.audit_service is not None
        assert self.audit_service.storage_backend == "database"
        assert len(self.audit_service.audit_logs) == 0
    
    def test_log_event_basic(self):
        """Test basic event logging"""
        event = self.audit_service.log_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            action="User logged in",
            user_id="user123",
            user_email="test@example.com",
            ip_address="192.168.1.1",
        )
        
        assert event is not None
        assert event.event_type == AuditEventType.AUTH_LOGIN_SUCCESS
        assert event.action == "User logged in"
        assert event.user_id == "user123"
        assert event.user_email == "test@example.com"
        assert event.ip_address == "192.168.1.1"
        assert event.severity == AuditSeverity.INFO
        assert event.timestamp is not None
    
    def test_log_login_success(self):
        """Test login success logging"""
        event = self.audit_service.log_login_success(
            user_id="user123",
            user_email="test@example.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            session_id="session123",
        )
        
        assert event.event_type == AuditEventType.AUTH_LOGIN_SUCCESS
        assert event.user_id == "user123"
        assert event.user_email == "test@example.com"
        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "Mozilla/5.0"
        assert event.session_id == "session123"
        assert event.severity == AuditSeverity.INFO
    
    def test_log_login_failure(self):
        """Test login failure logging"""
        event = self.audit_service.log_login_failure(
            email="test@example.com",
            reason="Invalid password",
            ip_address="192.168.1.1",
        )
        
        assert event.event_type == AuditEventType.AUTH_LOGIN_FAILURE
        assert event.user_email == "test@example.com"
        assert event.details["reason"] == "Invalid password"
        assert event.severity == AuditSeverity.WARNING
    
    def test_log_logout(self):
        """Test logout logging"""
        event = self.audit_service.log_logout(
            user_id="user123",
            user_email="test@example.com",
            session_id="session123",
        )
        
        assert event.event_type == AuditEventType.AUTH_LOGOUT
        assert event.user_id == "user123"
        assert event.session_id == "session123"
    
    def test_log_password_change(self):
        """Test password change logging"""
        event = self.audit_service.log_password_change(
            user_id="user123",
            user_email="test@example.com",
            ip_address="192.168.1.1",
        )
        
        assert event.event_type == AuditEventType.AUTH_PASSWORD_CHANGE
        assert event.user_id == "user123"
        assert event.severity == AuditSeverity.INFO
    
    def test_log_user_create(self):
        """Test user creation logging"""
        event = self.audit_service.log_user_create(
            admin_user_id="admin123",
            admin_email="admin@example.com",
            created_user_id="user456",
            created_user_email="newuser@example.com",
            roles=["user"],
        )
        
        assert event.event_type == AuditEventType.USER_CREATE
        assert event.user_id == "admin123"
        assert event.resource_type == "user"
        assert event.resource_id == "user456"
        assert event.details["created_user_email"] == "newuser@example.com"
        assert event.details["roles"] == ["user"]
    
    def test_log_user_role_change(self):
        """Test user role change logging"""
        event = self.audit_service.log_user_role_change(
            admin_user_id="admin123",
            admin_email="admin@example.com",
            target_user_id="user456",
            target_user_email="user@example.com",
            old_roles=["user"],
            new_roles=["user", "admin"],
        )
        
        assert event.event_type == AuditEventType.USER_ROLE_CHANGE
        assert event.severity == AuditSeverity.WARNING
        assert event.details["old_roles"] == ["user"]
        assert event.details["new_roles"] == ["user", "admin"]
    
    def test_log_user_delete(self):
        """Test user deletion logging"""
        event = self.audit_service.log_user_delete(
            admin_user_id="admin123",
            admin_email="admin@example.com",
            deleted_user_id="user456",
            deleted_user_email="deleted@example.com",
        )
        
        assert event.event_type == AuditEventType.USER_DELETE
        assert event.severity == AuditSeverity.WARNING
        assert event.resource_id == "user456"
    
    def test_log_settings_change(self):
        """Test settings change logging"""
        event = self.audit_service.log_settings_change(
            admin_user_id="admin123",
            admin_email="admin@example.com",
            setting_key="max_upload_size",
            old_value="10MB",
            new_value="50MB",
        )
        
        assert event.event_type == AuditEventType.ADMIN_SETTINGS_CHANGE
        assert event.resource_type == "setting"
        assert event.resource_id == "max_upload_size"
        assert event.details["old_value"] == "10MB"
        assert event.details["new_value"] == "50MB"
    
    def test_log_data_export(self):
        """Test data export logging"""
        event = self.audit_service.log_data_export(
            user_id="user123",
            user_email="test@example.com",
            data_type="users",
            record_count=100,
        )
        
        assert event.event_type == AuditEventType.DATA_EXPORT
        assert event.resource_type == "users"
        assert event.details["record_count"] == 100
    
    def test_log_sensitive_data_access(self):
        """Test sensitive data access logging"""
        event = self.audit_service.log_sensitive_data_access(
            user_id="user123",
            user_email="test@example.com",
            data_type="credit_card",
            data_id="cc123",
            ip_address="192.168.1.1",
        )
        
        assert event.event_type == AuditEventType.DATA_SENSITIVE_ACCESS
        assert event.resource_type == "credit_card"
        assert event.resource_id == "cc123"
    
    def test_log_security_breach_attempt(self):
        """Test security breach attempt logging"""
        event = self.audit_service.log_security_breach_attempt(
            attack_type="SQL Injection",
            ip_address="192.168.1.100",
            user_agent="BadBot/1.0",
            details={"payload": "'; DROP TABLE users; --"},
        )
        
        assert event.event_type == AuditEventType.SECURITY_BREACH_ATTEMPT
        assert event.severity == AuditSeverity.CRITICAL
        assert event.ip_address == "192.168.1.100"
        assert event.details["attack_type"] == "SQL Injection"
    
    def test_log_rate_limit_exceeded(self):
        """Test rate limit exceeded logging"""
        event = self.audit_service.log_rate_limit_exceeded(
            ip_address="192.168.1.1",
            endpoint="/api/login",
            request_count=100,
        )
        
        assert event.event_type == AuditEventType.SECURITY_RATE_LIMIT_EXCEEDED
        assert event.severity == AuditSeverity.WARNING
        assert event.details["endpoint"] == "/api/login"
        assert event.details["request_count"] == 100
    
    def test_log_access_denied(self):
        """Test access denied logging"""
        event = self.audit_service.log_access_denied(
            user_id="user123",
            user_email="test@example.com",
            resource_type="admin_panel",
            resource_id="settings",
            reason="Insufficient permissions",
        )
        
        assert event.event_type == AuditEventType.SECURITY_ACCESS_DENIED
        assert event.severity == AuditSeverity.WARNING
        assert event.details["reason"] == "Insufficient permissions"
    
    def test_get_recent_events(self):
        """Test retrieving recent events"""
        # Log multiple events
        self.audit_service.log_login_success("user1", "user1@example.com")
        self.audit_service.log_login_success("user2", "user2@example.com")
        self.audit_service.log_login_failure("user3@example.com", "Invalid password")
        
        # Get all recent events
        events = self.audit_service.get_recent_events(limit=10)
        assert len(events) == 3
        
        # Filter by event type
        login_events = self.audit_service.get_recent_events(
            limit=10,
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS
        )
        assert len(login_events) == 2
        
        # Filter by user
        user1_events = self.audit_service.get_recent_events(
            limit=10,
            user_id="user1"
        )
        assert len(user1_events) == 1
        assert user1_events[0].user_id == "user1"
    
    def test_get_user_activity(self):
        """Test retrieving user activity"""
        # Log events for specific user
        self.audit_service.log_login_success("user123", "test@example.com")
        self.audit_service.log_password_change("user123", "test@example.com")
        self.audit_service.log_logout("user123", "test@example.com")
        
        # Get user activity
        activity = self.audit_service.get_user_activity("user123", limit=10)
        assert len(activity) == 3
        assert all(e.user_id == "user123" for e in activity)
    
    def test_get_security_events(self):
        """Test retrieving security events"""
        # Log various events
        self.audit_service.log_login_success("user1", "user1@example.com")
        self.audit_service.log_security_breach_attempt("XSS", "192.168.1.100")
        self.audit_service.log_rate_limit_exceeded("192.168.1.1", "/api/test", 100)
        self.audit_service.log_login_failure("user2@example.com", "Invalid password")
        
        # Get security events (should include breach, rate limit, and login failure)
        security_events = self.audit_service.get_security_events(limit=10)
        assert len(security_events) >= 3  # At least the security-specific events
    
    def test_event_to_dict(self):
        """Test converting event to dictionary"""
        event = self.audit_service.log_login_success(
            user_id="user123",
            user_email="test@example.com",
            ip_address="192.168.1.1",
        )
        
        event_dict = event.to_dict()
        assert isinstance(event_dict, dict)
        assert event_dict["event_type"] == "auth.login.success"
        assert event_dict["user_id"] == "user123"
        assert event_dict["user_email"] == "test@example.com"
        assert event_dict["ip_address"] == "192.168.1.1"
    
    def test_global_audit_service(self):
        """Test global audit service instance"""
        service1 = get_audit_service()
        service2 = get_audit_service()
        
        # Should return same instance
        assert service1 is service2
        
        # Log event through global service
        service1.log_login_success("user123", "test@example.com")
        
        # Should be accessible through both references
        assert len(service1.audit_logs) == 1
        assert len(service2.audit_logs) == 1
    
    def test_log_audit_event_convenience_function(self):
        """Test convenience function for logging"""
        event = log_audit_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            action="Test login",
            user_id="user123",
            user_email="test@example.com",
        )
        
        assert event is not None
        assert event.event_type == AuditEventType.AUTH_LOGIN_SUCCESS
        assert event.action == "Test login"
    
    def test_audit_log_memory_limit(self):
        """Test that audit logs are limited in memory"""
        # Log more than 1000 events
        for i in range(1100):
            self.audit_service.log_login_success(f"user{i}", f"user{i}@example.com")
        
        # Should keep only last 1000
        assert len(self.audit_service.audit_logs) == 1000
        
        # Should have most recent events
        last_event = self.audit_service.audit_logs[-1]
        assert last_event.user_id == "user1099"


class TestAuditEventTypes:
    """Test audit event type enumeration"""
    
    def test_auth_event_types(self):
        """Test authentication event types"""
        assert AuditEventType.AUTH_LOGIN_SUCCESS.value == "auth.login.success"
        assert AuditEventType.AUTH_LOGIN_FAILURE.value == "auth.login.failure"
        assert AuditEventType.AUTH_LOGOUT.value == "auth.logout"
        assert AuditEventType.AUTH_REGISTER.value == "auth.register"
    
    def test_user_event_types(self):
        """Test user management event types"""
        assert AuditEventType.USER_CREATE.value == "user.create"
        assert AuditEventType.USER_UPDATE.value == "user.update"
        assert AuditEventType.USER_DELETE.value == "user.delete"
        assert AuditEventType.USER_ROLE_CHANGE.value == "user.role.change"
    
    def test_admin_event_types(self):
        """Test admin action event types"""
        assert AuditEventType.ADMIN_SETTINGS_CHANGE.value == "admin.settings.change"
        assert AuditEventType.ADMIN_ROLE_CREATE.value == "admin.role.create"
    
    def test_security_event_types(self):
        """Test security event types"""
        assert AuditEventType.SECURITY_BREACH_ATTEMPT.value == "security.breach.attempt"
        assert AuditEventType.SECURITY_RATE_LIMIT_EXCEEDED.value == "security.rate_limit.exceeded"


class TestAuditSeverity:
    """Test audit severity levels"""
    
    def test_severity_levels(self):
        """Test all severity levels"""
        assert AuditSeverity.DEBUG.value == "debug"
        assert AuditSeverity.INFO.value == "info"
        assert AuditSeverity.WARNING.value == "warning"
        assert AuditSeverity.ERROR.value == "error"
        assert AuditSeverity.CRITICAL.value == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
