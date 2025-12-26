"""
Data Subject Rights

Implements GDPR data subject access rights (DSAR).
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid

from core.utils.logger import get_logger
from .anonymizer import DataAnonymizer
from .consent_manager import ConsentManager

logger = get_logger(__name__)


class DSARType(Enum):
    """Types of Data Subject Access Requests"""
    ACCESS = "access"  # Right to access
    RECTIFICATION = "rectification"  # Right to rectification
    ERASURE = "erasure"  # Right to be forgotten
    PORTABILITY = "portability"  # Right to data portability
    RESTRICTION = "restriction"  # Right to restrict processing
    OBJECT = "object"  # Right to object


class DSARStatus(Enum):
    """DSAR status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    PARTIAL = "partial"


class DSARRequest:
    """Data Subject Access Request"""
    
    def __init__(self, user_id: int, request_type: DSARType,
                 details: Dict = None, requested_at: datetime = None):
        self.request_id = str(uuid.uuid4())
        self.user_id = user_id
        self.request_type = request_type
        self.status = DSARStatus.PENDING
        self.requested_at = requested_at or datetime.utcnow()
        self.details = details or {}
        self.processed_at = None
        self.completed_at = None
        self.notes = []
        self.attachments = []
    
    def add_note(self, note: str, author: str = "system"):
        """Add a note to the request"""
        self.notes.append({
            "timestamp": datetime.utcnow().isoformat(),
            "author": author,
            "note": note
        })
    
    def add_attachment(self, filename: str, path: str, type: str):
        """Add an attachment"""
        self.attachments.append({
            "filename": filename,
            "path": path,
            "type": type,
            "added_at": datetime.utcnow().isoformat()
        })


