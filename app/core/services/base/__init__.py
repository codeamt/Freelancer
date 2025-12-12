"""
Base Service Classes for Add-on Extensibility

Abstract base classes that add-ons can extend for custom implementations.

Note: Only includes services where add-ons might provide custom implementations.
Core platform services (auth, db) do not need base classes as they are not extensible.
"""

from .storage import BaseStorageService
from .email import BaseEmailService
from .notification import BaseNotificationService

__all__ = [
    'BaseStorageService',
    'BaseEmailService',
    'BaseNotificationService',
]
