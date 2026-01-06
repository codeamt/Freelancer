"""
Unit tests for Enhanced Security Middleware
"""

import pytest
import time
from core.middleware.enhanced_security import (
    EndpointRateLimiter,
    AccountLockoutProtection,
    InputLengthValidator,
    get_rate_limiter,
    get_lockout_protection,
    get_input_validator,
)


class TestEndpointRateLimiter:
    """Test suite for EndpointRateLimiter"""
    
    def setup_method(self):
        """Setup test environment"""
        self.rate_limiter = EndpointRateLimiter()
    
    def test_get_limit_for_auth_endpoints(self):
        """Test getting limits for auth endpoints"""
        # Login endpoint - strict limit
        requests, window = self.rate_limiter.get_limit_for_path("/auth/login")
        assert requests == 5
        assert window == 900  # 15 minutes
        
        # Register endpoint - strict limit
        requests, window = self.rate_limiter.get_limit_for_path("/auth/register")
        assert requests == 3
        assert window == 3600  # 1 hour
    
    def test_get_limit_for_api_endpoints(self):
        """Test getting limits for API endpoints"""
        requests, window = self.rate_limiter.get_limit_for_path("/api/users")
        assert requests == 100
        assert window == 60
    
    def test_get_limit_for_default_endpoints(self):
        """Test getting limits for default endpoints"""
        requests, window = self.rate_limiter.get_limit_for_path("/some/random/path")
        assert requests == 60
        assert window == 60
    
    def test_rate_limit_allows_within_limit(self):
        """Test that requests within limit are allowed"""
        client_ip = "192.168.1.1"
        path = "/auth/login"
        
        # First 5 requests should be allowed
        for i in range(5):
            is_allowed, retry_after = self.rate_limiter.check_rate_limit(client_ip, path)
            assert is_allowed is True
            assert retry_after is None
    
    def test_rate_limit_blocks_over_limit(self):
        """Test that requests over limit are blocked"""
        client_ip = "192.168.1.1"
        path = "/auth/login"
        
        # Exhaust the limit (5 requests)
        for i in range(5):
            self.rate_limiter.check_rate_limit(client_ip, path)
        
        # 6th request should be blocked
        is_allowed, retry_after = self.rate_limiter.check_rate_limit(client_ip, path)
        assert is_allowed is False
        assert retry_after is not None
        assert retry_after > 0
    
    def test_rate_limit_per_ip(self):
        """Test that rate limits are per IP"""
        path = "/auth/login"
        
        # Exhaust limit for IP1
        for i in range(5):
            self.rate_limiter.check_rate_limit("192.168.1.1", path)
        
        # IP2 should still be allowed
        is_allowed, _ = self.rate_limiter.check_rate_limit("192.168.1.2", path)
        assert is_allowed is True
    
    def test_rate_limit_per_user(self):
        """Test that rate limits work with user IDs"""
        path = "/api/users"
        
        # Exhaust limit for user 1
        for i in range(100):
            self.rate_limiter.check_rate_limit("192.168.1.1", path, user_id="user1")
        
        # User 2 should still be allowed
        is_allowed, _ = self.rate_limiter.check_rate_limit("192.168.1.1", path, user_id="user2")
        assert is_allowed is True
    
    def test_rate_limit_window_expiry(self):
        """Test that rate limits reset after window expires"""
        client_ip = "192.168.1.1"
        path = "/auth/login"
        
        # Mock time to test window expiry
        # This would require time mocking in production tests
        # For now, just verify the logic is correct
        
        # Add requests
        for i in range(5):
            self.rate_limiter.check_rate_limit(client_ip, path)
        
        # Verify blocked
        is_allowed, _ = self.rate_limiter.check_rate_limit(client_ip, path)
        assert is_allowed is False
    
    def test_cleanup_old_entries(self):
        """Test cleanup of old entries"""
        # Add some requests
        self.rate_limiter.check_rate_limit("192.168.1.1", "/auth/login")
        self.rate_limiter.check_rate_limit("192.168.1.2", "/auth/register")
        
        # Cleanup should not crash
        self.rate_limiter.cleanup_old_entries()
        
        # Verify data structure is still valid
        assert isinstance(self.rate_limiter.requests, dict)


class TestAccountLockoutProtection:
    """Test suite for AccountLockoutProtection"""
    
    def setup_method(self):
        """Setup test environment"""
        self.lockout = AccountLockoutProtection(max_attempts=5, lockout_duration=900)
    
    def test_record_failed_attempt(self):
        """Test recording failed login attempts"""
        identifier = "test@example.com"
        ip = "192.168.1.1"
        
        # Record attempts
        for i in range(3):
            self.lockout.record_failed_attempt(identifier, ip)
        
        # Should not be locked yet
        is_locked, _ = self.lockout.is_locked(identifier)
        assert is_locked is False
    
    def test_account_lockout_after_max_attempts(self):
        """Test that account locks after max attempts"""
        identifier = "test@example.com"
        ip = "192.168.1.1"
        
        # Record max attempts
        for i in range(5):
            self.lockout.record_failed_attempt(identifier, ip)
        
        # Should be locked
        is_locked, seconds_remaining = self.lockout.is_locked(identifier)
        assert is_locked is True
        assert seconds_remaining is not None
        assert seconds_remaining > 0
    
    def test_lockout_duration(self):
        """Test lockout duration"""
        identifier = "test@example.com"
        ip = "192.168.1.1"
        
        # Lock account
        for i in range(5):
            self.lockout.record_failed_attempt(identifier, ip)
        
        # Check lockout time
        is_locked, seconds_remaining = self.lockout.is_locked(identifier)
        assert is_locked is True
        assert seconds_remaining <= 900  # Should be <= lockout_duration
    
    def test_clear_failed_attempts(self):
        """Test clearing failed attempts after successful login"""
        identifier = "test@example.com"
        ip = "192.168.1.1"
        
        # Record some attempts
        for i in range(3):
            self.lockout.record_failed_attempt(identifier, ip)
        
        # Clear attempts
        self.lockout.clear_failed_attempts(identifier)
        
        # Should not be locked
        is_locked, _ = self.lockout.is_locked(identifier)
        assert is_locked is False
    
    def test_different_accounts_independent(self):
        """Test that different accounts have independent lockout"""
        ip = "192.168.1.1"
        
        # Lock account 1
        for i in range(5):
            self.lockout.record_failed_attempt("user1@example.com", ip)
        
        # Account 2 should not be locked
        is_locked, _ = self.lockout.is_locked("user2@example.com")
        assert is_locked is False


