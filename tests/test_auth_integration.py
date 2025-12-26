"""
Integration tests for authentication flow
"""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock
from fasthtml.common import Request, Response
from starlette.testclient import TestClient
import os

from app import create_app
from core.services.auth.models import LoginRequest


class TestAuthIntegration:
    """Integration tests for authentication endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test app"""
        with patch.dict(os.environ, {
            'JWT_SECRET': 'test-secret-key-for-testing',
            'ENVIRONMENT': 'test'
        }):
            app, _ = create_app(demo=True)
            return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_auth_page_loads(self, client):
        """Test auth page loads successfully"""
        response = client.get("/auth")
        
        assert response.status_code == 200
        assert "Login" in response.text
        assert "Register" in response.text
    
    def test_login_success(self, client):
        """Test successful login"""
        # Mock user verification
        with patch('core.services.auth.user_repository.UserRepository.verify_password') as mock_verify:
            mock_user = type('User', (), {
                'id': 123,
                'email': 'test@example.com',
                'role': 'user',
                'is_active': True,
                'is_verified': True
            })()
            mock_verify.return_value = mock_user
            
            # Submit login form
            response = client.post("/auth/login", data={
                'email': 'test@example.com',
                'password': 'password'
            })
            
            # Should redirect after successful login
            assert response.status_code == 303
            assert 'auth_token' in response.cookies
    
    def test_login_failure(self, client):
        """Test failed login"""
        # Mock failed verification
        with patch('core.services.auth.user_repository.UserRepository.verify_password') as mock_verify:
            mock_verify.return_value = None
            
            # Submit login form
            response = client.post("/auth/login", data={
                'email': 'test@example.com',
                'password': 'wrong-password'
            })
            
            # Should redirect back to login with error
            assert response.status_code == 303
            assert 'error=Invalid+credentials' in response.headers['location']
    
    def test_register_success(self, client):
        """Test successful registration"""
        # Mock user creation
        with patch('core.services.auth.user_repository.UserRepository.create_user') as mock_create:
            mock_user = type('User', (), {
                'id': 123,
                'email': 'new@example.com',
                'role': 'user'
            })()
            mock_create.return_value = mock_user
            
            # Submit registration form
            response = client.post("/auth/register", data={
                'email': 'new@example.com',
                'password': 'password',
                'confirm_password': 'password',
                'role': 'user'
            })
            
            # Should redirect after successful registration
            assert response.status_code == 303
            assert 'auth_token' in response.cookies
    
    def test_register_password_mismatch(self, client):
        """Test registration with password mismatch"""
        response = client.post("/auth/register", data={
            'email': 'new@example.com',
            'password': 'password',
            'confirm_password': 'different-password',
            'role': 'user'
        })
        
        # Should show error
        assert response.status_code == 303
        assert 'error=Passwords+do+not+match' in response.headers['location']
    
    def test_refresh_token_endpoint(self, client):
        """Test refresh token endpoint"""
        # Mock device manager
        with patch('core.services.auth.device_manager.DeviceManager') as mock_device_mgr:
            mock_instance = mock_device_mgr.return_value
            mock_instance.validate_refresh_token.return_value = {
                'user_id': 123,
                'device_id': 'device-123'
            }
            mock_instance.update_refresh_token_usage.return_value = True
            
            # Make refresh request
            response = client.post("/auth/refresh", json={
                'refresh_token': 'valid-refresh-token'
            })
            
            assert response.status_code == 200
            data = response.json()
            assert 'access_token' in data
            assert data['token_type'] == 'Bearer'
    
    def test_refresh_token_invalid(self, client):
        """Test refresh token with invalid token"""
        with patch('core.services.auth.device_manager.DeviceManager') as mock_device_mgr:
            mock_instance = mock_device_mgr.return_value
            mock_instance.validate_refresh_token.return_value = None
            
            response = client.post("/auth/refresh", json={
                'refresh_token': 'invalid-token'
            })
            
            assert response.status_code == 401
            assert 'error' in response.json()
    
    def test_devices_endpoint_unauthorized(self, client):
        """Test devices endpoint without authentication"""
        response = client.get("/auth/devices")
        
        assert response.status_code == 401
        assert 'error' in response.json()
    
    def test_devices_endpoint_authorized(self, client):
        """Test devices endpoint with authentication"""
        # Mock authentication
        with patch('core.services.auth.helpers.get_current_user') as mock_get_user:
            mock_user = type('User', (), {'id': 123})()
            mock_get_user.return_value = mock_user
            
            # Mock device manager
            with patch('core.services.auth.device_manager.DeviceManager') as mock_device_mgr:
                mock_instance = mock_device_mgr.return_value
                mock_instance.get_user_devices.return_value = [
                    {'device_id': 'device-1', 'device_name': 'Chrome on Windows'}
                ]
                
                response = client.get("/auth/devices")
                
                assert response.status_code == 200
                data = response.json()
                assert 'devices' in data
                assert len(data['devices']) == 1
    
    def test_revoke_device_endpoint(self, client):
        """Test device revocation endpoint"""
        # Mock authentication
        with patch('core.services.auth.helpers.get_current_user') as mock_get_user:
            mock_user = type('User', (), {'id': 123})()
            mock_get_user.return_value = mock_user
            
            # Mock device manager
            with patch('core.services.auth.device_manager.DeviceManager') as mock_device_mgr:
                mock_instance = mock_device_mgr.return_value
                mock_instance.revoke_device.return_value = True
                
                response = client.post("/auth/device/revoke", json={
                    'device_id': 'device-123'
                })
                
                assert response.status_code == 200
                data = response.json()
                assert data['success'] == True
    
    def test_trust_device_endpoint(self, client):
        """Test device trust endpoint"""
        # Mock authentication
        with patch('core.services.auth.helpers.get_current_user') as mock_get_user:
            mock_user = type('User', (), {'id': 123})()
            mock_get_user.return_value = mock_user
            
            # Mock device manager
            with patch('core.services.auth.device_manager.DeviceManager') as mock_device_mgr:
                mock_instance = mock_device_mgr.return_value
                mock_instance.trust_device.return_value = True
                
                response = client.post("/auth/devices/device-123/trust")
                
                assert response.status_code == 200
                data = response.json()
                assert data['success'] == True
    
    def test_untrust_device_endpoint(self, client):
        """Test device untrust endpoint"""
        # Mock authentication
        with patch('core.services.auth.helpers.get_current_user') as mock_get_user:
            mock_user = type('User', (), {'id': 123})()
            mock_get_user.return_value = mock_user
            
            # Mock device manager
            with patch('core.services.auth.device_manager.DeviceManager') as mock_device_mgr:
                mock_instance = mock_device_mgr.return_value
                mock_instance.untrust_device.return_value = True
                
                response = client.delete("/auth/devices/device-123/trust")
                
                assert response.status_code == 200
                data = response.json()
                assert data['success'] == True
    
    def test_token_expiry_check(self, client):
        """Test token expiry check endpoint"""
        # Mock JWT provider
        with patch('core.services.auth.providers.jwt.JWTProvider') as mock_jwt:
            mock_instance = mock_jwt.return_value
            mock_instance.is_token_expiring_soon.return_value = False
            
            # Set auth cookie
            client.cookies.set('auth_token', 'valid-token')
            
            response = client.get("/auth/token/expiry")
            
            assert response.status_code == 200
            data = response.json()
            assert 'expiring_soon' in data
            assert data['expiring_soon'] == False
    
    def test_device_management_page(self, client):
        """Test device management UI page"""
        # Mock authentication
        with patch('core.services.auth.helpers.get_current_user') as mock_get_user:
            mock_user = type('User', (), {
                'id': 123,
                'email': 'test@example.com'
            })()
            mock_get_user.return_value = mock_user
            
            # Mock device manager
            with patch('core.services.auth.device_manager.DeviceManager') as mock_device_mgr:
                mock_instance = mock_device_mgr.return_value
                mock_instance.get_user_devices.return_value = [
                    {
                        'device_id': 'device-1',
                        'device_name': 'Chrome on Windows',
                        'device_type': 'desktop',
                        'platform': 'Windows',
                        'browser': 'Chrome',
                        'ip_address': '192.168.1.1',
                        'last_seen_at': '2023-12-26 12:00:00',
                        'is_trusted': False,
                        'active_sessions': 2
                    }
                ]
                
                response = client.get("/profile/devices")
                
                assert response.status_code == 200
                assert 'Device Management' in response.text
                assert 'Chrome on Windows' in response.text
    
    def test_logout(self, client):
        """Test logout functionality"""
        # Mock authentication
        with patch('core.services.auth.helpers.get_current_user') as mock_get_user:
            mock_user = type('User', (), {'id': 123})()
            mock_get_user.return_value = mock_user
            
            # Mock blacklist service
            with patch('core.services.auth.jwt_blacklist.get_blacklist_service') as mock_blacklist:
                mock_instance = mock_blacklist.return_value
                mock_instance.blacklist_token.return_value = True
                
                # Set auth cookie
                client.cookies.set('auth_token', 'valid-token')
                
                response = client.post("/auth/logout")
                
                assert response.status_code == 303
                # Check that cookie is cleared
                assert 'auth_token' not in response.cookies
