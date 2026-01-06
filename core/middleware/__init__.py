from .redis_session import RedisSessionMiddleware
from .minimal_security import MinimalSecurityMiddleware, apply_minimal_security
from .unified_security import (
    UnifiedSecurityMiddleware,
    SecurityHeaders,
    CSRFMiddleware,
    apply_security,
    issue_jwt,
    verify_jwt,
)
import os


# Legacy function for backward compatibility
def apply_security_legacy(app):
    from .security import apply_security as _apply_security
    return _apply_security(app)

# Create middleware instance
session_middleware = RedisSessionMiddleware

__all__ = [
    "RedisSessionMiddleware",
    "MinimalSecurityMiddleware",
    "UnifiedSecurityMiddleware",
    "SecurityHeaders", 
    "CSRFMiddleware",
    "apply_security",
    "apply_minimal_security",
    "apply_security_legacy",
    "issue_jwt",
    "verify_jwt",
    "session_middleware",
]