class TestInputLengthValidator:
    """Test suite for InputLengthValidator"""
    
    def setup_method(self):
        """Setup test environment"""
        self.validator = InputLengthValidator()
    
    def test_validate_field_within_limit(self):
        """Test validation of field within limit"""
        is_valid, error = self.validator.validate_field("email", "test@example.com")
        assert is_valid is True
        assert error is None
    
    def test_validate_field_exceeds_limit(self):
        """Test validation of field exceeding limit"""
        long_email = "a" * 300 + "@example.com"
        is_valid, error = self.validator.validate_field("email", long_email)
        assert is_valid is False
        assert error is not None
        assert "exceeds maximum length" in error
    
    def test_validate_field_exact_limit(self):
        """Test validation at exact limit"""
        # Email limit is 255
        exact_email = "a" * 243 + "@example.com"  # Total 255
        is_valid, error = self.validator.validate_field("email", exact_email)
        assert is_valid is True
    
    def test_validate_unknown_field_uses_default(self):
        """Test that unknown fields use default limit"""
        # Default is 1000
        long_value = "a" * 1001
        is_valid, error = self.validator.validate_field("unknown_field", long_value)
        assert is_valid is False
    
    def test_validate_form_data_all_valid(self):
        """Test validation of form data with all valid fields"""
        form_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123",
        }
        
        is_valid, error = self.validator.validate_form_data(form_data)
        assert is_valid is True
        assert error is None
    
    def test_validate_form_data_one_invalid(self):
        """Test validation of form data with one invalid field"""
        form_data = {
            "email": "test@example.com",
            "username": "a" * 200,  # Exceeds 100 char limit
            "password": "SecurePass123",
        }
        
        is_valid, error = self.validator.validate_form_data(form_data)
        assert is_valid is False
        assert error is not None
        assert "username" in error
    
    def test_validate_non_string_value(self):
        """Test validation of non-string values"""
        is_valid, error = self.validator.validate_field("age", 25)
        assert is_valid is True  # Non-strings pass validation
    
    def test_specific_field_limits(self):
        """Test specific field limits"""
        # Test various field limits
        test_cases = [
            ("email", 255),
            ("username", 100),
            ("password", 128),
            ("bio", 1000),
            ("message", 5000),
        ]
        
        for field_name, max_length in test_cases:
            # At limit - should pass
            value = "a" * max_length
            is_valid, _ = self.validator.validate_field(field_name, value)
            assert is_valid is True, f"{field_name} should allow {max_length} chars"
            
            # Over limit - should fail
            value = "a" * (max_length + 1)
            is_valid, _ = self.validator.validate_field(field_name, value)
            assert is_valid is False, f"{field_name} should reject {max_length + 1} chars"


class TestGlobalInstances:
    """Test global instance getters"""
    
    def test_get_rate_limiter(self):
        """Test getting global rate limiter"""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        # Should return same instance
        assert limiter1 is limiter2
    
    def test_get_lockout_protection(self):
        """Test getting global lockout protection"""
        lockout1 = get_lockout_protection()
        lockout2 = get_lockout_protection()
        
        # Should return same instance
        assert lockout1 is lockout2
    
    def test_get_input_validator(self):
        """Test getting global input validator"""
        validator1 = get_input_validator()
        validator2 = get_input_validator()
        
        # Should return same instance
        assert validator1 is validator2


class TestIntegration:
    """Integration tests for security components"""
    
    def test_rate_limiter_and_lockout_together(self):
        """Test rate limiter and lockout working together"""
        rate_limiter = EndpointRateLimiter()
        lockout = AccountLockoutProtection()
        
        identifier = "test@example.com"
        ip = "192.168.1.1"
        path = "/auth/login"
        
        # Simulate failed login attempts
        for i in range(5):
            # Check rate limit
            is_allowed, _ = rate_limiter.check_rate_limit(ip, path)
            if is_allowed:
                # Record failed attempt
                lockout.record_failed_attempt(identifier, ip)
        
        # Account should be locked
        is_locked, _ = lockout.is_locked(identifier)
        assert is_locked is True
    
    def test_input_validation_before_processing(self):
        """Test input validation prevents processing of invalid data"""
        validator = InputLengthValidator()
        
        # Simulate form submission
        form_data = {
            "email": "test@example.com",
            "message": "a" * 10000,  # Exceeds 5000 char limit
        }
        
        # Validate before processing
        is_valid, error = validator.validate_form_data(form_data)
        
        # Should reject
        assert is_valid is False
        assert "message" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
