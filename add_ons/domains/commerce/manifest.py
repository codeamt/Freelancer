"""
Commerce (E-commerce) Add-on Manifest

Registers:
- Roles (merchant, customer, commerce_admin)
- Settings (Stripe, PayPal, tax, shipping, etc.)
- Components (product listings, cart, checkout, etc.)
- Routes
"""

from dataclasses import dataclass
from typing import List, Dict, Any

from core.services.auth.permissions import Role, Permission
from core.services.settings import (
    SettingDefinition,
    SettingType,
    SettingSensitivity,
    SettingScope,
    register_addon_settings
)
from core.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Commerce Roles
# ============================================================================

COMMERCE_ROLES = [
    Role(
        id="commerce_admin",
        name="Commerce Administrator",
        description="Full e-commerce management access",
        permissions=[
            Permission("commerce", "*", "*"),         # All commerce operations
            Permission("product", "*", "*"),          # All products
            Permission("order", "*", "*"),            # All orders
            Permission("customer", "*", "*"),         # Manage all customers
            Permission("payment", "*", "*"),          # Payment operations
            Permission("refund", "*", "*"),           # Process refunds
            Permission("integration", "write", "commerce"),  # Configure integrations
        ],
        inherits_from=["admin"],
        domain="commerce"
    ),
    
    Role(
        id="merchant",
        name="Merchant",
        description="Manage products and orders",
        permissions=[
            Permission("commerce", "read", "*"),      # Read commerce settings
            Permission("product", "*", "own"),        # Manage own products
            Permission("order", "read", "*"),         # View all orders
            Permission("order", "update", "own"),     # Update own orders
            Permission("customer", "read", "*"),      # View customers
            Permission("refund", "create", "own"),    # Process refunds for own orders
        ],
        inherits_from=["member"],
        domain="commerce"
    ),
    
    Role(
        id="customer",
        name="Customer",
        description="Purchase products and manage orders",
        permissions=[
            Permission("product", "read", "*"),       # View all products
            Permission("cart", "*", "own"),           # Manage own cart
            Permission("order", "*", "own"),          # Manage own orders
            Permission("payment", "create", "own"),   # Make payments
            Permission("review", "*", "own"),         # Write reviews
        ],
        inherits_from=["member"],
        domain="commerce"
    )
]


# ============================================================================
# Commerce Settings
# ============================================================================

COMMERCE_SETTINGS = [
    # Payment Gateway Settings
    SettingDefinition(
        key="stripe.api_key",
        name="Stripe API Key",
        description="Stripe secret key for payment processing",
        type=SettingType.ENCRYPTED,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.SECRET,
        category="commerce",
        ui_component="password",
        read_permission=("commerce", "admin"),
        write_permission=("commerce", "admin"),
        placeholder="sk_live_...",
        help_text="Required for Stripe payment processing"
    ),
    
    SettingDefinition(
        key="stripe.webhook_secret",
        name="Stripe Webhook Secret",
        description="Stripe webhook signing secret",
        type=SettingType.ENCRYPTED,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.SECRET,
        category="commerce",
        ui_component="password",
        read_permission=("commerce", "admin"),
        write_permission=("commerce", "admin"),
        help_text="For webhook signature verification"
    ),
    
    SettingDefinition(
        key="stripe.enabled",
        name="Stripe Enabled",
        description="Enable Stripe payment processing",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="commerce",
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin")
    ),
    
    SettingDefinition(
        key="paypal.client_id",
        name="PayPal Client ID",
        description="PayPal client ID for payment processing",
        type=SettingType.ENCRYPTED,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.SECRET,
        category="commerce",
        ui_component="password",
        read_permission=("commerce", "admin"),
        write_permission=("commerce", "admin"),
        placeholder="AXX..."
    ),
    
    SettingDefinition(
        key="paypal.enabled",
        name="PayPal Enabled",
        description="Enable PayPal payment processing",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=False,
        category="commerce",
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin")
    ),
    
    # Tax Settings
    SettingDefinition(
        key="tax.enabled",
        name="Tax Calculation Enabled",
        description="Enable automatic tax calculation",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="commerce",
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin")
    ),
    
    SettingDefinition(
        key="tax.rate",
        name="Default Tax Rate (%)",
        description="Default tax rate percentage",
        type=SettingType.FLOAT,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=8.5,
        category="commerce",
        validation=lambda v: 0 <= float(v) <= 100,
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin"),
        help_text="0-100%"
    ),
    
    # Shipping Settings
    SettingDefinition(
        key="shipping.enabled",
        name="Shipping Enabled",
        description="Enable shipping calculations",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="commerce",
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin")
    ),
    
    SettingDefinition(
        key="shipping.flat_rate",
        name="Flat Shipping Rate",
        description="Flat rate shipping cost",
        type=SettingType.FLOAT,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=5.99,
        category="commerce",
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin"),
        help_text="Flat rate in dollars"
    ),
    
    SettingDefinition(
        key="shipping.free_threshold",
        name="Free Shipping Threshold",
        description="Order total for free shipping",
        type=SettingType.FLOAT,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=50.0,
        category="commerce",
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin"),
        help_text="Minimum order amount for free shipping"
    ),
    
    # Inventory Settings
    SettingDefinition(
        key="inventory.track_stock",
        name="Track Inventory",
        description="Enable inventory tracking",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="commerce",
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin")
    ),
    
    SettingDefinition(
        key="inventory.low_stock_threshold",
        name="Low Stock Alert Threshold",
        description="Alert when stock falls below this number",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=10,
        category="commerce",
        validation=lambda v: int(v) >= 0,
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin")
    ),
    
    # Order Settings
    SettingDefinition(
        key="orders.auto_complete_days",
        name="Auto-Complete Orders (Days)",
        description="Automatically complete orders after N days",
        type=SettingType.INTEGER,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=7,
        category="commerce",
        validation=lambda v: 1 <= int(v) <= 90,
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin"),
        help_text="1-90 days"
    ),
    
    SettingDefinition(
        key="orders.allow_guest_checkout",
        name="Allow Guest Checkout",
        description="Allow purchases without account creation",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="commerce",
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin")
    ),
    
    # Notification Settings
    SettingDefinition(
        key="notifications.order_confirmation",
        name="Send Order Confirmation Email",
        description="Email customer on order placement",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="commerce",
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin")
    ),
    
    SettingDefinition(
        key="notifications.low_stock_alert",
        name="Low Stock Alert Email",
        description="Email merchant when stock is low",
        type=SettingType.BOOLEAN,
        scope=SettingScope.ADDON,
        sensitivity=SettingSensitivity.INTERNAL,
        default=True,
        category="commerce",
        read_permission=("commerce", "read"),
        write_permission=("commerce", "admin")
    )
]


