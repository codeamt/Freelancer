"""Commerce Routes - Checkout & Payment"""
from fasthtml.common import *
from core.ui.layout import Layout
from core.utils.logger import get_logger
from core.services.auth import get_current_user_from_context
from core.services import CartService, OrderService, PaymentService, get_db_service

logger = get_logger(__name__)

# Initialize router and services
router_checkout = APIRouter()
cart_service = CartService()
order_service = OrderService()
payment_service = PaymentService()
db = get_db_service()  # Multi-database service with state integration


@router_checkout.get("/shop/checkout")
async def checkout_page(request: Request):
    """Checkout page (requires auth)"""
    user = get_current_user_from_context()
    
    if not user:
        return RedirectResponse("/auth/login?redirect=/shop/checkout")
    
    content = Div(
        H1("Checkout", cls="text-3xl font-bold mb-8"),
        
        Div(
            # Order Summary
            Div(
                H2("Order Summary", cls="text-2xl font-bold mb-4"),
                P("Review your order before completing purchase", cls="text-gray-500 mb-6"),
                # Fetch cart from service
                Div(
                    P("No items in cart", cls="text-gray-500 py-4"),
                    cls="border rounded p-4 mb-6"
                ),
                cls="mb-8"
            ),
            
            # Payment Form
            Div(
                H2("Payment Information", cls="text-2xl font-bold mb-4"),
                Form(
                    Div(
                        Label("Card Number", cls="block text-sm font-medium mb-2"),
                        Input(
                            type="text",
                            placeholder="1234 5678 9012 3456",
                            cls="input input-bordered w-full",
                            required=True
                        ),
                        cls="mb-4"
                    ),
                    Div(
                        Div(
                            Label("Expiry Date", cls="block text-sm font-medium mb-2"),
                            Input(
                                type="text",
                                placeholder="MM/YY",
                                cls="input input-bordered w-full",
                                required=True
                            ),
                            cls="flex-1 mr-2"
                        ),
                        Div(
                            Label("CVV", cls="block text-sm font-medium mb-2"),
                            Input(
                                type="text",
                                placeholder="123",
                                cls="input input-bordered w-full",
                                required=True
                            ),
                            cls="flex-1"
                        ),
                        cls="flex mb-4"
                    ),
                    Button("Complete Purchase", type="submit", cls="btn btn-primary w-full"),
                    hx_post="/shop/checkout/process",
                    hx_target="#checkout-result"
                ),
                Div(id="checkout-result", cls="mt-4"),
                cls="bg-base-200 p-6 rounded-lg"
            ),
            
            cls="max-w-2xl mx-auto"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="Checkout | FastApp")


@router_checkout.post("/shop/checkout/process")
async def process_checkout(request: Request):
    """Process checkout with Stripe and create order"""
    user = get_current_user_from_context()
    
    if not user:
        return Div(
            P("Please sign in to complete purchase", cls="text-error"),
            cls="alert alert-error"
        )
    
    cart_id = str(user['id'])
    cart = cart_service.get_cart(cart_id)
    
    if not cart or cart.is_empty:
        return Div(
            P("Your cart is empty", cls="text-error"),
            cls="alert alert-error"
        )
    
    try:
        # Create Stripe checkout session
        base_url = str(request.base_url).rstrip('/')
        success_url = f"{base_url}/shop/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}/shop/checkout"
        
        checkout_session = cart_service.create_checkout_session(
            cart_id=cart_id,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if not checkout_session:
            return Div(
                P("Failed to create checkout session", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Create order (pending payment)
        order = order_service.create_order_from_cart(
            user_id=cart_id,
            cart=cart
        )
        
        logger.info(f"Created order {order.order_id} for user {user.get('_id')}")
        
        # Redirect to Stripe checkout
        return Div(
            Script(f"""
                window.location.href = '{checkout_session['session_url']}';
            """)
        )
        
    except Exception as e:
        logger.error(f"Checkout failed: {e}")
        return Div(
            P("Checkout failed. Please try again.", cls="text-error"),
            cls="alert alert-error"
        )


@router_checkout.get("/shop/checkout/success")
async def checkout_success(request: Request, session_id: str = None):
    """Checkout success page - mark order as paid and clear cart"""
    user = get_current_user_from_context()
    
    if not user:
        return RedirectResponse("/auth/login")
    
    cart_id = str(user['id'])
    
    # Mark most recent order as paid
    user_orders = order_service.get_user_orders(cart_id)
    if user_orders:
        latest_order = user_orders[-1]
        order_service.mark_order_as_paid(latest_order.order_id, session_id)
        logger.info(f"Order {latest_order.order_id} marked as paid, session: {session_id}")
    
    # Clear cart
    cart_service.clear_cart(cart_id)
    logger.info(f"Cleared cart for user {user.get('_id')}")
    
    content = Div(
        Div(
            H1("✓ Order Complete!", cls="text-4xl font-bold text-success mb-4"),
            P("Thank you for your purchase!", cls="text-xl mb-8"),
            Div(
                P("Your order has been confirmed and you'll receive an email shortly.", cls="mb-4"),
                P(f"Order ID: {latest_order.order_id if user_orders else 'N/A'}", cls="text-sm text-gray-600 mb-4"),
                P("You can now access your purchased courses.", cls="mb-6"),
                Div(
                    A("View My Courses", href="/lms/student/dashboard", cls="btn btn-primary mr-2"),
                    A("Continue Shopping", href="/shop", cls="btn btn-outline"),
                    cls="flex justify-center"
                )
            ),
            cls="text-center max-w-2xl mx-auto bg-base-200 p-12 rounded-lg"
        ),
        cls="container mx-auto px-4 py-16"
    )
    
    return Layout(content, title="Order Complete | FastApp")
