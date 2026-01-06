"""
Audit Logging Service

Provides comprehensive audit logging for security, compliance, and debugging.
Logs authentication events, admin actions, sensitive data access, and system changes.
"""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, asdict
from core.utils.logger import get_logger

logger = get_logger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_REGISTER = "auth.register"
    AUTH_PASSWORD_CHANGE = "auth.password.change"
    AUTH_PASSWORD_RESET = "auth.password.reset"
    AUTH_TOKEN_REFRESH = "auth.token.refresh"
    AUTH_TOKEN_REVOKE = "auth.token.revoke"
    
    # User management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_CHANGE = "user.role.change"
    USER_PERMISSION_CHANGE = "user.permission.change"
    USER_DEACTIVATE = "user.deactivate"
    USER_REACTIVATE = "user.reactivate"
    
    # Admin actions
    ADMIN_SETTINGS_CHANGE = "admin.settings.change"
    ADMIN_USER_IMPERSONATE = "admin.user.impersonate"
    ADMIN_ROLE_CREATE = "admin.role.create"
    ADMIN_ROLE_UPDATE = "admin.role.update"
    ADMIN_ROLE_DELETE = "admin.role.delete"
    ADMIN_PERMISSION_GRANT = "admin.permission.grant"
    ADMIN_PERMISSION_REVOKE = "admin.permission.revoke"
    
    # Data access
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    DATA_DELETE = "data.delete"
    DATA_SENSITIVE_ACCESS = "data.sensitive.access"
    
    # System events
    SYSTEM_CONFIG_CHANGE = "system.config.change"
    SYSTEM_BACKUP_CREATE = "system.backup.create"
    SYSTEM_BACKUP_RESTORE = "system.backup.restore"
    SYSTEM_MAINTENANCE_START = "system.maintenance.start"
    SYSTEM_MAINTENANCE_END = "system.maintenance.end"
    
    # Security events
    SECURITY_BREACH_ATTEMPT = "security.breach.attempt"
    SECURITY_RATE_LIMIT_EXCEEDED = "security.rate_limit.exceeded"
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious.activity"
    SECURITY_ACCESS_DENIED = "security.access.denied"
    
    # GDPR-specific events (merged from core/gdpr/audit_logger.py)
    GDPR_CONSENT_GRANTED = "gdpr.consent.granted"
    GDPR_CONSENT_WITHDRAWN = "gdpr.consent.withdrawn"
    GDPR_DATA_ACCESSED = "gdpr.data.accessed"
    GDPR_DATA_MODIFIED = "gdpr.data.modified"
    GDPR_DATA_DELETED = "gdpr.data.deleted"
    GDPR_DATA_EXPORTED = "gdpr.data.exported"
    GDPR_DATA_PORTED = "gdpr.data.ported"
    GDPR_DATA_ANONYMIZED = "gdpr.data.anonymized"
    GDPR_DSAR_REQUESTED = "gdpr.dsar.requested"
    GDPR_DSAR_COMPLETED = "gdpr.dsar.completed"
    GDPR_RETENTION_APPLIED = "gdpr.retention.applied"
    GDPR_LEGAL_HOLD_PLACED = "gdpr.legal_hold.placed"
    GDPR_LEGAL_HOLD_RELEASED = "gdpr.legal_hold.released"
    GDPR_BREACH_OCCURRED = "gdpr.breach.occurred"
    GDPR_POLICY_UPDATED = "gdpr.policy.updated"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[str]
    user_email: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    timestamp: str
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "details": self.details,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "request_id": self.request_id,
        }


