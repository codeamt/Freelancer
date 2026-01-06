"""
Unit tests for User Profile Service
"""

import pytest
import os
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from core.services.user_profile_service import (
    UserProfileService,
    UserProfile,
    UserPreferences,
    AccountStatus,
    get_profile_service,
)


class MockUser:
    """Mock user object"""
    def __init__(self, user_id, email, **kwargs):
        self.id = user_id
        self.email = email
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestUserProfileService:
    """Test suite for UserProfileService"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock user service
        self.mock_user_service = Mock()
        self.mock_user_service.get_user = AsyncMock()
        self.mock_user_service.update_user = AsyncMock()
        self.mock_user_service.update_profile = AsyncMock()
        
        # Create profile service
        self.profile_service = UserProfileService(
            user_service=self.mock_user_service,
            storage_path="test_uploads/avatars"
        )
    
    def teardown_method(self):
        """Cleanup test environment"""
        # Clean up test uploads directory
        if os.path.exists("test_uploads"):
            import shutil
            shutil.rmtree("test_uploads")
    
    # ========================================================================
    # Profile Management Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_get_profile_success(self):
        """Test getting user profile"""
        # Mock user data
        mock_user = MockUser(
            user_id=1,
            email="test@example.com",
            display_name="Test User",
            first_name="Test",
            last_name="User",
            bio="Test bio",
            avatar_url="/avatars/test.jpg",
        )
        self.mock_user_service.get_user.return_value = mock_user
        
        # Get profile
        profile = await self.profile_service.get_profile(1)
        
        assert profile is not None
        assert profile.user_id == 1
        assert profile.email == "test@example.com"
        assert profile.display_name == "Test User"
        assert profile.first_name == "Test"
        assert profile.last_name == "User"
        assert profile.bio == "Test bio"
        assert profile.avatar_url == "/avatars/test.jpg"
    
    @pytest.mark.asyncio
    async def test_get_profile_not_found(self):
        """Test getting profile for non-existent user"""
        self.mock_user_service.get_user.return_value = None
        
        profile = await self.profile_service.get_profile(999)
        
        assert profile is None
    
    @pytest.mark.asyncio
    async def test_get_profile_with_preferences(self):
        """Test getting profile with preferences"""
        mock_user = MockUser(
            user_id=1,
            email="test@example.com",
            preferences={
                "theme": "dark",
                "language": "en",
                "email_notifications": True,
            }
        )
        self.mock_user_service.get_user.return_value = mock_user
        
        profile = await self.profile_service.get_profile(1, include_preferences=True)
        
        assert profile is not None
        assert profile.preferences is not None
        assert profile.preferences["theme"] == "dark"
    
    @pytest.mark.asyncio
    async def test_update_profile_success(self):
        """Test updating user profile"""
        self.mock_user_service.update_profile.return_value = True
        self.mock_user_service.get_user.return_value = MockUser(1, "test@example.com")
        
        profile_data = {
            "display_name": "New Name",
            "bio": "New bio",
            "location": "New York",
        }
        
        success = await self.profile_service.update_profile(1, profile_data)
        
        assert success is True
        self.mock_user_service.update_profile.assert_called_once()
        
        # Verify only allowed fields were updated
        call_args = self.mock_user_service.update_profile.call_args[0]
        updates = call_args[1]
        assert "display_name" in updates
        assert "bio" in updates
        assert "location" in updates
        assert "updated_at" in updates
    
    @pytest.mark.asyncio
    async def test_update_profile_filters_forbidden_fields(self):
        """Test that forbidden fields are filtered out"""
        self.mock_user_service.update_profile.return_value = True
        self.mock_user_service.get_user.return_value = MockUser(1, "test@example.com")
        
        profile_data = {
            "display_name": "New Name",
            "password": "should_be_filtered",  # Not allowed
            "email": "should_be_filtered",  # Not allowed
        }
        
        success = await self.profile_service.update_profile(1, profile_data)
        
        assert success is True
        call_args = self.mock_user_service.update_profile.call_args[0]
        updates = call_args[1]
        
        # Only display_name should be in updates
        assert "display_name" in updates
        assert "password" not in updates
        assert "email" not in updates
    
    @pytest.mark.asyncio
    async def test_delete_profile_success(self):
        """Test deleting user profile"""
        self.mock_user_service.update_profile.return_value = True
        self.mock_user_service.get_user.return_value = MockUser(1, "test@example.com")
        
        success = await self.profile_service.delete_profile(1)
        
        assert success is True
        
        # Verify profile fields were cleared
        call_args = self.mock_user_service.update_profile.call_args[0]
        updates = call_args[1]
        assert updates["display_name"] is None
        assert updates["first_name"] is None
        assert updates["bio"] is None
        assert updates["avatar_url"] is None
    
    # ========================================================================
    # Avatar Management Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_upload_avatar_success(self):
        """Test uploading avatar"""
        self.mock_user_service.update_profile.return_value = True
        self.mock_user_service.get_user.return_value = MockUser(1, "test@example.com")
        
        # Create test image data
        file_data = b"fake_image_data" * 100
        
        avatar_url = await self.profile_service.upload_avatar(
            user_id=1,
            file_data=file_data,
            filename="test.jpg",
            content_type="image/jpeg"
        )
        
        assert avatar_url is not None
        assert avatar_url.startswith("/uploads/avatars/")
        assert avatar_url.endswith(".jpg")
        
        # Verify file was saved
        filename = avatar_url.split("/")[-1]
        file_path = os.path.join("test_uploads/avatars", filename)
        assert os.path.exists(file_path)
    
    @pytest.mark.asyncio
    async def test_upload_avatar_file_too_large(self):
        """Test uploading avatar that's too large"""
        # Create file larger than 5MB
        file_data = b"x" * (6 * 1024 * 1024)
        
        avatar_url = await self.profile_service.upload_avatar(
            user_id=1,
            file_data=file_data,
            filename="large.jpg",
            content_type="image/jpeg"
        )
        
        assert avatar_url is None
    
    @pytest.mark.asyncio
    async def test_upload_avatar_invalid_content_type(self):
        """Test uploading avatar with invalid content type"""
        file_data = b"fake_data"
        
        avatar_url = await self.profile_service.upload_avatar(
            user_id=1,
            file_data=file_data,
            filename="test.exe",
            content_type="application/exe"
        )
        
        assert avatar_url is None
    
    @pytest.mark.asyncio
    async def test_delete_avatar_success(self):
        """Test deleting avatar"""
        # First upload an avatar
        self.mock_user_service.update_profile.return_value = True
        mock_user = MockUser(1, "test@example.com", avatar_url="/uploads/avatars/test.jpg")
        self.mock_user_service.get_user.return_value = mock_user
        
        # Create fake avatar file
        os.makedirs("test_uploads/avatars", exist_ok=True)
        test_file = "test_uploads/avatars/test.jpg"
        with open(test_file, "wb") as f:
            f.write(b"fake_image")
        
        success = await self.profile_service.delete_avatar(1)
        
        assert success is True
        assert not os.path.exists(test_file)
    
    # ========================================================================
    # User Preferences Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_get_preferences_default(self):
        """Test getting default preferences"""
        mock_user = MockUser(1, "test@example.com")
        self.mock_user_service.get_user.return_value = mock_user
        
        prefs = await self.profile_service.get_preferences(1)
        
        assert prefs is not None
        assert prefs.theme == "light"
        assert prefs.language == "en"
        assert prefs.email_notifications is True
    
    @pytest.mark.asyncio
    async def test_get_preferences_custom(self):
        """Test getting custom preferences"""
        mock_user = MockUser(
            1,
            "test@example.com",
            preferences={
                "theme": "dark",
                "language": "es",
                "email_notifications": False,
            }
        )
        self.mock_user_service.get_user.return_value = mock_user
        
        prefs = await self.profile_service.get_preferences(1)
        
        assert prefs.theme == "dark"
        assert prefs.language == "es"
        assert prefs.email_notifications is False
    
    @pytest.mark.asyncio
    async def test_update_preferences_success(self):
        """Test updating preferences"""
        mock_user = MockUser(1, "test@example.com", preferences={})
        self.mock_user_service.get_user.return_value = mock_user
        self.mock_user_service.update_profile.return_value = True
        
        new_prefs = {
            "theme": "dark",
            "language": "fr",
        }
        
        success = await self.profile_service.update_preferences(1, new_prefs)
        
        assert success is True
        self.mock_user_service.update_profile.assert_called_once()
    
    # ========================================================================
    # Account Management Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_deactivate_account_success(self):
        """Test deactivating account"""
        self.mock_user_service.update_user.return_value = True
        self.mock_user_service.get_user.return_value = MockUser(1, "test@example.com")
        
        success = await self.profile_service.deactivate_account(1, reason="User request")
        
        assert success is True
        
        # Verify account status was updated
        call_args = self.mock_user_service.update_user.call_args[0]
        updates = call_args[1]
        assert updates["account_status"] == AccountStatus.DEACTIVATED.value
        assert "deactivated_at" in updates
        assert updates["deactivation_reason"] == "User request"
    
    @pytest.mark.asyncio
    async def test_reactivate_account_success(self):
        """Test reactivating account"""
        self.mock_user_service.update_user.return_value = True
        self.mock_user_service.get_user.return_value = MockUser(1, "test@example.com")
        
        success = await self.profile_service.reactivate_account(1)
        
        assert success is True
        
        # Verify account status was updated
        call_args = self.mock_user_service.update_user.call_args[0]
        updates = call_args[1]
        assert updates["account_status"] == AccountStatus.ACTIVE.value
        assert updates["deactivated_at"] is None
    
    @pytest.mark.asyncio
    async def test_get_account_status(self):
        """Test getting account status"""
        mock_user = MockUser(1, "test@example.com", account_status="active")
        self.mock_user_service.get_user.return_value = mock_user
        
        status = await self.profile_service.get_account_status(1)
        
        assert status == AccountStatus.ACTIVE
    
    # ========================================================================
    # Profile Visibility Tests
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_set_profile_visibility_public(self):
        """Test setting profile to public"""
        mock_user = MockUser(1, "test@example.com", preferences={})
        self.mock_user_service.get_user.return_value = mock_user
        self.mock_user_service.update_profile.return_value = True
        
        success = await self.profile_service.set_profile_visibility(1, is_public=True)
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_set_profile_visibility_private(self):
        """Test setting profile to private"""
        mock_user = MockUser(1, "test@example.com", preferences={})
        self.mock_user_service.get_user.return_value = mock_user
        self.mock_user_service.update_profile.return_value = True
        
        success = await self.profile_service.set_profile_visibility(1, is_public=False)
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_is_profile_public_default(self):
        """Test checking if profile is public (default)"""
        mock_user = MockUser(1, "test@example.com")
        self.mock_user_service.get_user.return_value = mock_user
        
        is_public = await self.profile_service.is_profile_public(1)
        
        assert is_public is True
    
    @pytest.mark.asyncio
    async def test_is_profile_public_private(self):
        """Test checking if profile is private"""
        mock_user = MockUser(
            1,
            "test@example.com",
            preferences={"privacy_public_profile": False}
        )
        self.mock_user_service.get_user.return_value = mock_user
        
        is_public = await self.profile_service.is_profile_public(1)
        
        assert is_public is False


