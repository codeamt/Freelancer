"""User Service - User CRUD operations"""
from core.utils.logger import get_logger
from core.utils.security import hash_password
from typing import Dict, List, Optional
from datetime import datetime

logger = get_logger(__name__)


class UserService:
    """
    Service for user CRUD operations.
    Handles user profile management, updates, and queries.
    """
    
    def __init__(self, db_service=None):
        """
        Initialize user service.
        
        Args:
            db_service: Database service instance (injected)
        """
        self.db = db_service
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Get user by email address.
        
        Args:
            email: User email
            
        Returns:
            User data dict or None if not found
        """
        try:
            if not self.db:
                return None
            
            user = await self.db.find_one("users", {"email": email})
            if user:
                # Remove sensitive data
                return {k: v for k, v in user.items() if k != "password_hash"}
            return None
            
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User data dict or None if not found
        """
        try:
            if not self.db:
                return None
            
            user = await self.db.find_one("users", {"username": username})
            if user:
                # Remove sensitive data
                return {k: v for k, v in user.items() if k != "password_hash"}
            return None
            
        except Exception as e:
            logger.error(f"Error fetching user by username {username}: {e}")
            return None
    
    async def update_user_profile(
        self,
        user_id: str,
        updates: Dict
    ) -> Optional[Dict]:
        """
        Update user profile.
        
        Args:
            user_id: User's unique identifier
            updates: Dict of fields to update
            
        Returns:
            Updated user data or None if failed
        """
        try:
            if not self.db:
                return None
            
            # Don't allow updating sensitive fields directly
            forbidden_fields = ["password_hash", "roles", "_id", "created_at"]
            clean_updates = {k: v for k, v in updates.items() if k not in forbidden_fields}
            
            # Add updated_at timestamp
            clean_updates["updated_at"] = datetime.utcnow()
            
            # Update user
            updated_user = await self.db.update_one(
                "users",
                {"_id": user_id},
                clean_updates
            )
            
            if updated_user:
                logger.info(f"Updated profile for user {user_id}")
                return {k: v for k, v in updated_user.items() if k != "password_hash"}
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            return None
    
    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User's unique identifier
            old_password: Current password (for verification)
            new_password: New password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.db:
                return False
            
            # Get user with password hash
            user = await self.db.find_one("users", {"_id": user_id})
            if not user:
                return False
            
            # Verify old password
            from core.utils.security import verify_password
            if not verify_password(old_password, user.get("password_hash", "")):
                logger.warning(f"Password change failed: Invalid old password for user {user_id}")
                return False
            
            # Update password
            new_hash = hash_password(new_password)
            await self.db.update_one(
                "users",
                {"_id": user_id},
                {
                    "password_hash": new_hash,
                    "password_changed_at": datetime.utcnow()
                }
            )
            
            logger.info(f"Password changed successfully for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user account.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.db:
                return False
            
            # Soft delete - mark as deleted instead of removing
            await self.db.update_one(
                "users",
                {"_id": user_id},
                {
                    "deleted": True,
                    "deleted_at": datetime.utcnow()
                }
            )
            
            logger.info(f"User {user_id} marked as deleted")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 50,
        role: Optional[str] = None
    ) -> List[Dict]:
        """
        List users with pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of users per page
            role: Optional role filter
            
        Returns:
            List of user dicts
        """
        try:
            if not self.db:
                return []
            
            # Build query
            query = {"deleted": {"$ne": True}}
            if role:
                query["roles"] = role
            
            # Calculate skip
            skip = (page - 1) * page_size
            
            # Fetch users
            users = await self.db.find_many(
                "users",
                query,
                limit=page_size,
                skip=skip,
                sort={"created_at": -1}
            )
            
            # Remove sensitive data
            return [
                {k: v for k, v in user.items() if k != "password_hash"}
                for user in users
            ]
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    async def search_users(self, search_term: str, limit: int = 20) -> List[Dict]:
        """
        Search users by username or email.
        
        Args:
            search_term: Search term
            limit: Maximum results
            
        Returns:
            List of matching user dicts
        """
        try:
            if not self.db:
                return []
            
            # Search by username or email (case-insensitive)
            query = {
                "$or": [
                    {"username": {"$regex": search_term, "$options": "i"}},
                    {"email": {"$regex": search_term, "$options": "i"}}
                ],
                "deleted": {"$ne": True}
            }
            
            users = await self.db.find_many("users", query, limit=limit)
            
            # Remove sensitive data
            return [
                {k: v for k, v in user.items() if k != "password_hash"}
                for user in users
            ]
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
