"""Base abstract classes for core services that add-ons can extend"""
from .auth import BaseAuthService
from .db import BaseDBService
from .storage import BaseStorageService
from .email import BaseEmailService
from .notification import BaseNotificationService

__all__ = [
    "BaseAuthService",
    "BaseDBService",
    "BaseStorageService",
    "BaseEmailService",
    "BaseNotificationService",
]
