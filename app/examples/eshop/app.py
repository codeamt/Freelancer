"""
E-Shop Example Application

Demonstrates proper use of:
- Repository pattern with multi-database coordination
- Service layer for business logic
- Dependency injection from parent app
- Transaction management
"""
from fasthtml.common import *
from monsterui.all import *
from typing import Optional

from core.utils.logger import get_logger
from core.ui.layout import Layout
from core.services.auth import AuthService, UserService
from core.services.auth.utils import get_current_user_from_request
from core.db.adapters import PostgresAdapter, MongoDBAdapter, RedisAdapter

# Commerce domain imports
from add_ons.domains.commerce.repositories import ProductRepository
from add_ons.domains.commerce.data import SAMPLE_PRODUCTS, get_product_by_id

# Custom auth UI
from .auth_ui import EShopLoginPage, EShopRegisterPage

logger = get_logger(__name__)


def create_eshop_app(
    auth_service: AuthService,
    user_service: UserService,
    postgres: PostgresAdapter,
    mongodb: Optional[MongoDBAdapter] = None,
    redis: Optional[RedisAdapter] = None
) -> FastHTML:
    """
    Create E-Shop example application.
    
    Args:
        auth_service: Injected authentication service
        user_service: Injected user management service
        postgres: PostgreSQL adapter
        mongodb: MongoDB adapter (optional)
        redis: Redis adapter (optional)
        
    Returns:
        FastHTML app instance
    """
    logger.info("Initializing E-Shop example app...")
    
    # Initialize commerce repository
    product_repo = ProductRepository(
        postgres=postgres,
        mongodb=mongodb,
        redis=redis
    )
    
    # Create app with theme
    app = FastHTML(hdrs=[*Theme.slate.headers()])
    
    # In-memory cart storage (TODO: Move to Redis or database)
    cart_storage = {}  # {user_id: {product_id: quantity}}
    
    # Base path
    BASE = "/eshop-example"
    
    # ========================================================================
    # Helper Functions
    # ========================================================================
    
    async def get_user(request: Request):
        """Get current user from request."""
        return await get_current_user_from_request(request, auth_service)
    
    # ========================================================================
    # Routes
    # ========================================================================
    
    @app.get("/")
    async def home(request: Request):
        """Shop homepage."""
        user = await get_user(request)
        
        # Navigation
        nav_items = [
            A("Home", href=f"{BASE}/", cls="btn btn-ghost"),
            A("Cart", href=f"{BASE}/cart", cls="btn btn-ghost"),
        ]
        
        if user and not isinstance(user, type(None)):
            nav_items.append(
                A(f"Hello, {user.email}", href=f"{BASE}/profile", cls="btn btn-ghost")
            )
            nav_items.append(
                Form(
                    Button("Logout", type="submit", cls="btn btn-ghost"),
                    method="post",
                    action=f"{BASE}/auth/logout"
                )
            )
        else:
            nav_items.append(A("Login", href=f"{BASE}/login", cls="btn btn-ghost"))
        
        nav = Div(*nav_items, cls="flex gap-2 mb-8 justify-end")
        
        content = Div(
            nav,
            # Header
            Div(
                H1("E-Shop Demo", cls="text-4xl font-bold mb-4"),
                P(
                    "Browse our curated selection of products",
                    cls="text-xl text-gray-500 mb-8"
                ),
                cls="text-center mb-12"
            ),
            
            # Products Grid
            Div(
                *[ProductCard(product, user, BASE) for product in SAMPLE_PRODUCTS],
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title="E-Shop | Demo")
    
    @app.get("/product/{product_id}")
    async def product_detail(request: Request, product_id: int):
        """Product detail page."""
        user = await get_user(request)
        
        # Get product (could use repo here for real DB)
        product = get_product_by_id(product_id)
        
        if not product:
            return Layout(
                Div(
                    H1("Product Not Found", cls="text-3xl font-bold mb-4"),
                    A("← Back to Shop", href=f"{BASE}/", cls="btn btn-primary"),
                    cls="text-center py-20"
                ),
                title="Not Found"
            )
        
        content = Div(
            # Back button
            A("← Back to Shop", href=f"{BASE}/", cls="btn btn-ghost mb-6"),
            
            # Product details
            Div(
                # Image
                Div(
                    Img(
                        src=product["image"],
                        alt=product["name"],
                        cls="w-full rounded-lg"
                    ),
                    cls="lg:w-1/2"
                ),
                
                # Info
                Div(
                    H1(product["name"], cls="text-3xl font-bold mb-4"),
                    P(product["description"], cls="text-lg text-gray-600 mb-4"),
                    P(
                        f"${product['price']}",
                        cls="text-4xl font-bold text-blue-600 mb-6"
                    ),
                    
                    # Features
                    Div(
                        H3("Features:", cls="font-semibold mb-2"),
                        Ul(*[
                            Li(f, cls="text-gray-600")
                            for f in product.get("features", [])
                        ]),
                        cls="mb-6"
                    ) if product.get("features") else None,
                    
                    # Add to cart button
                    (Button(
                        "Add to Cart",
                        cls="btn btn-primary btn-lg w-full",
                        hx_post=f"{BASE}/cart/add/{product_id}",
                        hx_target="#cart-notification"
                    ) if user else A(
                        "Sign in to purchase",
                        href=f"{BASE}/login",
                        cls="btn btn-primary btn-lg w-full"
                    )),
                    
                    Div(id="cart-notification", cls="mt-4"),
                    
                    cls="lg:w-1/2"
                ),
                
                cls="flex flex-col lg:flex-row gap-8"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title=f"{product['name']} | E-Shop")
    
    @app.post("/cart/add/{product_id}")
    async def add_to_cart(request: Request, product_id: int):
        """Add product to cart."""
        user = await get_user(request)
        
        if not user:
            return Div(
                P("Please sign in to add items to cart", cls="text-error"),
                cls="alert alert-error"
            )
        
        product = get_product_by_id(product_id)
        if not product:
            return Div(
                P("Product not found", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Add to cart
        user_id = user.id
        if user_id not in cart_storage:
            cart_storage[user_id] = {}
        
        if product_id in cart_storage[user_id]:
            cart_storage[user_id][product_id] += 1
        else:
            cart_storage[user_id][product_id] = 1
        
        logger.info(f"User {user_id} added product {product_id} to cart")
        
        return Div(
            P(f"✓ {product['name']} added to cart!", cls="text-success"),
            A("View Cart", href=f"{BASE}/cart", cls="btn btn-sm btn-outline mt-2"),
            cls="alert alert-success"
        )
    
    @app.get("/cart")
    async def view_cart(request: Request):
        """View shopping cart."""
        user = await get_user(request)
        
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/cart")
        
        user_id = user.id
        cart_items = cart_storage.get(user_id, {})
        
        if not cart_items:
            content = Div(
                H1("Your Cart", cls="text-4xl font-bold mb-8"),
                Div(
                    H2("Your cart is empty", cls="text-2xl mb-4"),
                    P("Add some products to get started!", cls="text-gray-600 mb-6"),
                    A("Browse Products", href=f"{BASE}/", cls="btn btn-primary"),
                    cls="text-center py-12"
                ),
                cls="container mx-auto px-4 py-8"
            )
            return Layout(content, title="Cart | E-Shop")
        
        # Calculate totals
        cart_products = []
        subtotal = 0
        for pid, qty in cart_items.items():
            product = get_product_by_id(pid)
            if product:
                cart_products.append({**product, "quantity": qty})
                subtotal += product["price"] * qty
        
        tax = subtotal * 0.1
        total = subtotal + tax
        
        content = Div(
            H1("Your Cart", cls="text-4xl font-bold mb-8"),
            
            # Cart items
            Div(
                *[CartItem(item, BASE) for item in cart_products],
                cls="space-y-4 mb-8"
            ),
            
            # Cart summary
            Div(
                H2("Order Summary", cls="text-2xl font-bold mb-4"),
                Div(
                    Div(
                        Span("Subtotal:", cls="font-semibold"),
                        Span(f"${subtotal:.2f}"),
                        cls="flex justify-between mb-2"
                    ),
                    Div(
                        Span("Tax (10%):", cls="font-semibold"),
                        Span(f"${tax:.2f}"),
                        cls="flex justify-between mb-2"
                    ),
                    Div(cls="divider"),
                    Div(
                        Span("Total:", cls="font-bold text-xl"),
                        Span(
                            f"${total:.2f}",
                            cls="font-bold text-xl text-blue-600"
                        ),
                        cls="flex justify-between mb-6"
                    ),
                    A(
                        "Proceed to Checkout",
                        href=f"{BASE}/checkout",
                        cls="btn btn-primary btn-lg w-full"
                    ),
                    cls="bg-base-200 p-6 rounded-lg"
                ),
                cls="lg:w-1/3"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title="Cart | E-Shop")
    
    @app.post("/cart/remove/{product_id}")
    async def remove_from_cart(request: Request, product_id: int):
        """Remove product from cart."""
        user = await get_user(request)
        
        if not user:
            return Div(P("Not authenticated", cls="text-error"), cls="alert alert-error")
        
        user_id = user.id
        if user_id in cart_storage and product_id in cart_storage[user_id]:
            del cart_storage[user_id][product_id]
        
        return RedirectResponse(f"{BASE}/cart", status_code=303)
    
    @app.get("/checkout")
    async def checkout_page(request: Request):
        """Checkout page."""
        user = await get_user(request)
        
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/checkout")
        
        user_id = user.id
        cart_items = cart_storage.get(user_id, {})
        
        if not cart_items:
            return RedirectResponse(f"{BASE}/cart")
        
        # Calculate totals
        cart_products = []
        subtotal = 0
        for pid, qty in cart_items.items():
            product = get_product_by_id(pid)
            if product:
                cart_products.append({**product, "quantity": qty})
                subtotal += product["price"] * qty
        
        tax = subtotal * 0.1
        total = subtotal + tax
        
        content = Div(
            H1("Checkout", cls="text-4xl font-bold mb-8"),
            
            Div(
                # Order summary
                Div(
                    H2("Order Summary", cls="text-2xl font-bold mb-4"),
                    *[Div(
                        Span(
                            f"{item['name']} x{item['quantity']}",
                            cls="font-semibold"
                        ),
                        Span(f"${item['price'] * item['quantity']:.2f}"),
                        cls="flex justify-between mb-2"
                    ) for item in cart_products],
                    Div(cls="divider"),
                    Div(
                        Span("Total:", cls="font-bold text-xl"),
                        Span(
                            f"${total:.2f}",
                            cls="font-bold text-xl text-blue-600"
                        ),
                        cls="flex justify-between mb-6"
                    ),
                    cls="bg-base-200 p-6 rounded-lg mb-8"
                ),
                
                # Payment form (demo)
                Div(
                    H2("Payment Information", cls="text-2xl font-bold mb-4"),
                    Form(
                        Div(
                            Label("Card Number", cls="label"),
                            Input(
                                type="text",
                                placeholder="1234 5678 9012 3456",
                                cls="input input-bordered w-full",
                                required=True
                            ),
                            cls="form-control mb-4"
                        ),
                        Button(
                            "Place Order",
                            type="submit",
                            cls="btn btn-primary btn-lg w-full"
                        ),
                        hx_post=f"{BASE}/checkout/complete",
                        hx_target="#checkout-result"
                    ),
                    Div(id="checkout-result", cls="mt-4"),
                    cls="bg-base-100 p-6 rounded-lg"
                ),
                
                cls="max-w-2xl mx-auto"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title="Checkout | E-Shop")
    
    @app.post("/checkout/complete")
    async def complete_checkout(request: Request):
        """Complete checkout."""
        user = await get_user(request)
        
        if not user:
            return Div(
                P("Not authenticated", cls="text-error"),
                cls="alert alert-error"
            )
        
        user_id = user.id
        
        # Clear cart
        if user_id in cart_storage:
            cart_storage[user_id] = {}
        
        return Div(
            H2(
                "✓ Order Placed Successfully!",
                cls="text-success text-2xl font-bold mb-4"
            ),
            P(
                "Thank you for your purchase! Your order has been confirmed.",
                cls="mb-4"
            ),
            A("Continue Shopping", href=f"{BASE}/", cls="btn btn-primary"),
            cls="alert alert-success"
        )
    
    # ========================================================================
    # Auth Routes
    # ========================================================================
    
    @app.get("/login")
    async def login_page(request: Request):
        """Login page."""
        return EShopLoginPage(base_path=BASE)
    
    @app.get("/register")
    async def register_page(request: Request):
        """Register page."""
        return EShopRegisterPage(base_path=BASE)
    
    @app.post("/auth/login")
    async def login(request: Request):
        """Handle login."""
        form = await request.form()
        email = form.get("email")
        password = form.get("password")
        
        result = await auth_service.login(email, password)
        
        if result:
            response = RedirectResponse(f"{BASE}/", status_code=303)
            response.set_cookie(
                "auth_token",
                result["token"],
                httponly=True,
                secure=os.getenv("ENVIRONMENT") == "production",
                samesite="lax",
                max_age=86400
            )
            return response
        
        return EShopLoginPage(base_path=BASE, error="Invalid credentials")
    
    @app.post("/auth/register")
    async def register(request: Request):
        """Handle registration."""
        form = await request.form()
        email = form.get("email")
        password = form.get("password")
        
        try:
            user_id = await user_service.register(email, password)
            
            # Log in automatically
            result = await auth_service.login(email, password)
            
            if result:
                response = RedirectResponse(f"{BASE}/", status_code=303)
                response.set_cookie(
                    "auth_token",
                    result["token"],
                    httponly=True,
                    secure=os.getenv("ENVIRONMENT") == "production",
                    samesite="lax",
                    max_age=86400
                )
                return response
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return EShopRegisterPage(base_path=BASE, error=str(e))
        
        return EShopRegisterPage(base_path=BASE, error="Registration failed")
    
    @app.post("/auth/logout")
    async def logout(request: Request):
        """Handle logout."""
        token = request.cookies.get("auth_token")
        if token:
            await auth_service.logout(token)
        
        response = RedirectResponse(f"{BASE}/", status_code=303)
        response.delete_cookie("auth_token")
        return response
    
    logger.info("✓ E-Shop example app initialized")
    return app


# ============================================================================
# Helper Components
# ============================================================================

def ProductCard(product: dict, user, base_path: str):
    """Product card component."""
    return Div(
        A(
            Div(
                Img(
                    src=product["image"],
                    alt=product["name"],
                    cls="w-full h-48 object-cover"
                ),
                Div(
                    H3(product["name"], cls="text-lg font-semibold mb-2"),
                    P(product["description"], cls="text-sm text-gray-500 mb-4"),
                    Div(
                        Span(
                            f"${product['price']}",
                            cls="text-2xl font-bold text-blue-600"
                        ),
                        Span(product["category"], cls="badge badge-outline"),
                        cls="flex justify-between items-center"
                    ),
                    cls="p-4"
                ),
                cls="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow"
            ),
            href=f"{base_path}/product/{product['id']}"
        )
    )


def CartItem(item: dict, base_path: str):
    """Cart item component."""
    return Div(
        Div(
            Img(
                src=item["image"],
                alt=item["name"],
                cls="w-24 h-24 object-cover rounded"
            ),
            Div(
                H3(item["name"], cls="font-semibold text-lg"),
                P(f"${item['price']}", cls="text-blue-600"),
                P(f"Quantity: {item['quantity']}", cls="text-sm text-gray-600"),
                cls="flex-1 ml-4"
            ),
            Div(
                P(
                    f"${item['price'] * item['quantity']:.2f}",
                    cls="font-bold text-xl"
                ),
                Button(
                    "Remove",
                    cls="btn btn-sm btn-error mt-2",
                    hx_post=f"{base_path}/cart/remove/{item['id']}",
                    hx_swap="outerHTML",
                    hx_target="closest div.card"
                ),
                cls="text-right"
            ),
            cls="flex items-center gap-4"
        ),
        cls="card bg-base-100 shadow p-4"
    )