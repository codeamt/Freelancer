"""Commerce Routes - Checkout & Payment"""
from fasthtml.common import *
from core.ui.layout import Layout
from core.utils.logger import get_logger
from add_ons.services.auth import get_current_user

logger = get_logger(__name__)

# Initialize router
router_checkout = APIRouter()


@router_checkout.get("/shop/checkout")
async def checkout_page(request: Request):
    """Checkout page (requires auth)"""
    user = await get_current_user(request)
    
    if not user:
        return RedirectResponse("/auth/login?redirect=/shop/checkout")
    
    content = Div(
        H1("Checkout", cls="text-3xl font-bold mb-8"),
        
        Div(
            # Order Summary
            Div(
                H2("Order Summary", cls="text-2xl font-bold mb-4"),
                P("Review your order before completing purchase", cls="text-gray-500 mb-6"),
                # Cart items would go here
                # TODO: Fetch from database and display
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
    """Process checkout (requires auth)"""
    user = await get_current_user(request)
    
    if not user:
        return Div(
            P("Please sign in to complete purchase", cls="text-error"),
            cls="alert alert-error"
        )
    
    # In a real app:
    # 1. Validate cart items
    # 2. Create Stripe checkout session using StripeService
    # 3. Process payment
    # 4. Create order record
    # 5. Clear cart
    # 6. Send confirmation email
    
    # TODO: from add_ons.services.stripe import StripeService
    # TODO: stripe = StripeService()
    # TODO: checkout_url = stripe.create_checkout_session(
    #     amount_cents=total * 100,
    #     currency="usd",
    #     success_url=f"{request.base_url}/shop/checkout/success",
    #     cancel_url=f"{request.base_url}/shop/checkout"
    # )
    
    logger.info(f"Processing checkout for user {user.get('_id')}")
    
    return Div(
        Div(
            P("✓ Purchase successful! Thank you for your order.", cls="text-success"),
            P("You will receive a confirmation email shortly.", cls="text-sm mt-2"),
            A("View My Courses", href="/lms/student/dashboard", cls="btn btn-primary mt-4"),
            cls="alert alert-success"
        ),
        Script("""
            setTimeout(() => {
                window.location.href = '/lms/student/dashboard';
            }, 3000);
        """)
    )


@router_checkout.get("/shop/checkout/success")
async def checkout_success(request: Request):
    """Checkout success page"""
    user = await get_current_user(request)
    
    if not user:
        return RedirectResponse("/auth/login")
    
    content = Div(
        Div(
            H1("✓ Order Complete!", cls="text-4xl font-bold text-success mb-4"),
            P("Thank you for your purchase!", cls="text-xl mb-8"),
            Div(
                P("Your order has been confirmed and you'll receive an email shortly.", cls="mb-4"),
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
