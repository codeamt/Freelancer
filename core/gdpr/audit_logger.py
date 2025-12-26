"""
GDPR Audit Logger

Logs all GDPR-related activities for compliance auditing.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json

from core.utils.logger import get_logger

logger = get_logger(__name__)


class AuditEventType(Enum):
    """GDPR audit event types"""
    CONSENT_GRANTED = "consent_granted"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    DATA_ACCESSED = "data_accessed"
    DATA_MODIFIED = "data_modified"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"
    DATA_PORTED = "data_ported"
    DATA_ANONYMIZED = "data_anonymized"
    DSAR_REQUESTED = "dsar_requested"
    DSAR_COMPLETED = "dsar_completed"
    RETENTION_APPLIED = "retention_applied"
    LEGAL_HOLD_PLACED = "legal_hold_placed"
    LEGAL_HOLD_RELEASED = "legal_hold_released"
    BREACH_OCCURRED = "breach_occurred"
    POLICY_UPDATED = "policy_updated"


class AuditSeverity(Enum):
    """Audit event severity"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GDPRAuditLogger:
    """Logs GDPR compliance events"""
    
    def __init__(self, postgres_adapter):
        self.postgres = postgres_adapter
        self._ensure_tables()
    
    async def _ensure_tables(self):
        """Ensure audit tables exist"""
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_audit_log (
                id SERIAL PRIMARY KEY,
                event_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL DEFAULT 'medium',
                user_id INTEGER,
                session_id VARCHAR(255),
                ip_address INET,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details JSONB DEFAULT '{}',
                affected_records INTEGER DEFAULT 0,
                performed_by VARCHAR(100),
                reference_id VARCHAR(255)
            )
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_gdpr_audit_timestamp 
            ON gdpr_audit_log(timestamp DESC)
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_gdpr_audit_user_id 
            ON gdpr_audit_log(user_id, timestamp)
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_gdpr_audit_event_type 
            ON gdpr_audit_log(event_type, timestamp)
        """)
        
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_data_processing_log (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                processing_type VARCHAR(100) NOT NULL,
                legal_basis VARCHAR(100),
                purpose TEXT,
                data_categories TEXT[],
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                automated BOOLEAN DEFAULT false
            )
        """)
        
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_breach_log (
                id SERIAL PRIMARY KEY,
                breach_id VARCHAR(255) UNIQUE NOT NULL,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                severity VARCHAR(20) NOT NULL,
                affected_users INTEGER,
                data_types TEXT[],
                description TEXT,
                containment_actions TEXT[],
                notification_sent BOOLEAN DEFAULT false,
                notification_date TIMESTAMP,
                resolved_at TIMESTAMP,
                resolution_details TEXT
            )
        """)
    
    async def log_event(self, event_type: AuditEventType, 
                       user_id: int = None, details: Dict = None,
                       severity: AuditSeverity = AuditSeverity.MEDIUM,
                       session_id: str = None, ip_address: str = None,
                       user_agent: str = None, performed_by: str = None,
                       reference_id: str = None, affected_records: int = 0):
        """
        Log a GDPR event
        
        Args:
            event_type: Type of event
            user_id: User ID if applicable
            details: Event details
            severity: Event severity
            session_id: Session ID
            ip_address: IP address
            user_agent: User agent string
            performed_by: Who performed the action
            reference_id: Reference ID for tracking
            affected_records: Number of records affected
        """
        await self.postgres.execute("""
            INSERT INTO gdpr_audit_log 
            (event_type, severity, user_id, session_id, ip_address,
             user_agent, details, performed_by, reference_id, affected_records)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, event_type.value, severity.value, user_id, session_id,
              ip_address, user_agent, json.dumps(details or {}),
              performed_by, reference_id, affected_records)
        
        # Also log to application logger for critical events
        if severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
            logger.warning(
                f"GDPR Audit Event: {event_type.value} - User: {user_id} - "
                f"Details: {json.dumps(details or {})}"
            )
    
    async def log_consent(self, user_id: int, consent_type: str, 
                         action: str, metadata: Dict = None):
        """Log consent-related event"""
        event_type = (
            AuditEventType.CONSENT_GRANTED if action == "granted"
            else AuditEventType.CONSENT_WITHDRAWN
        )
        
        await self.log_event(
            event_type=event_type,
            user_id=user_id,
            details={
                "consent_type": consent_type,
                "action": action,
                "metadata": metadata or {}
            },
            severity=AuditSeverity.MEDIUM
        )
    
    async def log_data_access(self, user_id: int, accessed_by: str,
                            data_types: List[str], purpose: str = None):
        """Log data access"""
        await self.log_event(
            event_type=AuditEventType.DATA_ACCESSED,
            user_id=user_id,
            details={
                "accessed_by": accessed_by,
                "data_types": data_types,
                "purpose": purpose
            },
            severity=AuditSeverity.LOW
        )
    
    async def log_data_modification(self, user_id: int, modified_by: str,
                                  changes: Dict[str, Any]):
        """Log data modification"""
        await self.log_event(
            event_type=AuditEventType.DATA_MODIFIED,
            user_id=user_id,
            details={
                "modified_by": modified_by,
                "changes": changes
            },
            severity=AuditSeverity.MEDIUM,
            affected_records=len(changes)
        )
    
    async def log_data_deletion(self, user_id: int, deleted_by: str,
                              data_types: List[str], reason: str = None):
        """Log data deletion"""
        await self.log_event(
            event_type=AuditEventType.DATA_DELETED,
            user_id=user_id,
            details={
                "deleted_by": deleted_by,
                "data_types": data_types,
                "reason": reason
            },
            severity=AuditSeverity.HIGH
        )
    
    async def log_data_export(self, user_id: int, exported_by: str,
                            format: str, record_count: int):
        """Log data export"""
        await self.log_event(
            event_type=AuditEventType.DATA_EXPORTED,
            user_id=user_id,
            details={
                "exported_by": exported_by,
                "format": format,
                "record_count": record_count
            },
            severity=AuditSeverity.MEDIUM,
            affected_records=record_count
        )
    
    async def log_data_anonymization(self, user_id: int, anonymized_by: str,
                                   details: Dict = None):
        """Log data anonymization"""
        await self.log_event(
            event_type=AuditEventType.DATA_ANONYMIZED,
            user_id=user_id,
            details={
                "anonymized_by": anonymized_by,
                **(details or {})
            },
            severity=AuditSeverity.HIGH
        )
    
    async def log_dsar(self, user_id: int, request_type: str, 
                      status: str, details: Dict = None):
        """Log DSAR request"""
        await self.log_event(
            event_type=AuditEventType.DSAR_REQUESTED if status == "requested"
            else AuditEventType.DSAR_COMPLETED,
            user_id=user_id,
            details={
                "request_type": request_type,
                "status": status,
                **(details or {})
            },
            severity=AuditSeverity.HIGH
        )
    
    async def log_processing_activity(self, user_id: int, processing_type: str,
                                    legal_basis: str, purpose: str,
                                    data_categories: List[str],
                                    expires_at: datetime = None):
        """Log data processing activity"""
        await self.postgres.execute("""
            INSERT INTO gdpr_data_processing_log 
            (user_id, processing_type, legal_basis, purpose,
             data_categories, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, user_id, processing_type, legal_basis, purpose,
              data_categories, expires_at)
    
    async def log_breach(self, breach_id: str, severity: AuditSeverity,
                        affected_users: int, data_types: List[str],
                        description: str, containment_actions: List[str] = None):
        """Log data breach"""
        await self.postgres.execute("""
            INSERT INTO gdpr_breach_log 
            (breach_id, severity, affected_users, data_types,
             description, containment_actions)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, breach_id, severity.value, affected_users, data_types,
              description, containment_actions or [])
        
        # Also log to audit log
        await self.log_event(
            event_type=AuditEventType.BREACH_OCCURRED,
            details={
                "breach_id": breach_id,
                "severity": severity.value,
                "affected_users": affected_users,
                "data_types": data_types,
                "description": description
            },
            severity=severity
        )
    
    async def update_breach(self, breach_id: str, notification_sent: bool = False,
                          resolved_at: datetime = None, 
                          resolution_details: str = None):
        """Update breach record"""
        updates = ["notification_sent = $2"]
        values = [breach_id, notification_sent]
        param_count = 3
        
        if resolved_at:
            updates.append(f"resolved_at = ${param_count}")
            values.append(resolved_at)
            param_count += 1
        
        if resolution_details:
            updates.append(f"resolution_details = ${param_count}")
            values.append(resolution_details)
            param_count += 1
        
        values.insert(0, f"UPDATE gdpr_breach_log SET {', '.join(updates)} WHERE breach_id = $1")
        
        await self.postgres.execute(*values)
    
    async def log_retention_applied(self, applied_by: str, results: Dict[str, int]):
        """Log retention policy application"""
        await self.log_event(
            event_type=AuditEventType.RETENTION_APPLIED,
            details={
                "applied_by": applied_by,
                "results": results
            },
            severity=AuditSeverity.MEDIUM,
            affected_records=sum(results.values())
        )
    
    async def get_user_audit_trail(self, user_id: int, 
                                 start_date: datetime = None,
                                 end_date: datetime = None) -> List[Dict]:
        """
        Get audit trail for a user
        
        Args:
            user_id: User ID
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of audit events
        """
        query = """
            SELECT * FROM gdpr_audit_log 
            WHERE user_id = $1
        """
        params = [user_id]
        
        if start_date:
            query += " AND timestamp >= $2"
            params.append(start_date)
        
        if end_date:
            query += f" AND timestamp <= ${len(params) + 1}"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC"
        
        return await self.postgres.fetch_all(query, *params)
    
    async def get_processing_activities(self, user_id: int = None) -> List[Dict]:
        """
        Get processing activities
        
        Args:
            user_id: Filter by user ID
            
        Returns:
            List of processing activities
        """
        query = """
            SELECT * FROM gdpr_data_processing_log 
            WHERE 1=1
        """
        params = []
        
        if user_id:
            query += " AND user_id = $1"
            params.append(user_id)
        
        query += " ORDER BY timestamp DESC"
        
        return await self.postgres.fetch_all(query, *params)
    
    async def get_breach_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Get breach report
        
        Args:
            days: Number of days to look back
            
        Returns:
            Breach statistics
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        breaches = await self.postgres.fetch_all("""
            SELECT * FROM gdpr_breach_log 
            WHERE discovered_at >= $1
            ORDER BY discovered_at DESC
        """, cutoff)
        
        # Statistics
        total_breaches = len(breaches)
        resolved = len([b for b in breaches if b['resolved_at']])
        high_severity = len([b for b in breaches if b['severity'] in ['high', 'critical']])
        total_affected = sum(b['affected_users'] or 0 for b in breaches)
        
        return {
            "period_days": days,
            "total_breaches": total_breaches,
            "resolved_breaches": resolved,
            "high_severity_breaches": high_severity,
            "total_affected_users": total_affected,
            "breaches": [dict(b) for b in breaches]
        }
    
    async def generate_compliance_report(self, start_date: datetime = None,
                                       end_date: datetime = None) -> Dict[str, Any]:
        """
        Generate GDPR compliance report
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Compliance report
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get audit statistics
        audit_stats = await self.postgres.fetch_one("""
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_events,
                COUNT(CASE WHEN severity = 'high' THEN 1 END) as high_events
            FROM gdpr_audit_log 
            WHERE timestamp BETWEEN $1 AND $2
        """, start_date, end_date)
        
        # Get event type breakdown
        events_by_type = await self.postgres.fetch_all("""
            SELECT event_type, COUNT(*) as count
            FROM gdpr_audit_log 
            WHERE timestamp BETWEEN $1 AND $2
            GROUP BY event_type
            ORDER BY count DESC
        """, start_date, end_date)
        
        # Get DSAR statistics
        dsar_stats = await self.postgres.fetch_one("""
            SELECT 
                COUNT(*) as total_requests,
                COUNT(CASE WHEN details->>'status' = 'completed' THEN 1 END) as completed,
                AVG(EXTRACT(EPOCH FROM (completed_at - requested_at))/86400) as avg_days
            FROM gdpr_audit_log 
            WHERE event_type IN ('dsar_requested', 'dsar_completed')
            AND timestamp BETWEEN $1 AND $2
        """, start_date, end_date)
        
        # Get processing activities
        processing = await self.postgres.fetch_all("""
            SELECT processing_type, COUNT(*) as count
            FROM gdpr_data_processing_log 
            WHERE timestamp BETWEEN $1 AND $2
            GROUP BY processing_type
        """, start_date, end_date)
        
        return {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "audit_summary": dict(audit_stats),
            "events_by_type": [dict(e) for e in events_by_type],
            "dsar_summary": dict(dsar_stats),
            "processing_activities": [dict(p) for p in processing]
        }
