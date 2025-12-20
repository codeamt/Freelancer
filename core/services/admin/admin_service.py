"""Admin Service - Admin operations and user management"""
from core.utils.logger import get_logger
from typing import Dict, List, Optional
from datetime import datetime

logger = get_logger(__name__)


class AdminService:
    """
    Core admin service.
    Provides admin operations for user management and system monitoring.
    """
    
    def __init__(self, db_service=None, auth_service=None):
        """
        Initialize admin service.
        
        Args:
            db_service: Database service instance
            auth_service: Auth service instance
        """
        self.db = db_service
        self.auth = auth_service
    
    async def get_all_users(self, limit: int = 100, skip: int = 0) -> List[Dict]:
        """
        Get all users (admin only).
        
        Args:
            limit: Maximum number of users to return
            skip: Number of users to skip (pagination)
            
        Returns:
            List of user data dicts
        """
        try:
            if self.db:
                users = await self.db.find("users", {}, limit=limit, skip=skip)
                # Remove sensitive data
                return [{k: v for k, v in user.items() if k != "password_hash"} 
                        for user in users]
            return []
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []
    
    async def get_user_count(self) -> int:
        """
        Get total number of users.
        
        Returns:
            Total user count
        """
        try:
            if self.db:
                return await self.db.count("users", {})
            return 0
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0
    
    async def get_users_by_role(self, role: str) -> List[Dict]:
        """
        Get all users with a specific role.
        
        Args:
            role: Role name to filter by
            
        Returns:
            List of user data dicts
        """
        try:
            if self.db:
                users = await self.db.find("users", {"roles": role})
                return [{k: v for k, v in user.items() if k != "password_hash"} 
                        for user in users]
            return []
        except Exception as e:
            logger.error(f"Error fetching users by role {role}: {e}")
            return []
    
    async def update_user_role(self, user_id: str, roles: List[str]) -> bool:
        """
        Update user roles (admin only).
        
        Args:
            user_id: User's unique identifier
            roles: List of role names
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.db:
                await self.db.update_one("users", {"_id": user_id}, {"roles": roles})
                logger.info(f"Admin updated roles for user {user_id}: {roles}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating user roles: {e}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user (admin only).
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.db:
                await self.db.delete_one("users", {"_id": user_id})
                logger.info(f"Admin deleted user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    async def ban_user(self, user_id: str, reason: str = None) -> bool:
        """
        Ban a user (admin only).
        
        Args:
            user_id: User's unique identifier
            reason: Optional reason for ban
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.db:
                await self.db.update_one("users", {"_id": user_id}, {
                    "banned": True,
                    "banned_at": datetime.utcnow(),
                    "ban_reason": reason
                })
                logger.info(f"Admin banned user {user_id}: {reason}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            return False
    
    async def unban_user(self, user_id: str) -> bool:
        """
        Unban a user (admin only).
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.db:
                await self.db.update_one("users", {"_id": user_id}, {
                    "banned": False,
                    "banned_at": None,
                    "ban_reason": None
                })
                logger.info(f"Admin unbanned user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            return False
    
    async def get_system_stats(self) -> Dict:
        """
        Get system statistics (admin only).
        
        Returns:
            Dictionary with system stats
        """
        try:
            stats = {
                "total_users": await self.get_user_count(),
                "timestamp": datetime.utcnow()
            }
            
            # Get role counts
            if self.db:
                for role in ["admin", "instructor", "student", "user"]:
                    users = await self.get_users_by_role(role)
                    stats[f"{role}_count"] = len(users)
            
            return stats
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    async def search_users(self, query: str) -> List[Dict]:
        """
        Search users by username or email.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching user data dicts
        """
        try:
            if self.db:
                users = await self.db.find("users", {
                    "$or": [
                        {"username": {"$regex": query, "$options": "i"}},
                        {"email": {"$regex": query, "$options": "i"}}
                    ]
                })
                return [{k: v for k, v in user.items() if k != "password_hash"} 
                        for user in users]
            return []
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