class AuditService:
    """
    Audit logging service for tracking security and compliance events.
    
    Features:
    - Structured audit logging
    - Event categorization and severity
    - User and session tracking
    - IP and user agent logging
    - Searchable audit trail
    - Database persistence (PostgreSQL)
    - GDPR-specific event handling
    """
    
    def __init__(self, storage_backend: str = "database", postgres_adapter=None):
        """
        Initialize audit service.
        
        Args:
            storage_backend: Where to store audit logs (database, file, both)
            postgres_adapter: PostgreSQL adapter for database persistence
        """
        self.storage_backend = storage_backend
        self.postgres = postgres_adapter
        self.audit_logs: List[AuditEvent] = []  # In-memory cache
        
        # Initialize database tables if adapter provided
        if self.postgres:
            self._ensure_tables()
    
    async def _ensure_tables(self):
        """Ensure audit tables exist in database"""
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                event_type VARCHAR(100) NOT NULL,
                severity VARCHAR(20) NOT NULL DEFAULT 'info',
                user_id VARCHAR(255),
                user_email VARCHAR(255),
                ip_address INET,
                user_agent TEXT,
                resource_type VARCHAR(100),
                resource_id VARCHAR(255),
                action TEXT NOT NULL,
                details JSONB DEFAULT '{}',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id VARCHAR(255),
                request_id VARCHAR(255)
            )
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp 
            ON audit_log(timestamp DESC)
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_log_user_id 
            ON audit_log(user_id, timestamp)
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_log_event_type 
            ON audit_log(event_type, timestamp)
        """)
        
    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditEvent:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            action: Human-readable action description
            user_id: ID of user performing action
            user_email: Email of user performing action
            ip_address: IP address of request
            user_agent: User agent string
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional event details
            severity: Event severity level
            session_id: Session ID
            request_id: Request ID for tracing
            
        Returns:
            Created audit event
        """
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            request_id=request_id,
        )
        
        # Store event
        if self.postgres:
            # Async storage - need to handle this properly
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, create a task
                    asyncio.create_task(self._store_event(event))
                else:
                    # If we're in sync context, run the coroutine
                    loop.run_until_complete(self._store_event(event))
            except RuntimeError:
                # No event loop, use sync fallback
                self.audit_logs.append(event)
        else:
            # Sync fallback for in-memory only
            self.audit_logs.append(event)
            
            # Keep only last 1000 events in memory
            if len(self.audit_logs) > 1000:
                self.audit_logs = self.audit_logs[-1000:]
        
        # Log to application logger
        log_message = self._format_log_message(event)
        if severity == AuditSeverity.CRITICAL:
            logger.critical(log_message)
        elif severity == AuditSeverity.ERROR:
            logger.error(log_message)
        elif severity == AuditSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        return event
    
    async def _store_event(self, event: AuditEvent):
        """Store audit event to configured backend"""
        # Add to in-memory cache
        self.audit_logs.append(event)
        
        # Keep only last 1000 events in memory
        if len(self.audit_logs) > 1000:
            self.audit_logs = self.audit_logs[-1000:]
        
        # Store to database if available
        if self.postgres:
            await self.postgres.execute("""
                INSERT INTO audit_log 
                (event_type, severity, user_id, user_email, ip_address, user_agent,
                 resource_type, resource_id, action, details, timestamp, session_id, request_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """, 
                event.event_type.value,
                event.severity.value,
                event.user_id,
                event.user_email,
                event.ip_address,
                event.user_agent,
                event.resource_type,
                event.resource_id,
                event.action,
                json.dumps(event.details),
                event.timestamp,
                event.session_id,
                event.request_id
            )
    
    def _format_log_message(self, event: AuditEvent) -> str:
        """Format audit event for logging"""
        parts = [
            f"[AUDIT]",
            f"type={event.event_type.value}",
            f"action={event.action}",
        ]
        
        if event.user_id:
            parts.append(f"user_id={event.user_id}")
        if event.user_email:
            parts.append(f"user_email={event.user_email}")
        if event.ip_address:
            parts.append(f"ip={event.ip_address}")
        if event.resource_type:
            parts.append(f"resource={event.resource_type}:{event.resource_id}")
        
        if event.details:
            parts.append(f"details={json.dumps(event.details)}")
        
        return " ".join(parts)
    
    # Authentication event helpers
    
    def log_login_success(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Log successful login"""
        return self.log_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            action=f"User {user_email} logged in successfully",
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            severity=AuditSeverity.INFO,
        )
    
    def log_login_failure(
        self,
        email: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log failed login attempt"""
        return self.log_event(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            action=f"Failed login attempt for {email}",
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"reason": reason},
            severity=AuditSeverity.WARNING,
        )
    
    def log_logout(
        self,
        user_id: str,
        user_email: str,
        session_id: Optional[str] = None,
    ):
        """Log user logout"""
        return self.log_event(
            event_type=AuditEventType.AUTH_LOGOUT,
            action=f"User {user_email} logged out",
            user_id=user_id,
            user_email=user_email,
            session_id=session_id,
            severity=AuditSeverity.INFO,
        )
    
    def log_password_change(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
    ):
        """Log password change"""
        return self.log_event(
            event_type=AuditEventType.AUTH_PASSWORD_CHANGE,
            action=f"User {user_email} changed password",
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            severity=AuditSeverity.INFO,
        )
    
    # User management event helpers
    
    def log_user_create(
        self,
        admin_user_id: str,
        admin_email: str,
        created_user_id: str,
        created_user_email: str,
        roles: List[str],
    ):
        """Log user creation"""
        return self.log_event(
            event_type=AuditEventType.USER_CREATE,
            action=f"Admin {admin_email} created user {created_user_email}",
            user_id=admin_user_id,
            user_email=admin_email,
            resource_type="user",
            resource_id=created_user_id,
            details={"created_user_email": created_user_email, "roles": roles},
            severity=AuditSeverity.INFO,
        )
    
    def log_user_role_change(
        self,
        admin_user_id: str,
        admin_email: str,
        target_user_id: str,
        target_user_email: str,
        old_roles: List[str],
        new_roles: List[str],
    ):
        """Log user role change"""
        return self.log_event(
            event_type=AuditEventType.USER_ROLE_CHANGE,
            action=f"Admin {admin_email} changed roles for {target_user_email}",
            user_id=admin_user_id,
            user_email=admin_email,
            resource_type="user",
            resource_id=target_user_id,
            details={
                "target_user_email": target_user_email,
                "old_roles": old_roles,
                "new_roles": new_roles,
            },
            severity=AuditSeverity.WARNING,
        )
    
    def log_user_delete(
        self,
        admin_user_id: str,
        admin_email: str,
        deleted_user_id: str,
        deleted_user_email: str,
    ):
        """Log user deletion"""
        return self.log_event(
            event_type=AuditEventType.USER_DELETE,
            action=f"Admin {admin_email} deleted user {deleted_user_email}",
            user_id=admin_user_id,
            user_email=admin_email,
            resource_type="user",
            resource_id=deleted_user_id,
            details={"deleted_user_email": deleted_user_email},
            severity=AuditSeverity.WARNING,
        )
    
    # Admin action helpers
    
    def log_settings_change(
        self,
        admin_user_id: str,
        admin_email: str,
        setting_key: str,
        old_value: Any,
        new_value: Any,
    ):
        """Log settings change"""
        return self.log_event(
            event_type=AuditEventType.ADMIN_SETTINGS_CHANGE,
            action=f"Admin {admin_email} changed setting {setting_key}",
            user_id=admin_user_id,
            user_email=admin_email,
            resource_type="setting",
            resource_id=setting_key,
            details={
                "setting_key": setting_key,
                "old_value": str(old_value),
                "new_value": str(new_value),
            },
            severity=AuditSeverity.INFO,
        )
    
    # Data access helpers
    
    def log_data_export(
        self,
        user_id: str,
        user_email: str,
        data_type: str,
        record_count: int,
    ):
        """Log data export"""
        return self.log_event(
            event_type=AuditEventType.DATA_EXPORT,
            action=f"User {user_email} exported {record_count} {data_type} records",
            user_id=user_id,
            user_email=user_email,
            resource_type=data_type,
            details={"record_count": record_count},
            severity=AuditSeverity.INFO,
        )
    
    def log_sensitive_data_access(
        self,
        user_id: str,
        user_email: str,
        data_type: str,
        data_id: str,
        ip_address: Optional[str] = None,
    ):
        """Log access to sensitive data"""
        return self.log_event(
            event_type=AuditEventType.DATA_SENSITIVE_ACCESS,
            action=f"User {user_email} accessed sensitive {data_type}",
            user_id=user_id,
            user_email=user_email,
            resource_type=data_type,
            resource_id=data_id,
            ip_address=ip_address,
            severity=AuditSeverity.INFO,
        )
    
    # Security event helpers
    
    def log_security_breach_attempt(
        self,
        attack_type: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log security breach attempt"""
        event_details = {"attack_type": attack_type}
        if details:
            event_details.update(details)
        
        return self.log_event(
            event_type=AuditEventType.SECURITY_BREACH_ATTEMPT,
            action=f"Security breach attempt detected: {attack_type}",
            ip_address=ip_address,
            user_agent=user_agent,
            details=event_details,
            severity=AuditSeverity.CRITICAL,
        )
    
    def log_rate_limit_exceeded(
        self,
        ip_address: str,
        endpoint: str,
        request_count: int,
    ):
        """Log rate limit exceeded"""
        return self.log_event(
            event_type=AuditEventType.SECURITY_RATE_LIMIT_EXCEEDED,
            action=f"Rate limit exceeded for {endpoint}",
            ip_address=ip_address,
            details={"endpoint": endpoint, "request_count": request_count},
            severity=AuditSeverity.WARNING,
        )
    
    def log_access_denied(
        self,
        user_id: Optional[str],
        user_email: Optional[str],
        resource_type: str,
        resource_id: str,
        reason: str,
    ):
        """Log access denied"""
        return self.log_event(
            event_type=AuditEventType.SECURITY_ACCESS_DENIED,
            action=f"Access denied to {resource_type}:{resource_id}",
            user_id=user_id,
            user_email=user_email,
            resource_type=resource_type,
            resource_id=resource_id,
            details={"reason": reason},
            severity=AuditSeverity.WARNING,
        )
    
    # Query methods
    
    def get_recent_events(
        self,
        limit: int = 100,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
    ) -> List[AuditEvent]:
        """
        Get recent audit events with optional filtering.
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type
            user_id: Filter by user ID
            severity: Filter by severity
            
        Returns:
            List of audit events
        """
        events = self.audit_logs
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        if severity:
            events = [e for e in events if e.severity == severity]
        
        # Return most recent events
        return events[-limit:]
    
    def get_user_activity(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[AuditEvent]:
        """Get recent activity for a specific user"""
        return self.get_recent_events(limit=limit, user_id=user_id)
    
    def get_security_events(
        self,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Get recent security-related events"""
        security_events = [
            e for e in self.audit_logs
            if e.event_type.value.startswith("security.")
            or e.severity in [AuditSeverity.WARNING, AuditSeverity.ERROR, AuditSeverity.CRITICAL]
        ]
        return security_events[-limit:]
    
    # GDPR-specific methods (merged from core/gdpr/audit_logger.py)
    
    def log_gdpr_consent(self, user_id: str, consent_type: str, 
                        action: str, metadata: Dict = None):
        """Log GDPR consent event"""
        event_type = (
            AuditEventType.GDPR_CONSENT_GRANTED if action == "granted"
            else AuditEventType.GDPR_CONSENT_WITHDRAWN
        )
        
        return self.log_event(
            event_type=event_type,
            action=f"User {action} {consent_type} consent",
            user_id=user_id,
            details={
                "consent_type": consent_type,
                "action": action,
                "metadata": metadata or {}
            },
            severity=AuditSeverity.INFO
        )
    
    def log_gdpr_data_access(self, user_id: str, accessed_by: str,
                            data_types: List[str], purpose: str = None):
        """Log GDPR data access"""
        return self.log_event(
            event_type=AuditEventType.GDPR_DATA_ACCESSED,
            action=f"GDPR data accessed for user {user_id}",
            user_id=accessed_by,
            resource_type="user_data",
            resource_id=user_id,
            details={
                "data_subject_id": user_id,
                "data_types": data_types,
                "purpose": purpose
            },
            severity=AuditSeverity.INFO
        )
    
    def log_gdpr_data_modification(self, user_id: str, modified_by: str,
                                  changes: Dict[str, Any]):
        """Log GDPR data modification"""
        return self.log_event(
            event_type=AuditEventType.GDPR_DATA_MODIFIED,
            action=f"GDPR data modified for user {user_id}",
            user_id=modified_by,
            resource_type="user_data",
            resource_id=user_id,
            details={
                "data_subject_id": user_id,
                "modified_by": modified_by,
                "changes": changes
            },
            severity=AuditSeverity.WARNING
        )
    
    def log_gdpr_data_deletion(self, user_id: str, deleted_by: str,
                              data_types: List[str], reason: str = None):
        """Log GDPR data deletion"""
        return self.log_event(
            event_type=AuditEventType.GDPR_DATA_DELETED,
            action=f"GDPR data deleted for user {user_id}",
            user_id=deleted_by,
            resource_type="user_data",
            resource_id=user_id,
            details={
                "data_subject_id": user_id,
                "deleted_by": deleted_by,
                "data_types": data_types,
                "reason": reason
            },
            severity=AuditSeverity.WARNING
        )
    
    def log_gdpr_data_export(self, user_id: str, exported_by: str,
                            format: str, record_count: int):
        """Log GDPR data export"""
        return self.log_event(
            event_type=AuditEventType.GDPR_DATA_EXPORTED,
            action=f"GDPR data exported for user {user_id}",
            user_id=exported_by,
            resource_type="user_data",
            resource_id=user_id,
            details={
                "data_subject_id": user_id,
                "exported_by": exported_by,
                "format": format,
                "record_count": record_count
            },
            severity=AuditSeverity.INFO
        )
    
    def log_gdpr_data_anonymization(self, user_id: str, anonymized_by: str,
                                   details: Dict = None):
        """Log GDPR data anonymization"""
        return self.log_event(
            event_type=AuditEventType.GDPR_DATA_ANONYMIZED,
            action=f"GDPR data anonymized for user {user_id}",
            user_id=anonymized_by,
            resource_type="user_data",
            resource_id=user_id,
            details={
                "data_subject_id": user_id,
                "anonymized_by": anonymized_by,
                **(details or {})
            },
            severity=AuditSeverity.WARNING
        )
    
    def log_gdpr_dsar(self, user_id: str, request_type: str, 
                      status: str, details: Dict = None):
        """Log GDPR DSAR request"""
        event_type = (
            AuditEventType.GDPR_DSAR_REQUESTED if status == "requested"
            else AuditEventType.GDPR_DSAR_COMPLETED
        )
        
        return self.log_event(
            event_type=event_type,
            action=f"GDPR DSAR {status} for user {user_id}",
            user_id=user_id,
            resource_type="dsar",
            details={
                "data_subject_id": user_id,
                "request_type": request_type,
                "status": status,
                **(details or {})
            },
            severity=AuditSeverity.WARNING
        )
    
    def log_gdpr_breach(self, breach_id: str, affected_users: int, 
                        data_types: List[str], description: str):
        """Log GDPR data breach"""
        return self.log_event(
            event_type=AuditEventType.GDPR_BREACH_OCCURRED,
            action=f"GDPR data breach: {breach_id}",
            resource_type="breach",
            resource_id=breach_id,
            details={
                "breach_id": breach_id,
                "affected_users": affected_users,
                "data_types": data_types,
                "description": description
            },
            severity=AuditSeverity.CRITICAL
        )


# Global audit service instance
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """Get global audit service instance"""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service


def log_audit_event(
    event_type: AuditEventType,
    action: str,
    **kwargs
) -> AuditEvent:
    """Convenience function to log audit event"""
    audit_service = get_audit_service()
    return audit_service.log_event(event_type, action, **kwargs)
