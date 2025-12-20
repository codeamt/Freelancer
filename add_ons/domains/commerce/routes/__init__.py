"""Commerce Routes Package"""
from fasthtml.common import *
from .products import router_products
from .cart import router_cart
from .checkout import router_checkout

# Import shared data from domain
from ..data import SAMPLE_PRODUCTS as PRODUCTS

# -----------------------------------------------------------------------------
# Router Configuration
# -----------------------------------------------------------------------------

# Combine all commerce routers
# Note: APIRouter doesn't have .mount(), so we include routes from all sub-routers
router_commerce = APIRouter()

# Include routes from sub-routers
router_commerce.routes.extend(router_products.routes)
router_commerce.routes.extend(router_cart.routes)
router_commerce.routes.extend(router_checkout.routes)

__all__ = ["router_commerce", "PRODUCTS"]
