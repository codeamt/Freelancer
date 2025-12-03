"""Core Auth Service - Shared authentication functionality"""
from core.utils.security import hash_password, verify_password
from core.utils.logger import get_logger
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import jwt
import os

logger = get_logger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = 24


class AuthService:
    """
    Core authentication service.
    Provides JWT token management and user authentication.
    """
    
    def __init__(self, db_service=None):
        """
        Initialize auth service.
        
        Args:
            db_service: Database service instance (injected)
        """
        self.db = db_service
        # In-memory cache for demo - replace with Redis in production
        self._user_cache = {}
        self._role_cache = {}
    
    @staticmethod
    def create_token(data: dict) -> str:
        """
        Create a JWT token.
        
        Args:
            data: Token payload data
            
        Returns:
            Encoded JWT token string
        """
        payload = {
            **data,
            "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token data or None if invalid
        """
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user with username/email and password.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User data dict if authenticated, None otherwise
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
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Get user data by ID.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User data dict or None if not found
        """
        try:
            # Check if database is available and connected
            if self.db and hasattr(self.db, 'db') and self.db.db is not None:
                user = await self.db.find_one("users", {"_id": user_id})
            else:
                # Demo mode - use in-memory cache
                user = self._user_cache.get(user_id)
            
            if user:
                # Remove sensitive data
                return {k: v for k, v in user.items() if k != "password_hash"}
            return None
            
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None
    
    async def register_user(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
        **extra_fields
    ) -> Optional[Dict]:
        """
        Register a new user.
        
        Args:
            email: User email
            password: Plain text password
            username: Optional username (defaults to email)
            **extra_fields: Additional user fields (e.g., roles)
            
        Returns:
            User data dict if successful, None otherwise
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
                    if cached_user.get("email") == email or cached_user.get("username") == (username or email):
                        existing = cached_user
                        break
            
            if existing:
                logger.warning(f"Registration failed: User already exists - {email}")
                return None
            
            # Create user document
            import uuid
            user_id = str(uuid.uuid4())
            
            # Get roles from extra_fields or default to ["user"]
            roles = extra_fields.pop("roles", ["user"])
            
            user_data = {
                "_id": user_id,
                "email": email,
                "username": username or email,
                "password_hash": hash_password(password),
                "roles": roles,
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
                # Also store by email and username for lookup
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
        if self.db:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                user = loop.run_until_complete(
                    self.db.find_one("users", {"_id": user_id})
                )
                if user:
                    roles = user.get("roles", ["user"])
                    # Cache for future requests
                    self._role_cache[user_id] = {"roles": roles}
                    return roles
            except Exception as e:
                logger.error(f"Error fetching roles for user {user_id}: {e}")
        
        # Default role
        return ["user"]
    
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
