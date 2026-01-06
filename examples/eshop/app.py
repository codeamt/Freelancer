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
import os

from core.utils.logger import get_logger
from core.ui.layout import Layout
from core.services.auth import AuthService, UserService
from core.services.auth.helpers import get_current_user
from core.services.auth.context import set_user_context, UserContext
from core.db.adapters import PostgresAdapter, MongoDBAdapter, RedisAdapter

# Commerce domain imports
from add_ons.domains.commerce.repositories import ProductRepository
from add_ons.domains.commerce.data import SAMPLE_PRODUCTS, get_product_by_id, get_products_by_category, get_all_categories

# Cart service from core infrastructure
from core.services.cart import CartService

# E-Shop UI
from .ui import EShopLoginPage, EShopRegisterPage, CartItem, ProductCard, CartSummary, SocialLinks, NewsletterModal, EShopSubNav

# Core marketing components
from core.ui.components.marketing import NewsletterSignup

logger = get_logger(__name__)


def create_eshop_app(
    auth_service: AuthService,
    user_service: UserService,
    postgres: PostgresAdapter,
    mongodb: Optional[MongoDBAdapter] = None,
    redis: Optional[RedisAdapter] = None,
    demo: bool = False
) -> FastHTML:
    """
    Create E-Shop example application.
    
    Args:
        auth_service: Injected authentication service
        user_service: Injected user management service
        postgres: PostgreSQL adapter
        mongodb: MongoDB adapter (optional)
        redis: Redis adapter (optional)
        demo: Whether to run in demo mode (uses mock data, limited features)
        
    Returns:
        FastHTML app instance
    """
    logger.info(f"Initializing E-Shop example app (demo={demo})...")
    
    # Initialize services using passed adapters
    product_repo = ProductRepository(
        postgres=postgres,
        mongodb=mongodb,
        redis=redis
    )
    cart_service = CartService()
    
    # Create app with theme
    app = FastHTML(hdrs=[*Theme.stone.headers(mode="dark")])
    
    # Store demo flag in app state
    app.state.demo = demo
    
    # Base path
    BASE = "/eshop-example"
    
    # ========================================================================
    # Helper Functions
    # ========================================================================
    
    async def get_user_with_context(request: Request):
        """Get current user from request and set context."""
        user = await get_current_user(request, auth_service)
        if user:
            # Set user context for state system using factory
            from core.services.auth.context import create_user_context
            from core.services.auth.permissions import permission_registry
            
            # Create a simple user object for the factory
            class SimpleUser:
                def __init__(self, user_dict):
                    self.id = user_dict.get("id") or int(user_dict.get("_id", 0))
                    self.role = user_dict.get("role", "user")
                    self.email = user_dict.get("email", "")
            
            user_obj = SimpleUser(user)
            user_context = create_user_context(user_obj, request)
            set_user_context(user_context)
        return user
    
    # ========================================================================
    # Routes
    # ========================================================================
    
    @app.get("/")
    async def home(request: Request, search: str = "", category: str = "all"):
        """Shop homepage with dark theme, hero banner, and filtering."""
        user = await get_user_with_context(request)
        
        # Get cart count (simplified for demo)
        cart_count = 0  # In real app, this would come from cart service
        
        # Filter products based on search and category
        filtered_products = SAMPLE_PRODUCTS
        
        if category != "all":
            filtered_products = [p for p in filtered_products if p["category"] == category]
        
        if search:
            search_lower = search.lower()
            filtered_products = [p for p in filtered_products 
                              if search_lower in p["name"].lower() 
                              or search_lower in p["description"].lower()
                              or search_lower in p["category"].lower()]
        
        categories = get_all_categories()
        
        content = Div(
            # E-Shop Sub Navigation
            EShopSubNav(user, BASE, cart_count),
            
            # Newsletter Modal (shows on page load)
            NewsletterModal(BASE),
            
            # Hero Section with Dark Theme
            Section(
                Div(
                    Div(
                        H1("Premium E-Shop", cls="text-5xl md:text-6xl font-bold text-white mb-4"),
                        P(
                            "Discover our curated selection of high-quality products",
                            cls="text-xl md:text-2xl text-gray-200 mb-8 max-w-2xl"
                        ),
                        Div(
                            A(
                                "Shop Now",
                                href=f"{BASE}/#products",
                                cls="btn btn-primary btn-lg text-lg px-8 py-4 bg-blue-600 hover:bg-blue-700 border-none"
                            ),
                            A(
                                "Learn More",
                                href=f"{BASE}/about",
                                cls="btn btn-outline btn-lg text-lg px-8 py-4 ml-4 text-white border-white hover:bg-white hover:text-gray-900"
                            ),
                            cls="flex flex-col sm:flex-row gap-4"
                        ),
                        cls="z-10 text-center"
                    ),
                    cls="relative z-10 flex flex-col justify-center items-center h-full min-h-[600px]"
                ),
                # Hero background with overlay
                Div(
                    style=f"""
                    background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), 
                                    url('https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=1920&h=1080&fit=crop');
                    background-size: cover;
                    background-position: center;
                    background-attachment: fixed;
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    z-index: 0;
                    """
                ),
                cls="relative bg-black"
            ),
            
            # Features Section (Dark Theme)
            Section(
                Div(
                    Div(
                        H2("Why Choose Our Products?", cls="text-4xl font-bold text-white mb-12 text-center"),
                        Div(
                            Div(
                                Div(
                                    Div(
                                        UkIcon("shield", width="48", height="48", cls="text-blue-400 mb-4 block"),
                                        cls="flex justify-center"
                                    ),
                                    H3("Professional Grade", cls="text-xl font-semibold text-white mb-2 text-center"),
                                    P("Commercial-quality leather care trusted by professionals", cls="text-gray-300 text-center"),
                                    cls="text-center"
                                ),
                                cls="col-span-1"
                            ),
                            Div(
                                Div(
                                    Div(
                                        UkIcon("droplet", width="48", height="48", cls="text-blue-400 mb-4 block"),
                                        cls="flex justify-center"
                                    ),
                                    H3("Deep Conditioning", cls="text-xl font-semibold text-white mb-2 text-center"),
                                    P("Restores and protects all types of leather goods", cls="text-gray-300 text-center"),
                                    cls="text-center"
                                ),
                                cls="col-span-1"
                            ),
                            Div(
                                Div(
                                    Div(
                                        UkIcon("award", width="48", height="48", cls="text-blue-400 mb-4 block"),
                                        cls="flex justify-center"
                                    ),
                                    H3("Made in USA", cls="text-xl font-semibold text-white mb-2 text-center"),
                                    P("Proudly crafted with premium ingredients", cls="text-gray-300 text-center"),
                                    cls="text-center"
                                ),
                                cls="col-span-1"
                            ),
                            cls="grid grid-cols-1 md:grid-cols-3 gap-8"
                        ),
                        cls="container mx-auto px-4 py-16"
                    ),
                    cls="bg-black"
                ),
                id="features"
            ),
            
            # Products Section with Search and Filtering (Dark Theme)
            Section(
                Div(
                    H2("Our Products", cls="text-4xl font-bold text-white mb-12 text-center"),
                    
                    # Search and Filter Controls
                    Div(
                        Form(
                            Div(
                                Div(
                                    Input(
                                        type="text",
                                        name="search",
                                        placeholder="Search products...",
                                        value=search,
                                        cls="input input-bordered bg-gray-800 text-white border-gray-600 placeholder-gray-400 w-full",
                                        hx_get=f"{BASE}/",
                                        hx_target="section",
                                        hx_include="[name='category']",
                                        hx_trigger="input changed delay:300ms"
                                    ),
                                    cls="w-full md:w-1/2"
                                ),
                                Div(
                                    Select(
                                        Option("All Categories", value="all", selected=(category == "all")),
                                        *[Option(cat.capitalize(), value=cat, selected=(category == cat)) for cat in sorted(categories)],
                                        name="category",
                                        cls="select select-bordered bg-gray-800 text-white border-gray-600 w-full",
                                        hx_get=f"{BASE}/",
                                        hx_target="section",
                                        hx_include="[name='search']",
                                        hx_trigger="change"
                                    ),
                                    cls="w-full md:w-1/4 md:ml-2"
                                ),
                                Div(
                                    P(f"Showing {len(filtered_products)} products", cls="text-gray-300 self-center"),
                                    cls="w-full md:w-1/4 md:ml-2 text-center"
                                ),
                                cls="flex flex-col md:flex-row gap-4 items-center mb-8"
                            ),
                            cls="w-full"
                        ),
                        
                        # Active filters display
                        (Div(
                            Span("Active filters:", cls="text-gray-400 mr-2"),
                            (Span(search, cls="badge badge-primary mr-2") if search else None),
                            (Span(category.capitalize(), cls="badge badge-secondary") if category != "all" else None),
                            A("Clear all", href=f"{BASE}/", cls="link link-primary ml-4 text-sm"),
                            cls="flex items-center justify-center mb-6"
                        ) if search or category != "all" else None),
                        
                        cls="container mx-auto px-4"
                    ),
                    
                    # Products Grid
                    Div(
                        *[ProductCard(product, user, BASE) for product in filtered_products],
                        cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                    ) if filtered_products else Div(
                        H3("No products found", cls="text-2xl font-semibold text-white mb-4"),
                        P("Try adjusting your search or filters", cls="text-gray-300 mb-6"),
                        A("Clear filters", href=f"{BASE}/", cls="btn btn-primary"),
                        cls="text-center py-12"
                    ),
                    
                    cls="container mx-auto px-4 py-16"
                ),
                id="products",
                cls="bg-black"
            ),
            
            # Newsletter Section
            Section(
                NewsletterSignup(
                    title="Stay in the Loop",
                    subtitle="Get exclusive offers and be the first to know about new products",
                    placeholder="Enter your email address",
                    button_text="Subscribe",
                    action_url=f"{BASE}/newsletter/subscribe",
                    description="Join our community of savvy shoppers and never miss a deal!",
                    theme="dark"
                ),
                cls="bg-gray-900 border-t border-gray-800"
            ),
            
            # Social Links Section
            Section(
                Div(
                    SocialLinks(),
                    cls="container mx-auto px-4 py-8"
                ),
                cls="bg-black border-t border-gray-800"
            ),
            
            cls="w-full"
        )
        
        return Layout(content, title="Premium E-Shop | Demo", current_path=f"{BASE}/", user=user, show_auth=True, demo=demo)
    
    @app.get("/product/{product_id}")
    async def product_detail(request: Request, product_id: int):
        """Product detail page."""
        user = await get_user_with_context(request)
        
        # Get product (could use repo here for real DB)
        product = get_product_by_id(product_id)
        
        if not product:
            return Layout(
                Div(
                    H1("Product Not Found", cls="text-3xl font-bold mb-4"),
                    A("← Back to Shop", href=f"{BASE}/", cls="btn btn-primary"),
                    cls="text-center py-20"
                ),
                title="Not Found",
                user=user,
                show_auth=True,
                demo=demo
            )
        
        content = Div(
            # Back button
            A("← Back to Shop", href=f"{BASE}/", cls="btn btn-ghost mb-6"),
            
            # Stripe notification
            Div(
                Div(
                    UkIcon("info", width="20", height="20", cls="mr-2"),
                    Span("This shop is pre-configured for Stripe payments. In production, this would process real payments.", cls="text-sm"),
                    cls="flex items-center"
                ),
                cls="alert alert-info mb-6"
            ),
            
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
                    
                    # Stripe secure note
                    Div(
                        UkIcon("credit-card", width="16", height="16", cls="mr-2"),
                        Span("Pre-configured for Stripe payments", cls="text-xs text-gray-500"),
                        cls="flex items-center justify-center mt-4"
                    ),
                    
                    cls="lg:w-1/2"
                ),
                
                cls="flex flex-col lg:flex-row gap-8"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title=f"{product['name']} | E-Shop", user=user, show_auth=True, demo=demo)
    
    @app.post("/cart/add/{product_id}")
    async def add_to_cart(request: Request, product_id: int):
        """Add product to cart."""
        user = await get_user_with_context(request)
        
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
        
        # Add to cart using CartService
        user_id = str(user.get("id") or user.get("_id"))
        cart_service.add_to_cart(
            cart_id=user_id,
            product_id=str(product_id),
            name=product["name"],
            price=product["price"],
            quantity=1,
            user_id=user_id
        )
        
        logger.info(f"User {user_id} added product {product_id} to cart")
        
        return Div(
            P(f"✓ {product['name']} added to cart!", cls="text-success"),
            A("View Cart", href=f"{BASE}/cart", cls="btn btn-sm btn-outline mt-2"),
            cls="alert alert-success"
        )
    
    @app.get("/cart")
    async def view_cart(request: Request):
        """View shopping cart."""
        user = await get_user_with_context(request)
        
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/cart")
        
        user_id = str(user.get("id") or user.get("_id"))
        cart = cart_service.get_cart(user_id)
        cart_items = []
        if cart:
            cart_items = [{"product_id": int(pid), "quantity": item.quantity, "price": float(item.price)} for pid, item in cart.items.items()]
        
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
            return Layout(content, title="Cart | E-Shop", user=user, show_auth=True, demo=demo)
        
        # Calculate totals from cart
        cart_products = []
        subtotal = 0
        for item in cart_items:
            product = get_product_by_id(item["product_id"])
            if product:
                cart_products.append({**product, "quantity": item["quantity"]})
                subtotal += item["price"] * item["quantity"]
        
        tax = subtotal * 0.1
        total = subtotal + tax
        
        content = Div(
            H1("Your Cart", cls="text-4xl font-bold mb-8"),
            
            # Stripe notification
            Div(
                Div(
                    UkIcon("info", width="20", height="20", cls="mr-2"),
                    Span("This shop is pre-configured for Stripe payments. In production, this would process real payments.", cls="text-sm"),
                    cls="flex items-center"
                ),
                cls="alert alert-info mb-6"
            ),
            
            # Cart content (HTMX target)
            Div(
                # Cart items
                Div(
                    *[CartItem(item, BASE) for item in cart_products],
                    cls="space-y-4 mb-8 lg:w-2/3"
                ),
                # Summary
                Div(
                    CartSummary(subtotal, tax, total, BASE),
                    cls="lg:w-1/3"
                ),
                cls="flex flex-col lg:flex-row gap-8",
                id="cart-content"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title="Cart | E-Shop", user=user, show_auth=True, demo=demo)
    
    @app.post("/cart/remove/{product_id}")
    async def remove_from_cart(request: Request, product_id: int):
        """Remove product from cart."""
        user = await get_user_with_context(request)
        
        if not user:
            return Div(P("Not authenticated", cls="text-error"), cls="alert alert-error")
        
        user_id = str(user.get("id") or user.get("_id"))
        cart_service.remove_from_cart(user_id, str(product_id))
        
        # Return updated cart content for HTMX
        return get_cart_content_sync(user_id)
    
    @app.post("/cart/update/{product_id}")
    async def update_cart_quantity(request: Request, product_id: int, action: str = "increase"):
        """Update product quantity in cart."""
        user = await get_user_with_context(request)
        
        if not user:
            return Div(P("Not authenticated", cls="text-error"), cls="alert alert-error")
        
        user_id = str(user.get("id") or user.get("_id"))
        
        if action == "increase":
            product = get_product_by_id(product_id)
            if product:
                cart_service.add_to_cart(
                    cart_id=user_id,
                    product_id=str(product_id),
                    name=product["name"],
                    price=product["price"],
                    quantity=1,
                    user_id=user_id
                )
        elif action == "decrease":
            cart = cart_service.get_cart(user_id)
            if cart and str(product_id) in cart.items:
                item = cart.items[str(product_id)]
                if item.quantity > 1:
                    cart_service.update_quantity(user_id, str(product_id), item.quantity - 1)
                else:
                    cart_service.remove_from_cart(user_id, str(product_id))
        
        # Return updated cart content for HTMX
        return get_cart_content_sync(user_id)
    
    def get_cart_content_sync(user_id):
        """Helper to get cart content HTML (synchronous)."""
        cart = cart_service.get_cart(user_id)
        cart_items = []
        if cart:
            cart_items = [{"product_id": int(pid), "quantity": item.quantity, "price": float(item.price)} for pid, item in cart.items.items()]
        
        if not cart_items:
            return Div(
                H2("Your cart is empty", cls="text-2xl mb-4"),
                P("Add some products to get started!", cls="text-gray-600 mb-6"),
                A("Browse Products", href=f"{BASE}/", cls="btn btn-primary"),
                cls="text-center py-12"
            )
        
        # Build cart products list
        cart_products = []
        subtotal = 0
        for item in cart_items:
            product = get_product_by_id(item["product_id"])
            if product:
                cart_products.append({**product, "quantity": item["quantity"]})
                subtotal += item["price"] * item["quantity"]
        
        tax = subtotal * 0.1
        total = subtotal + tax
        
        return Div(
            # Cart items
            Div(
                *[CartItem(item, BASE) for item in cart_products],
                cls="space-y-4 mb-8 lg:w-2/3"
            ),
            # Summary
            Div(
                CartSummary(subtotal, tax, total, BASE),
                cls="lg:w-1/3"
            ),
            cls="flex flex-col lg:flex-row gap-8"
        )
    
    @app.get("/checkout")
    async def checkout_page(request: Request):
        """Checkout page."""
        user = await get_user_with_context(request)
        
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/checkout")
        
        user_id = str(user.get("id") or user.get("_id"))
        cart = cart_service.get_cart(user_id)
        cart_items = []
        if cart:
            cart_items = [{"product_id": int(pid), "quantity": item.quantity, "price": float(item.price)} for pid, item in cart.items.items()]
        
        if not cart_items:
            return RedirectResponse(f"{BASE}/cart")
        
        # Calculate totals from cart
        cart_products = []
        subtotal = 0
        for item in cart_items:
            product = get_product_by_id(item["product_id"])
            if product:
                cart_products.append({**product, "quantity": item["quantity"]})
                subtotal += item["price"] * item["quantity"]
        
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
        
        return Layout(content, title="Checkout | E-Shop", user=user, show_auth=True, demo=demo)
    
    @app.post("/checkout/complete")
    async def complete_checkout(request: Request):
        """Complete checkout."""
        user = await get_user_with_context(request)
        
        if not user:
            return Div(
                P("Not authenticated", cls="text-error"),
                cls="alert alert-error"
            )
        
        user_id = str(user.get("id") or user.get("_id"))
        
        # Store order in database (using mongodb adapter)
        order_data = {
            "user_id": user_id,
            "status": "completed",
            "total": 0  # Calculate from cart
        }
        if mongodb:
            await mongodb.insert_one("orders", order_data)
        
        # Clear cart using CartService
        cart_service.clear_cart(user_id)
        
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
        # Try sanitized form first (from security middleware), fallback to raw form
        form = getattr(request.state, 'sanitized_form', None) or await request.form()
        email = form.get("email")
        password = form.get("password")
        
        if not email or not password:
            return EShopLoginPage(base_path=BASE, error="Email and password are required")
        
        from core.services.auth.models import LoginRequest
        result = await auth_service.login(LoginRequest(username=email, password=password))
        
        if result:
            response = RedirectResponse(f"{BASE}/", status_code=303)
            response.set_cookie(
                "auth_token",
                result.access_token,
                httponly=True,
                secure=os.getenv("ENVIRONMENT") == "production",
                samesite="lax",
                max_age=result.expires_in
            )
            return response
        
        return EShopLoginPage(base_path=BASE, error="Invalid credentials")
    
    @app.post("/auth/register")
    async def register(request: Request):
        """Handle registration."""
        # Try sanitized form first (from security middleware), fallback to raw form
        form = getattr(request.state, 'sanitized_form', None) or await request.form()
        email = form.get("email")
        password = form.get("password")
        
        if not email or not password:
            return EShopRegisterPage(base_path=BASE, error="Email and password are required")
        
        try:
            user_id = await user_service.register(email, password)
            
            # Log in automatically
            from core.services.auth.models import LoginRequest
            result = await auth_service.login(LoginRequest(username=email, password=password))
            
            if result:
                response = RedirectResponse(f"{BASE}/", status_code=303)
                response.set_cookie(
                    "auth_token",
                    result.access_token,
                    httponly=True,
                    secure=os.getenv("ENVIRONMENT") == "production",
                    samesite="lax",
                    max_age=result.expires_in
                )
                return response
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return EShopRegisterPage(base_path=BASE, error=str(e))
        
        return EShopRegisterPage(base_path=BASE, error="Registration failed")
    
    @app.post("/newsletter/subscribe")
    async def newsletter_subscribe(request: Request):
        """Handle newsletter subscription."""
        form = await request.form()
        email = form.get("email")
        
        if not email:
            return Div(
                P("Please enter a valid email address", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Here you would typically save to database or send to email service
        logger.info(f"Newsletter subscription: {email}")
        
        return Div(
            H4("🎉 Welcome to the club!", cls="text-success text-lg font-semibold mb-2"),
            P(f"Check {email} for your 15% discount code!", cls="text-gray-300 mb-4"),
            P("Thank you for joining our newsletter.", cls="text-gray-400 text-sm"),
            Button(
                "Start Shopping",
                onclick="this.closest('dialog').close()",
                cls="btn btn-primary btn-sm mt-4"
            ),
            cls="text-center"
        )
    
    @app.post("/auth/logout")
    async def logout(request: Request):
        """Handle logout."""
        token = request.cookies.get("auth_token")
        if token:
            await auth_service.logout(token)
        
        response = RedirectResponse(f"{BASE}/", status_code=303)
        response.delete_cookie("auth_token")
        return response
    
    # =========================================================================
    # Admin Routes
    # =========================================================================
    
    @app.get("/admin")
    async def admin_dashboard(request: Request):
        """E-Shop Admin Dashboard."""
        from .admin import EShopAdminDashboard
        
        user = await get_user_with_context(request)
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/admin")
        
        # Check if user has admin role
        user_role = user.get("role", "user")
        if user_role not in ["admin", "super_admin", "shop_owner"]:
            return Layout(
                Div(
                    H1("Access Denied", cls="text-3xl font-bold text-error mb-4"),
                    P("You don't have permission to access the admin dashboard.", cls="text-gray-600 mb-4"),
                    A("Back to Shop", href=f"{BASE}/", cls="btn btn-primary"),
                    cls="text-center py-20"
                ),
                title="Access Denied | E-Shop",
                user=user,
                show_auth=True,
                demo=demo
            )
        
        return EShopAdminDashboard(user, demo=demo)
    
    @app.get("/admin/inventory")
    async def admin_inventory(request: Request):
        """Inventory management page."""
        from .admin import InventoryManagementPage
        
        user = await get_user_with_context(request)
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/admin/inventory")
        
        return InventoryManagementPage(user, SAMPLE_PRODUCTS, demo=demo)
    
    @app.get("/admin/shipping")
    async def admin_shipping(request: Request):
        """Shipping providers page."""
        from .admin import ShippingProvidersPage
        
        user = await get_user_with_context(request)
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/admin/shipping")
        
        return ShippingProvidersPage(user, demo=demo)
    
    logger.info("✓ E-Shop example app initialized")
    return app
