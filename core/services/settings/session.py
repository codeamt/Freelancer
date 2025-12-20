"""
Session and Cookie Management

Reads configuration from settings and provides:
- Session creation and validation
- Cookie configuration based on security settings
- Session cleanup and expiry
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import secrets

from core.utils.logger import get_logger
from .service import settings_service

logger = get_logger(__name__)


# ============================================================================
# Configuration Classes
# ============================================================================

@dataclass
class SessionConfig:
    """Session configuration from settings"""
    timeout_minutes: int = 60
    jwt_secret: str = None
    jwt_expiry_hours: int = 24
    
    @classmethod
    async def from_settings(cls, user_roles: list = None):
        """Load session config from settings"""
        # Default to admin roles for reading auth settings
        roles = user_roles or ["super_admin"]
        
        # Get session timeout
        timeout_result = await settings_service.get_setting(
            "auth.session_timeout",
            roles,
            decrypt=True
        )
        timeout = timeout_result.get("value", 60) if timeout_result["success"] else 60
        
        # Get JWT secret
        jwt_result = await settings_service.get_setting(
            "auth.jwt_secret",
            roles,
            decrypt=True
        )
        jwt_secret = jwt_result.get("value") if jwt_result["success"] else None
        
        # Get JWT expiry
        expiry_result = await settings_service.get_setting(
            "auth.jwt_expiry",
            roles,
            decrypt=True
        )
        jwt_expiry = expiry_result.get("value", 24) if expiry_result["success"] else 24
        
        return cls(
            timeout_minutes=int(timeout),
            jwt_secret=jwt_secret,
            jwt_expiry_hours=int(jwt_expiry)
        )


@dataclass
class CookieConfig:
    """Cookie configuration from settings"""
    secure: bool = True
    httponly: bool = True
    samesite: str = "Lax"
    max_age: int = 3600
    domain: Optional[str] = None
    path: str = "/"
    
    @classmethod
    async def from_settings(cls, user_roles: list = None):
        """Load cookie config from settings"""
        roles = user_roles or ["super_admin"]
        
        # Get secure flag
        secure_result = await settings_service.get_setting(
            "auth.cookie_secure",
            roles
        )
        secure = secure_result.get("value", True) if secure_result["success"] else True
        
        # Get httponly flag
        httponly_result = await settings_service.get_setting(
            "auth.cookie_httponly",
            roles
        )
        httponly = httponly_result.get("value", True) if httponly_result["success"] else True
        
        # Get samesite policy
        samesite_result = await settings_service.get_setting(
            "auth.cookie_samesite",
            roles
        )
        samesite = samesite_result.get("value", "Lax") if samesite_result["success"] else "Lax"
        
        # Get max age
        max_age_result = await settings_service.get_setting(
            "auth.cookie_max_age",
            roles
        )
        max_age = max_age_result.get("value", 3600) if max_age_result["success"] else 3600
        
        return cls(
            secure=bool(secure),
            httponly=bool(httponly),
            samesite=str(samesite),
            max_age=int(max_age)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for FastHTML/Starlette"""
        config = {
            "secure": self.secure,
            "httponly": self.httponly,
            "samesite": self.samesite,
            "max_age": self.max_age,
            "path": self.path
        }
        
        if self.domain:
            config["domain"] = self.domain
        
        return config


# ============================================================================
# Session Manager
# ============================================================================

