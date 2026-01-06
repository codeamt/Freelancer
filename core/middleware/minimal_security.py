"""
Minimal Security Middleware

Very conservative security middleware that only applies to specific dangerous endpoints.
Does NOT interfere with CSS, MonsterUI, or styling content.
"""

import time
from typing import Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.utils.logger import get_logger
from core.services.audit_service import get_audit_service, AuditEventType

logger = get_logger(__name__)


class MinimalRateLimiter:
    """Very basic rate limiting for auth endpoints only"""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.audit = get_audit_service()
        
        # Only rate limit auth endpoints
        self.limits = {
            "/auth/login": {"requests": 10, "window": 900},  # 10 per 15 minutes
            "/auth/register": {"requests": 5, "window": 3600},  # 5 per hour
            "/auth/password-reset": {"requests": 5, "window": 3600},  # 5 per hour
        }
    
    def check_rate_limit(self, identifier: str, path: str) -> Tuple[bool, Optional[int]]:
        """Check rate limit only for auth endpoints"""
        if path not in self.limits:
            return True, None
        
        limit = self.limits[path]
        current_time = time.time()
        window = limit["window"]
        max_requests = limit["requests"]
        
        # Clean old entries
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < window
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= max_requests:
            retry_after = int(window - (current_time - self.requests[identifier][0]))
            return False, retry_after
        
        # Record this request
        self.requests[identifier].append(current_time)
        return True, None


class MinimalSecurityMiddleware(BaseHTTPMiddleware):
    """
    Minimal security middleware that only protects against the most critical threats.
    
    This middleware:
    - Only applies rate limiting to auth endpoints
    - Does NOT sanitize any input data (preserves CSS, HTML, etc.)
    - Only adds basic security headers
    - Logs critical security events
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = MinimalRateLimiter()
        self.audit = get_audit_service()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with minimal security checks"""
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # Skip security processing for static files and assets
        if (path.startswith('/static/') or 
            path.startswith('/css/') or 
            path.startswith('/js/') or
            path.endswith('.css') or 
            path.endswith('.js') or
            path.endswith('.ico') or
            path.endswith('.png') or
            path.endswith('.jpg') or
            path.endswith('.gif') or
            path.endswith('.svg') or
            path.endswith('.woff') or
            path.endswith('.woff2')):
            return await call_next(request)
        
        # Only apply rate limiting to auth endpoints
        if path.startswith('/auth/'):
            user_id = getattr(request.state, "user_id", None)
            identifier = f"{user_id or 'anonymous'}:{client_ip}"
            
            is_allowed, retry_after = self.rate_limiter.check_rate_limit(identifier, path)
            if not is_allowed:
                self.audit.log_rate_limit_exceeded(client_ip, path, retry_after)
                raise HTTPException(
                    429, 
                    f"Too many requests. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )
        
        # Process request without any input sanitization
        response = await call_next(request)
        
        # Add basic security headers (don't interfere with CSS)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        
        return response


# Backward compatibility
def apply_minimal_security(app):
    """Apply minimal security middleware to app"""
    app.add_middleware(MinimalSecurityMiddleware)
    return app
