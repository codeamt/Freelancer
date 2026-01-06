"""
Unified Security Middleware

Combines the best features from security.py and enhanced_security.py:
- Security headers
- CSRF protection  
- Endpoint-specific rate limiting
- Account lockout protection
- Input validation and sanitization
- JWT helpers
- Audit logging integration
"""

import os
import uuid
import time
import secrets
import jwt
from typing import Dict, Optional, Tuple, Callable, Any
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response, JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.utils.security import sanitize_html, sanitize_sql_input
from core.utils.logger import get_logger
from core.services.audit_service import get_audit_service, AuditEventType

logger = get_logger(__name__)

# JWT configuration
JWT_ALGO = "HS256"

def _get_jwt_secret():
    """Get JWT secret from environment"""
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise ValueError(
            "JWT_SECRET environment variable is required for JWT operations. "
            "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )
    return secret

COOKIE_OPTS = {"httponly": True, "secure": False, "samesite": "lax", "path": "/"}
CSRF_COOKIE = "csrf_token"


# --- JWT helpers -------------------------------------------------------------
def issue_jwt(payload: dict, exp_seconds: int = 3600) -> str:
    """Issue JWT token with expiration"""
    payload = {**payload, "exp": int(time.time()) + exp_seconds}
    return jwt.encode(payload, _get_jwt_secret(), algorithm=JWT_ALGO)

def verify_jwt(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        return jwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")


# --- Security Headers ------------------------------------------------------
class SecurityHeaders(BaseHTTPMiddleware):
    """Security headers middleware with FastHTML/MonsterUI compatibility"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # CSP (permissive for development with CDN resources)
        csp = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.jsdelivr.net https://unpkg.com https://fonts.googleapis.com "
            "https://fonts.gstatic.com data: blob:;"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response


# --- CSRF Protection ----------------------------------------------------
class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip CSRF for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        # Check CSRF token for unsafe methods
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            csrf_token = request.cookies.get(CSRF_COOKIE)
        
        if not csrf_token or not self._validate_csrf_token(csrf_token, request):
            raise HTTPException(403, "CSRF token validation failed")
        
        return await call_next(request)
    
    def _validate_csrf_token(self, token: str, request: Request) -> bool:
        """Validate CSRF token"""
        # Simple validation - in production, use proper CSRF token validation
        return len(token) >= 32


# --- Endpoint Rate Limiting -------------------------------------------
class EndpointRateLimiter:
    """Endpoint-specific rate limiting with different limits per endpoint"""
    
    def __init__(self):
        self.requests: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        self.audit = get_audit_service()
        
        # Define rate limits per endpoint pattern
        self.limits = {
            # Auth endpoints - strict limits
            "/auth/login": {"requests": 5, "window": 900},  # 5 per 15 minutes
            "/auth/register": {"requests": 3, "window": 3600},  # 3 per hour
            "/auth/password-reset": {"requests": 3, "window": 3600},  # 3 per hour
            "/auth/password-reset/confirm": {"requests": 5, "window": 3600},  # 5 per hour
            
            # API endpoints - moderate limits
            "/api/": {"requests": 100, "window": 60},  # 100 per minute
            
            # Default - lenient limits
            "default": {"requests": 60, "window": 60},  # 60 per minute
        }
    
    def get_limit_for_path(self, path: str) -> Tuple[int, int]:
        """Get rate limit for a specific path"""
        for pattern, limit in self.limits.items():
            if pattern != "default" and path.startswith(pattern):
                return limit["requests"], limit["window"]
        return self.limits["default"]["requests"], self.limits["default"]["window"]
    
    def check_rate_limit(self, identifier: str, path: str) -> Tuple[bool, Optional[int]]:
        """Check if request is allowed"""
        max_requests, window = self.get_limit_for_path(path)
        current_time = time.time()
        
        # Clean old entries
        self.requests[identifier][path] = [
            req_time for req_time in self.requests[identifier][path]
            if current_time - req_time < window
        ]
        
        # Check limit
        if len(self.requests[identifier][path]) >= max_requests:
            retry_after = int(window - (current_time - self.requests[identifier][path][0]))
            return False, retry_after
        
        # Record this request
        self.requests[identifier][path].append(current_time)
        return True, None
    
    def cleanup_old_entries(self):
        """Clean up old rate limit entries"""
        current_time = time.time()
        for identifier in list(self.requests.keys()):
            for path in list(self.requests[identifier].keys()):
                self.requests[identifier][path] = [
                    req_time for req_time in self.requests[identifier][path]
                    if current_time - req_time < 3600  # Keep entries for 1 hour
                ]
                if not self.requests[identifier][path]:
                    del self.requests[identifier][path]
            if not self.requests[identifier]:
                del self.requests[identifier]


# --- Account Lockout Protection ----------------------------------------
class AccountLockoutProtection:
    """Account lockout protection after failed attempts"""
    
    def __init__(self, max_attempts: int = 5, lockout_duration: int = 900):
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        self.failed_attempts: Dict[str, Dict[str, Any]] = {}
        self.audit = get_audit_service()
    
    def record_failed_attempt(self, identifier: str, ip_address: str):
        """Record a failed authentication attempt"""
        key = f"{identifier}:{ip_address}"
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = {
                "attempts": 0,
                "first_attempt": time.time(),
                "last_attempt": time.time(),
                "locked_until": None
            }
        
        self.failed_attempts[key]["attempts"] += 1
        self.failed_attempts[key]["last_attempt"] = time.time()
        
        # Check if should lock
        if self.failed_attempts[key]["attempts"] >= self.max_attempts:
            self.failed_attempts[key]["locked_until"] = time.time() + self.lockout_duration
            
            # Log to audit
            self.audit.log_security_breach_attempt(
                attack_type="account_lockout",
                ip_address=ip_address,
                details={
                    "identifier": identifier,
                    "attempts": self.failed_attempts[key]["attempts"],
                    "locked_until": self.failed_attempts[key]["locked_until"]
                }
            )
    
    def is_locked(self, identifier: str) -> Tuple[bool, Optional[int]]:
        """Check if account is locked"""
        key = identifier
        
        if key not in self.failed_attempts:
            return False, None
        
        locked_until = self.failed_attempts[key].get("locked_until")
        if not locked_until:
            return False, None
        
        if time.time() > locked_until:
            # Lockout expired
            del self.failed_attempts[key]
            return False, None
        
        return True, int(locked_until - time.time())
    
    def clear_failed_attempts(self, identifier: str):
        """Clear failed attempts after successful login"""
        keys_to_remove = [k for k in self.failed_attempts.keys() if k.startswith(identifier + ":")]
        for key in keys_to_remove:
            del self.failed_attempts[key]


# --- Input Validation ---------------------------------------------------
class InputLengthValidator:
    """Input length validation for security"""
    
    def __init__(self):
        self.max_lengths = {
            "username": 50,
            "email": 255,
            "password": 128,
            "title": 200,
            "content": 10000,
            "comment": 1000,
            "name": 100,
            "subject": 200,
        }
    
    def validate_input(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate input lengths"""
        for field, value in data.items():
            if field in self.max_lengths and isinstance(value, str):
                if len(value) > self.max_lengths[field]:
                    return False, f"{field} exceeds maximum length of {self.max_lengths[field]}"
        return True, None


# --- Unified Security Middleware ----------------------------------------
class UnifiedSecurityMiddleware(BaseHTTPMiddleware):
    """
    Unified security middleware combining all security features:
    - Input sanitization and validation
    - Endpoint-specific rate limiting
    - Account lockout protection
    - Audit logging
    - Suspicious activity detection
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = EndpointRateLimiter()
        self.lockout_protection = AccountLockoutProtection()
        self.input_validator = InputLengthValidator()
        self.audit = get_audit_service()
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security checks"""
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # Periodic cleanup (every 5 minutes)
        current_time = time.time()
        if current_time - self.last_cleanup > 300:
            self.rate_limiter.cleanup_old_entries()
            self.last_cleanup = current_time
        
        # 1. Check rate limiting
        user_id = getattr(request.state, "user_id", None)
        identifier = f"{user_id or 'anonymous'}:{client_ip}"
        
        is_allowed, retry_after = self.rate_limiter.check_rate_limit(identifier, path)
        if not is_allowed:
            self.audit.log_rate_limit_exceeded(client_ip, path, retry_after)
            raise HTTPException(
                429, 
                f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # 2. Check account lockout for auth endpoints
        if path.startswith("/auth/") and request.method in ["POST"]:
            # Extract identifier from request (email, username, etc.)
            auth_identifier = self._extract_auth_identifier(request)
            if auth_identifier:
                is_locked, lock_time = self.lockout_protection.is_locked(auth_identifier)
                if is_locked:
                    self.audit.log_security_breach_attempt(
                        attack_type="locked_account_access",
                        ip_address=client_ip,
                        details={"identifier": auth_identifier, "lock_time": lock_time}
                    )
                    raise HTTPException(423, "Account temporarily locked due to failed attempts")
        
        # 3. Sanitize and validate input
        suspicious_inputs = 0
        sanitization_failures = 0
        
        # Sanitize query parameters
        clean_query = {}
        for k, v in request.query_params.items():
            safe_v = sanitize_sql_input(sanitize_html(v))
            if v != safe_v:
                suspicious_inputs += 1
            clean_query[k] = safe_v
        request.state.sanitized_query = clean_query
        
        # Sanitize form data
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                form = await request.form()
                clean_form = {}
                for k, v in form.items():
                    safe_v = sanitize_sql_input(sanitize_html(v))
                    if v != safe_v:
                        suspicious_inputs += 1
                    clean_form[k] = safe_v
                
                # Validate input lengths
                is_valid, error_msg = self.input_validator.validate_input(clean_form)
                if not is_valid:
                    sanitization_failures += 1
                    self.audit.log_security_breach_attempt(
                        attack_type="input_validation",
                        ip_address=client_ip,
                        details={"error": error_msg, "path": path}
                    )
                
                request.state.sanitized_form = clean_form
                
            except Exception as e:
                logger.warning(f"Failed to process form data: {e}")
                sanitization_failures += 1
        
        # 4. Log suspicious activity
        if suspicious_inputs > 0 or sanitization_failures > 0:
            self.audit.log_security_breach_attempt(
                attack_type="suspicious_input",
                ip_address=client_ip,
                details={
                    "suspicious_inputs": suspicious_inputs,
                    "sanitization_failures": sanitization_failures,
                    "path": path
                }
            )
        
        # 5. Process request
        response = await call_next(request)
        
        # 6. Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
    
    def _extract_auth_identifier(self, request: Request) -> Optional[str]:
        """Extract identifier from auth request for lockout checking"""
        try:
            if request.method == "POST":
                # Try to get from form data
                form = getattr(request.state, "sanitized_form", {})
                return form.get("email") or form.get("username") or form.get("identifier")
        except Exception:
            pass
        return None


# --- Legacy Compatibility Classes ------------------------------------
# Keep the original class names for backward compatibility
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Legacy rate limiting middleware - use UnifiedSecurityMiddleware instead"""
    
    def __init__(self, app):
        super().__init__(app)
        logger.warning("RateLimitMiddleware is deprecated. Use UnifiedSecurityMiddleware instead.")

# Backward compatibility function
def apply_security(app):
    """Apply security middleware to app (legacy function)"""
    app.add_middleware(UnifiedSecurityMiddleware)
    app.add_middleware(SecurityHeaders)
    app.add_middleware(CSRFMiddleware)
    return app
