"""
Core Database Models

Only core models that are used across all domains.
Domain-specific models should be in their respective domain directories.
"""

from .user import User

__all__ = ["User"]
