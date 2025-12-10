"""User Service - User management functionality"""
"""
User Service - User Management

Handles user CRUD operations and profile management.
Does NOT handle authentication (that's AuthService).
"""
from typing import Dict, Optional, List
from datetime import datetime
from core.db.repositories.user_repository import UserRepository
from core.utils.logger import get_logger
import re

logger = get_logger(__name__)


class UserService:
    """
    User management service.
    
    Responsibilities:
    - Create, read, update, delete users
    - User validation
    - Profile management
    
    Does NOT handle:
    - Authentication (that's AuthService)
    - Authorization checks (that's AuthService)
    """
    
    def __init__(self, user_repository: UserRepository):
        """
        Initialize user service.
        
        Args:
            user_repository: User repository instance
        """
        self.repo = user_repository
    
    # ========================================================================
    # User Creation
    # ========================================================================
    
    async def create_user(
        self,
        email: str,
        password: str,
        role: str = "user",
        profile_data: Optional[Dict] = None,
        skip_validation: bool = False
    ) -> Optional[int]:
        """
        Create new user.
        
        Args:
            email: User email
            password: Plain text password
            role: User role
            profile_data: Optional profile data
            skip_validation: Skip validation (for imports/seeds)
            
        Returns:
            User ID or None if creation fails
        """
        # Validate unless skipped
        if not skip_validation:
            # Check if email exists
            if await self.repo.user_exists(email):
                logger.warning(f"User creation failed: {email} already exists")
                return None
            
            # Validate email format
            if not self._is_valid_email(email):
                logger.warning(f"User creation failed: invalid email {email}")
                return None
            
            # Validate password strength
            validation_error = self._validate_password(password)
            if validation_error:
                logger.warning(f"User creation failed: {validation_error}")
                return None
        
        # Create user via repository
        try:
            user_id = await self.repo.create_user(
                email=email,
                password=password,
                role=role,
                profile_data=profile_data
            )
            
            logger.info(f"User {user_id} created with email {email}")
            return user_id
            
        except Exception as e:
            logger.error(f"Failed to create user {email}: {e}")
            return None
    
    async def register(
        self,
        email: str,
        password: str,
        profile_data: Optional[Dict] = None
    ) -> Optional[int]:
        """
        Register new user (alias for create_user with 'user' role).
        
        Args:
            email: User email
            password: Plain text password
            profile_data: Optional profile data
            
        Returns:
            User ID or None if registration fails
        """
        return await self.create_user(
            email=email,
            password=password,
            role="user",
            profile_data=profile_data
        )
    
    # ========================================================================
    # User Retrieval
    # ========================================================================
    
    async def get_user(
        self,
        user_id: int,
        include_profile: bool = False
    ):
        """Get user by ID."""
        return await self.repo.get_user_by_id(user_id, include_profile)
    
    async def get_user_by_email(self, email: str):
        """Get user by email."""
        user_data = await self.repo.get_user_by_email(email)
        if not user_data:
            return None
        return self.repo.from_dict(user_data)
    
    async def user_exists(self, email: str) -> bool:
        """Check if user exists."""
        return await self.repo.user_exists(email)
    
    async def list_users(
        self,
        role: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict:
        """
        List users with pagination.
        
        Args:
            role: Optional role filter
            page: Page number (1-indexed)
            per_page: Results per page
            
        Returns:
            Dict with users and pagination info
        """
        offset = (page - 1) * per_page
        
        users = await self.repo.list_users(role, per_page, offset)
        total = await self.repo.count_users(role)
        
        return {
            "users": users,
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page
        }
    
    # ========================================================================
    # User Updates
    # ========================================================================
    
    async def update_user(
        self,
        user_id: int,
        updates: Dict
    ) -> bool:
        """
        Update user data.
        
        Args:
            user_id: User ID
            updates: Fields to update
            
        Returns:
            True if successful
        """
        # Remove fields that shouldn't be updated this way
        forbidden = ['password_hash', 'created_at']
        updates = {k: v for k, v in updates.items() if k not in forbidden}
        
        if not updates:
            return True
        
        try:
            return await self.repo.update_user(user_id, updates)
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            return False
    
    async def update_profile(
        self,
        user_id: int,
        profile_updates: Dict
    ) -> bool:
        """
        Update user profile (MongoDB data).
        
        Args:
            user_id: User ID
            profile_updates: Profile fields to update
            
        Returns:
            True if successful
        """
        return await self.update_user(user_id, profile_updates)
    
    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password with verification.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            True if successful
        """
        # Get user to verify old password
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify old password
        verified = await self.repo.verify_password(user.email, old_password)
        if not verified:
            logger.warning(f"Password change failed: incorrect old password")
            return False
        
        # Validate new password
        validation_error = self._validate_password(new_password)
        if validation_error:
            logger.warning(f"Password change failed: {validation_error}")
            return False
        
        # Update password
        success = await self.repo.update_password(user_id, new_password)
        
        if success:
            logger.info(f"Password changed for user {user_id}")
        
        return success
    
    async def reset_password(
        self,
        user_id: int,
        new_password: str
    ) -> bool:
        """
        Reset password (admin function, no old password required).
        
        Args:
            user_id: User ID
            new_password: New password
            
        Returns:
            True if successful
        """
        # Validate new password
        validation_error = self._validate_password(new_password)
        if validation_error:
            logger.warning(f"Password reset failed: {validation_error}")
            return False
        
        success = await self.repo.update_password(user_id, new_password)
        
        if success:
            logger.info(f"Password reset for user {user_id}")
        
        return success
    
    async def change_role(
        self,
        user_id: int,
        new_role: str
    ) -> bool:
        """
        Change user role.
        
        Args:
            user_id: User ID
            new_role: New role
            
        Returns:
            True if successful
        """
        success = await self.repo.update_user(user_id, {'role': new_role})
        
        if success:
            logger.info(f"Role changed to {new_role} for user {user_id}")
        
        return success
    
    # ========================================================================
    # User Deletion
    # ========================================================================
    
    async def delete_user(self, user_id: int) -> bool:
        """
        Delete user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        try:
            success = await self.repo.delete_user(user_id)
            if success:
                logger.info(f"User {user_id} deleted")
            return success
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            return False
    
    # ========================================================================
    # Validation Helpers
    # ========================================================================
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _validate_password(self, password: str) -> Optional[str]:
        """
        Validate password strength.
        
        Returns:
            Error message if invalid, None if valid
        """
        if len(password) < 8:
            return "Password must be at least 8 characters"
        
        if not any(c.isupper() for c in password):
            return "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return "Password must contain at least one number"
        
        return None