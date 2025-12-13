"""Commerce Routes - Shopping Cart"""
from fasthtml.common import *
from decimal import Decimal
from core.utils.logger import get_logger
from core.services.auth import get_current_user_from_context

logger = get_logger(__name__)

# Initialize router
router_cart = APIRouter()


@router_cart.post("/shop/cart/add/{product_id}")
async def add_to_cart(request: Request, product_id: int):
    """Add product to cart (requires auth)"""
    # Get services from app state
    cart_service = request.app.state.cart_service
    product_service = request.app.state.product_service
    
    user = get_current_user_from_context()
    
    if not user:
        return Div(
            P("Please sign in to add items to cart", cls="text-error"),
            cls="alert alert-error"
        )
    
    cart_id = str(user['id'])
    
    # Fetch product from database
    product = product_service.get_product(str(product_id))
    
    if not product:
        return Div(
            P("Product not found", cls="text-error"),
            cls="alert alert-error"
        )
    
    if not product.in_stock:
        return Div(
            P("Product out of stock", cls="text-error"),
            cls="alert alert-error"
        )
    
    try:
        cart = cart_service.add_to_cart(
            cart_id=cart_id,
            product_id=product.product_id,
            name=product.name,
            price=product.price,
            quantity=1,
            user_id=cart_id
        )
        
        logger.info(f"User {user.get('_id')} added product {product_id} to cart")
        
        return Div(
            Div(
                P(f"Product {product_id} added to cart", cls="text-success"),
                P(f"Cart total: ${cart.total}", cls="text-sm text-gray-600"),
                cls="border-b pb-2 mb-2"
            ),
            Script("""
                document.getElementById('checkout-btn').disabled = false;
            """)
        )
    except Exception as e:
        logger.error(f"Failed to add to cart: {e}")
        return Div(
            P("Failed to add item to cart", cls="text-error"),
            cls="alert alert-error"
        )


@router_cart.delete("/shop/cart/remove/{product_id}")
async def remove_from_cart(request: Request, product_id: int):
    """Remove product from cart (requires auth)"""
    cart_service = request.app.state.cart_service
    
    user = get_current_user_from_context()
    
    if not user:
        return Div(
            P("Please sign in", cls="text-error"),
            cls="alert alert-error"
        )
    
    cart_id = str(user['id'])
    success = cart_service.remove_from_cart(cart_id, str(product_id))
    
    if success:
        logger.info(f"User {user.get('_id')} removed product {product_id} from cart")
        return Div(
            P("Item removed from cart", cls="text-success"),
            cls="alert alert-success"
        )
    
    return Div(
        P("Item not found in cart", cls="text-error"),
        cls="alert alert-error"
    )


@router_cart.get("/shop/cart")
async def view_cart(request: Request):
    """View cart contents (requires auth)"""
    cart_service = request.app.state.cart_service
    
    user = get_current_user_from_context()
    
    if not user:
        return RedirectResponse("/auth/login?redirect=/shop/cart")
    
    cart_id = str(user['id'])
    cart = cart_service.get_cart(cart_id)
    
    if not cart or cart.is_empty:
        content = Div(
            H1("Shopping Cart", cls="text-3xl font-bold mb-8"),
            Div(
                P("Your cart is empty", cls="text-gray-500 text-center py-8"),
                A("Continue Shopping", href="/shop", cls="btn btn-primary"),
                cls="text-center"
            ),
            cls="container mx-auto px-4 py-8"
        )
    else:
        items_html = [
            Div(
                P(item.name, cls="font-bold"),
                P(f"${item.price} x {item.quantity} = ${item.subtotal}", cls="text-sm"),
                cls="border-b py-2"
            )
            for item in cart.items.values()
        ]
        
        content = Div(
            H1("Shopping Cart", cls="text-3xl font-bold mb-8"),
            Div(*items_html, cls="mb-4"),
            Div(
                P(f"Total: ${cart.total}", cls="text-xl font-bold"),
                A("Checkout", href="/shop/checkout", cls="btn btn-primary mt-4"),
                cls="border-t pt-4"
            ),
            cls="container mx-auto px-4 py-8"
        )
    
    from core.ui.layout import Layout
    return Layout(content, title="Cart | FastApp")