# ============================================================================
# Commerce Components
# ============================================================================

COMMERCE_COMPONENTS = [
    {
        "id": "product_grid",
        "name": "Product Grid",
        "type": "content",
        "description": "Display products in a grid layout",
        "factory": "commerce.components.create_product_grid",
        "category": "commerce"
    },
    {
        "id": "product_detail",
        "name": "Product Detail",
        "type": "content",
        "description": "Show detailed product information",
        "factory": "commerce.components.create_product_detail",
        "category": "commerce"
    },
    {
        "id": "cart_widget",
        "name": "Shopping Cart",
        "type": "widget",
        "description": "Shopping cart with item management",
        "factory": "commerce.components.create_cart_widget",
        "category": "commerce"
    },
    {
        "id": "checkout_form",
        "name": "Checkout Form",
        "type": "form",
        "description": "Complete checkout flow",
        "factory": "commerce.components.create_checkout_form",
        "category": "commerce"
    },
    {
        "id": "order_history",
        "name": "Order History",
        "type": "content",
        "description": "Customer order history",
        "factory": "commerce.components.create_order_history",
        "category": "commerce"
    }
]


# ============================================================================
# Commerce Routes
# ============================================================================

COMMERCE_ROUTES = [
    {
        "path": "/products",
        "handler": "commerce.routes.list_products",
        "methods": ["GET"],
        "permission": ("product", "read")
    },
    {
        "path": "/products/{product_id}",
        "handler": "commerce.routes.get_product",
        "methods": ["GET"],
        "permission": ("product", "read")
    },
    {
        "path": "/cart",
        "handler": "commerce.routes.view_cart",
        "methods": ["GET"],
        "permission": ("cart", "read")
    },
    {
        "path": "/checkout",
        "handler": "commerce.routes.checkout",
        "methods": ["GET", "POST"],
        "permission": ("order", "create")
    },
    {
        "path": "/orders",
        "handler": "commerce.routes.list_orders",
        "methods": ["GET"],
        "permission": ("order", "read")
    },
    {
        "path": "/orders/{order_id}",
        "handler": "commerce.routes.get_order",
        "methods": ["GET"],
        "permission": ("order", "read")
    }
]


# ============================================================================
# Theme Extensions
# ============================================================================

COMMERCE_THEME_EXTENSIONS = {
    "colors": {
        "product_primary": "#10b981",
        "product_secondary": "#059669",
        "cart_accent": "#f59e0b",
        "sale_badge": "#ef4444"
    },
    "components": {
        "product_card": {
            "border_radius": "0.75rem",
            "shadow": "md",
            "hover_shadow": "lg"
        },
        "cart_button": {
            "bg_color": "product_primary",
            "hover_bg": "product_secondary"
        }
    }
}


# ============================================================================
# Manifest
# ============================================================================

@dataclass
class AddonManifest:
    """Manifest for add-on registration"""
    id: str
    name: str
    version: str
    description: str
    domain: str
    roles: List[Role]
    settings: List[SettingDefinition]
    components: List[Dict[str, Any]]
    routes: List[Dict[str, Any]]
    theme_extensions: Dict[str, Any]


COMMERCE_MANIFEST = AddonManifest(
    id="commerce",
    name="E-Commerce",
    version="1.0.0",
    description="Complete e-commerce solution with products, cart, and checkout",
    domain="commerce",
    roles=COMMERCE_ROLES,
    settings=COMMERCE_SETTINGS,
    components=COMMERCE_COMPONENTS,
    routes=COMMERCE_ROUTES,
    theme_extensions=COMMERCE_THEME_EXTENSIONS
)


# ============================================================================
# Registration Functions
# ============================================================================

def register_commerce_roles():
    """Register commerce roles with permission system"""
    from core.services.auth.permissions import permission_registry
    
    for role in COMMERCE_ROLES:
        permission_registry.register_role(role)
        logger.info(f"Registered commerce role: {role.id}")


def register_commerce_settings():
    """Register commerce settings"""
    register_addon_settings("commerce", COMMERCE_SETTINGS)
    logger.info(f"Registered {len(COMMERCE_SETTINGS)} commerce settings")


def register_commerce_addon():
    """Complete commerce add-on registration"""
    register_commerce_roles()
    register_commerce_settings()
    logger.info("✓ Commerce add-on registered successfully")
