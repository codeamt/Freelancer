"""Commerce Routes - Shopping Cart"""
from fasthtml.common import *
from core.utils.logger import get_logger
from add_ons.services.auth import get_current_user

logger = get_logger(__name__)

# Initialize router
router_cart = APIRouter()


@router_cart.post("/shop/cart/add/{product_id}")
async def add_to_cart(request: Request, product_id: int):
    """Add product to cart (requires auth)"""
    user = await get_current_user(request)
    
    if not user:
        return Div(
            P("Please sign in to add items to cart", cls="text-error"),
            cls="alert alert-error"
        )
    
    # In a real app, save to database and fetch product details
    # TODO: 
    # product = await db.find_one("products", {"_id": product_id})
    # if not product:
    #     return error response
    # 
    # await db.insert_one("cart_items", {
    #     "user_id": user["_id"],
    #     "product_id": product_id,
    #     "quantity": 1,
    #     "added_at": datetime.utcnow()
    # })
    
    logger.info(f"User {user.get('_id')} added product {product_id} to cart")
    
    # For demo, just return success message
    # In production, fetch actual product data from database
    return Div(
        Div(
            P(f"Product {product_id} added to cart", cls="text-success"),
            cls="border-b pb-2 mb-2"
        ),
        Script("""
            // In production, update cart total from server response
            document.getElementById('checkout-btn').disabled = false;
        """)
    )


@router_cart.delete("/shop/cart/remove/{product_id}")
async def remove_from_cart(request: Request, product_id: int):
    """Remove product from cart (requires auth)"""
    user = await get_current_user(request)
    
    if not user:
        return Div(
            P("Please sign in", cls="text-error"),
            cls="alert alert-error"
        )
    
    # In a real app, remove from database
    # TODO: await db.delete_one("cart_items", {
    #     "user_id": user["_id"],
    #     "product_id": product_id
    # })
    
    logger.info(f"User {user.get('_id')} removed product {product_id} from cart")
    
    return Div(
        P("Item removed from cart", cls="text-success"),
        cls="alert alert-success"
    )


@router_cart.get("/shop/cart")
async def view_cart(request: Request):
    """View cart contents (requires auth)"""
    user = await get_current_user(request)
    
    if not user:
        return RedirectResponse("/auth/login?redirect=/shop/cart")
    
    # In a real app, fetch cart items from database
    # TODO: cart_items = await db.find("cart_items", {"user_id": user["_id"]})
    
    content = Div(
        H1("Shopping Cart", cls="text-3xl font-bold mb-8"),
        Div(
            P("Your cart is empty", cls="text-gray-500 text-center py-8"),
            A("Continue Shopping", href="/shop", cls="btn btn-primary"),
            cls="text-center"
        ),
        cls="container mx-auto px-4 py-8"
    )
    
    from core.ui.layout import Layout
    return Layout(content, title="Cart | FastApp")
