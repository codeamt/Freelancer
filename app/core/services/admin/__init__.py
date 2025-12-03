"""Core Admin Service - Shared admin functionality for all add-ons"""
from .admin_service import AdminService
from .decorators import require_admin, require_role
from .utils import is_admin, has_role

__all__ = ['AdminService', 'require_admin', 'require_role', 'is_admin', 'has_role']
