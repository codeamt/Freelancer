"""
Data Retention Manager

Manages data retention policies and automatic cleanup.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json

from core.utils.logger import get_logger
from .anonymizer import DataAnonymizer

logger = get_logger(__name__)


class RetentionPolicy(Enum):
    """Data retention policies"""
    IMMEDIATE = "immediate"  # Delete immediately
    DAYS_30 = "30_days"
    DAYS_90 = "90_days"
    DAYS_180 = "180_days"
    DAYS_365 = "365_days"
    YEARS_1 = "1_year"
    YEARS_2 = "2_years"
    YEARS_5 = "5_years"
    YEARS_7 = "7_years"
    YEARS_10 = "10_years"
    INDEFINITE = "indefinite"  # Keep forever
    LEGAL_HOLD = "legal_hold"  # Keep due to legal requirements


class DataCategory(Enum):
    """Categories of data for retention"""
    USER_PROFILE = "user_profile"
    USER_ACTIVITY = "user_activity"
    COMMUNICATION = "communication"
    TRANSACTIONS = "transactions"
    ANALYTICS = "analytics"
    LOGS = "logs"
    SESSIONS = "sessions"
    DEVICES = "devices"
    COOKIES = "cookies"
    CONSENTS = "consents"
    BACKUPS = "backups"


class RetentionRule:
    """Retention rule for data"""
    
    def __init__(self, category: DataCategory, policy: RetentionPolicy,
                 action: str = "delete", conditions: Dict = None):
        self.category = category
        self.policy = policy
        self.action = action  # delete, anonymize, archive
        self.conditions = conditions or {}
    
    def get_retention_date(self, from_date: datetime = None) -> datetime:
        """Calculate retention date based on policy"""
        if from_date is None:
            from_date = datetime.utcnow()
        
        if self.policy == RetentionPolicy.IMMEDIATE:
            return from_date
        elif self.policy == RetentionPolicy.DAYS_30:
            return from_date + timedelta(days=30)
        elif self.policy == RetentionPolicy.DAYS_90:
            return from_date + timedelta(days=90)
        elif self.policy == RetentionPolicy.DAYS_180:
            return from_date + timedelta(days=180)
        elif self.policy == RetentionPolicy.DAYS_365:
            return from_date + timedelta(days=365)
        elif self.policy == RetentionPolicy.YEARS_1:
            return from_date + timedelta(days=365)
        elif self.policy == RetentionPolicy.YEARS_2:
            return from_date + timedelta(days=730)
        elif self.policy == RetentionPolicy.YEARS_5:
            return from_date + timedelta(days=1825)
        elif self.policy == RetentionPolicy.YEARS_7:
            return from_date + timedelta(days=2555)
        elif self.policy == RetentionPolicy.YEARS_10:
            return from_date + timedelta(days=3650)
        elif self.policy in [RetentionPolicy.INDEFINITE, RetentionPolicy.LEGAL_HOLD]:
            return datetime.max
        
        return from_date


class RetentionManager:
    """Manages data retention policies"""
    
    def __init__(self, postgres_adapter):
        self.postgres = postgres_adapter
        self.anonymizer = DataAnonymizer()
        self.rules: Dict[DataCategory, RetentionRule] = {}
        self._ensure_tables()
        self._load_default_rules()
    
    async def _ensure_tables(self):
        """Ensure retention tables exist"""
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_retention_policies (
                id SERIAL PRIMARY KEY,
                category VARCHAR(50) NOT NULL,
                policy VARCHAR(20) NOT NULL,
                action VARCHAR(20) NOT NULL DEFAULT 'delete',
                conditions JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category)
            )
        """)
        
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_retention_log (
                id SERIAL PRIMARY KEY,
                category VARCHAR(50) NOT NULL,
                record_id VARCHAR(255),
                action VARCHAR(20) NOT NULL,
                performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details JSONB DEFAULT '{}'
            )
        """)
        
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_legal_holds (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                data_type VARCHAR(100),
                reason TEXT,
                hold_until TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            )
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_retention_log_category 
            ON gdpr_retention_log(category, performed_at)
        """)
    
    def _load_default_rules(self):
        """Load default retention rules"""
        self.rules[DataCategory.USER_PROFILE] = RetentionRule(
            DataCategory.USER_PROFILE, RetentionPolicy.YEARS_7, "anonymize"
        )
        
        self.rules[DataCategory.USER_ACTIVITY] = RetentionRule(
            DataCategory.USER_ACTIVITY, RetentionPolicy.DAYS_365, "delete"
        )
        
        self.rules[DataCategory.COMMUNICATION] = RetentionRule(
            DataCategory.COMMUNICATION, RetentionPolicy.YEARS_2, "delete"
        )
        
        self.rules[DataCategory.TRANSACTIONS] = RetentionRule(
            DataCategory.TRANSACTIONS, RetentionPolicy.YEARS_7, "archive"
        )
        
        self.rules[DataCategory.ANALYTICS] = RetentionRule(
            DataCategory.ANALYTICS, RetentionPolicy.DAYS_90, "delete"
        )
        
        self.rules[DataCategory.LOGS] = RetentionRule(
            DataCategory.LOGS, RetentionPolicy.DAYS_90, "delete"
        )
        
        self.rules[DataCategory.SESSIONS] = RetentionRule(
            DataCategory.SESSIONS, RetentionPolicy.DAYS_30, "delete"
        )
        
        self.rules[DataCategory.DEVICES] = RetentionRule(
            DataCategory.DEVICES, RetentionPolicy.YEARS_1, "delete"
        )
        
        self.rules[DataCategory.COOKIES] = RetentionRule(
            DataCategory.COOKIES, RetentionPolicy.DAYS_180, "delete"
        )
        
        self.rules[DataCategory.CONSENTS] = RetentionRule(
            DataCategory.CONSENTS, RetentionPolicy.YEARS_10, "archive"
        )
        
        self.rules[DataCategory.BACKUPS] = RetentionRule(
            DataCategory.BACKUPS, RetentionPolicy.YEARS_7, "delete"
        )
    
    async def add_retention_rule(self, category: DataCategory, 
                               policy: RetentionPolicy, action: str = "delete",
                               conditions: Dict = None) -> bool:
        """
        Add or update retention rule
        
        Args:
            category: Data category
            policy: Retention policy
            action: Action to take (delete, anonymize, archive)
            conditions: Additional conditions
            
        Returns:
            True if successful
        """
        try:
            await self.postgres.execute("""
                INSERT INTO gdpr_retention_policies 
                (category, policy, action, conditions)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (category) DO UPDATE SET
                policy = $2, action = $3, conditions = $4, updated_at = $5
            """, category.value, policy.value, action, 
                  json.dumps(conditions or {}), datetime.utcnow())
            
            # Update in-memory rules
            self.rules[category] = RetentionRule(category, policy, action, conditions)
            
            logger.info(f"Added retention rule: {category.value} -> {policy.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add retention rule: {e}")
            return False
    
    async def apply_retention_policies(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Apply all retention policies
        
        Args:
            dry_run: If True, only report what would be done
            
        Returns:
            Dictionary of actions performed
        """
        results = {}
        
        for category, rule in self.rules.items():
            count = await self._apply_rule(category, rule, dry_run)
            results[category.value] = count
        
        if not dry_run:
            logger.info(f"Applied retention policies: {results}")
        
        return results
    
    async def _apply_rule(self, category: DataCategory, rule: RetentionRule,
                         dry_run: bool = False) -> int:
        """Apply a specific retention rule"""
        count = 0
        
        if category == DataCategory.USER_ACTIVITY:
            # Clean old activity logs
            cutoff = datetime.utcnow() - timedelta(days=365)
            
            if rule.action == "delete":
                if not dry_run:
                    await self.postgres.execute("""
                        DELETE FROM user_activity_logs 
                        WHERE created_at < $1
                    """, cutoff)
                
                count = await self._get_count("user_activity_logs", f"created_at < '{cutoff}'")
        
        elif category == DataCategory.SESSIONS:
            # Clean old sessions
            cutoff = datetime.utcnow() - timedelta(days=30)
            
            if not dry_run:
                await self.postgres.execute("""
                    DELETE FROM user_sessions 
                    WHERE created_at < $1
                """, cutoff)
            
            count = await self._get_count("user_sessions", f"created_at < '{cutoff}'")
        
        elif category == DataCategory.DEVICES:
            # Clean old inactive devices
            cutoff = datetime.utcnow() - timedelta(days=365)
            
            if rule.action == "delete":
                if not dry_run:
                    await self.postgres.execute("""
                        DELETE FROM devices 
                        WHERE last_seen_at < $1 AND is_active = false
                    """, cutoff)
                
                count = await self._get_count("devices", 
                    f"last_seen_at < '{cutoff}' AND is_active = false")
        
        elif category == DataCategory.REFRESH_TOKENS:
            # Clean expired tokens
            if not dry_run:
                await self.postgres.execute("""
                    DELETE FROM refresh_tokens 
                    WHERE expires_at < NOW()
                """)
            
            count = await self._get_count("refresh_tokens", "expires_at < NOW()")
        
        elif category == DataCategory.CONSENTS:
            # Archive old consents instead of deleting
            cutoff = datetime.utcnow() - timedelta(days=3650)  # 10 years
            
            if rule.action == "archive":
                # Move to archive table
                if not dry_run:
                    await self.postgres.execute("""
                        INSERT INTO gdpr_consent_archive 
                        SELECT * FROM gdpr_consents 
                        WHERE granted_at < $1
                    """, cutoff)
                    
                    await self.postgres.execute("""
                        DELETE FROM gdpr_consents 
                        WHERE granted_at < $1
                    """, cutoff)
                
                count = await self._get_count("gdpr_consents", f"granted_at < '{cutoff}'")
        
        # Log the action
        if not dry_run and count > 0:
            await self._log_retention_action(category, rule.action, count)
        
        return count
    
    async def place_legal_hold(self, user_id: int, data_type: str, 
                             reason: str, hold_until: datetime = None,
                             created_by: str = None) -> bool:
        """
        Place legal hold on user data
        
        Args:
            user_id: User ID
            data_type: Type of data to hold
            reason: Reason for hold
            hold_until: When hold expires
            created_by: Who placed the hold
            
        Returns:
            True if successful
        """
        try:
            await self.postgres.execute("""
                INSERT INTO gdpr_legal_holds 
                (user_id, data_type, reason, hold_until, created_by)
                VALUES ($1, $2, $3, $4, $5)
            """, user_id, data_type, reason, hold_until, created_by)
            
            logger.info(f"Placed legal hold on user {user_id} data: {data_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to place legal hold: {e}")
            return False
    
    async def check_legal_hold(self, user_id: int, data_type: str = None) -> bool:
        """
        Check if user data is under legal hold
        
        Args:
            user_id: User ID
            data_type: Specific data type to check
            
        Returns:
            True if under hold
        """
        query = """
            SELECT COUNT(*) as count FROM gdpr_legal_holds 
            WHERE user_id = $1 
            AND (hold_until IS NULL OR hold_until > NOW())
        """
        params = [user_id]
        
        if data_type:
            query += " AND data_type = $2"
            params.append(data_type)
        
        result = await self.postgres.fetch_one(query, *params)
        return result['count'] > 0
    
    async def release_legal_hold(self, user_id: int, data_type: str = None) -> bool:
        """
        Release legal hold on user data
        
        Args:
            user_id: User ID
            data_type: Specific data type to release
            
        Returns:
            True if successful
        """
        try:
            query = "DELETE FROM gdpr_legal_holds WHERE user_id = $1"
            params = [user_id]
            
            if data_type:
                query += " AND data_type = $2"
                params.append(data_type)
            
            await self.postgres.execute(query, *params)
            
            logger.info(f"Released legal hold on user {user_id} data")
            return True
            
        except Exception as e:
            logger.error(f"Failed to release legal hold: {e}")
            return False
    
    async def get_retention_report(self) -> Dict[str, Any]:
        """
        Get retention policy report
        
        Returns:
            Retention statistics
        """
        report = {
            "policies": {},
            "legal_holds": 0,
            "recent_actions": []
        }
        
        # Get policies
        for category, rule in self.rules.items():
            report["policies"][category.value] = {
                "policy": rule.policy.value,
                "action": rule.action,
                "retention_days": self._get_retention_days(rule.policy)
            }
        
        # Get legal holds count
        result = await self.postgres.fetch_one("""
            SELECT COUNT(*) as count FROM gdpr_legal_holds 
            WHERE hold_until IS NULL OR hold_until > NOW()
        """)
        report["legal_holds"] = result['count']
        
        # Get recent actions
        actions = await self.postgres.fetch_all("""
            SELECT category, action, performed_at, details
            FROM gdpr_retention_log 
            ORDER BY performed_at DESC 
            LIMIT 10
        """)
        
        report["recent_actions"] = [dict(a) for a in actions]
        
        return report
    
    async def _get_count(self, table: str, condition: str = "1=1") -> int:
        """Get count of records matching condition"""
        result = await self.postgres.fetch_one(
            f"SELECT COUNT(*) as count FROM {table} WHERE {condition}"
        )
        return result['count']
    
    async def _log_retention_action(self, category: DataCategory, 
                                  action: str, count: int):
        """Log retention action"""
        await self.postgres.execute("""
            INSERT INTO gdpr_retention_log 
            (category, action, details)
            VALUES ($1, $2, $3)
        """, category.value, action, json.dumps({"records_count": count}))
    
    def _get_retention_days(self, policy: RetentionPolicy) -> int:
        """Get retention period in days"""
        mapping = {
            RetentionPolicy.IMMEDIATE: 0,
            RetentionPolicy.DAYS_30: 30,
            RetentionPolicy.DAYS_90: 90,
            RetentionPolicy.DAYS_180: 180,
            RetentionPolicy.DAYS_365: 365,
            RetentionPolicy.YEARS_1: 365,
            RetentionPolicy.YEARS_2: 730,
            RetentionPolicy.YEARS_5: 1825,
            RetentionPolicy.YEARS_7: 2555,
            RetentionPolicy.YEARS_10: 3650,
            RetentionPolicy.INDEFINITE: -1,
            RetentionPolicy.LEGAL_HOLD: -1
        }
        return mapping.get(policy, 0)
