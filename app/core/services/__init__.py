# Services Package Initialization
# Import database services from add_ons/services (universal services)
from add_ons.services.mongodb import MongoDBService as DBService  # Backwards compatibility
from add_ons.services.postgres import PostgresService
from add_ons.services.mongodb import MongoDBService
from add_ons.services.analytics import AnalyticsService

from .admin import AdminService, require_admin, is_admin, has_role
from .search import SearchService
from .web3 import Web3Service
from .ai import AIService

# Import auth from add_ons/services (universal auth service)
from add_ons.services.auth import AuthService, get_current_user, require_role, require_permission

# Keep UserService from old auth for backwards compatibility (if needed)
try:
    from .auth import UserService
    has_user_service = True
except ImportError:
    has_user_service = False

__all__ = [
    'DBService',  # Backwards compatibility (alias for MongoDBService)
    'PostgresService',
    'MongoDBService',
    'AnalyticsService',
    'AuthService', 
    'get_current_user',
    'require_role',
    'require_permission',
    'AdminService',
    'require_admin',
    'is_admin',
    'has_role',
    'SearchService',
    'Web3Service',
    'AIService'
]

if has_user_service:
    __all__.append('UserService')