"""User Service - User management functionality"""
from core.utils.logger import get_logger
from typing import Dict, Optional
from core.services.auth.security import security
from core.services.auth.providers.jwt import JWTProvider

logger = get_logger(__name__)


class UserService:
    """
    User management service.
    Handles user CRUD operations.
    """
    
    def __init__(self, db_service=None):
        """
        Initialize user service.
        
        Args:
            db_service: Database service instance (injected)
        """
        self.db = db_service
        self.jwt = JWTProvider()

    async def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user and return JWT"""
        user = await self.get_user_by_email(email)
        if not user or not security.verify_password(password, user.get('password_hash', '')):
            return None
            
        token = self.jwt.create({
            "user_id": user["_id"],
            "roles": user.get("roles", [])
        })
        return {"user": user, "token": token}

    async def register(self, email: str, password: str, **extra) -> Optional[Dict]:
        """Register new user with hashed password"""
        if await self.get_user_by_email(email):
            return None
            
        user_data = {
            **extra,
            "email": email,
            "password_hash": security.hash_password(password),
            "created_at": datetime.utcnow()
        }
        # Save to DB
        return await self._create_user(user_data)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User data dict or None if not found
        """
        try:
            if self.db:
                user = await self.db.find_one("users", {"email": email})
                if user:
                    # Remove sensitive data
                    return {k: v for k, v in user.items() if k != "password_hash"}
            return None
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            return None
    
    async def update_user(self, user_id: str, updates: Dict) -> bool:
        """
        Update user data.
        
        Args:
            user_id: User's unique identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Don't allow updating sensitive fields directly
            forbidden_fields = ["password_hash", "_id", "created_at"]
            updates = {k: v for k, v in updates.items() if k not in forbidden_fields}
            
            if self.db:
                await self.db.update_one("users", {"_id": user_id}, updates)
                logger.info(f"Updated user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.db:
                await self.db.delete_one("users", {"_id": user_id})
                logger.info(f"Deleted user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
