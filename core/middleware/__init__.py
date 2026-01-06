from .redis_session import RedisSessionMiddleware
from .security import SecurityMiddleware, apply_security
from .csrf_protection import CSRFProtection
from .auth_context import AuthContextMiddleware
import os


# Legacy function for backward compatibility
def apply_security_legacy(app):
    from .security import apply_security as _apply_security
    return _apply_security(app)

# Create middleware instance
session_middleware = RedisSessionMiddleware

__all__ = [
    "RedisSessionMiddleware",
    "SecurityMiddleware",
    "CSRFProtection",
    "AuthContextMiddleware",
    "apply_security",
    "apply_security_legacy",
    "session_middleware",
]