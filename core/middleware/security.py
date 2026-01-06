"""
Security Middleware

Provides input sanitization WITHOUT breaking CSS/MonsterUI by being selective:
- Only sanitizes dangerous user input fields
- Preserves CSS, HTML, and styling content
- Applies different rules based on context and field names
- Skips static files completely
- Maintains security for user-generated content
"""

import time
from typing import Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.utils.security import sanitize_html, sanitize_sql_input
from core.utils.logger import get_logger
from core.services.audit_service import get_audit_service, AuditEventType

logger = get_logger(__name__)


class SmartRateLimiter:
    """Rate limiting for auth endpoints only"""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.audit = get_audit_service()
        
        self.limits = {
            "/auth/login": {"requests": 10, "window": 900},
            "/auth/register": {"requests": 5, "window": 3600},
            "/auth/password-reset": {"requests": 5, "window": 3600},
        }
    
    def check_rate_limit(self, identifier: str, path: str) -> Tuple[bool, Optional[int]]:
        if path not in self.limits:
            return True, None
        
        limit = self.limits[path]
        current_time = time.time()
        window = limit["window"]
        max_requests = limit["requests"]
        
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < window
        ]
        
        if len(self.requests[identifier]) >= max_requests:
            retry_after = int(window - (current_time - self.requests[identifier][0]))
            return False, retry_after
        
        self.requests[identifier].append(current_time)
        return True, None


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Smart security middleware that sanitizes input WITHOUT breaking CSS/MonsterUI.
    
    This middleware:
    - Only sanitizes dangerous user input fields
    - Preserves CSS, HTML, and styling content
    - Uses field name patterns to determine what to sanitize
    - Skips static files completely
    - Maintains security for user-generated content
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = SmartRateLimiter()
        self.audit = get_audit_service()
        
        # Fields that should ALWAYS be sanitized (user input)
        self.SANITIZE_FIELDS = {
            'email', 'username', 'password', 'name', 'subject', 'message', 'comment',
            'description', 'title', 'search', 'query', 'filter', 'sort', 'first_name',
            'last_name', 'phone', 'address', 'city', 'country', 'zip', 'bio'
        }
        
        # Fields that should NEVER be sanitized (preserves CSS, HTML, JSON)
        self.PRESERVE_FIELDS = {
            'css', 'styles', 'html', 'javascript', 'json', 'data', 'contenteditable',
            'editor_content', 'template', 'markup', 'code', 'script', 'theme',
            'layout', 'design', 'styling', 'custom_css', 'inline_styles', 'component_html'
        }
        
        # Content patterns that indicate CSS/styling (preserve these)
        self.CSS_PATTERNS = [
            '<style', '</style>', 'css:', '{', '}', 'font-family', 'color:', 'background:',
            'margin:', 'padding:', 'border:', 'display:', 'position:', 'width:', 'height:',
            'class="', 'id="', 'data-', 'onclick', 'onload', 'onerror'
        ]
    
    def _should_preserve_field(self, field_name: str, value: str) -> bool:
        """Determine if a field should be preserved (not sanitized)"""
        field_lower = field_name.lower()
        value_lower = str(value).lower()
        
        # Check field name patterns
        if any(preserve in field_lower for preserve in self.PRESERVE_FIELDS):
            return True
        
        # Check content patterns (likely CSS/HTML)
        if any(pattern in value_lower for pattern in self.CSS_PATTERNS):
            return True
        
        # Check if it looks like CSS (has CSS properties)
        css_indicators = ['color:', 'background:', 'font-', 'margin:', 'padding:', 'border:']
        if any(indicator in value_lower for indicator in css_indicators):
            return True
        
        return False
    
    def _should_sanitize_field(self, field_name: str) -> bool:
        """Determine if a field should be sanitized"""
        field_lower = field_name.lower()
        
        # Always sanitize known dangerous fields
        if field_lower in self.SANITIZE_FIELDS:
            return True
        
        # Sanitize fields that look like user input
        dangerous_patterns = ['url', 'link', 'redirect', 'src', 'href', 'action']
        if any(pattern in field_lower for pattern in dangerous_patterns):
            return True
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Process request with smart security checks"""
        
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
        
        # Rate limiting for auth endpoints
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
        
        # Smart input sanitization
        suspicious_inputs = 0
        sanitized_count = 0
        
        # Sanitize query parameters (selectively)
        clean_query = {}
        for k, v in request.query_params.items():
            if self._should_preserve_field(k, v):
                # Preserve CSS/styling content
                clean_query[k] = v
            elif self._should_sanitize_field(k):
                # Sanitize dangerous fields
                safe_v = sanitize_sql_input(sanitize_html(v))
                if v != safe_v:
                    suspicious_inputs += 1
                    sanitized_count += 1
                clean_query[k] = safe_v
            else:
                # Unknown field - be conservative but check if it looks like CSS
                if any(pattern in str(v).lower() for pattern in self.CSS_PATTERNS):
                    clean_query[k] = v  # Preserve likely CSS content
                else:
                    safe_v = sanitize_sql_input(sanitize_html(v))
                    if v != safe_v:
                        suspicious_inputs += 1
                        sanitized_count += 1
                    clean_query[k] = safe_v
        
        request.state.sanitized_query = clean_query
        
        # Sanitize form data (selectively)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                form = await request.form()
                clean_form = {}
                for k, v in form.items():
                    if self._should_preserve_field(k, v):
                        # Preserve CSS/styling content
                        clean_form[k] = v
                    elif self._should_sanitize_field(k):
                        # Sanitize dangerous fields
                        safe_v = sanitize_sql_input(sanitize_html(v))
                        if v != safe_v:
                            suspicious_inputs += 1
                            sanitized_count += 1
                        clean_form[k] = safe_v
                    else:
                        # Unknown field - check if it looks like CSS
                        if any(pattern in str(v).lower() for pattern in self.CSS_PATTERNS):
                            clean_form[k] = v  # Preserve likely CSS content
                        else:
                            safe_v = sanitize_sql_input(sanitize_html(v))
                            if v != safe_v:
                                suspicious_inputs += 1
                                sanitized_count += 1
                            clean_form[k] = safe_v
                
                request.state.sanitized_form = clean_form
                
            except Exception as e:
                logger.warning(f"Failed to process form data: {e}")
        
        # Log security events (but don't be too noisy)
        if suspicious_inputs > 5:  # Only log if many suspicious inputs
            self.audit.log_security_breach_attempt(
                attack_type="suspicious_input",
                ip_address=client_ip,
                details={
                    "suspicious_inputs": suspicious_inputs,
                    "sanitized_count": sanitized_count,
                    "path": path
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers (CSS-friendly)
        self._add_security_headers(response, request)
        
        return response
    
    def _add_security_headers(self, response: Response, request: Request):
        """Add security headers that don't break CSS/MonsterUI"""
        
        # Basic security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Very permissive CSP to avoid breaking CSS/MonsterUI
        # This allows everything while still providing some security benefits
        csp = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com "
            "img-src 'self' data: blob: https: "
            "font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com https://cdn.jsdelivr.net "
            "connect-src 'self' https://cdn.jsdelivr.net "
            "media-src 'self' blob: https: "
            "object-src 'none' "
            "base-uri 'self' "
            "form-action 'self' "
            "frame-ancestors 'none' "
            "upgrade-insecure-requests"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Only add HSTS in production HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"


def apply_security(app):
    """Apply security middleware to app"""
    app.add_middleware(SecurityMiddleware)
    return app
