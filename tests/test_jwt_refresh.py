"""
Tests for JWT refresh token functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import jwt
import os

from core.services.auth.providers.jwt import JWTProvider
from core.services.auth.auth_service import AuthService
from core.services.auth.models import LoginRequest, TokenRefreshRequest


class TestJWTProvider:
    """Test JWT provider with refresh token support"""
    
    @pytest.fixture
    def jwt_provider(self):
        """Create JWT provider with test secret"""
        with patch.dict(os.environ, {'JWT_SECRET': 'test-secret-key-for-testing'}):
            return JWTProvider()
    
    def test_create_access_token(self, jwt_provider):
        """Test creating access token"""
        payload = {
            'user_id': 123,
            'email': 'test@example.com',
            'role': 'user'
        }
        
        token = jwt_provider.create_access_token(payload)
        
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts
        
        # Decode and verify
        decoded = jwt.decode(token, 'test-secret-key-for-testing', algorithms=['HS256'])
        assert decoded['user_id'] == 123
        assert decoded['email'] == 'test@example.com'
        assert decoded['type'] == 'access'
    
    def test_create_refresh_token(self, jwt_provider):
        """Test creating refresh token"""
        payload = {
            'user_id': 123,
            'device_id': 'device-123'
        }
        
        token = jwt_provider.create_refresh_token(payload)
        
        assert isinstance(token, str)
        assert len(token.split('.')) == 3
        
        # Decode and verify
        decoded = jwt.decode(token, 'test-secret-key-for-testing', algorithms=['HS256'])
        assert decoded['user_id'] == 123
        assert decoded['device_id'] == 'device-123'
        assert decoded['type'] == 'refresh'
    
    def test_create_token_pair(self, jwt_provider):
        """Test creating access and refresh token pair"""
        payload = {
            'user_id': 123,
            'email': 'test@example.com',
            'role': 'user',
            'device_id': 'device-123'
        }
        
        tokens = jwt_provider.create_token_pair(payload)
        
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert isinstance(tokens['access_token'], str)
        assert isinstance(tokens['refresh_token'], str)
        
        # Verify access token
        access_decoded = jwt.decode(tokens['access_token'], 'test-secret-key-for-testing', algorithms=['HS256'])
        assert access_decoded['type'] == 'access'
        
        # Verify refresh token
        refresh_decoded = jwt.decode(tokens['refresh_token'], 'test-secret-key-for-testing', algorithms=['HS256'])
        assert refresh_decoded['type'] == 'refresh'
    
    def test_verify_access_token_valid(self, jwt_provider):
        """Test verifying valid access token"""
        payload = {'user_id': 123, 'type': 'access'}
        token = jwt_provider.create_access_token(payload)
        
        result = jwt_provider.verify_access_token(token)
        
        assert result is not None
        assert result['user_id'] == 123
        assert result['type'] == 'access'
    
    def test_verify_access_token_invalid_type(self, jwt_provider):
        """Test verifying refresh token as access token"""
        payload = {'user_id': 123, 'type': 'refresh'}
        token = jwt_provider.create_refresh_token(payload)
        
        result = jwt_provider.verify_access_token(token)
        
        assert result is None
    
    def test_verify_refresh_token_valid(self, jwt_provider):
        """Test verifying valid refresh token"""
        payload = {'user_id': 123, 'device_id': 'device-123', 'type': 'refresh'}
        token = jwt_provider.create_refresh_token(payload)
        
        result = jwt_provider.verify_refresh_token(token)
        
        assert result is not None
        assert result['user_id'] == 123
        assert result['device_id'] == 'device-123'
    
    def test_verify_refresh_token_invalid_type(self, jwt_provider):
        """Test verifying access token as refresh token"""
        payload = {'user_id': 123, 'type': 'access'}
        token = jwt_provider.create_access_token(payload)
        
        result = jwt_provider.verify_refresh_token(token)
        
        assert result is None
    
    def test_is_token_expiring_soon_true(self, jwt_provider):
        """Test token expiring soon check - expiring"""
        # Create token that expires in 2 minutes
        with patch('core.services.auth.providers.jwt.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 12, 26, 12, 0, 0)
            
            payload = {
                'user_id': 123,
                'exp': datetime(2023, 12, 26, 12, 2, 0)  # 2 minutes later
            }
            token = jwt.encode(payload, 'test-secret-key-for-testing', algorithm='HS256')
            
            expiring = jwt_provider.is_token_expiring_soon(token, minutes_threshold=5)
            
            assert expiring == True
    
    def test_is_token_expiring_soon_false(self, jwt_provider):
        """Test token expiring soon check - not expiring"""
        # Create token that expires in 10 minutes
        with patch('core.services.auth.providers.jwt.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 12, 26, 12, 0, 0)
            
            payload = {
                'user_id': 123,
                'exp': datetime(2023, 12, 26, 12, 10, 0)  # 10 minutes later
            }
            token = jwt.encode(payload, 'test-secret-key-for-testing', algorithm='HS256')
            
            expiring = jwt_provider.is_token_expiring_soon(token, minutes_threshold=5)
            
            assert expiring == False
    
    def test_get_token_expiration(self, jwt_provider):
        """Test getting token expiration time"""
        exp_time = datetime(2023, 12, 26, 12, 0, 0)
        payload = {
            'user_id': 123,
            'exp': exp_time
        }
        token = jwt.encode(payload, 'test-secret-key-for-testing', algorithm='HS256')
        
        expiration = jwt_provider.get_token_expiration(token)
        
        assert expiration == exp_time


class TestAuthServiceRefresh:
    """Test auth service refresh token functionality"""
    
    @pytest.fixture
    def mock_auth_service(self):
        """Create auth service with mocked dependencies"""
        with patch.dict(os.environ, {'JWT_SECRET': 'test-secret-key-for-testing'}):
            mock_user_repo = MagicMock()
            mock_postgres = MagicMock()
            mock_device_manager = MagicMock()
            
            service = AuthService(mock_user_repo, postgres=mock_postgres)
            service.device_manager = mock_device_manager
            
            return service
    
    async def test_refresh_token_success(self, mock_auth_service):
        """Test successful token refresh"""
        # Setup mock device manager
        mock_auth_service.device_manager.validate_refresh_token.return_value = {
            'user_id': 123,
            'device_id': 'device-123'
        }
        mock_auth_service.device_manager.update_refresh_token_usage.return_value = True
        
        # Create refresh request
        request = TokenRefreshRequest(refresh_token="valid-refresh-token")
        
        result = await mock_auth_service.refresh_token(request)
        
        assert result is not None
        assert 'access_token' in result
        assert result['token_type'] == 'bearer'
        assert isinstance(result['access_token'], str)
    
    async def test_refresh_token_invalid(self, mock_auth_service):
        """Test refresh with invalid token"""
        # Setup mock device manager
        mock_auth_service.device_manager.validate_refresh_token.return_value = None
        
        request = TokenRefreshRequest(refresh_token="invalid-token")
        
        result = await mock_auth_service.refresh_token(request)
        
        assert result is None
    
    async def test_login_with_device(self, mock_auth_service):
        """Test login with device tracking"""
        # Setup mocks
        mock_user = MagicMock()
        mock_user.id = 123
        mock_user.email = 'test@example.com'
        mock_user.role = 'user'
        
        mock_auth_service.user_repo.verify_password.return_value = mock_user
        
        mock_auth_service.device_manager.register_device.return_value = 'device-123'
        mock_auth_service.device_manager.create_refresh_token.return_value = 'refresh-token-123'
        
        # Create login request
        request = LoginRequest(username='test@example.com', password='password')
        
        result = await mock_auth_service.login_with_device(
            request,
            user_agent='Mozilla/5.0 Chrome/120.0',
            ip_address='192.168.1.1',
            remember_me=True
        )
        
        assert result is not None
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert 'device_id' in result
        assert result['device_id'] == 'device-123'
        assert result['refresh_token'] == 'refresh-token-123'
    
    async def test_revoke_device(self, mock_auth_service):
        """Test revoking a device"""
        mock_auth_service.device_manager.revoke_device.return_value = True
        
        success = await mock_auth_service.revoke_device(123, 'device-123')
        
        assert success == True
        mock_auth_service.device_manager.revoke_device.assert_called_once_with(123, 'device-123')
    
    async def test_get_user_devices(self, mock_auth_service):
        """Test getting user devices"""
        expected_devices = [
            {'device_id': 'device-1', 'device_name': 'Chrome on Windows'},
            {'device_id': 'device-2', 'device_name': 'Safari on iPhone'}
        ]
        
        mock_auth_service.device_manager.get_user_devices.return_value = expected_devices
        
        devices = await mock_auth_service.get_user_devices(123)
        
        assert devices == expected_devices
        mock_auth_service.device_manager.get_user_devices.assert_called_once_with(123)
    
    async def test_trust_device(self, mock_auth_service):
        """Test trusting a device"""
        mock_auth_service.device_manager.trust_device.return_value = True
        
        success = await mock_auth_service.trust_device(123, 'device-123')
        
        assert success == True
        mock_auth_service.device_manager.trust_device.assert_called_once_with(123, 'device-123')
    
    async def test_untrust_device(self, mock_auth_service):
        """Test untrusting a device"""
        mock_auth_service.device_manager.untrust_device.return_value = True
        
        success = await mock_auth_service.untrust_device(123, 'device-123')
        
        assert success == True
        mock_auth_service.device_manager.untrust_device.assert_called_once_with(123, 'device-123')
