"""JWT Token Blacklist Service

Manages blacklisted JWT tokens to ensure logout security.
Tokens are added to blacklist on logout and checked during verification.
"""

import os
from typing import Optional, Set
from datetime import datetime, timedelta
import json
import redis.asyncio as redis
from core.utils.logger import get_logger
from core.services.auth.providers.jwt import JWTProvider

logger = get_logger(__name__)


class JWTBlacklistService:
    """Service for managing JWT token blacklist"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize blacklist service
        
        Args:
            redis_url: Redis connection URL. If None, uses REDIS_URL env var
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client: Optional[redis.Redis] = None
        self.jwt_provider = JWTProvider()
        
        # Blacklist key prefix
        self.BLACKLIST_PREFIX = "jwt:blacklist:"
        # Token expiration buffer (in seconds)
        self.EXPIRATION_BUFFER = 300  # 5 minutes
        
    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                await self.redis_client.ping()
                logger.info("Connected to Redis for JWT blacklist")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self.redis_client
    
    async def add_to_blacklist(self, token: str, reason: str = "logout") -> bool:
        """Add a JWT token to the blacklist
        
        Args:
            token: JWT token to blacklist
            reason: Reason for blacklisting (e.g., "logout", "revoke", "password_change")
            
        Returns:
            True if successfully added, False otherwise
        """
        try:
            # Decode token to get expiration
            payload = self.jwt_provider.verify(token, allow_expired=True)
            if not payload:
                logger.warning("Cannot blacklist invalid token")
                return False
            
            # Get token JTI (JWT ID) or create one from token hash
            jti = payload.get("jti")
            if not jti:
                # Create JTI from token hash if not present
                import hashlib
                jti = hashlib.sha256(token.encode()).hexdigest()
            
            # Calculate blacklist expiration
            exp = payload.get("exp")
            if exp:
                # Use token expiration + buffer
                blacklist_until = datetime.fromtimestamp(exp) + timedelta(seconds=self.EXPIRATION_BUFFER)
            else:
                # Default to 24 hours from now
                blacklist_until = datetime.utcnow() + timedelta(hours=24)
            
            # Store in Redis with TTL
            redis = await self._get_redis()
            key = f"{self.BLACKLIST_PREFIX}{jti}"
            
            # Store blacklist entry with metadata
            blacklist_data = {
                "jti": jti,
                "reason": reason,
                "blacklisted_at": datetime.utcnow().isoformat(),
                "expires_at": blacklist_until.isoformat(),
                "user_id": payload.get("user_id"),
                "role": payload.get("role")
            }
            
            # Calculate TTL in seconds
            ttl = int((blacklist_until - datetime.utcnow()).total_seconds())
            if ttl > 0:
                await redis.setex(key, ttl, json.dumps(blacklist_data))
                logger.info(f"Token {jti} blacklisted until {blacklist_until}")
                return True
            else:
                logger.warning(f"Token {jti} already expired")
                return False
                
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    async def is_blacklisted(self, token: str) -> bool:
        """Check if a JWT token is blacklisted
        
        Args:
            token: JWT token to check
            
        Returns:
            True if token is blacklisted, False otherwise
        """
        try:
            # Decode token to get JTI
            payload = self.jwt_provider.verify(token, allow_expired=True)
            if not payload:
                return False
            
            # Get token JTI
            jti = payload.get("jti")
            if not jti:
                # Create JTI from token hash if not present
                import hashlib
                jti = hashlib.sha256(token.encode()).hexdigest()
            
            # Check Redis
            redis = await self._get_redis()
            key = f"{self.BLACKLIST_PREFIX}{jti}"
            result = await redis.get(key)
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to check blacklist: {e}")
            # On error, assume not blacklisted (fail open)
            return False
    
    async def remove_from_blacklist(self, jti: str) -> bool:
        """Remove a token from blacklist (e.g., for testing)
        
        Args:
            jti: JWT ID to remove
            
        Returns:
            True if successfully removed, False otherwise
        """
        try:
            redis = await self._get_redis()
            key = f"{self.BLACKLIST_PREFIX}{jti}"
            result = await redis.delete(key)
            
            if result > 0:
                logger.info(f"Token {jti} removed from blacklist")
                return True
            else:
                logger.warning(f"Token {jti} not found in blacklist")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove from blacklist: {e}")
            return False
    
    async def get_blacklist_info(self, jti: str) -> Optional[dict]:
        """Get blacklist information for a token
        
        Args:
            jti: JWT ID to lookup
            
        Returns:
            Blacklist data or None if not found
        """
        try:
            redis = await self._get_redis()
            key = f"{self.BLACKLIST_PREFIX}{jti}"
            result = await redis.get(key)
            
            if result:
                return json.loads(result)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get blacklist info: {e}")
            return None
    
    async def cleanup_expired(self) -> int:
        """Clean up expired blacklist entries
        Redis handles this automatically with TTL, but this can be used for manual cleanup
        
        Returns:
            Number of entries cleaned
        """
        # Redis automatically expires keys with TTL
        # This is a placeholder for potential manual cleanup
        logger.info("Blacklist cleanup handled automatically by Redis TTL")
        return 0
    
    async def blacklist_user_tokens(self, user_id: int, reason: str = "password_change") -> bool:
        """Blacklist all tokens for a user (e.g., on password change)
        
        Args:
            user_id: User ID whose tokens to blacklist
            reason: Reason for blacklisting
            
        Returns:
            True if successful, False otherwise
        """
        # This would require tracking active tokens per user
        # For now, we'll log the action
        logger.info(f"Would blacklist all tokens for user {user_id} (reason: {reason})")
        # TODO: Implement token tracking per user
        return True
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None


# Global blacklist service instance
_blacklist_service: Optional[JWTBlacklistService] = None


def get_blacklist_service() -> JWTBlacklistService:
    """Get global blacklist service instance"""
    global _blacklist_service
    if _blacklist_service is None:
        _blacklist_service = JWTBlacklistService()
    return _blacklist_service
