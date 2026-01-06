# Services Package Initialization
# Import database services from add_ons/services (universal services)
# TODO: Create missing services in add_ons/services
# from add_ons.services.mongodb import MongoDBService as DBService  # Backwards compatibility
# from add_ons.services.postgres import PostgresService
# from add_ons.services.mongodb import MongoDBService
# from add_ons.services.analytics import AnalyticsService

from .admin import AdminService, require_admin, is_admin, has_role
from .search_service import SearchService
from .cart_service import CartService, Cart, CartItem, RedisCartService
from .product_service import ProductService, Product
from .order_service import OrderService, Order, OrderItem, OrderStatus
from .db_service import DBService, get_db_service

# Import auth from core.services.auth (universal auth service)
from core.services.auth import AuthService, get_current_user, require_role, require_permission

# Import payment service
from core.services.payment_service import PaymentService, StripeWebhookHandler

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
    'RedisCartService',
    'ProductService',
    'Product',
    'OrderService',
    'Order',
    'OrderItem',
    'OrderStatus',
    'DBService',
    'get_db_service',
    'PaymentService',
    'StripeWebhookHandler',
    'StripeClient',
    'Web3Client',
    'HuggingFaceClient',
]

if has_user_service:
    __all__.append('UserService')