class TestUserProfile:
    """Test UserProfile data structure"""
    
    def test_user_profile_creation(self):
        """Test creating user profile"""
        profile = UserProfile(
            user_id=1,
            email="test@example.com",
            display_name="Test User",
        )
        
        assert profile.user_id == 1
        assert profile.email == "test@example.com"
        assert profile.display_name == "Test User"
    
    def test_user_profile_to_dict(self):
        """Test converting profile to dict"""
        profile = UserProfile(
            user_id=1,
            email="test@example.com",
            display_name="Test User",
            bio="Test bio",
        )
        
        profile_dict = profile.to_dict()
        
        assert isinstance(profile_dict, dict)
        assert profile_dict["user_id"] == 1
        assert profile_dict["email"] == "test@example.com"
        assert profile_dict["display_name"] == "Test User"
        assert profile_dict["bio"] == "Test bio"
        # None values should be excluded
        assert "phone" not in profile_dict


class TestUserPreferences:
    """Test UserPreferences data structure"""
    
    def test_user_preferences_defaults(self):
        """Test default preferences"""
        prefs = UserPreferences()
        
        assert prefs.theme == "light"
        assert prefs.language == "en"
        assert prefs.timezone == "UTC"
        assert prefs.email_notifications is True
        assert prefs.push_notifications is True
        assert prefs.marketing_emails is False
    
    def test_user_preferences_to_dict(self):
        """Test converting preferences to dict"""
        prefs = UserPreferences(theme="dark", language="es")
        
        prefs_dict = prefs.to_dict()
        
        assert isinstance(prefs_dict, dict)
        assert prefs_dict["theme"] == "dark"
        assert prefs_dict["language"] == "es"
    
    def test_user_preferences_from_dict(self):
        """Test creating preferences from dict"""
        data = {
            "theme": "dark",
            "language": "fr",
            "email_notifications": False,
        }
        
        prefs = UserPreferences.from_dict(data)
        
        assert prefs.theme == "dark"
        assert prefs.language == "fr"
        assert prefs.email_notifications is False


class TestAccountStatus:
    """Test AccountStatus enum"""
    
    def test_account_status_values(self):
        """Test account status enum values"""
        assert AccountStatus.ACTIVE.value == "active"
        assert AccountStatus.INACTIVE.value == "inactive"
        assert AccountStatus.SUSPENDED.value == "suspended"
        assert AccountStatus.DEACTIVATED.value == "deactivated"
        assert AccountStatus.DELETED.value == "deleted"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
