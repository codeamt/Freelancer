"""Cart Routes
 
 Handles shopping cart operations and checkout.
 """
from fasthtml.common import *
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse, JSONResponse
from typing import Optional
from decimal import Decimal
from core.services.cart_service import CartService
from core.services.auth import get_current_user_from_context
from core.utils.logger import get_logger

logger = get_logger(__name__)

router_cart = APIRouter()

# Initialize cart service (should be injected via dependency injection in production)
cart_service = CartService()


@router_cart.post("/cart/add")
async def add_to_cart(request: Request):
    """
    Add item to cart.
    
    Returns JSON response for HTMX updates.
    """
    user = get_current_user_from_context()

    form = getattr(request.state, "sanitized_form", None) or await request.form()
    product_id = form.get("product_id")
    name = form.get("name")
    price = form.get("price")
    quantity_raw = form.get("quantity", 1)

    if product_id is None or name is None or price is None:
        return JSONResponse({"success": False, "error": "Missing required fields"}, status_code=422)

    try:
        quantity = int(quantity_raw) if quantity_raw is not None else 1
    except (TypeError, ValueError):
        return JSONResponse({"success": False, "error": "Invalid quantity"}, status_code=422)
    
    # Use user ID if authenticated, otherwise use session ID
    cart_id = str(user['id']) if user else request.session.get('cart_id', str(request.client.host))
    
    if not user:
        request.session['cart_id'] = cart_id
    
    try:
        cart = cart_service.add_to_cart(
            cart_id=cart_id,
            product_id=product_id,
            name=name,
            price=Decimal(str(price)),
            quantity=quantity,
            user_id=str(user['id']) if user else None
        )
        
        return JSONResponse({
            "success": True,
            "message": f"Added {quantity}x {name} to cart",
            "cart": cart.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to add item to cart: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router_cart.delete("/cart/remove/{product_id}")
async def remove_from_cart(request: Request, product_id: str):
    """Remove item from cart."""
    user = get_current_user_from_context()
    cart_id = str(user['id']) if user else request.session.get('cart_id')
    
    if not cart_id:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    success = cart_service.remove_from_cart(cart_id, product_id)
    
    if success:
        cart = cart_service.get_cart(cart_id)
        return JSONResponse({
            "success": True,
            "message": "Item removed from cart",
            "cart": cart.to_dict() if cart else None
        })
    
    return JSONResponse({
        "success": False,
        "error": "Item not found in cart"
    }, status_code=404)


@router_cart.put("/cart/update/{product_id}")
async def update_quantity(request: Request, product_id: str):
    """Update item quantity in cart."""
    user = get_current_user_from_context()
    cart_id = str(user['id']) if user else request.session.get('cart_id')
    
    if not cart_id:
        raise HTTPException(status_code=404, detail="Cart not found")

    form = getattr(request.state, "sanitized_form", None) or await request.form()
    quantity_raw = form.get("quantity")
    try:
        quantity = int(quantity_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Invalid quantity")
    
    success = cart_service.update_quantity(cart_id, product_id, quantity)
    
    if success:
        cart = cart_service.get_cart(cart_id)
        return JSONResponse({
            "success": True,
            "message": "Quantity updated",
            "cart": cart.to_dict() if cart else None
        })
    
    return JSONResponse({
        "success": False,
        "error": "Failed to update quantity"
    }, status_code=400)


@router_cart.get("/cart/view")
async def view_cart(request: Request):
    """View cart contents."""
    user = get_current_user_from_context()
    cart_id = str(user['id']) if user else request.session.get('cart_id')
    
    if not cart_id:
        return JSONResponse({
            "cart": None,
            "message": "Cart is empty"
        })
    
    cart = cart_service.get_cart(cart_id)
    
    if not cart:
        return JSONResponse({
            "cart": None,
            "message": "Cart is empty"
        })
    
    return JSONResponse({
        "cart": cart.to_dict()
    })


@router_cart.delete("/cart/clear")
async def clear_cart(request: Request):
    """Clear all items from cart."""
    user = get_current_user_from_context()
    cart_id = str(user['id']) if user else request.session.get('cart_id')
    
    if not cart_id:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    success = cart_service.clear_cart(cart_id)
    
    return JSONResponse({
        "success": success,
        "message": "Cart cleared" if success else "Failed to clear cart"
    })


@router_cart.post("/cart/checkout")
async def checkout(request: Request):
    """
    Create Stripe checkout session for cart.
    
    Redirects to Stripe checkout page.
    """
    user = get_current_user_from_context()
    
    if not user:
        return RedirectResponse("/login?redirect=/cart/checkout", status_code=303)
    
    cart_id = str(user['id'])
    cart = cart_service.get_cart(cart_id)
    
    if not cart or cart.is_empty:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Create checkout session
    base_url = str(request.base_url).rstrip('/')
    success_url = f"{base_url}/cart/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}/cart/cancel"
    
    checkout_session = cart_service.create_checkout_session(
        cart_id=cart_id,
        success_url=success_url,
        cancel_url=cancel_url
    )
    
    if not checkout_session:
        raise HTTPException(status_code=500, detail="Failed to create checkout session")
    
    # Redirect to Stripe checkout
    return RedirectResponse(checkout_session['session_url'], status_code=303)


@router_cart.get("/cart/success")
async def checkout_success(request: Request, session_id: Optional[str] = None):
    """
    Handle successful checkout.
    
    Clear cart and show success message.
    """
    user = get_current_user_from_context()
    
    if user:
        cart_id = str(user['id'])
        cart_service.clear_cart(cart_id)
        logger.info(f"Checkout successful for user {user['id']}, session: {session_id}")
    
    return JSONResponse({
        "success": True,
        "message": "Payment successful! Your order has been placed.",
        "session_id": session_id
    })


@router_cart.get("/cart/cancel")
async def checkout_cancel(request: Request):
    """
    Handle cancelled checkout.
    
    Cart remains intact.
    """
    return JSONResponse({
        "success": False,
        "message": "Checkout cancelled. Your cart has been saved."
    })


@router_cart.post("/cart/merge")
async def merge_carts(request: Request):
    """
    Merge session cart into user cart on login.
    
    Called automatically after user authentication.
    """
    user = get_current_user_from_context()
    
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_cart_id = request.session.get('cart_id')
    user_cart_id = str(user['id'])
    
    if session_cart_id and session_cart_id != user_cart_id:
        cart = cart_service.merge_carts(session_cart_id, user_cart_id)
        request.session.pop('cart_id', None)
        
        return JSONResponse({
            "success": True,
            "message": "Carts merged successfully",
            "cart": cart.to_dict()
        })
    
    return JSONResponse({
        "success": True,
        "message": "No merge needed"
    })
