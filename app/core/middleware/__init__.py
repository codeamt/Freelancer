from .redis_session import RedisSessionMiddleware
from .security import apply_security
import os

# Create middleware instance
session_middleware = RedisSessionMiddleware

__all__ = [
    "RedisSessionMiddleware",
    "apply_security",
    "session_middleware",
]