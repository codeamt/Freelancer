"""Unit tests for JWT blacklist functionality"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from core.services.auth.jwt_blacklist import JWTBlacklistService
from core.services.auth.providers.jwt import JWTProvider


@pytest.fixture
async def blacklist_service():
    """Create a blacklist service for testing"""
    with patch('core.services.auth.jwt_blacklist.redis.from_url') as mock_redis:
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True
        
        service = JWTBlacklistService(redis_url="redis://test:6379")
        service.redis_client = mock_client
        return service


@pytest.fixture
def jwt_provider():
    """Create a JWT provider for testing"""
    with patch.dict('os.environ', {'JWT_SECRET': 'test-secret-key-for-jwt'}):
        return JWTProvider()


class TestJWTBlacklistService:
    """Test JWT blacklist service"""
    
    @pytest.mark.asyncio
    async def test_add_to_blacklist(self, blacklist_service, jwt_provider):
        """Test adding a token to blacklist"""
        # Create a test token
        token = jwt_provider.create({
            "user_id": 123,
            "email": "test@example.com",
            "role": "user"
        })
        
        # Add to blacklist
        result = await blacklist_service.add_to_blacklist(token, reason="logout")
        
        assert result is True
        
        # Verify Redis was called
        blacklist_service.redis_client.setex.assert_called_once()
        
        # Check the key and data
        call_args = blacklist_service.redis_client.setex.call_args
        key = call_args[0][0]
        assert key.startswith("jwt:blacklist:")
        
        # Verify data structure
        data = call_args[0][1]
        import json
        parsed_data = json.loads(data)
        assert parsed_data["reason"] == "logout"
        assert parsed_data["user_id"] == 123
        assert "blacklisted_at" in parsed_data
    
    @pytest.mark.asyncio
    async def test_is_blacklisted(self, blacklist_service, jwt_provider):
        """Test checking if a token is blacklisted"""
        # Create a test token
        token = jwt_provider.create({
            "user_id": 123,
            "email": "test@example.com",
            "role": "user"
        })
        
        # Initially not blacklisted
        is_blacklisted = await blacklist_service.is_blacklisted(token)
        assert is_blacklisted is False
        
        # Add to blacklist
        await blacklist_service.add_to_blacklist(token, reason="logout")
        
        # Now should be blacklisted
        blacklist_service.redis_client.get.return_value = '{"jti": "test", "reason": "logout"}'
        is_blacklisted = await blacklist_service.is_blacklisted(token)
        assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_is_blacklisted_invalid_token(self, blacklist_service):
        """Test checking blacklist for invalid token"""
        is_blacklisted = await blacklist_service.is_blacklisted("invalid-token")
        assert is_blacklisted is False
    
    @pytest.mark.asyncio
    async def test_remove_from_blacklist(self, blacklist_service):
        """Test removing a token from blacklist"""
        jti = "test-jti-123"
        
        # Mock successful deletion
        blacklist_service.redis_client.delete.return_value = 1
        
        result = await blacklist_service.remove_from_blacklist(jti)
        
        assert result is True
        blacklist_service.redis_client.delete.assert_called_once_with("jwt:blacklist:test-jti-123")
    
    @pytest.mark.asyncio
    async def test_remove_from_blacklist_not_found(self, blacklist_service):
        """Test removing a non-existent token from blacklist"""
        jti = "non-existent-jti"
        
        # Mock no deletion
        blacklist_service.redis_client.delete.return_value = 0
        
        result = await blacklist_service.remove_from_blacklist(jti)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_blacklist_info(self, blacklist_service):
        """Test getting blacklist info for a token"""
        jti = "test-jti-123"
        mock_data = '{"jti": "test-jti-123", "reason": "logout", "user_id": 123}'
        
        blacklist_service.redis_client.get.return_value = mock_data
        
        info = await blacklist_service.get_blacklist_info(jti)
        
        assert info is not None
        assert info["jti"] == "test-jti-123"
        assert info["reason"] == "logout"
        assert info["user_id"] == 123
    
    @pytest.mark.asyncio
    async def test_get_blacklist_info_not_found(self, blacklist_service):
        """Test getting blacklist info for non-existent token"""
        jti = "non-existent-jti"
        
        blacklist_service.redis_client.get.return_value = None
        
        info = await blacklist_service.get_blacklist_info(jti)
        
        assert info is None
    
    @pytest.mark.asyncio
    async def test_blacklist_user_tokens(self, blacklist_service):
        """Test blacklisting all tokens for a user"""
        user_id = 123
        
        result = await blacklist_service.blacklist_user_tokens(user_id, reason="password_change")
        
        assert result is True  # Currently returns True as placeholder
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, blacklist_service):
        """Test cleaning up expired blacklist entries"""
        cleaned = await blacklist_service.cleanup_expired()
        
        assert cleaned == 0  # Redis handles TTL automatically
    
    @pytest.mark.asyncio
    async def test_add_to_blacklist_expired_token(self, blacklist_service, jwt_provider):
        """Test adding an already expired token to blacklist"""
        # Create an expired token
        token = jwt_provider.create({
            "user_id": 123,
            "email": "test@example.com",
            "role": "user"
        }, expires_hours=-1)  # Already expired
        
        result = await blacklist_service.add_to_blacklist(token, reason="logout")
        
        assert result is False  # Should not blacklist expired tokens
    
    @pytest.mark.asyncio
    async def test_add_to_blacklist_without_jti(self, blacklist_service, jwt_provider):
        """Test adding token without JTI to blacklist"""
        # Create token without JTI (old format)
        payload = {
            "user_id": 123,
            "email": "test@example.com",
            "role": "user"
        }
        token = jwt_provider.create(payload)
        
        # Remove JTI from payload for testing
        with patch.object(jwt_provider, 'verify') as mock_verify:
            mock_verify.return_value = payload  # No JTI
            
            result = await blacklist_service.add_to_blacklist(token, reason="logout")
            
            assert result is True
            # Should still work by creating JTI from hash


class TestJWTProviderWithBlacklist:
    """Test JWT provider integration with blacklist"""
    
    @pytest.mark.asyncio
    async def test_verify_with_blacklist_enabled(self, jwt_provider):
        """Test token verification with blacklist enabled"""
        jwt_provider.use_blacklist = True
        
        with patch('core.services.auth.providers.jwt.get_blacklist_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.is_blacklisted.return_value = False
            mock_get_service.return_value = mock_service
            
            # Create valid token
            token = jwt_provider.create({"user_id": 123, "role": "user"})
            
            # Verify should pass
            payload = await jwt_provider.verify(token)
            
            assert payload is not None
            assert payload["user_id"] == 123
            mock_service.is_blacklisted.assert_called_once_with(token)
    
    @pytest.mark.asyncio
    async def test_verify_blacklisted_token(self, jwt_provider):
        """Test verifying a blacklisted token"""
        jwt_provider.use_blacklist = True
        
        with patch('core.services.auth.providers.jwt.get_blacklist_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.is_blacklisted.return_value = True
            mock_get_service.return_value = mock_service
            
            # Create token
            token = jwt_provider.create({"user_id": 123, "role": "user"})
            
            # Verify should fail for blacklisted token
            payload = await jwt_provider.verify(token)
            
            assert payload is None
            mock_service.is_blacklisted.assert_called_once_with(token)
    
    @pytest.mark.asyncio
    async def test_verify_with_blacklist_disabled(self, jwt_provider):
        """Test token verification with blacklist disabled"""
        jwt_provider.use_blacklist = False
        
        with patch('core.services.auth.providers.jwt.get_blacklist_service') as mock_get_service:
            # Create valid token
            token = jwt_provider.create({"user_id": 123, "role": "user"})
            
            # Verify should pass without checking blacklist
            payload = await jwt_provider.verify(token)
            
            assert payload is not None
            assert payload["user_id"] == 123
            mock_get_service.assert_not_called()
    
    def test_create_token_with_jti(self, jwt_provider):
        """Test that created tokens include JTI"""
        token = jwt_provider.create({"user_id": 123, "role": "user"})
        
        # Decode without verification to check JTI
        payload = jwt_provider.decode_without_verification(token)
        
        assert payload is not None
        assert "jti" in payload
        assert len(payload["jti"]) == 36  # UUID length
        assert "iat" in payload  # Issued at
        assert "iss" in payload  # Issuer
        assert "aud" in payload  # Audience
    
    def test_verify_sync_no_blacklist(self, jwt_provider):
        """Test synchronous verification skips blacklist"""
        token = jwt_provider.create({"user_id": 123, "role": "user"})
        
        # Sync verify should work
        payload = jwt_provider.verify_sync(token)
        
        assert payload is not None
        assert payload["user_id"] == 123