class SessionManager:
    """
    Manages user sessions with configuration from settings.
    
    Features:
    - Session creation with configurable timeout
    - Session validation and renewal
    - Automatic cleanup of expired sessions
    - Cookie configuration from settings
    """
    
    def __init__(self, db_service=None):
        """
        Initialize session manager.
        
        Args:
            db_service: Database service for session storage
        """
        self.db = db_service
        self._session_config: Optional[SessionConfig] = None
        self._cookie_config: Optional[CookieConfig] = None
    
    async def get_session_config(self) -> SessionConfig:
        """Get current session configuration from settings"""
        # Cache for 5 minutes to avoid constant DB queries
        if self._session_config is None:
            self._session_config = await SessionConfig.from_settings()
        return self._session_config
    
    async def get_cookie_config(self) -> CookieConfig:
        """Get current cookie configuration from settings"""
        if self._cookie_config is None:
            self._cookie_config = await CookieConfig.from_settings()
        return self._cookie_config
    
    async def refresh_config(self):
        """Refresh configuration from settings"""
        self._session_config = None
        self._cookie_config = None
        await self.get_session_config()
        await self.get_cookie_config()
    
    # ========================================================================
    # Session Operations
    # ========================================================================
    
    async def create_session(
        self,
        user_id: str,
        user_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new session.
        
        Args:
            user_id: User's unique identifier
            user_data: User data to store in session
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            {
                "session_id": str,
                "expires_at": datetime,
                "user_id": str
            }
        """
        config = await self.get_session_config()
        
        # Generate session ID
        session_id = secrets.token_urlsafe(32)
        
        # Calculate expiry
        expires_at = datetime.utcnow() + timedelta(minutes=config.timeout_minutes)
        
        # Create session data
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "user_data": user_data,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "last_activity": datetime.utcnow(),
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        # Store in database
        if self.db:
            try:
                await self.db.insert_one("sessions", session_data)
                logger.info(f"Created session for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                return {"success": False, "error": "Failed to create session"}
        
        return {
            "success": True,
            "session_id": session_id,
            "expires_at": expires_at,
            "user_id": user_id
        }
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by session ID.
        
        Returns None if session doesn't exist or is expired.
        """
        if not self.db:
            logger.warning("No database service configured")
            return None
        
        try:
            session = await self.db.find_one("sessions", {"session_id": session_id})
            
            if not session:
                return None
            
            # Check if expired
            if session["expires_at"] < datetime.utcnow():
                logger.info(f"Session {session_id} expired")
                await self.delete_session(session_id)
                return None
            
            return session
        except Exception as e:
            logger.error(f"Error fetching session: {e}")
            return None
    
    async def update_activity(self, session_id: str) -> bool:
        """
        Update last activity timestamp for session.
        
        This can be used to implement sliding window sessions.
        """
        if not self.db:
            return False
        
        try:
            config = await self.get_session_config()
            
            # Update last activity and extend expiry
            new_expiry = datetime.utcnow() + timedelta(minutes=config.timeout_minutes)
            
            await self.db.update_one(
                "sessions",
                {"session_id": session_id},
                {
                    "last_activity": datetime.utcnow(),
                    "expires_at": new_expiry
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session (logout)"""
        if not self.db:
            return False
        
        try:
            await self.db.delete_one("sessions", {"session_id": session_id})
            logger.info(f"Deleted session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user.
        
        Useful for logout from all devices.
        
        Returns:
            Number of sessions deleted
        """
        if not self.db:
            return 0
        
        try:
            result = await self.db.delete_many("sessions", {"user_id": user_id})
            count = result.deleted_count if hasattr(result, 'deleted_count') else 0
            logger.info(f"Deleted {count} sessions for user {user_id}")
            return count
        except Exception as e:
            logger.error(f"Failed to delete user sessions: {e}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Should be run periodically (e.g., hourly cron job).
        
        Returns:
            Number of sessions cleaned up
        """
        if not self.db:
            return 0
        
        try:
            result = await self.db.delete_many("sessions", {
                "expires_at": {"$lt": datetime.utcnow()}
            })
            count = result.deleted_count if hasattr(result, 'deleted_count') else 0
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")
            return 0
    
    async def get_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user.
        
        Useful for "active devices" display.
        """
        if not self.db:
            return []
        
        try:
            sessions = await self.db.find("sessions", {
                "user_id": user_id,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            return [
                {
                    "session_id": s["session_id"],
                    "created_at": s["created_at"],
                    "last_activity": s["last_activity"],
                    "ip_address": s.get("ip_address"),
                    "user_agent": s.get("user_agent")
                }
                for s in sessions
            ]
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []
    
    # ========================================================================
    # Cookie Helpers
    # ========================================================================
    
    async def create_session_cookie(
        self,
        session_id: str,
        response
    ):
        """
        Set session cookie on response.
        
        Args:
            session_id: Session ID to set
            response: FastHTML/Starlette response object
        """
        config = await self.get_cookie_config()
        
        response.set_cookie(
            key="session_id",
            value=session_id,
            **config.to_dict()
        )
    
    async def delete_session_cookie(self, response):
        """Delete session cookie from response"""
        response.delete_cookie(key="session_id")
    
    # ========================================================================
    # Validation
    # ========================================================================
    
    async def validate_session(
        self,
        session_id: str,
        update_activity: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Validate session and optionally update activity.
        
        Args:
            session_id: Session ID to validate
            update_activity: Whether to update last activity (sliding window)
            
        Returns:
            Session data if valid, None if invalid/expired
        """
        session = await self.get_session(session_id)
        
        if not session:
            return None
        
        # Update activity for sliding window
        if update_activity:
            await self.update_activity(session_id)
        
        return session


# Global session manager instance
session_manager = SessionManager()


# Initialization function
def initialize_session_manager(db_service):
    """Initialize session manager with database"""
    global session_manager
    session_manager = SessionManager(db_service)
    logger.info("Session manager initialized")