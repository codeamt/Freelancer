"""Integration tests for JWT blacklist"""

import pytest
import asyncio
from unittest.mock import patch
from fasthtml.common import Request
from fastapi.testclient import TestClient

from core.services.auth.auth_service import AuthService
from core.services.auth.jwt_blacklist import get_blacklist_service
from core.services.auth.providers.jwt import JWTProvider
from tests.conftest import sample_user


@pytest.mark.integration
class TestJWTBlacklistIntegration:
    """Integration tests for JWT blacklist functionality"""
    
    @pytest.mark.asyncio
    async def test_logout_adds_token_to_blacklist(self):
        """Test that logout adds token to blacklist"""
        # Create auth service
        auth_service = AuthService()
        
        # Create a test token
        jwt_provider = JWTProvider()
        token = jwt_provider.create({
            "user_id": 123,
            "email": "test@example.com",
            "role": "user"
        })
        
        # Mock blacklist service
        with patch('core.services.auth.auth_service.get_blacklist_service') as mock_get_service:
            mock_blacklist = AsyncMock()
            mock_blacklist.add_to_blacklist.return_value = True
            mock_get_service.return_value = mock_blacklist
            
            # Logout
            await auth_service.logout(token)
            
            # Verify token was added to blacklist
            mock_blacklist.add_to_blacklist.assert_called_once_with(token, reason="logout")
    
    @pytest.mark.asyncio
    async def test_logout_all_blacklists_user_tokens(self):
        """Test that logout all blacklists user's tokens"""
        auth_service = AuthService()
        user_id = 123
        
        # Mock blacklist service
        with patch('core.services.auth.auth_service.get_blacklist_service') as mock_get_service:
            mock_blacklist = AsyncMock()
            mock_blacklist.blacklist_user_tokens.return_value = True
            mock_get_service.return_value = mock_blacklist
            
            # Logout all
            await auth_service.logout_all(user_id)
            
            # Verify user tokens were blacklisted
            mock_blacklist.blacklist_user_tokens.assert_called_once_with(user_id, reason="logout_all")
    
    @pytest.mark.asyncio
    async def test_blacklisted_token_verification_fails(self):
        """Test that blacklisted tokens fail verification"""
        # Create JWT provider with blacklist enabled
        with patch.dict('os.environ', {'JWT_SECRET': 'test-secret', 'JWT_USE_BLACKLIST': 'true'}):
            jwt_provider = JWTProvider()
            
            # Create test token
            token = jwt_provider.create({
                "user_id": 123,
                "email": "test@example.com",
                "role": "user"
            })
            
            # Mock blacklist service to return True (is blacklisted)
            with patch('core.services.auth.providers.jwt.get_blacklist_service') as mock_get_service:
                mock_blacklist = AsyncMock()
                mock_blacklist.is_blacklisted.return_value = True
                mock_get_service.return_value = mock_blacklist
                
                # Verify should return None for blacklisted token
                payload = await jwt_provider.verify(token)
                assert payload is None
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_blacklisted_token(self):
        """Test get_current_user fails with blacklisted token"""
        from core.services.auth.helpers import get_current_user
        
        # Create request with blacklisted token
        request = Request({
            "type": "http",
            "headers": [(b"authorization", b"Bearer blacklisted-token")],
            "cookies": {}
        })
        
        # Mock auth service
        with patch('core.services.auth.helpers.AuthService') as mock_auth_service:
            mock_service = AsyncMock()
            mock_jwt = AsyncMock()
            mock_jwt.verify.return_value = None  # Blacklisted
            mock_service.jwt = mock_jwt
            mock_auth_service.return_value = mock_service
            
            # Get current user
            user = await get_current_user(request)
            
            # Should return None for blacklisted token
            assert user is None
    
    @pytest.mark.asyncio
    async def test_admin_blacklist_endpoints(self):
        """Test admin blacklist management endpoints"""
        from fasthtml.common import FastHTML
        from core.routes.admin_jwt_blacklist import router_jwt_blacklist
        
        # Create test app
        app = FastHTML()
        app.include_router(router_jwt_blacklist)
        
        # Create test token
        jwt_provider = JWTProvider()
        admin_token = jwt_provider.create({
            "user_id": 1,
            "email": "admin@example.com",
            "role": "admin"
        })
        
        # Mock dependencies
        with patch('core.services.auth.decorators.get_current_user') as mock_get_user, \
             patch('core.services.auth.jwt_blacklist.get_blacklist_service') as mock_get_blacklist:
            
            # Mock admin user
            mock_get_user.return_value = {
                "id": 1,
                "email": "admin@example.com",
                "role": "admin",
                "roles": ["admin"]
            }
            
            # Mock blacklist service
            mock_blacklist = AsyncMock()
            mock_blacklist.add_to_blacklist.return_value = True
            mock_blacklist.get_blacklist_info.return_value = {
                "jti": "test-jti",
                "reason": "admin_action",
                "blacklisted_at": "2024-01-01T00:00:00",
                "expires_at": "2024-01-02T00:00:00"
            }
            mock_blacklist.remove_from_blacklist.return_value = True
            mock_blacklist.blacklist_user_tokens.return_value = True
            mock_blacklist.cleanup_expired.return_value = 0
            mock_get_blacklist.return_value = mock_blacklist
            
            # Test add to blacklist
            with TestClient(app) as client:
                response = client.post(
                    "/admin/jwt/blacklist",
                    json={"token": "test-token", "reason": "admin_action"},
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert response.status_code == 200
                assert response.json()["message"] == "Token added to blacklist"
                
                # Test get blacklist entry
                response = client.get(
                    "/admin/jwt/blacklist/test-jti",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert response.status_code == 200
                assert response.json()["jti"] == "test-jti"
                
                # Test remove from blacklist
                response = client.delete(
                    "/admin/jwt/blacklist/test-jti",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert response.status_code == 200
                assert response.json()["message"] == "Token removed from blacklist"
                
                # Test blacklist user tokens
                response = client.post(
                    "/admin/jwt/blacklist/user/123",
                    json={"reason": "admin_action"},
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert response.status_code == 200
                assert "all tokens for user 123 blacklisted" in response.json()["message"]
                
                # Test cleanup
                response = client.post(
                    "/admin/jwt/blacklist/cleanup",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert response.status_code == 200
                assert response.json()["entries_cleaned"] == 0
    
    @pytest.mark.asyncio
    async def test_blacklist_with_redis_fallback(self):
        """Test blacklist behavior when Redis is unavailable"""
        # Create blacklist service with invalid Redis URL
        service = JWTBlacklistService(redis_url="redis://invalid:6379")
        
        # Test operations gracefully handle Redis errors
        result = await service.add_to_blacklist("test-token", "test")
        assert result is False  # Should fail gracefully
        
        is_blacklisted = await service.is_blacklisted("test-token")
        assert is_blacklisted is False  # Should fail open
    
    @pytest.mark.asyncio
    async def test_token_expiration_buffer(self):
        """Test that blacklist includes expiration buffer"""
        # Create blacklist service
        with patch('core.services.auth.jwt_blacklist.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.ping.return_value = True
            
            service = JWTBlacklistService()
            service.redis_client = mock_client
            
            # Create JWT provider
            jwt_provider = JWTProvider()
            
            # Create token with short expiration
            token = jwt_provider.create({
                "user_id": 123,
                "role": "user"
            }, expires_hours=1)
            
            # Add to blacklist
            await service.add_to_blacklist(token, "test")
            
            # Check that TTL includes buffer
            call_args = mock_client.setex.call_args
            ttl = call_args[0][2]
            
            # Should be approximately 1 hour + 5 minutes (300 seconds buffer)
            expected_ttl = 1 * 3600 + 300  # 1 hour + 5 minutes
            assert abs(ttl - expected_ttl) < 10  # Allow small variance
