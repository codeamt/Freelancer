"""
Device Management Service for tracking user devices and refresh tokens.
"""

import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from core.db.adapters import PostgresAdapter
from core.utils.logger import get_logger
from user_agents import parse as parse_user_agent

logger = get_logger(__name__)


class DeviceInfo:
    """Device information container"""
    
    def __init__(
        self,
        device_id: str,
        device_name: str,
        device_type: str,
        platform: str,
        browser: str,
        ip_address: str
    ):
        self.device_id = device_id
        self.device_name = device_name
        self.device_type = device_type
        self.platform = platform
        self.browser = browser
        self.ip_address = ip_address


class DeviceManager:
    """Manages device tracking and refresh tokens"""
    
    def __init__(self, postgres: PostgresAdapter):
        self.postgres = postgres
    
    def generate_device_id(self, user_agent: str, ip_address: str) -> str:
        """Generate a unique device ID based on user agent and IP"""
        hash_input = f"{user_agent}:{ip_address}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:32]
    
    def parse_device_info(self, user_agent: str, ip_address: str) -> DeviceInfo:
        """Parse user agent string to extract device information"""
        ua = parse_user_agent(user_agent)
        
        # Generate device ID
        device_id = self.generate_device_id(user_agent, ip_address)
        
        # Determine device type
        if ua.is_mobile:
            device_type = "mobile"
        elif ua.is_tablet:
            device_type = "tablet"
        elif ua.is_pc:
            device_type = "desktop"
        else:
            device_type = "unknown"
        
        # Create device name
        if ua.device.family != "Other":
            device_name = f"{ua.device.family} - {ua.browser.family}"
        else:
            device_name = f"{ua.os.family} - {ua.browser.family}"
        
        return DeviceInfo(
            device_id=device_id,
            device_name=device_name,
            device_type=device_type,
            platform=ua.os.family or "Unknown",
            browser=ua.browser.family or "Unknown",
            ip_address=ip_address
        )
    
    async def register_device(
        self,
        user_id: int,
        device_info: DeviceInfo,
        trust_device: bool = False
    ) -> Dict[str, Any]:
        """Register a new device for a user"""
        try:
            # Check if device already exists
            check_query = """
                SELECT id FROM devices 
                WHERE user_id = $1 AND device_id = $2
            """
            existing = await self.postgres.fetch_one(
                check_query,
                user_id,
                device_info.device_id
            )
            
            if existing:
                # Update last seen
                update_query = """
                    UPDATE devices 
                    SET last_seen_at = CURRENT_TIMESTAMP, 
                        is_active = true,
                        ip_address = $3
                    WHERE user_id = $1 AND device_id = $2
                """
                await self.postgres.execute(
                    update_query,
                    user_id,
                    device_info.device_id,
                    device_info.ip_address
                )
            else:
                # Insert new device
                insert_query = """
                    INSERT INTO devices 
                    (user_id, device_id, device_name, device_type, platform, browser, ip_address, is_trusted)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                """
                await self.postgres.execute(
                    insert_query,
                    user_id,
                    device_info.device_id,
                    device_info.device_name,
                    device_info.device_type,
                    device_info.platform,
                    device_info.browser,
                    device_info.ip_address,
                    trust_device
                )
            
            return {
                "device_id": device_info.device_id,
                "device_name": device_info.device_name,
                "is_new": not existing
            }
            
        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            raise
    
    async def create_refresh_token(
        self,
        user_id: int,
        device_info: DeviceInfo,
        expires_days: int = 30
    ) -> str:
        """Create a refresh token for a device"""
        try:
            # Generate unique token ID
            token_id = str(uuid.uuid4())
            
            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
            
            # Insert refresh token
            insert_query = """
                INSERT INTO refresh_tokens 
                (user_id, token_id, device_id, device_name, device_type, platform, browser, ip_address, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """
            
            await self.postgres.execute(
                insert_query,
                user_id,
                token_id,
                device_info.device_id,
                device_info.device_name,
                device_info.device_type,
                device_info.platform,
                device_info.browser,
                device_info.ip_address,
                expires_at
            )
            
            return token_id
            
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise
    
    async def validate_refresh_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Validate a refresh token and return its data"""
        try:
            query = """
                SELECT rt.*, u.email, u.role, u.roles
                FROM refresh_tokens rt
                JOIN users u ON rt.user_id = u.id
                WHERE rt.token_id = $1 
                AND rt.is_active = true 
                AND rt.expires_at > CURRENT_TIMESTAMP
            """
            
            result = await self.postgres.fetch_one(query, token_id)
            
            if result:
                # Update last used time
                update_query = """
                    UPDATE refresh_tokens 
                    SET last_used_at = CURRENT_TIMESTAMP
                    WHERE token_id = $1
                """
                await self.postgres.execute(update_query, token_id)
                
                return {
                    "user_id": result["user_id"],
                    "email": result["email"],
                    "role": result["role"],
                    "roles": result["roles"],
                    "device_id": result["device_id"],
                    "device_name": result["device_name"]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to validate refresh token: {e}")
            return None
    
    async def revoke_refresh_token(self, token_id: str) -> bool:
        """Revoke a specific refresh token"""
        try:
            query = """
                UPDATE refresh_tokens 
                SET is_active = false 
                WHERE token_id = $1
            """
            result = await self.postgres.execute(query, token_id)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to revoke refresh token: {e}")
            return False
    
    async def revoke_device_tokens(self, user_id: int, device_id: str) -> int:
        """Revoke all tokens for a specific device"""
        try:
            query = """
                UPDATE refresh_tokens 
                SET is_active = false 
                WHERE user_id = $1 AND device_id = $2
            """
            result = await self.postgres.execute(query, user_id, device_id)
            return result
            
        except Exception as e:
            logger.error(f"Failed to revoke device tokens: {e}")
            return 0
    
    async def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user"""
        try:
            query = """
                UPDATE refresh_tokens 
                SET is_active = false 
                WHERE user_id = $1
            """
            result = await self.postgres.execute(query, user_id)
            return result
            
        except Exception as e:
            logger.error(f"Failed to revoke all user tokens: {e}")
            return 0
    
    async def get_user_devices(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all devices for a user"""
        try:
            query = """
                SELECT 
                    device_id,
                    device_name,
                    device_type,
                    platform,
                    browser,
                    ip_address,
                    first_seen_at,
                    last_seen_at,
                    is_active,
                    is_trusted,
                    COUNT(rt.id) as active_sessions
                FROM devices d
                LEFT JOIN refresh_tokens rt ON d.device_id = rt.device_id AND rt.is_active = true
                WHERE d.user_id = $1
                GROUP BY d.id, d.device_id, d.device_name, d.device_type, d.platform, d.browser, d.ip_address, d.first_seen_at, d.last_seen_at, d.is_active, d.is_trusted
                ORDER BY d.last_seen_at DESC
            """
            
            results = await self.postgres.fetch_all(query, user_id)
            return [dict(r) for r in results]
            
        except Exception as e:
            logger.error(f"Failed to get user devices: {e}")
            return []
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired refresh tokens"""
        try:
            query = """
                DELETE FROM refresh_tokens 
                WHERE expires_at < CURRENT_TIMESTAMP
            """
            result = await self.postgres.execute(query)
            return result
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            return 0
    
    async def trust_device(self, user_id: int, device_id: str) -> bool:
        """Mark a device as trusted"""
        try:
            query = """
                UPDATE devices 
                SET is_trusted = true 
                WHERE user_id = $1 AND device_id = $2
            """
            result = await self.postgres.execute(query, user_id, device_id)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to trust device: {e}")
            return False
    
    async def untrust_device(self, user_id: int, device_id: str) -> bool:
        """Unmark a device as trusted"""
        try:
            query = """
                UPDATE devices 
                SET is_trusted = false 
                WHERE user_id = $1 AND device_id = $2
            """
            result = await self.postgres.execute(query, user_id, device_id)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to untrust device: {e}")
            return False
