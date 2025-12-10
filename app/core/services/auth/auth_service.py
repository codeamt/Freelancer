"""
Authentication Service

Handles authentication, authorization, and session management.
Delegates user data access to UserRepository.
"""
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from core.db.repositories.user_repository import UserRepository
from core.services.auth.providers.jwt import JWTProvider
from core.services.auth.permissions import permission_registry
from core.utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """
    Authentication and authorization service.
    
    Responsibilities:
    - Authenticate users (login)
    - Create and verify tokens
    - Manage sessions
    - Check permissions
    
    Does NOT handle:
    - User CRUD (that's UserService)
    - Direct database access (that's UserRepository)
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        jwt_provider: Optional[JWTProvider] = None
    ):
        """
        Initialize auth service.
        
        Args:
            user_repository: User repository for data access
            jwt_provider: JWT provider (creates one if not provided)
        """
        self.user_repo = user_repository
        self.jwt = jwt_provider or JWTProvider()
    
    # ========================================================================
    # Authentication
    # ========================================================================
    
    async def login(
        self,
        email: str,
        password: str,
        create_session: bool = True
    ) -> Optional[Dict]:
        """
        Authenticate user with email/password.
        
        Args:
            email: User email
            password: Plain text password
            create_session: Whether to create Redis session
            
        Returns:
            Dict with user and token, or None if auth fails
            {
                "user": User entity,
                "token": JWT string,
                "expires_at": datetime
            }
        """
        # Verify credentials via repository
        user = await self.user_repo.verify_password(email, password)
        
        if not user:
            logger.warning(f"Login failed for {email}")
            return None
        
        # Check if user is active (if you have that field)
        # if not user.is_active:
        #     logger.warning(f"Login blocked for inactive user {user.id}")
        #     return None
        
        # Create JWT token
        token_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "type": "access"
        }
        
        token = self.jwt.create(token_data, expires_hours=24)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Create session in Redis
        if create_session:
            await self.user_repo.create_session(
                user_id=user.id,
                session_token=token,
                ttl_seconds=86400  # 24 hours
            )
        
        logger.info(f"User {user.id} logged in successfully")
        
        return {
            "user": user,
            "token": token,
            "expires_at": expires_at
        }
    
    async def logout(self, token: str):
        """
        Log out user by revoking token/session.
        
        Args:
            token: JWT token to revoke
        """
        # Revoke session in Redis
        await self.user_repo.revoke_session(token)
        logger.info("User logged out")
    
    async def logout_all(self, user_id: int):
        """
        Log out user from all devices/sessions.
        
        Args:
            user_id: User ID
        """
        await self.user_repo.revoke_all_sessions(user_id)
        logger.info(f"User {user_id} logged out from all devices")
    
    async def refresh_token(self, old_token: str) -> Optional[Dict]:
        """
        Refresh an expired or expiring token.
        
        Args:
            old_token: Current token
            
        Returns:
            Dict with new token or None if invalid
        """
        # Verify old token (allow expired tokens for refresh)
        payload = self.jwt.verify(old_token, allow_expired=True)
        
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        # Get fresh user data
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            return None
        
        # Create new token
        new_token = self.jwt.create({
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "type": "access"
        })
        
        # Update session
        await self.user_repo.revoke_session(old_token)
        await self.user_repo.create_session(user.id, new_token)
        
        logger.info(f"Token refreshed for user {user_id}")
        
        return {
            "user": user,
            "token": new_token,
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
    
    # ========================================================================
    # Token Verification
    # ========================================================================
    
    async def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify token and return payload.
        
        Args:
            token: JWT token
            
        Returns:
            Token payload or None if invalid
        """
        # Verify JWT signature and expiration
        payload = self.jwt.verify(token)
        
        if not payload:
            return None
        
        # Check if session exists in Redis (if using sessions)
        session = await self.user_repo.get_session(token)
        if session is None:
            # Token is valid but session doesn't exist
            # This is OK if not using Redis sessions
            logger.debug(f"Token valid but no Redis session found")
        
        return payload
    
    async def get_current_user(self, token: str):
        """
        Get user from token.
        
        Args:
            token: JWT token
            
        Returns:
            User entity or None
        """
        payload = await self.verify_token(token)
        
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        return await self.user_repo.get_user_by_id(user_id)
    
    # ========================================================================
    # Authorization
    # ========================================================================
    
    async def check_permission(
        self,
        user_id: int,
        resource: str,
        action: str,
        context: Optional[Dict] = None
    ) -> bool:
        """
        Check if user has permission for resource/action.
        
        Args:
            user_id: User ID
            resource: Resource name (e.g., "product", "order")
            action: Action name (e.g., "read", "write", "delete")
            context: Optional context (e.g., {"product_id": 123})
            
        Returns:
            True if permitted
        """
        user = await self.user_repo.get_user_by_id(user_id)
        
        if not user:
            return False
        
        # Build context
        ctx = context or {}
        ctx.update({
            "user_id": user_id,
            "user_role": user.role,
            "user_email": user.email
        })
        
        # Check via permission registry
        has_perm = permission_registry.check_permission(
            roles=[user.role],
            resource=resource,
            action=action,
            context=ctx
        )
        
        if not has_perm:
            logger.warning(
                f"Permission denied: user {user_id} ({user.role}) "
                f"cannot {action} {resource}"
            )
        
        return has_perm
    
    async def require_permission(
        self,
        user_id: int,
        resource: str,
        action: str,
        context: Optional[Dict] = None
    ):
        """
        Require permission or raise exception.
        
        Args:
            user_id: User ID
            resource: Resource name
            action: Action name
            context: Optional context
            
        Raises:
            PermissionError: If user lacks permission
        """
        if not await self.check_permission(user_id, resource, action, context):
            raise PermissionError(
                f"User {user_id} lacks permission to {action} {resource}"
            )
    
    async def has_role(self, user_id: int, role: str) -> bool:
        """
        Check if user has specific role.
        
        Args:
            user_id: User ID
            role: Role name
            
        Returns:
            True if user has role
        """
        user = await self.user_repo.get_user_by_id(user_id)
        return user and user.role == role
    
    async def has_any_role(self, user_id: int, roles: List[str]) -> bool:
        """
        Check if user has any of the specified roles.
        
        Args:
            user_id: User ID
            roles: List of role names
            
        Returns:
            True if user has any role
        """
        user = await self.user_repo.get_user_by_id(user_id)
        return user and user.role in roles
    
    async def require_role(self, user_id: int, role: str):
        """
        Require role or raise exception.
        
        Args:
            user_id: User ID
            role: Required role
            
        Raises:
            PermissionError: If user lacks role
        """
        if not await self.has_role(user_id, role):
            raise PermissionError(f"User {user_id} must have role '{role}'")


class AnonymousUser:
    """
    Represents an anonymous (not logged in) user.
    
    Useful for permission checks on unauthenticated requests.
    """
    id = None
    email = None
    role = "anonymous"
    
    def __bool__(self):
        return False
    
    def __repr__(self):
        return "<AnonymousUser>"