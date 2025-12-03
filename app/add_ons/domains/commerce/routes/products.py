"""Commerce Routes - Product Catalog"""
from fasthtml.common import *
from core.ui.layout import Layout
from core.utils.logger import get_logger
from add_ons.services.auth import get_current_user

logger = get_logger(__name__)

# Initialize router
router_products = APIRouter()

# Import shared product data
# Note: This creates a circular import that Python handles via late binding
# PRODUCTS will be available after __init__.py finishes loading
def get_products():
    """Get products list (lazy import to avoid circular dependency)"""
    from . import PRODUCTS
    return PRODUCTS


def ProductCard(product: dict, user: dict = None):
    """Product card with add to cart button"""
    return Div(
        Div(
            # Product image
            Img(
                src=product["image"],
                alt=product["name"],
                cls="w-full h-48 object-cover rounded-t-lg"
            ),
            # Product info
            Div(
                H3(product["name"], cls="text-lg font-semibold mb-2"),
                P(product["description"], cls="text-sm text-gray-500 mb-4"),
                Div(
                    Span(f"${product['price']}", cls="text-2xl font-bold text-blue-600"),
                    cls="mb-4"
                ),
                # Add to cart button
                (Button(
                    "Add to Cart",
                    cls="btn btn-primary w-full",
                    hx_post=f"/shop/cart/add/{product['id']}",
                    hx_target="#cart-items",
                    hx_swap="innerHTML"
                ) if user else A(
                    "Sign in to purchase",
                    href="/auth/login?redirect=/shop",
                    cls="btn btn-outline w-full"
                )),
                cls="p-4"
            ),
            cls="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow"
        )
    )


@router_products.get("/shop")
async def shop_page(request: Request):
    """Display shop page with products"""
    user = await get_current_user(request)
    products = get_products()
    
    content = Div(
        # Header
        Div(
            H1("Course Shop", cls="text-4xl font-bold mb-4"),
            P("Premium courses to boost your career", cls="text-xl text-gray-500 mb-8"),
            cls="text-center mb-12"
        ),
        
        # Products Grid
        Div(
            *[ProductCard(product, user) for product in products],
            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12"
        ),
        
        # Cart Summary (if user is logged in)
        (Div(
            H2("Your Cart", cls="text-2xl font-bold mb-4"),
            Div(
                P("Your cart is empty", cls="text-gray-500 text-center py-8"),
                id="cart-items"
            ),
            Div(
                Div(
                    Span("Total:", cls="text-xl font-bold"),
                    Span("$0.00", id="cart-total", cls="text-xl font-bold text-blue-600"),
                    cls="flex justify-between mb-4"
                ),
                Button(
                    "Proceed to Checkout",
                    cls="btn btn-primary w-full",
                    disabled=True,
                    id="checkout-btn"
                ),
                cls="border-t pt-4"
            ),
            cls="bg-base-200 p-6 rounded-lg"
        ) if user else Div(
            H2("Sign in to purchase", cls="text-2xl font-bold mb-4 text-center"),
            P("Create an account or sign in to add items to your cart", cls="text-gray-500 text-center mb-4"),
            Div(
                A("Sign In", href="/auth/login", cls="btn btn-primary mr-2"),
                A("Register", href="/auth/register", cls="btn btn-outline"),
                cls="flex justify-center"
            ),
            cls="bg-base-200 p-8 rounded-lg text-center"
        )),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="Shop | FastApp")
