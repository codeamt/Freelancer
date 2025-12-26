"""
GDPR Consent Manager

Manages user consent for data processing activities.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json

from core.utils.logger import get_logger

logger = get_logger(__name__)


class ConsentType(Enum):
    """Types of consent"""
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    PERSONALIZATION = "personalization"
    THIRD_PARTY = "third_party"
    COOKIES = "cookies"
    EMAIL_COMMUNICATION = "email_communication"
    SMS_COMMUNICATION = "sms_communication"
    DATA_PROCESSING = "data_processing"


class ConsentStatus(Enum):
    """Consent status"""
    GRANTED = "granted"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"


class ConsentRecord:
    """Consent record"""
    
    def __init__(self, user_id: int, consent_type: ConsentType, 
                 status: ConsentStatus, granted_at: datetime = None,
                 expires_at: datetime = None, metadata: Dict = None):
        self.user_id = user_id
        self.consent_type = consent_type
        self.status = status
        self.granted_at = granted_at or datetime.utcnow()
        self.expires_at = expires_at
        self.metadata = metadata or {}
        self.updated_at = datetime.utcnow()
        self.ip_address = metadata.get('ip_address') if metadata else None
        self.user_agent = metadata.get('user_agent') if metadata else None
        self.consent_document_id = metadata.get('document_id') if metadata else None


class ConsentManager:
    """Manages GDPR consent"""
    
    def __init__(self, postgres_adapter):
        self.postgres = postgres_adapter
        self._ensure_tables()
    
    async def _ensure_tables(self):
        """Ensure consent tables exist"""
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_consents (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                consent_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                withdrawn_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address INET,
                user_agent TEXT,
                consent_document_id VARCHAR(255),
                metadata JSONB DEFAULT '{}',
                UNIQUE(user_id, consent_type)
            )
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_gdpr_consents_user_id 
            ON gdpr_consents(user_id)
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_gdpr_consents_type_status 
            ON gdpr_consents(consent_type, status)
        """)
        
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_consent_history (
                id SERIAL PRIMARY KEY,
                consent_id INTEGER REFERENCES gdpr_consents(id),
                user_id INTEGER NOT NULL,
                consent_type VARCHAR(50) NOT NULL,
                old_status VARCHAR(20),
                new_status VARCHAR(20) NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                changed_by VARCHAR(50),
                ip_address INET,
                reason TEXT
            )
        """)
    
    async def record_consent(self, user_id: int, consent_type: ConsentType,
                           status: ConsentStatus, expires_at: datetime = None,
                           metadata: Dict = None) -> ConsentRecord:
        """
        Record user consent
        
        Args:
            user_id: User ID
            consent_type: Type of consent
            status: Consent status
            expires_at: When consent expires
            metadata: Additional metadata
            
        Returns:
            Consent record
        """
        record = ConsentRecord(
            user_id=user_id,
            consent_type=consent_type,
            status=status,
            expires_at=expires_at,
            metadata=metadata
        )
        
        # Check if consent already exists
        existing = await self._get_consent(user_id, consent_type)
        
        if existing:
            # Update existing record
            old_status = existing.status
            
            await self.postgres.execute("""
                UPDATE gdpr_consents 
                SET status = $1, expires_at = $2, updated_at = $3,
                    ip_address = $4, user_agent = $5, metadata = $6,
                    withdrawn_at = CASE WHEN $1 = 'withdrawn' THEN $3 ELSE withdrawn_at END
                WHERE user_id = $7 AND consent_type = $8
            """, status.value, expires_at, datetime.utcnow(),
                  record.ip_address, record.user_agent, 
                  json.dumps(metadata), user_id, consent_type.value)
            
            # Record in history
            await self._record_history(
                existing.id, user_id, consent_type,
                old_status.value, status.value, metadata
            )
        else:
            # Insert new record
            result = await self.postgres.fetch_one("""
                INSERT INTO gdpr_consents 
                (user_id, consent_type, status, expires_at, ip_address, 
                 user_agent, metadata, consent_document_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """, user_id, consent_type.value, status.value, expires_at,
                  record.ip_address, record.user_agent,
                  json.dumps(metadata), record.consent_document_id)
            
            # Record in history
            await self._record_history(
                result['id'], user_id, consent_type,
                None, status.value, metadata
            )
        
        logger.info(f"Recorded consent: user={user_id}, type={consent_type.value}, status={status.value}")
        return record
    
    async def check_consent(self, user_id: int, consent_type: ConsentType) -> Optional[ConsentRecord]:
        """
        Check if user has valid consent
        
        Args:
            user_id: User ID
            consent_type: Type of consent to check
            
        Returns:
            Consent record if valid, None otherwise
        """
        record = await self._get_consent(user_id, consent_type)
        
        if not record:
            return None
        
        # Check if consent is still valid
        if record.status == ConsentStatus.GRANTED:
            if record.expires_at and record.expires_at < datetime.utcnow():
                # Expired
                await self._update_status(record, ConsentStatus.EXPIRED)
                return None
        
        # Return based on status
        if record.status in [ConsentStatus.GRANTED]:
            return record
        
        return None
    
    async def withdraw_consent(self, user_id: int, consent_type: ConsentType,
                             reason: str = None, metadata: Dict = None) -> bool:
        """
        Withdraw user consent
        
        Args:
            user_id: User ID
            consent_type: Type of consent to withdraw
            reason: Reason for withdrawal
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        record = await self._get_consent(user_id, consent_type)
        
        if not record or record.status != ConsentStatus.GRANTED:
            return False
        
        await self._update_status(record, ConsentStatus.WITHDRAWN, metadata)
        
        logger.info(f"Withdrew consent: user={user_id}, type={consent_type.value}, reason={reason}")
        return True
    
    async def get_user_consents(self, user_id: int) -> List[ConsentRecord]:
        """
        Get all consents for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of consent records
        """
        results = await self.postgres.fetch_all("""
            SELECT * FROM gdpr_consents 
            WHERE user_id = $1 
            ORDER BY granted_at DESC
        """, user_id)
        
        consents = []
        for row in results:
            consent = ConsentRecord(
                user_id=row['user_id'],
                consent_type=ConsentType(row['consent_type']),
                status=ConsentStatus(row['status']),
                granted_at=row['granted_at'],
                expires_at=row['expires_at'],
                metadata=row['metadata']
            )
            consent.updated_at = row['updated_at']
            consents.append(consent)
        
        return consents
    
    async def get_consent_history(self, user_id: int, consent_type: ConsentType = None) -> List[Dict]:
        """
        Get consent change history
        
        Args:
            user_id: User ID
            consent_type: Filter by consent type
            
        Returns:
            List of history records
        """
        query = """
            SELECT * FROM gdpr_consent_history 
            WHERE user_id = $1
        """
        params = [user_id]
        
        if consent_type:
            query += " AND consent_type = $2"
            params.append(consent_type.value)
        
        query += " ORDER BY changed_at DESC"
        
        return await self.postgres.fetch_all(query, *params)
    
    async def cleanup_expired_consents(self) -> int:
        """
        Clean up expired consents
        
        Returns:
            Number of consents cleaned up
        """
        result = await self.postgres.fetch_one("""
            UPDATE gdpr_consents 
            SET status = 'expired', updated_at = $1
            WHERE status = 'granted' 
            AND expires_at IS NOT NULL 
            AND expires_at < $1
            RETURNING COUNT(*) as count
        """, datetime.utcnow())
        
        count = result['count']
        logger.info(f"Cleaned up {count} expired consents")
        return count
    
    async def get_consents_by_type(self, consent_type: ConsentType, 
                                  status: ConsentStatus = None) -> List[ConsentRecord]:
        """
        Get consents by type and optionally status
        
        Args:
            consent_type: Type of consent
            status: Filter by status
            
        Returns:
            List of consent records
        """
        query = """
            SELECT * FROM gdpr_consents 
            WHERE consent_type = $1
        """
        params = [consent_type.value]
        
        if status:
            query += " AND status = $2"
            params.append(status.value)
        
        query += " ORDER BY granted_at DESC"
        
        results = await self.postgres.fetch_all(query, *params)
        
        consents = []
        for row in results:
            consent = ConsentRecord(
                user_id=row['user_id'],
                consent_type=ConsentType(row['consent_type']),
                status=ConsentStatus(row['status']),
                granted_at=row['granted_at'],
                expires_at=row['expires_at'],
                metadata=row['metadata']
            )
            consent.updated_at = row['updated_at']
            consents.append(consent)
        
        return consents
    
    async def _get_consent(self, user_id: int, consent_type: ConsentType) -> Optional[ConsentRecord]:
        """Get consent record"""
        result = await self.postgres.fetch_one("""
            SELECT * FROM gdpr_consents 
            WHERE user_id = $1 AND consent_type = $2
        """, user_id, consent_type.value)
        
        if not result:
            return None
        
        consent = ConsentRecord(
            user_id=result['user_id'],
            consent_type=ConsentType(result['consent_type']),
            status=ConsentStatus(result['status']),
            granted_at=result['granted_at'],
            expires_at=result['expires_at'],
            metadata=result['metadata']
        )
        consent.updated_at = result['updated_at']
        consent.withdrawn_at = result.get('withdrawn_at')
        
        return consent
    
    async def _update_status(self, record: ConsentRecord, new_status: ConsentStatus,
                            metadata: Dict = None):
        """Update consent status"""
        old_status = record.status
        
        await self.postgres.execute("""
            UPDATE gdpr_consents 
            SET status = $1, updated_at = $2, metadata = $3,
                withdrawn_at = CASE WHEN $1 = 'withdrawn' THEN $2 ELSE withdrawn_at END
            WHERE id = $4
        """, new_status.value, datetime.utcnow(), 
              json.dumps(metadata or {}), record.id)
        
        # Record in history
        await self._record_history(
            record.id, record.user_id, record.consent_type,
            old_status.value, new_status.value, metadata
        )
    
    async def _record_history(self, consent_id: int, user_id: int, 
                             consent_type: ConsentType, old_status: str,
                             new_status: str, metadata: Dict = None):
        """Record consent change in history"""
        await self.postgres.execute("""
            INSERT INTO gdpr_consent_history 
            (consent_id, user_id, consent_type, old_status, new_status,
             ip_address, reason)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, consent_id, user_id, consent_type.value, old_status, new_status,
              metadata.get('ip_address') if metadata else None,
              metadata.get('reason') if metadata else None)
