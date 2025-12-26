"""
Role Audit Logging Service

Tracks all role assignments, changes, and provides audit trail for compliance.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from core.db.repositories.user_repository import UserRepository
from core.services.auth.models import UserRole
from core.utils.logger import get_logger

logger = get_logger(__name__)


class RoleAuditService:
    """Service for logging role changes and maintaining audit trails"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository
    
    async def log_role_change(
        self,
        user_id: int,
        action: str,
        previous_roles: Optional[List[UserRole]] = None,
        new_roles: Optional[List[UserRole]] = None,
        changed_by: Optional[int] = None,
        reason: Optional[str] = None,
        request: Optional[Any] = None
    ) -> bool:
        """
        Log a role change to the audit trail.
        
        Args:
            user_id: ID of the user whose roles are changing
            action: Type of change ('assign', 'revoke', 'bulk_update')
            previous_roles: List of roles before the change
            new_roles: List of roles after the change
            changed_by: ID of the admin making the change
            reason: Reason for the role change
            request: Request object for IP/user agent tracking
            
        Returns:
            True if logged successfully
        """
        try:
            # Extract request metadata
            ip_address = None
            user_agent = None
            
            if request:
                ip_address = getattr(request, 'client', None)
                if ip_address:
                    ip_address = getattr(ip_address, 'host', None)
                user_agent = getattr(request, 'headers', {}).get('user-agent')
            
            # Convert roles to strings for storage
            prev_roles_str = [r.value for r in previous_roles] if previous_roles else None
            new_roles_str = [r.value for r in new_roles] if new_roles else None
            
            # Insert audit record
            await self.user_repo.execute_query("""
                INSERT INTO role_audit_log (
                    user_id, changed_by, action, previous_roles, new_roles,
                    reason, ip_address, user_agent, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
            """, user_id, changed_by, action, prev_roles_str, new_roles_str,
                reason, ip_address, user_agent)
            
            logger.info(f"Role audit logged: user_id={user_id}, action={action}, by={changed_by}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log role audit: {e}")
            return False
    
    async def get_role_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get the role change history for a user.
        
        Args:
            user_id: User ID to get history for
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of audit records
        """
        try:
            records = await self.user_repo.fetch_all("""
                SELECT 
                    ral.*,
                    u.email as changed_by_email,
                    u2.email as user_email
                FROM role_audit_log ral
                LEFT JOIN users u ON ral.changed_by = u.id
                LEFT JOIN users u2 ON ral.user_id = u2.id
                WHERE ral.user_id = $1
                ORDER BY ral.created_at DESC
                LIMIT $2 OFFSET $3
            """, user_id, limit, offset)
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to get role history: {e}")
            return []
    
    async def get_recent_role_changes(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get recent role changes across all users.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of records
            
        Returns:
            List of recent audit records
        """
        try:
            records = await self.user_repo.fetch_all("""
                SELECT 
                    ral.*,
                    u.email as changed_by_email,
                    u2.email as user_email
                FROM role_audit_log ral
                LEFT JOIN users u ON ral.changed_by = u.id
                LEFT JOIN users u2 ON ral.user_id = u2.id
                WHERE ral.created_at >= NOW() - INTERVAL '{hours} hours'
                ORDER BY ral.created_at DESC
                LIMIT $1
            """.format(hours=hours), limit)
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to get recent role changes: {e}")
            return []
    
    async def get_role_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get statistics about role changes.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Get total changes
            total_changes = await self.user_repo.fetch_one("""
                SELECT COUNT(*) as count
                FROM role_audit_log
                WHERE created_at >= NOW() - INTERVAL '{days} days'
            """.format(days=days))
            
            # Get changes by action type
            changes_by_action = await self.user_repo.fetch_all("""
                SELECT action, COUNT(*) as count
                FROM role_audit_log
                WHERE created_at >= NOW() - INTERVAL '{days} days'
                GROUP BY action
                ORDER BY count DESC
            """.format(days=days))
            
            # Get top changers
            top_changers = await self.user_repo.fetch_all("""
                SELECT 
                    u.email,
                    COUNT(*) as change_count
                FROM role_audit_log ral
                JOIN users u ON ral.changed_by = u.id
                WHERE ral.created_at >= NOW() - INTERVAL '{days} days'
                GROUP BY u.email
                ORDER BY change_count DESC
                LIMIT 10
            """.format(days=days))
            
            return {
                "total_changes": total_changes['count'] if total_changes else 0,
                "changes_by_action": dict((r['action'], r['count']) for r in changes_by_action),
                "top_changers": top_changers,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get role statistics: {e}")
            return {}
    
    async def detect_suspicious_activity(
        self,
        hours: int = 1
    ) -> List[Dict]:
        """
        Detect potentially suspicious role changes.
        
        Args:
            hours: Time window to check
            
        Returns:
            List of suspicious activities
        """
        try:
            suspicious = []
            
            # Check for rapid role changes
            rapid_changes = await self.user_repo.fetch_all("""
                SELECT user_id, COUNT(*) as change_count
                FROM role_audit_log
                WHERE created_at >= NOW() - INTERVAL '{hours} hours'
                GROUP BY user_id
                HAVING COUNT(*) > 5
            """.format(hours=hours))
            
            for record in rapid_changes:
                user = await self.user_repo.get_by_id(record['user_id'])
                suspicious.append({
                    "type": "rapid_changes",
                    "user_id": record['user_id'],
                    "user_email": user['email'] if user else 'Unknown',
                    "change_count": record['change_count'],
                    "message": f"User had {record['change_count']} role changes in {hours} hour(s)"
                })
            
            # Check for self-privilege escalation
            self_escalation = await self.user_repo.fetch_all("""
                SELECT ral.*
                FROM role_audit_log ral
                WHERE ral.changed_by = ral.user_id
                AND ral.created_at >= NOW() - INTERVAL '{hours} hours'
                AND ral.action = 'assign'
            """.format(hours=hours))
            
            for record in self_escalation:
                # Check if admin roles were assigned
                if record['new_roles']:
                    for role in record['new_roles']:
                        if role in ['admin', 'super_admin', 'site_admin']:
                            user = await self.user_repo.get_by_id(record['user_id'])
                            suspicious.append({
                                "type": "self_escalation",
                                "user_id": record['user_id'],
                                "user_email": user['email'] if user else 'Unknown',
                                "role_assigned": role,
                                "message": f"User assigned admin role to themselves"
                            })
                            break
            
            return suspicious
            
        except Exception as e:
            logger.error(f"Failed to detect suspicious activity: {e}")
            return []
