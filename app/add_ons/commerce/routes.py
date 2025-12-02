"""Commerce Routes - Simple One-Page Shop"""
from fasthtml.common import *
from core.ui.layout import Layout
from core.utils.logger import get_logger
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from add_ons.auth.services import AuthService
from core.services.db import DBService

logger = get_logger(__name__)

# Initialize router
router_commerce = APIRouter()

# Initialize auth service
db_service = DBService()
auth_service = AuthService(db_service)

# Sample products
PRODUCTS = [
    {
        "id": 1,
        "name": "Python Mastery Course",
        "description": "Complete Python programming course from beginner to advanced",
        "price": 49.99,
        "image": "https://via.placeholder.com/300x200?text=Python+Course"
    },
    {
        "id": 2,
        "name": "Web Development Bootcamp",
        "description": "Learn HTML, CSS, JavaScript, and modern frameworks",
        "price": 79.99,
        "image": "https://via.placeholder.com/300x200?text=Web+Dev"
    },
    {
        "id": 3,
        "name": "Data Science Fundamentals",
        "description": "Master data analysis, visualization, and machine learning",
        "price": 99.99,
        "image": "https://via.placeholder.com/300x200?text=Data+Science"
    },
    {
        "id": 4,
        "name": "Mobile App Development",
        "description": "Build iOS and Android apps with React Native",
        "price": 89.99,
        "image": "https://via.placeholder.com/300x200?text=Mobile+Dev"
    }
]


async def get_current_user(request: Request):
    """Get current user from request"""
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user_data = auth_service.verify_token(token)
            if user_data:
                return await auth_service.get_user_by_id(user_data.get("sub"))
        
        # Try cookie
        token = request.cookies.get("auth_token")
        if token:
            user_data = auth_service.verify_token(token)
            if user_data:
                return await auth_service.get_user_by_id(user_data.get("sub"))
        
        return None
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None


@router_commerce.get("/shop")
async def shop_page(request: Request):
    """Display shop page with products"""
    user = await get_current_user(request)
    
    content = Div(
        # Header
        Div(
            H1("Course Shop", cls="text-4xl font-bold mb-4"),
            P("Premium courses to boost your career", cls="text-xl text-gray-500 mb-8"),
            cls="text-center mb-12"
        ),
        
        # Products Grid
        Div(
            *[ProductCard(product, user) for product in PRODUCTS],
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


@router_commerce.post("/shop/cart/add/{product_id}")
async def add_to_cart(request: Request, product_id: int):
    """Add product to cart (requires auth)"""
    user = await get_current_user(request)
    
    if not user:
        return Div(
            P("Please sign in to add items to cart", cls="text-error"),
            cls="alert alert-error"
        )
    
    # Find product
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return Div(
            P("Product not found", cls="text-error"),
            cls="alert alert-error"
        )
    
    # In a real app, save to database
    # For now, just return success message
    logger.info(f"User {user.get('_id')} added product {product_id} to cart")
    
    return Div(
        Div(
            Div(
                Span(product["name"], cls="font-semibold"),
                Span(f"${product['price']}", cls="text-blue-600"),
                cls="flex justify-between mb-2"
            ),
            cls="border-b pb-2 mb-2"
        ),
        Script("""
            document.getElementById('cart-total').textContent = '$""" + str(product['price']) + """';
            document.getElementById('checkout-btn').disabled = false;
        """)
    )


@router_commerce.get("/shop/checkout")
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


@router_commerce.post("/shop/checkout/process")
async def process_checkout(request: Request):
    """Process checkout (requires auth)"""
    user = await get_current_user(request)
    
    if not user:
        return Div(
            P("Please sign in to complete purchase", cls="text-error"),
            cls="alert alert-error"
        )
    
    # In a real app, process payment here
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
