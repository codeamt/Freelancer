# app/core/services/auth/providers/jwt.py
import os
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from core.utils.logger import get_logger

logger = get_logger(__name__)

class JWTProvider:
    def __init__(self):
        # Use JWT_SECRET (consistent with rest of app) or JWT_SECRET_KEY
        self.secret = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY")
        if not self.secret:
            raise ValueError(
                "JWT_SECRET environment variable is required. "
                "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        self.algorithm = "HS256"
        self.exp_hours = 24
        self.use_blacklist = os.getenv("JWT_USE_BLACKLIST", "true").lower() == "true"
        # Refresh token settings
        self.refresh_exp_days = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "30"))
        self.access_exp_minutes = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "15"))

    def create(self, payload: Dict, expires_hours: Optional[int] = None) -> str:
        """Create JWT token with expiration"""
        exp_hours = self.exp_hours if expires_hours is None else expires_hours
        
        # Add standard claims
        token_payload = {
            **payload,
            "exp": datetime.utcnow() + timedelta(hours=exp_hours),
            "iat": datetime.utcnow(),
            "iss": "fastapp",
            "aud": "fastapp-users"
        }
        
        # Add JTI (JWT ID) for blacklist tracking
        import uuid
        token_payload["jti"] = str(uuid.uuid4())
        
        return jwt.encode(
            token_payload,
            self.secret,
            algorithm=self.algorithm
        )
    
    def create_access_token(self, payload: Dict) -> str:
        """Create short-lived access token"""
        token_payload = {
            **payload,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=self.access_exp_minutes),
            "iat": datetime.utcnow(),
            "iss": "fastapp",
            "aud": "fastapp-users"
        }
        
        # Add JTI
        import uuid
        token_payload["jti"] = str(uuid.uuid4())
        
        return jwt.encode(
            token_payload,
            self.secret,
            algorithm=self.algorithm
        )
    
    def create_refresh_token(self, payload: Dict) -> str:
        """Create long-lived refresh token"""
        token_payload = {
            **payload,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=self.refresh_exp_days),
            "iat": datetime.utcnow(),
            "iss": "fastapp",
            "aud": "fastapp-users"
        }
        
        # Add JTI
        import uuid
        token_payload["jti"] = str(uuid.uuid4())
        
        return jwt.encode(
            token_payload,
            self.secret,
            algorithm=self.algorithm
        )
    
    def create_token_pair(self, payload: Dict) -> Tuple[str, str]:
        """Create both access and refresh tokens"""
        access_token = self.create_access_token(payload)
        refresh_token = self.create_refresh_token(payload)
        return access_token, refresh_token

    async def verify(self, token: str, allow_expired: bool = False) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            # Check blacklist first (if enabled)
            if self.use_blacklist and not allow_expired:
                from core.services.auth.jwt_blacklist import get_blacklist_service
                blacklist = get_blacklist_service()
                if await blacklist.is_blacklisted(token):
                    logger.warning("Token is blacklisted")
                    return None
            
            # Verify token
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                options={"verify_exp": not allow_expired},
                audience="fastapp-users",
                issuer="fastapp"
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def verify_sync(self, token: str, allow_expired: bool = False) -> Optional[Dict]:
        """Synchronous version of verify (for backward compatibility)"""
        try:
            # Note: Blacklist check is async only, so sync version skips it
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                options={"verify_exp": not allow_expired},
                audience="fastapp-users",
                issuer="fastapp"
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def decode_without_verification(self, token: str) -> Optional[Dict]:
        """Decode token without verification (for blacklist purposes)"""
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=[self.algorithm]
            )
        except Exception as e:
            logger.error(f"Failed to decode token: {e}")
            return None
    
    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """Get expiration time from token without verification"""
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=[self.algorithm]
            )
            exp = payload.get("exp")
            if exp:
                return datetime.fromtimestamp(exp)
            return None
        except Exception:
            return None
    
    def is_token_expiring_soon(self, token: str, minutes_threshold: int = 5) -> bool:
        """Check if token expires within the threshold"""
        exp = self.get_token_expiration(token)
        if exp:
            return exp <= datetime.utcnow() + timedelta(minutes=minutes_threshold)
        return False