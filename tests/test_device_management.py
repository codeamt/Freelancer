"""
Tests for device management system
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import uuid

from core.services.auth.device_manager import DeviceManager
from core.services.auth.models import DeviceInfo


class TestDeviceManager:
    """Test device manager functionality"""
    
    @pytest.fixture
    def mock_postgres(self):
        """Create mock PostgreSQL adapter"""
        postgres = MagicMock()
        postgres.execute = AsyncMock()
        postgres.fetch_one = AsyncMock()
        postgres.fetch_all = AsyncMock()
        return postgres
    
    @pytest.fixture
    def device_manager(self, mock_postgres):
        """Create device manager with mock postgres"""
        return DeviceManager(mock_postgres)
    
    async def test_register_device_new(self, device_manager, mock_postgres):
        """Test registering a new device"""
        # Mock no existing device
        mock_postgres.fetch_one.return_value = None
        
        # Mock successful insert
        mock_postgres.execute.return_value = True
        
        user_id = 123
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ip_address = "192.168.1.1"
        
        result = await device_manager.register_device(user_id, user_agent, ip_address)
        
        assert result is not None
        assert len(result) == 32  # UUID length
        mock_postgres.execute.assert_called()
    
    async def test_register_device_existing(self, device_manager, mock_postgres):
        """Test registering an existing device"""
        # Mock existing device
        mock_postgres.fetch_one.return_value = {
            'id': 1,
            'device_id': 'existing-device-id',
            'is_active': True
        }
        
        user_id = 123
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ip_address = "192.168.1.1"
        
        result = await device_manager.register_device(user_id, user_agent, ip_address)
        
        assert result == 'existing-device-id'
        mock_postgres.execute.assert_not_called()  # Should not insert new device
    
    async def test_create_refresh_token(self, device_manager, mock_postgres):
        """Test creating refresh token"""
        mock_postgres.execute.return_value = True
        
        user_id = 123
        device_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        token_id = await device_manager.create_refresh_token(
            user_id, device_id, expires_at
        )
        
        assert token_id is not None
        assert len(token_id) == 32  # UUID length
        mock_postgres.execute.assert_called()
    
    async def test_validate_refresh_token_valid(self, device_manager, mock_postgres):
        """Test validating a valid refresh token"""
        token_id = str(uuid.uuid4())
        mock_postgres.fetch_one.return_value = {
            'id': 1,
            'user_id': 123,
            'device_id': 'device-123',
            'expires_at': datetime.utcnow() + timedelta(days=1),
            'is_active': True
        }
        
        result = await device_manager.validate_refresh_token(token_id)
        
        assert result is not None
        assert result['user_id'] == 123
        assert result['device_id'] == 'device-123'
    
    async def test_validate_refresh_token_expired(self, device_manager, mock_postgres):
        """Test validating an expired refresh token"""
        token_id = str(uuid.uuid4())
        mock_postgres.fetch_one.return_value = {
            'id': 1,
            'user_id': 123,
            'expires_at': datetime.utcnow() - timedelta(days=1),  # Expired
            'is_active': True
        }
        
        result = await device_manager.validate_refresh_token(token_id)
        
        assert result is None
    
    async def test_validate_refresh_token_inactive(self, device_manager, mock_postgres):
        """Test validating an inactive refresh token"""
        token_id = str(uuid.uuid4())
        mock_postgres.fetch_one.return_value = {
            'id': 1,
            'user_id': 123,
            'expires_at': datetime.utcnow() + timedelta(days=1),
            'is_active': False
        }
        
        result = await device_manager.validate_refresh_token(token_id)
        
        assert result is None
    
    async def test_revoke_device(self, device_manager, mock_postgres):
        """Test revoking a device"""
        mock_postgres.execute.return_value = True
        
        user_id = 123
        device_id = str(uuid.uuid4())
        
        success = await device_manager.revoke_device(user_id, device_id)
        
        assert success == True
        mock_postgres.execute.assert_called()
    
    async def test_revoke_all_user_devices(self, device_manager, mock_postgres):
        """Test revoking all devices for a user"""
        mock_postgres.execute.return_value = True
        
        user_id = 123
        
        await device_manager.revoke_all_user_devices(user_id)
        
        mock_postgres.execute.assert_called()
    
    async def test_get_user_devices(self, device_manager, mock_postgres):
        """Test getting all devices for a user"""
        mock_postgres.fetch_all.return_value = [
            {
                'device_id': 'device-1',
                'device_name': 'Chrome on Windows',
                'device_type': 'desktop',
                'platform': 'Windows',
                'browser': 'Chrome',
                'ip_address': '192.168.1.1',
                'first_seen_at': datetime.utcnow(),
                'last_seen_at': datetime.utcnow(),
                'is_active': True,
                'is_trusted': False,
                'active_sessions': 2
            },
            {
                'device_id': 'device-2',
                'device_name': 'Safari on iPhone',
                'device_type': 'mobile',
                'platform': 'iOS',
                'browser': 'Safari',
                'ip_address': '192.168.1.2',
                'first_seen_at': datetime.utcnow(),
                'last_seen_at': datetime.utcnow(),
                'is_active': True,
                'is_trusted': True,
                'active_sessions': 1
            }
        ]
        
        devices = await device_manager.get_user_devices(123)
        
        assert len(devices) == 2
        assert devices[0]['device_id'] == 'device-1'
        assert devices[0]['device_type'] == 'desktop'
        assert devices[1]['device_id'] == 'device-2'
        assert devices[1]['is_trusted'] == True
    
    async def test_trust_device(self, device_manager, mock_postgres):
        """Test trusting a device"""
        mock_postgres.execute.return_value = True
        
        user_id = 123
        device_id = str(uuid.uuid4())
        
        success = await device_manager.trust_device(user_id, device_id)
        
        assert success == True
        mock_postgres.execute.assert_called()
    
    async def test_untrust_device(self, device_manager, mock_postgres):
        """Test untrusting a device"""
        mock_postgres.execute.return_value = True
        
        user_id = 123
        device_id = str(uuid.uuid4())
        
        success = await device_manager.untrust_device(user_id, device_id)
        
        assert success == True
        mock_postgres.execute.assert_called()
    
    async def test_cleanup_expired_tokens(self, device_manager, mock_postgres):
        """Test cleaning up expired tokens"""
        mock_postgres.execute.return_value = 100  # 100 tokens cleaned up
        
        cleaned = await device_manager.cleanup_expired_tokens()
        
        assert cleaned == 100
        mock_postgres.execute.assert_called()
    
    def test_parse_user_agent_chrome(self, device_manager):
        """Test parsing Chrome user agent"""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        device_info = device_manager._parse_user_agent(user_agent)
        
        assert device_info['browser'] == 'Chrome'
        assert device_info['platform'] == 'Windows'
        assert device_info['device_type'] == 'desktop'
    
    def test_parse_user_agent_safari_mobile(self, device_manager):
        """Test parsing Safari mobile user agent"""
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        
        device_info = device_manager._parse_user_agent(user_agent)
        
        assert device_info['browser'] == 'Safari'
        assert device_info['platform'] == 'iOS'
        assert device_info['device_type'] == 'mobile'
    
    def test_parse_user_agent_unknown(self, device_manager):
        """Test parsing unknown user agent"""
        user_agent = "SomeRandomBot/1.0"
        
        device_info = device_manager._parse_user_agent(user_agent)
        
        assert device_info['browser'] == 'Unknown'
        assert device_info['platform'] == 'Unknown'
        assert device_info['device_type'] == 'unknown'
    
    def test_generate_device_id(self, device_manager):
        """Test device ID generation"""
        user_id = 123
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
        ip_address = "192.168.1.1"
        
        device_id1 = device_manager._generate_device_id(user_id, user_agent, ip_address)
        device_id2 = device_manager._generate_device_id(user_id, user_agent, ip_address)
        
        # Same inputs should generate same device ID
        assert device_id1 == device_id2
        assert len(device_id1) == 32  # MD5 hash length
    
    def test_generate_device_id_different_inputs(self, device_manager):
        """Test device ID generation with different inputs"""
        user_id = 123
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
        
        device_id1 = device_manager._generate_device_id(user_id, user_agent, "192.168.1.1")
        device_id2 = device_manager._generate_device_id(user_id, user_agent, "192.168.1.2")
        
        # Different IP should generate different device ID
        assert device_id1 != device_id2
