"""
CSRF Protection Middleware with HTMX Integration

Provides Cross-Site Request Forgery protection for state-changing operations.
Integrates with HTMX for seamless protection in FastHTML applications.
"""

import secrets
import hmac
import hashlib
from typing import Optional, Set
from datetime import datetime, timezone, timedelta

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from core.utils.logger import get_logger
from core.services.audit_service import get_audit_service, AuditEventType

logger = get_logger(__name__)


class CSRFProtection:
    """
    CSRF protection with token generation and validation.
    
    Features:
    - Token generation with HMAC
    - Token rotation after authentication
    - HTMX integration via headers
    - Exempt safe methods (GET, HEAD, OPTIONS)
    - Configurable token lifetime
    """
    
    def __init__(
        self,
        secret_key: str,
        token_length: int = 32,
        token_lifetime: int = 3600,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
    ):
        """
        Initialize CSRF protection.
        
        Args:
            secret_key: Secret key for HMAC signing
            token_length: Length of CSRF token
            token_lifetime: Token lifetime in seconds
            cookie_name: Name of CSRF cookie
            header_name: Name of CSRF header
        """
        self.secret_key = secret_key.encode() if isinstance(secret_key, str) else secret_key
        self.token_length = token_length
        self.token_lifetime = token_lifetime
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.audit = get_audit_service()
        
        # Safe HTTP methods that don't require CSRF protection
        self.safe_methods: Set[str] = {"GET", "HEAD", "OPTIONS", "TRACE"}
        
        # Paths that are exempt from CSRF protection
        self.exempt_paths: Set[str] = {
            "/health",
            "/metrics",
            "/static",
        }
    
    def generate_token(self) -> str:
        """
        Generate a new CSRF token.
        
        Returns:
            CSRF token string
        """
        # Generate random token
        random_token = secrets.token_urlsafe(self.token_length)
        
        # Create timestamp
        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        
        # Combine token and timestamp
        token_data = f"{random_token}:{timestamp}"
        
        # Sign with HMAC
        signature = hmac.new(
            self.secret_key,
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Return token with signature
        return f"{token_data}:{signature}"
    
    def validate_token(self, token: str) -> bool:
        """
        Validate CSRF token.
        
        Args:
            token: CSRF token to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not token:
            return False
        
        try:
            # Parse token
            parts = token.split(":")
            if len(parts) != 3:
                return False
            
            random_token, timestamp_str, signature = parts
            
            # Verify signature
            token_data = f"{random_token}:{timestamp_str}"
            expected_signature = hmac.new(
                self.secret_key,
                token_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("CSRF token signature mismatch")
                return False
            
            # Check token age
            timestamp = int(timestamp_str)
            current_time = int(datetime.now(timezone.utc).timestamp())
            
            if current_time - timestamp > self.token_lifetime:
                logger.warning("CSRF token expired")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"CSRF token validation error: {e}")
            return False
    
    def is_exempt(self, path: str) -> bool:
        """Check if path is exempt from CSRF protection"""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
    
    def add_exempt_path(self, path: str):
        """Add path to CSRF exemption list"""
        self.exempt_paths.add(path)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware with HTMX integration.
    
    Automatically adds CSRF tokens to responses and validates them on
    state-changing requests (POST, PUT, PATCH, DELETE).
    """
    
    def __init__(self, app, secret_key: str, enabled: bool = True):
        """
        Initialize CSRF middleware.
        
        Args:
            app: FastAPI/Starlette application
            secret_key: Secret key for token signing
            enabled: Whether CSRF protection is enabled
        """
        super().__init__(app)
        self.enabled = enabled
        self.csrf = CSRFProtection(secret_key) if enabled else None
        self.audit = get_audit_service()
    
    async def dispatch(self, request: Request, call_next):
        """Process request through CSRF protection"""
        
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip safe methods
        if request.method in self.csrf.safe_methods:
            response = await call_next(request)
            
            # Add CSRF token to response for future requests
            csrf_token = self.csrf.generate_token()
            response.set_cookie(
                key=self.csrf.cookie_name,
                value=csrf_token,
                httponly=True,
                secure=True,  # Only over HTTPS
                samesite="strict",
                max_age=self.csrf.token_lifetime,
            )
            
            # Add token to response headers for HTMX
            response.headers[self.csrf.header_name] = csrf_token
            
            return response
        
        # Skip exempt paths
        if self.csrf.is_exempt(request.url.path):
            return await call_next(request)
        
        # Validate CSRF token for state-changing methods
        # Check cookie
        cookie_token = request.cookies.get(self.csrf.cookie_name)
        
        # Check header (HTMX sends token in header)
        header_token = request.headers.get(self.csrf.header_name)
        
        # Check form data (traditional forms)
        form_token = None
        if request.method == "POST":
            try:
                form_data = await request.form()
                form_token = form_data.get("csrf_token")
            except:
                pass
        
        # Use header token (HTMX) or form token (traditional)
        provided_token = header_token or form_token
        
        # Validate token
        if not provided_token or not self.csrf.validate_token(provided_token):
            # Log CSRF violation
            client_ip = request.client.host if request.client else "unknown"
            user_id = getattr(request.state, "user_id", None)
            
            self.audit.log_event(
                event_type=AuditEventType.SECURITY_BREACH_ATTEMPT,
                action="CSRF token validation failed",
                user_id=user_id,
                ip_address=client_ip,
                details={
                    "path": request.url.path,
                    "method": request.method,
                    "has_cookie_token": bool(cookie_token),
                    "has_header_token": bool(header_token),
                    "has_form_token": bool(form_token),
                }
            )
            
            logger.warning(f"CSRF validation failed for {request.url.path} from {client_ip}")
            
            return JSONResponse(
                status_code=403,
                content={
                    "error": "CSRF token validation failed",
                    "message": "Invalid or missing CSRF token"
                }
            )
        
        # Token valid, process request
        response = await call_next(request)
        
        # Rotate token after successful state change
        new_token = self.csrf.generate_token()
        response.set_cookie(
            key=self.csrf.cookie_name,
            value=new_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=self.csrf.token_lifetime,
        )
        response.headers[self.csrf.header_name] = new_token
        
        return response


def get_csrf_token_html(csrf_token: str) -> str:
    """
    Generate HTML hidden input for CSRF token.
    
    Args:
        csrf_token: CSRF token value
        
    Returns:
        HTML string for hidden input
    """
    return f'<input type="hidden" name="csrf_token" value="{csrf_token}">'


def get_htmx_csrf_config(csrf_token: str) -> str:
    """
    Generate HTMX configuration for CSRF protection.
    
    Args:
        csrf_token: CSRF token value
        
    Returns:
        JavaScript configuration for HTMX
    """
    return f"""
    <script>
        // Configure HTMX to include CSRF token in all requests
        document.body.addEventListener('htmx:configRequest', function(event) {{
            event.detail.headers['X-CSRF-Token'] = '{csrf_token}';
        }});
        
        // Update CSRF token after each response
        document.body.addEventListener('htmx:afterOnLoad', function(event) {{
            const newToken = event.detail.xhr.getResponseHeader('X-CSRF-Token');
            if (newToken) {{
                // Update token for next request
                document.body.setAttribute('data-csrf-token', newToken);
            }}
        }});
    </script>
    """


# Global CSRF protection instance
_csrf_protection: Optional[CSRFProtection] = None


def get_csrf_protection(secret_key: Optional[str] = None) -> CSRFProtection:
    """Get global CSRF protection instance"""
    global _csrf_protection
    if _csrf_protection is None and secret_key:
        _csrf_protection = CSRFProtection(secret_key)
    return _csrf_protection


def generate_csrf_token(secret_key: str) -> str:
    """Convenience function to generate CSRF token"""
    csrf = get_csrf_protection(secret_key)
    return csrf.generate_token()


def validate_csrf_token(token: str, secret_key: str) -> bool:
    """Convenience function to validate CSRF token"""
    csrf = get_csrf_protection(secret_key)
    return csrf.validate_token(token)
