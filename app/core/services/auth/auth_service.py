"""
Authentication Service

Handles authentication, authorization, and session management.
Delegates user data access to UserRepository.
"""
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import os
import uuid
from core.db.repositories.user_repository import UserRepository
from core.services.auth.providers.jwt import JWTProvider
from core.services.auth.permissions import permission_registry
from core.utils.logger import get_logger
from core.utils.security import hash_password, verify_password
from core.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    NotFoundError,
    AuthenticationError
)
from core.services.auth.models import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    TokenPayload,
    User
)

logger = get_logger(__name__)

# JWT configuration - JWT_SECRET MUST be set via environment variable
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError(
        "JWT_SECRET environment variable is required. "
        "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
    )
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = int(os.getenv("TOKEN_EXPIRATION_HOURS", "12"))


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
        user_repository: Optional[UserRepository] = None,
        jwt_provider: Optional[JWTProvider] = None
    ):
        """
        Initialize auth service.
        
        Args:
            user_repository: User repository for data access (optional for demo mode)
            jwt_provider: JWT provider (creates one if not provided)
        """
        self.user_repo = user_repository
        self.jwt = jwt_provider or JWTProvider()
        self._user_cache = {}
        self._role_cache = {}
    
    # ========================================================================
    # Authentication
    # ========================================================================
    
    async def login(
        self,
        request: LoginRequest
    ) -> LoginResponse:
        """
        Authenticate user with email/password.
        
        Args:
            request: Login request with username/email and password
            
        Returns:
            LoginResponse with user data and access token
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        # Verify credentials via repository (username can be email or username)
        user = await self.user_repo.verify_password(request.username, request.password)
        
        if not user:
            logger.warning(f"Login failed for {request.username}")
            raise InvalidCredentialsError()
        
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
        
        expires_hours = 24
        token = self.jwt.create(token_data)
        
        # Create session in Redis if remember_me is enabled
        if request.remember_me:
            await self.user_repo.create_session(
                user_id=user.id,
                session_token=token,
                ttl_seconds=86400 * 30  # 30 days for remember me
            )
        else:
            await self.user_repo.create_session(
                user_id=user.id,
                session_token=token,
                ttl_seconds=86400  # 24 hours
            )
        
        logger.info(f"User {user.id} logged in successfully")
        
        # Convert user dict to User model if needed
        user_model = User(
            _id=str(user.id),
            email=user.email,
            username=getattr(user, 'username', user.email.split('@')[0]),
            roles=getattr(user, 'roles', [user.role]) if hasattr(user, 'role') else [],
            created_at=getattr(user, 'created_at', datetime.utcnow()),
            status=getattr(user, 'status', 'active')
        )
        
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_hours * 3600,
            user=user_model
        )
    
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
    
    async def refresh_token(self, request: TokenRefreshRequest) -> TokenRefreshResponse:
        """
        Refresh an expired or expiring token.
        
        Args:
            request: Token refresh request with refresh token
            
        Returns:
            TokenRefreshResponse with new access token
            
        Raises:
            InvalidTokenError: If token is invalid
            NotFoundError: If user not found
        """
        # Verify old token (allow expired tokens for refresh)
        payload = self.jwt.verify(request.refresh_token, allow_expired=True)
        
        if not payload:
            raise InvalidTokenError("Cannot refresh invalid token")
        
        user_id = payload.get("user_id")
        if not user_id:
            raise InvalidTokenError("Token missing user_id")
        
        # Get fresh user data
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        
        # Create new token
        expires_hours = 24
        new_token = self.jwt.create({
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "type": "access"
        }, expires_hours=expires_hours)
        
        # Update session
        await self.user_repo.revoke_session(request.refresh_token)
        await self.user_repo.create_session(user.id, new_token)
        
        logger.info(f"Token refreshed for user {user_id}")
        
        return TokenRefreshResponse(
            access_token=new_token,
            token_type="bearer",
            expires_in=expires_hours * 3600
        )
    
    # ========================================================================
    # Token Verification
    # ========================================================================
    
    async def verify_token(self, token: str) -> TokenPayload:
        """
        Verify token and return payload.
        
        Args:
            token: JWT token
            
        Returns:
            TokenPayload with user information
            
        Raises:
            InvalidTokenError: If token is invalid or expired
        """
        # Verify JWT signature and expiration
        payload = self.jwt.verify(token)
        
        if not payload:
            raise InvalidTokenError()
        
        # Check if session exists in Redis (if using sessions)
        session = await self.user_repo.get_session(token)
        if session is None:
            # Token is valid but session doesn't exist
            # This is OK if not using Redis sessions
            logger.debug(f"Token valid but no Redis session found")
        
        # Convert to TokenPayload model
        return TokenPayload(
            sub=payload.get("user_id"),
            exp=payload.get("exp"),
            iat=payload.get("iat", int(datetime.utcnow().timestamp())),
            roles=payload.get("roles", [payload.get("role")]) if payload.get("role") else [],
            email=payload.get("email")
        )
    
    async def get_current_user(self, token: str):
        """
        Get user from token.
        
        Args:
            token: JWT token
            
        Returns:
            User entity or None
        """
        try:
            payload = await self.verify_token(token)
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            return None
        
        if not payload:
            return None
        
        # TokenPayload uses 'sub' for user_id
        user_id = getattr(payload, 'sub', None)
        if not user_id:
            return None
        
        # Ensure user_id is an integer
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id format: {user_id}")
            return None
        
        if self.user_repo:
            return await self.user_repo.get_user_by_id(user_id)
        else:
            user = self._user_cache.get(user_id)
            if user and isinstance(user, dict):
                return {k: v for k, v in user.items() if k != "password_hash"}
            return None
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate user with username/email and password.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User data dict (without password_hash) if authenticated, None otherwise
        """
        try:
            user = None
            
            if self.user_repo:
                user_entity = await self.user_repo.verify_password(username, password)
                if user_entity:
                    user = {
                        "_id": str(user_entity.id),
                        "id": user_entity.id,
                        "email": user_entity.email,
                        "role": user_entity.role,
                        "last_login": datetime.utcnow()
                    }
            else:
                for cached_user in self._user_cache.values():
                    if isinstance(cached_user, dict) and (
                        cached_user.get("username") == username or 
                        cached_user.get("email") == username
                    ):
                        if verify_password(password, cached_user.get("password_hash", "")):
                            user = {k: v for k, v in cached_user.items() if k != "password_hash"}
                            user["last_login"] = datetime.utcnow()
                        break
            
            if user:
                logger.info(f"User authenticated successfully: {username}")
                return user
            else:
                logger.warning(f"Authentication failed: {username}")
                return None
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def register_user(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
        roles: List[str] = None,
        **extra_fields
    ) -> Optional[Dict]:
        """
        Register a new user.
        
        Args:
            email: User email
            password: Plain text password
            username: Optional username (defaults to email)
            roles: List of roles (defaults to ["user"])
            **extra_fields: Additional user fields
            
        Returns:
            User data dict (without password_hash) if successful, None otherwise
        """
        try:
            existing = None
            
            if self.user_repo:
                if await self.user_repo.user_exists(email):
                    logger.warning(f"Registration failed: User already exists - {email}")
                    return None
            else:
                for cached_user in self._user_cache.values():
                    if isinstance(cached_user, dict) and (
                        cached_user.get("email") == email or 
                        cached_user.get("username") == (username or email)
                    ):
                        existing = cached_user
                        break
                
                if existing:
                    logger.warning(f"Registration failed: User already exists - {email}")
                    return None
            
            user_id = str(uuid.uuid4())
            user_data = {
                "_id": user_id,
                "email": email,
                "username": username or email,
                "password_hash": hash_password(password),
                "roles": roles or ["user"],
                "created_at": datetime.utcnow(),
                "email_verified": False,
                **extra_fields
            }
            
            if self.user_repo:
                created_id = await self.user_repo.create_user(
                    email=email,
                    password=password,
                    role=roles[0] if roles else "user",
                    profile_data=extra_fields
                )
                user_data["_id"] = str(created_id)
                user_data["id"] = created_id
            else:
                self._user_cache[user_id] = user_data
                self._user_cache[email] = user_data
                if username:
                    self._user_cache[username] = user_data
            
            response_data = {k: v for k, v in user_data.items() if k != "password_hash"}
            
            logger.info(f"User registered successfully: {email}")
            return response_data
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Get user data by ID.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User data dict (without password_hash) or None if not found
        """
        try:
            if self.user_repo:
                user_entity = await self.user_repo.get_user_by_id(int(user_id) if user_id.isdigit() else user_id)
                if user_entity:
                    return {
                        "_id": str(user_entity.id),
                        "id": user_entity.id,
                        "email": user_entity.email,
                        "role": user_entity.role,
                    }
            else:
                user = self._user_cache.get(user_id)
                if user and isinstance(user, dict):
                    return {k: v for k, v in user.items() if k != "password_hash"}
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None
    
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
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get all roles for a user.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of role names
        """
        if user_id in self._role_cache:
            return self._role_cache[user_id].get("roles", [])
        
        if self.user_repo:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                user = loop.run_until_complete(
                    self.user_repo.get_user_by_id(int(user_id) if user_id.isdigit() else user_id)
                )
                if user:
                    roles = [user.role] if hasattr(user, 'role') else ["user"]
                    self._role_cache[user_id] = {"roles": roles}
                    return roles
            except Exception as e:
                logger.error(f"Error fetching roles for user {user_id}: {e}")
        else:
            user = self._user_cache.get(user_id)
            if user and isinstance(user, dict):
                roles = user.get("roles", ["user"])
                self._role_cache[user_id] = {"roles": roles}
                return roles
        
        return ["user"]
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """
        Get all permissions for a user based on their roles.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of permission strings
        """
        roles = self.get_user_roles(user_id)
        permissions = permission_registry.resolve_permissions(roles)
        
        permission_strings = []
        for perm in permissions:
            if perm.resource == "*" and perm.action == "*":
                permission_strings.append("*")
            else:
                permission_strings.append(f"{perm.resource}.{perm.action}")
        
        return permission_strings
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_id: User's unique identifier
            permission: Permission to check (e.g., "courses.create")
            
        Returns:
            True if user has permission, False otherwise
        """
        permissions = self.get_user_permissions(user_id)
        
        if "*" in permissions:
            return True
        
        if permission in permissions:
            return True
        
        permission_parts = permission.split(".")
        if len(permission_parts) > 1:
            wildcard = f"{permission_parts[0]}.*"
            if wildcard in permissions:
                return True
        
        return False
    
    async def update_user_roles(self, user_id: str, roles: List[str]) -> bool:
        """
        Update user roles.
        
        Args:
            user_id: User's unique identifier
            roles: List of role names
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.user_repo:
                await self.user_repo.update_user(int(user_id) if user_id.isdigit() else user_id, {"role": roles[0]})
            else:
                user = self._user_cache.get(user_id)
                if user and isinstance(user, dict):
                    user["roles"] = roles
            
            self._role_cache[user_id] = {"roles": roles}
            
            logger.info(f"Updated roles for user {user_id}: {roles}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating roles for user {user_id}: {e}")
            return False
    
    # ========================================================================
    # Password Management
    # ========================================================================
    
    async def update_password(self, user_id: int, new_password: str) -> Dict:
        """
        Update user password.
        
        Args:
            user_id: User ID
            new_password: New plain text password (will be hashed)
            
        Returns:
            Dict with success status and error if any
        """
        try:
            # Validate password strength
            if len(new_password) < 8:
                return {
                    "success": False,
                    "error": "Password must be at least 8 characters"
                }
            
            # Update password (repository handles hashing)
            success = await self.user_repo.update_password(user_id, new_password)
            
            if success:
                logger.info(f"Password updated for user {user_id}")
                return {"success": True, "error": None}
            else:
                return {
                    "success": False,
                    "error": "Failed to update password"
                }
                
        except Exception as e:
            logger.error(f"Error updating password for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


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