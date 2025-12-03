"""
Universal Authentication Service

Provides core authentication utilities for all domains.
Each domain implements its own UI/routes but uses this service for:
- JWT token creation/verification
- Password hashing/verification
- Role & permission management
- Session management
- User context helpers

Usage:
    from add_ons.services.auth import AuthService, get_current_user, require_role
    
    # In domain routes
    auth = AuthService(db_service)
    user = await auth.authenticate_user(email, password)
    token = auth.create_access_token(user["_id"])
"""

import jwt
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, Request
from functools import wraps
from core.utils.security import hash_password, verify_password
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = 12

# Role-Permission Mapping
ROLE_PERMISSIONS = {
    "admin": ["*"],  # Admin has all permissions
    "instructor": [
        "courses.create",
        "courses.update",
        "courses.delete",
        "lessons.create",
        "lessons.update",
        "lessons.delete",
    ],
    "student": [
        "courses.view",
        "courses.enroll",
        "lessons.view",
        "assessments.take",
    ],
    "user": [
        "profile.view",
        "profile.update",
    ]
}


class AuthService:
    """
    Universal authentication service for all domains.
    
    Provides JWT, password hashing, role/permission management.
    Domains use this service but implement their own UI/routes.
    """
    
    def __init__(self, db_service=None):
        """
        Initialize auth service.
        
        Args:
            db_service: Database service instance (optional for demo mode)
        """
        self.db = db_service
        # In-memory cache for demo mode
        self._user_cache = {}
        self._role_cache = {}
    
    # -------------------------------------------------------------------------
    # JWT Token Management
    # -------------------------------------------------------------------------
    
    def create_access_token(self, user_id: str, extra_data: dict = None) -> str:
        """
        Create JWT access token.
        
        Args:
            user_id: User's unique identifier
            extra_data: Additional data to include in token
            
        Returns:
            JWT token string
        """
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS),
            "iat": datetime.utcnow(),
            **(extra_data or {})
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        logger.debug(f"JWT created for user {user_id}")
        return token
    
    def verify_access_token(self, token: str) -> dict:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            logger.debug(f"JWT verified for user {payload.get('sub')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def get_user_from_token(self, token: str) -> str:
        """
        Extract user ID from token.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID
        """
        payload = self.verify_access_token(token)
        return payload.get("sub")
    
    # -------------------------------------------------------------------------
    # User Authentication
    # -------------------------------------------------------------------------
    
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
            # Find user by username or email
            if self.db and hasattr(self.db, 'db') and self.db.db is not None:
                user = await self.db.find_one("users", {
                    "$or": [
                        {"username": username},
                        {"email": username}
                    ]
                })
            else:
                # Demo mode - search in-memory cache
                user = None
                for cached_user in self._user_cache.values():
                    if isinstance(cached_user, dict) and (
                        cached_user.get("username") == username or 
                        cached_user.get("email") == username
                    ):
                        user = cached_user
                        break
            
            if not user:
                logger.warning(f"Authentication failed: User not found - {username}")
                return None
            
            # Verify password
            if not verify_password(password, user.get("password_hash", "")):
                logger.warning(f"Authentication failed: Invalid password - {username}")
                return None
            
            # Remove sensitive data
            user_data = {k: v for k, v in user.items() if k != "password_hash"}
            user_data["last_login"] = datetime.utcnow()
            
            # Update last login
            if self.db and hasattr(self.db, 'db') and self.db.db is not None:
                await self.db.update_one("users", {"_id": user["_id"]}, {
                    "last_login": user_data["last_login"]
                })
            
            logger.info(f"User authenticated successfully: {username}")
            return user_data
            
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
            # Check if user already exists
            if self.db and hasattr(self.db, 'db') and self.db.db is not None:
                existing = await self.db.find_one("users", {
                    "$or": [
                        {"email": email},
                        {"username": username or email}
                    ]
                })
            else:
                # Demo mode - check in-memory cache
                existing = None
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
            
            # Create user document
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
            
            # Save to database
            if self.db and hasattr(self.db, 'db') and self.db.db is not None:
                user_id = await self.db.insert_one("users", user_data)
                user_data["_id"] = user_id
            else:
                # Demo mode - store in memory
                self._user_cache[user_id] = user_data
                self._user_cache[email] = user_data
                if username:
                    self._user_cache[username] = user_data
            
            # Remove sensitive data from response
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
            if self.db and hasattr(self.db, 'db') and self.db.db is not None:
                user = await self.db.find_one("users", {"_id": user_id})
            else:
                user = self._user_cache.get(user_id)
            
            if user:
                return {k: v for k, v in user.items() if k != "password_hash"}
            return None
            
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None
    
    # -------------------------------------------------------------------------
    # Role & Permission Management
    # -------------------------------------------------------------------------
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get all roles for a user.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of role names
        """
        # Check cache first
        if user_id in self._role_cache:
            return self._role_cache[user_id].get("roles", [])
        
        # Fetch from database if available
        if self.db and hasattr(self.db, 'db') and self.db.db is not None:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                user = loop.run_until_complete(
                    self.db.find_one("users", {"_id": user_id})
                )
                if user:
                    roles = user.get("roles", ["user"])
                    self._role_cache[user_id] = {"roles": roles}
                    return roles
            except Exception as e:
                logger.error(f"Error fetching roles for user {user_id}: {e}")
        
        return ["user"]
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """
        Get all permissions for a user based on their roles.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of permission names
        """
        roles = self.get_user_roles(user_id)
        
        permissions = set()
        for role in roles:
            permissions.update(ROLE_PERMISSIONS.get(role, []))
        
        return list(permissions)
    
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
        
        # Check for wildcard permission (admin)
        if "*" in permissions:
            return True
        
        # Check for exact permission
        if permission in permissions:
            return True
        
        # Check for wildcard in permission (e.g., "courses.*")
        permission_parts = permission.split(".")
        if len(permission_parts) > 1:
            wildcard = f"{permission_parts[0]}.*"
            if wildcard in permissions:
                return True
        
        return False
    
    def has_role(self, user_id: str, role: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            user_id: User's unique identifier
            role: Role to check
            
        Returns:
            True if user has role, False otherwise
        """
        roles = self.get_user_roles(user_id)
        return role in roles
    
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
            if self.db and hasattr(self.db, 'db') and self.db.db is not None:
                await self.db.update_one("users", {"_id": user_id}, {"roles": roles})
            
            # Update cache
            self._role_cache[user_id] = {"roles": roles}
            
            logger.info(f"Updated roles for user {user_id}: {roles}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating roles for user {user_id}: {e}")
            return False


# -----------------------------------------------------------------------------
# Helper Functions & Decorators
# -----------------------------------------------------------------------------

async def get_current_user(request: Request, auth_service: AuthService = None) -> Optional[Dict]:
    """
    Get current user from request (cookie or header).
    
    Args:
        request: FastAPI/Starlette request
        auth_service: AuthService instance (optional)
        
    Returns:
        User data dict or None if not authenticated
    """
    # Try to get token from cookie
    token = request.cookies.get("access_token")
    
    # Fallback to Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        return None
    
    try:
        # Create temporary auth service if not provided
        if not auth_service:
            auth_service = AuthService()
        
        # Verify token and get user ID
        user_id = auth_service.get_user_from_token(token)
        
        # Fetch user data
        user = await auth_service.get_user_by_id(user_id)
        return user
        
    except Exception as e:
        logger.warning(f"Failed to get current user: {e}")
        return None


def require_role(required_role: str):
    """
    Decorator to require specific role for route access.
    
    Usage:
        @require_role("admin")
        async def admin_dashboard(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = next((a for a in args if isinstance(a, Request)), None)
            if not request:
                raise HTTPException(status_code=400, detail="Request not found")
            
            user = await get_current_user(request)
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            auth_service = AuthService()
            if not auth_service.has_role(user["_id"], required_role):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(required_permission: str):
    """
    Decorator to require specific permission for route access.
    
    Usage:
        @require_permission("courses.create")
        async def create_course(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = next((a for a in args if isinstance(a, Request)), None)
            if not request:
                raise HTTPException(status_code=400, detail="Request not found")
            
            user = await get_current_user(request)
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            auth_service = AuthService()
            if not auth_service.has_permission(user["_id"], required_permission):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


__all__ = [
    "AuthService",
    "get_current_user",
    "require_role",
    "require_permission",
    "ROLE_PERMISSIONS",
]
