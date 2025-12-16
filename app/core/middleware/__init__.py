from .redis_session import RedisSessionMiddleware
import os


def apply_security(app):
    from .security import apply_security as _apply_security

    return _apply_security(app)

# Create middleware instance
session_middleware = RedisSessionMiddleware

__all__ = [
    "RedisSessionMiddleware",
    "apply_security",
    "session_middleware",
]