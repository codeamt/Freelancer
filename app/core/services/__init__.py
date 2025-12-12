# Services Package Initialization
# Import database services from add_ons/services (universal services)
# TODO: Create missing services in add_ons/services
# from add_ons.services.mongodb import MongoDBService as DBService  # Backwards compatibility
# from add_ons.services.postgres import PostgresService
# from add_ons.services.mongodb import MongoDBService
# from add_ons.services.analytics import AnalyticsService

from .admin import AdminService, require_admin, is_admin, has_role
from .search import SearchService
from .cart import CartService, Cart, CartItem

# Import auth from core.services.auth (universal auth service)
from core.services.auth import AuthService, get_current_user, require_role, require_permission

# Import payment service
from core.services.payment import PaymentService

# Import integrations
from core.integrations.stripe import StripeClient
from core.integrations.web3 import Web3Client
from core.integrations.huggingface import HuggingFaceClient

# Keep UserService from old auth for backwards compatibility (if needed)
try:
    from .auth import UserService
    has_user_service = True
except ImportError:
    has_user_service = False

__all__ = [
    # 'DBService',  # Backwards compatibility (alias for MongoDBService)
    # 'PostgresService',
    # 'MongoDBService',
    # 'AnalyticsService',
    'AuthService', 
    'get_current_user',
    'require_role',
    'require_permission',
    'AdminService',
    'require_admin',
    'is_admin',
    'has_role',
    'SearchService',
    'CartService',
    'Cart',
    'CartItem',
    'PaymentService',
    'StripeClient',
    'Web3Client',
    'HuggingFaceClient',
]

if has_user_service:
    __all__.append('UserService')