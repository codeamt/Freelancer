"""
User Profile Service

Extends user management with profile features, avatar management, 
preferences, and account management.
"""

import os
import base64
import hashlib
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum

from core.utils.logger import get_logger
from core.services.audit_service import get_audit_service, AuditEventType

logger = get_logger(__name__)


class AccountStatus(Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"
    DELETED = "deleted"


@dataclass
class UserProfile:
    """User profile data structure"""
    user_id: int
    email: str
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    preferences: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class UserPreferences:
    """User preferences data structure"""
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    email_notifications: bool = True
    push_notifications: bool = True
    marketing_emails: bool = False
    newsletter: bool = False
    privacy_public_profile: bool = True
    privacy_show_email: bool = False
    privacy_show_activity: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreferences":
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class UserProfileService:
    """
    User profile management service.
    
    Features:
    - Profile management (view, edit, delete)
    - Avatar upload and management
    - User preferences and settings
    - Account deactivation workflow
    - Profile visibility controls
    """
    
    def __init__(self, user_service, storage_path: str = "uploads/avatars"):
        """
        Initialize profile service.
        
        Args:
            user_service: UserService instance
            storage_path: Path for avatar uploads
        """
        self.user_service = user_service
        self.storage_path = storage_path
        self.audit = get_audit_service()
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
    
    # ========================================================================
    # Profile Management
    # ========================================================================
    
    async def get_profile(
        self,
        user_id: int,
        include_preferences: bool = False
    ) -> Optional[UserProfile]:
        """
        Get user profile.
        
        Args:
            user_id: User ID
            include_preferences: Include user preferences
            
        Returns:
            UserProfile or None
        """
        try:
            user = await self.user_service.get_user(user_id, include_profile=True)
            if not user:
                return None
            
            profile = UserProfile(
                user_id=user.id,
                email=user.email,
                display_name=getattr(user, 'display_name', None),
                first_name=getattr(user, 'first_name', None),
                last_name=getattr(user, 'last_name', None),
                bio=getattr(user, 'bio', None),
                avatar_url=getattr(user, 'avatar_url', None),
                phone=getattr(user, 'phone', None),
                location=getattr(user, 'location', None),
                website=getattr(user, 'website', None),
                social_links=getattr(user, 'social_links', None),
                metadata=getattr(user, 'metadata', None),
                created_at=getattr(user, 'created_at', None),
                updated_at=getattr(user, 'updated_at', None),
            )
            
            if include_preferences:
                prefs = await self.get_preferences(user_id)
                profile.preferences = prefs.to_dict() if prefs else None
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get profile for user {user_id}: {e}")
            return None
    
    async def update_profile(
        self,
        user_id: int,
        profile_data: Dict[str, Any],
        actor_id: Optional[int] = None
    ) -> bool:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            profile_data: Profile fields to update
            actor_id: ID of user making the change (for audit)
            
        Returns:
            True if successful
        """
        try:
            # Allowed profile fields
            allowed_fields = {
                'display_name', 'first_name', 'last_name', 'bio',
                'phone', 'location', 'website', 'social_links'
            }
            
            # Filter to allowed fields
            updates = {
                k: v for k, v in profile_data.items() 
                if k in allowed_fields
            }
            
            if not updates:
                return True
            
            # Add updated timestamp
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Update profile
            success = await self.user_service.update_profile(user_id, updates)
            
            if success:
                # Get user email for audit
                user = await self.user_service.get_user(user_id)
                user_email = user.email if user else None
                
                # Audit log
                self.audit.log_event(
                    event_type=AuditEventType.USER_UPDATE,
                    action=f"Profile updated for user {user_id}",
                    user_id=actor_id or user_id,
                    user_email=user_email,
                    resource_type="profile",
                    resource_id=str(user_id),
                    details={"updated_fields": list(updates.keys())},
                )
                
                logger.info(f"Profile updated for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update profile for user {user_id}: {e}")
            return False
    
    async def delete_profile(
        self,
        user_id: int,
        actor_id: Optional[int] = None
    ) -> bool:
        """
        Delete user profile data (soft delete - clears fields).
        
        Args:
            user_id: User ID
            actor_id: ID of user making the change
            
        Returns:
            True if successful
        """
        try:
            # Clear profile fields
            updates = {
                'display_name': None,
                'first_name': None,
                'last_name': None,
                'bio': None,
                'phone': None,
                'location': None,
                'website': None,
                'social_links': None,
                'avatar_url': None,
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }
            
            success = await self.user_service.update_profile(user_id, updates)
            
            if success:
                # Get user email for audit
                user = await self.user_service.get_user(user_id)
                user_email = user.email if user else None
                
                # Audit log
                self.audit.log_event(
                    event_type=AuditEventType.USER_UPDATE,
                    action=f"Profile deleted for user {user_id}",
                    user_id=actor_id or user_id,
                    user_email=user_email,
                    resource_type="profile",
                    resource_id=str(user_id),
                )
                
                logger.info(f"Profile deleted for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete profile for user {user_id}: {e}")
            return False
    
    # ========================================================================
    # Avatar Management
    # ========================================================================
    
    async def upload_avatar(
        self,
        user_id: int,
        file_data: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> Optional[str]:
        """
        Upload user avatar.
        
        Args:
            user_id: User ID
            file_data: Image file data
            filename: Original filename
            content_type: MIME type
            
        Returns:
            Avatar URL or None
        """
        try:
            # Validate file size (max 5MB)
            max_size = 5 * 1024 * 1024
            if len(file_data) > max_size:
                logger.warning(f"Avatar upload failed: file too large ({len(file_data)} bytes)")
                return None
            
            # Validate content type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if content_type not in allowed_types:
                logger.warning(f"Avatar upload failed: invalid content type {content_type}")
                return None
            
            # Generate unique filename
            file_hash = hashlib.md5(file_data).hexdigest()
            extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            new_filename = f"{user_id}_{file_hash}.{extension}"
            file_path = os.path.join(self.storage_path, new_filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Generate URL (relative path)
            avatar_url = f"/uploads/avatars/{new_filename}"
            
            # Update user profile
            await self.user_service.update_profile(
                user_id,
                {'avatar_url': avatar_url}
            )
            
            # Get user email for audit
            user = await self.user_service.get_user(user_id)
            user_email = user.email if user else None
            
            # Audit log
            self.audit.log_event(
                event_type=AuditEventType.USER_UPDATE,
                action=f"Avatar uploaded for user {user_id}",
                user_id=user_id,
                user_email=user_email,
                resource_type="avatar",
                resource_id=str(user_id),
                details={"filename": new_filename, "size": len(file_data)},
            )
            
            logger.info(f"Avatar uploaded for user {user_id}: {avatar_url}")
            return avatar_url
            
        except Exception as e:
            logger.error(f"Failed to upload avatar for user {user_id}: {e}")
            return None
    
    async def delete_avatar(
        self,
        user_id: int
    ) -> bool:
        """
        Delete user avatar.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        try:
            # Get current avatar URL
            user = await self.user_service.get_user(user_id, include_profile=True)
            if not user:
                return False
            
            avatar_url = getattr(user, 'avatar_url', None)
            
            # Delete file if exists
            if avatar_url:
                filename = avatar_url.split('/')[-1]
                file_path = os.path.join(self.storage_path, filename)
                
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Clear avatar URL
            await self.user_service.update_profile(
                user_id,
                {'avatar_url': None}
            )
            
            # Audit log
            self.audit.log_event(
                event_type=AuditEventType.USER_UPDATE,
                action=f"Avatar deleted for user {user_id}",
                user_id=user_id,
                user_email=user.email,
                resource_type="avatar",
                resource_id=str(user_id),
            )
            
            logger.info(f"Avatar deleted for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete avatar for user {user_id}: {e}")
            return False
    
    # ========================================================================
    # User Preferences
    # ========================================================================
    
    async def get_preferences(
        self,
        user_id: int
    ) -> Optional[UserPreferences]:
        """
        Get user preferences.
        
        Args:
            user_id: User ID
            
        Returns:
            UserPreferences or None
        """
        try:
            user = await self.user_service.get_user(user_id, include_profile=True)
            if not user:
                return None
            
            # Get preferences from user metadata
            prefs_data = getattr(user, 'preferences', {}) or {}
            
            # Return default preferences if none set
            if not prefs_data:
                return UserPreferences()
            
            return UserPreferences.from_dict(prefs_data)
            
        except Exception as e:
            logger.error(f"Failed to get preferences for user {user_id}: {e}")
            return UserPreferences()
    
    async def update_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Update user preferences.
        
        Args:
            user_id: User ID
            preferences: Preference fields to update
            
        Returns:
            True if successful
        """
        try:
            # Get current preferences
            current_prefs = await self.get_preferences(user_id)
            if not current_prefs:
                current_prefs = UserPreferences()
            
            # Update preferences
            prefs_dict = current_prefs.to_dict()
            prefs_dict.update(preferences)
            
            # Save to user profile
            success = await self.user_service.update_profile(
                user_id,
                {'preferences': prefs_dict}
            )
            
            if success:
                logger.info(f"Preferences updated for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update preferences for user {user_id}: {e}")
            return False
    
    # ========================================================================
    # Account Management
    # ========================================================================
    
    async def deactivate_account(
        self,
        user_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """
        Deactivate user account (soft delete).
        
        Args:
            user_id: User ID
            reason: Deactivation reason
            
        Returns:
            True if successful
        """
        try:
            # Update account status
            updates = {
                'account_status': AccountStatus.DEACTIVATED.value,
                'deactivated_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }
            
            if reason:
                updates['deactivation_reason'] = reason
            
            success = await self.user_service.update_user(user_id, updates)
            
            if success:
                # Get user email for audit
                user = await self.user_service.get_user(user_id)
                user_email = user.email if user else None
                
                # Audit log
                self.audit.log_event(
                    event_type=AuditEventType.USER_DEACTIVATE,
                    action=f"Account deactivated for user {user_id}",
                    user_id=user_id,
                    user_email=user_email,
                    resource_type="account",
                    resource_id=str(user_id),
                    details={"reason": reason} if reason else {},
                )
                
                logger.info(f"Account deactivated for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to deactivate account for user {user_id}: {e}")
            return False
    
    async def reactivate_account(
        self,
        user_id: int
    ) -> bool:
        """
        Reactivate deactivated account.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        try:
            updates = {
                'account_status': AccountStatus.ACTIVE.value,
                'deactivated_at': None,
                'deactivation_reason': None,
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }
            
            success = await self.user_service.update_user(user_id, updates)
            
            if success:
                # Get user email for audit
                user = await self.user_service.get_user(user_id)
                user_email = user.email if user else None
                
                # Audit log
                self.audit.log_event(
                    event_type=AuditEventType.USER_REACTIVATE,
                    action=f"Account reactivated for user {user_id}",
                    user_id=user_id,
                    user_email=user_email,
                    resource_type="account",
                    resource_id=str(user_id),
                )
                
                logger.info(f"Account reactivated for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to reactivate account for user {user_id}: {e}")
            return False
    
    async def get_account_status(
        self,
        user_id: int
    ) -> Optional[AccountStatus]:
        """
        Get account status.
        
        Args:
            user_id: User ID
            
        Returns:
            AccountStatus or None
        """
        try:
            user = await self.user_service.get_user(user_id)
            if not user:
                return None
            
            status_str = getattr(user, 'account_status', AccountStatus.ACTIVE.value)
            return AccountStatus(status_str)
            
        except Exception as e:
            logger.error(f"Failed to get account status for user {user_id}: {e}")
            return None
    
    # ========================================================================
    # Profile Visibility
    # ========================================================================
    
    async def set_profile_visibility(
        self,
        user_id: int,
        is_public: bool
    ) -> bool:
        """
        Set profile visibility (public/private).
        
        Args:
            user_id: User ID
            is_public: True for public, False for private
            
        Returns:
            True if successful
        """
        return await self.update_preferences(
            user_id,
            {'privacy_public_profile': is_public}
        )
    
    async def is_profile_public(
        self,
        user_id: int
    ) -> bool:
        """
        Check if profile is public.
        
        Args:
            user_id: User ID
            
        Returns:
            True if public
        """
        prefs = await self.get_preferences(user_id)
        return prefs.privacy_public_profile if prefs else True


# Global instance
_profile_service: Optional[UserProfileService] = None


def get_profile_service(user_service=None) -> UserProfileService:
    """Get global profile service instance"""
    global _profile_service
    if _profile_service is None and user_service:
        _profile_service = UserProfileService(user_service)
    return _profile_service