class DataSubjectRights:
    """Handles GDPR data subject rights"""
    
    def __init__(self, postgres_adapter, consent_manager: ConsentManager):
        self.postgres = postgres_adapter
        self.consent_manager = consent_manager
        self.anonymizer = DataAnonymizer()
        self._ensure_tables()
    
    async def _ensure_tables(self):
        """Ensure DSAR tables exist"""
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_dsar_requests (
                request_id VARCHAR(255) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                request_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                completed_at TIMESTAMP,
                details JSONB DEFAULT '{}',
                notes JSONB DEFAULT '[]',
                attachments JSONB DEFAULT '[]',
                processed_by VARCHAR(100)
            )
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_gdpr_dsar_user_id 
            ON gdpr_dsar_requests(user_id)
        """)
        
        await self.postgres.execute("""
            CREATE INDEX IF NOT EXISTS idx_gdpr_dsar_status 
            ON gdpr_dsar_requests(status, requested_at)
        """)
        
        await self.postgres.execute("""
            CREATE TABLE IF NOT EXISTS gdpr_data_exports (
                export_id VARCHAR(255) PRIMARY KEY,
                request_id VARCHAR(255) REFERENCES gdpr_dsar_requests(request_id),
                user_id INTEGER NOT NULL,
                data_type VARCHAR(100),
                file_path VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                downloaded BOOLEAN DEFAULT FALSE
            )
        """)
    
    async def create_request(self, user_id: int, request_type: DSARType,
                            details: Dict = None) -> DSARRequest:
        """
        Create a new DSAR request
        
        Args:
            user_id: User ID
            request_type: Type of request
            details: Additional details
            
        Returns:
            DSAR request object
        """
        request = DSARRequest(user_id, request_type, details)
        
        await self.postgres.execute("""
            INSERT INTO gdpr_dsar_requests 
            (request_id, user_id, request_type, status, details)
            VALUES ($1, $2, $3, $4, $5)
        """, request.request_id, user_id, request_type.value,
              request.status.value, json.dumps(details or {}))
        
        logger.info(f"Created DSAR request: {request.request_id} for user {user_id}")
        return request
    
    async def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """
        Get all personal data for a user (Right to Access)
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary containing all user data
        """
        data = {
            "user_id": user_id,
            "export_date": datetime.utcnow().isoformat(),
            "personal_data": {},
            "consent_records": [],
            "activity_log": [],
            "processed_data": []
        }
        
        # Get user personal data
        user_data = await self.postgres.fetch_one("""
            SELECT id, email, first_name, last_name, created_at, updated_at,
                   phone, address, bio, avatar_url
            FROM users WHERE id = $1
        """, user_id)
        
        if user_data:
            data["personal_data"] = dict(user_data)
        
        # Get consent records
        consents = await self.consent_manager.get_user_consents(user_id)
        for consent in consents:
            data["consent_records"].append({
                "type": consent.consent_type.value,
                "status": consent.status.value,
                "granted_at": consent.granted_at.isoformat(),
                "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
                "updated_at": consent.updated_at.isoformat()
            })
        
        # Get device information
        devices = await self.postgres.fetch_all("""
            SELECT device_id, device_name, device_type, platform, browser,
                   ip_address, first_seen_at, last_seen_at, is_active, is_trusted
            FROM devices WHERE user_id = $1
        """, user_id)
        
        data["devices"] = [dict(d) for d in devices]
        
        # Get session information
        sessions = await self.postgres.fetch_all("""
            SELECT session_token, expires_at, created_at, last_accessed
            FROM user_sessions WHERE user_id = $1
        """, user_id)
        
        data["sessions"] = [dict(s) for s in sessions]
        
        # Get refresh tokens
        tokens = await self.postgres.fetch_all("""
            SELECT token_id, device_id, device_name, device_type,
                   created_at, expires_at, last_used_at
            FROM refresh_tokens WHERE user_id = $1
        """, user_id)
        
        data["refresh_tokens"] = [dict(t) for t in tokens]
        
        # Get site associations
        sites = await self.postgres.fetch_all("""
            SELECT id, name, domain, description, created_at, updated_at
            FROM sites WHERE owner_id = $1
        """, user_id)
        
        data["owned_sites"] = [dict(s) for s in sites]
        
        logger.info(f"Exported data for user {user_id}")
        return data
    
    async def rectify_data(self, user_id: int, corrections: Dict[str, Any],
                          reason: str = None) -> bool:
        """
        Correct inaccurate personal data (Right to Rectification)
        
        Args:
            user_id: User ID
            corrections: Data corrections
            reason: Reason for correction
            
        Returns:
            True if successful
        """
        try:
            # Build update query
            updates = []
            values = []
            param_count = 1
            
            for field, value in corrections.items():
                if field in ['first_name', 'last_name', 'phone', 'address', 'bio', 'avatar_url']:
                    updates.append(f"{field} = ${param_count}")
                    values.append(value)
                    param_count += 1
            
            if not updates:
                return False
            
            # Add updated_at
            updates.append(f"updated_at = ${param_count}")
            values.append(datetime.utcnow())
            param_count += 1
            
            # Add user_id
            values.append(user_id)
            
            # Execute update
            await self.postgres.execute(f"""
                UPDATE users 
                SET {', '.join(updates)}
                WHERE id = ${param_count}
            """, *values)
            
            # Log the correction
            await self._log_data_action(
                user_id, "rectification", 
                {"corrections": corrections, "reason": reason}
            )
            
            logger.info(f"Rectified data for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rectify data for user {user_id}: {e}")
            return False
    
    async def erase_user_data(self, user_id: int, keep_essential: bool = True,
                             reason: str = None) -> bool:
        """
        Erase user personal data (Right to Erasure/Right to be Forgotten)
        
        Args:
            user_id: User ID
            keep_essential: Keep essential data for legal purposes
            reason: Reason for erasure
            
        Returns:
            True if successful
        """
        try:
            if keep_essential:
                # Anonymize instead of deleting
                await self.anonymizer.anonymize_user(user_id)
            else:
                # Full deletion
                await self._delete_user_data(user_id)
            
            # Log the erasure
            await self._log_data_action(
                user_id, "erasure",
                {"keep_essential": keep_essential, "reason": reason}
            )
            
            logger.info(f"Erased data for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to erase data for user {user_id}: {e}")
            return False
    
    async def export_user_data(self, user_id: int, format: str = "json") -> str:
        """
        Export user data in portable format (Right to Data Portability)
        
        Args:
            user_id: User ID
            format: Export format (json, csv, xml)
            
        Returns:
            Path to exported file
        """
        # Get user data
        data = await self.get_user_data(user_id)
        
        # Create export file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"user_data_{user_id}_{timestamp}.{format}"
        export_path = f"/tmp/exports/{filename}"
        
        # Ensure directory exists
        import os
        os.makedirs("/tmp/exports", exist_ok=True)
        
        # Export based on format
        if format == "json":
            import json
            with open(export_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        elif format == "csv":
            import csv
            with open(export_path, 'w', newline='') as f:
                writer = csv.writer(f)
                # Flatten data for CSV
                flattened = self._flatten_dict(data)
                writer.writerow(flattened.keys())
                writer.writerow(flattened.values())
        
        # Record export
        export_id = str(uuid.uuid4())
        await self.postgres.execute("""
            INSERT INTO gdpr_data_exports 
            (export_id, user_id, data_type, file_path, expires_at)
            VALUES ($1, $2, $3, $4, $5)
        """, export_id, user_id, "full_export", export_path,
           datetime.utcnow() + timedelta(days=30))
        
        logger.info(f"Exported data for user {user_id} to {export_path}")
        return export_path
    
    async def restrict_processing(self, user_id: int, restriction_type: str,
                                reason: str = None) -> bool:
        """
        Restrict processing of user data
        
        Args:
            user_id: User ID
            restriction_type: Type of restriction
            reason: Reason for restriction
            
        Returns:
            True if successful
        """
        try:
            # Add processing restriction flag
            await self.postgres.execute("""
                INSERT INTO gdpr_processing_restrictions 
                (user_id, restriction_type, reason, created_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE SET
                restriction_type = $2, reason = $3, updated_at = $4
            """, user_id, restriction_type, reason, datetime.utcnow())
            
            # Log the restriction
            await self._log_data_action(
                user_id, "processing_restriction",
                {"type": restriction_type, "reason": reason}
            )
            
            logger.info(f"Restricted processing for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restrict processing for user {user_id}: {e}")
            return False
    
    async def get_dsar_request(self, request_id: str) -> Optional[DSARRequest]:
        """Get DSAR request by ID"""
        result = await self.postgres.fetch_one("""
            SELECT * FROM gdpr_dsar_requests WHERE request_id = $1
        """, request_id)
        
        if not result:
            return None
        
        request = DSARRequest(
            user_id=result['user_id'],
            request_type=DSARType(result['request_type']),
            details=result['details']
        )
        request.request_id = result['request_id']
        request.status = DSARStatus(result['status'])
        request.requested_at = result['requested_at']
        request.processed_at = result['processed_at']
        request.completed_at = result['completed_at']
        request.notes = result['notes'] or []
        request.attachments = result['attachments'] or []
        
        return request
    
    async def update_dsar_status(self, request_id: str, status: DSARStatus,
                                notes: str = None, processed_by: str = None) -> bool:
        """Update DSAR request status"""
        updates = ["status = $2"]
        values = [request_id, status.value]
        param_count = 3
        
        if status in [DSARStatus.PROCESSING, DSARStatus.COMPLETED, DSARStatus.REJECTED]:
            updates.append(f"processed_at = ${param_count}")
            values.append(datetime.utcnow())
            param_count += 1
        
        if status == DSARStatus.COMPLETED:
            updates.append(f"completed_at = ${param_count}")
            values.append(datetime.utcnow())
            param_count += 1
        
        if processed_by:
            updates.append(f"processed_by = ${param_count}")
            values.append(processed_by)
            param_count += 1
        
        values.insert(0, f"UPDATE gdpr_dsar_requests SET {', '.join(updates)} WHERE request_id = $1")
        
        await self.postgres.execute(*values)
        
        if notes:
            await self.postgres.execute("""
                UPDATE gdpr_dsar_requests 
                SET notes = notes || $2::jsonb
                WHERE request_id = $1
            """, request_id, json.dumps([{
                "timestamp": datetime.utcnow().isoformat(),
                "author": processed_by or "system",
                "note": notes
            }]))
        
        return True
    
    async def _delete_user_data(self, user_id: int):
        """Completely delete user data"""
        # Delete in order of dependencies
        await self.postgres.execute("DELETE FROM refresh_tokens WHERE user_id = $1", user_id)
        await self.postgres.execute("DELETE FROM user_sessions WHERE user_id = $1", user_id)
        await self.postgres.execute("DELETE FROM devices WHERE user_id = $1", user_id)
        await self.postgres.execute("DELETE FROM gdpr_consents WHERE user_id = $1", user_id)
        await self.postgres.execute("DELETE FROM sites WHERE owner_id = $1", user_id)
        await self.postgres.execute("DELETE FROM users WHERE id = $1", user_id)
    
    async def _log_data_action(self, user_id: int, action: str, details: Dict = None):
        """Log data action for audit"""
        await self.postgres.execute("""
            INSERT INTO gdpr_audit_log 
            (user_id, action, details, timestamp)
            VALUES ($1, $2, $3, $4)
        """, user_id, action, json.dumps(details or {}), datetime.utcnow())
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}_{i}", item))
            else:
                items.append((new_key, v))
        return dict(items)
