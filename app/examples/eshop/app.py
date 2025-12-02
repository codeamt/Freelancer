"""
E-Shop Example Application

Standalone one-page shop demonstrating auth integration.
Can be mounted at any endpoint (e.g., /eshop-example).
"""
from fasthtml.common import *
from monsterui.all import *
from core.utils.logger import get_logger
from core.ui.layout import Layout
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from add_ons.auth.services import AuthService
from core.services.db import DBService

logger = get_logger(__name__)

# Sample products
PRODUCTS = [
    {
        "id": 1,
        "name": "Getting Started Guide",
        "description": "Free introductory guide to our platform - Perfect for beginners!",
        "price": 0.00,
        "image": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=1170&auto=format&fit=crop",
        "category": "Free",
        "features": ["Instant access", "Beginner friendly", "30-minute read", "Downloadable PDF"],
        "long_description": "Start your learning journey with our comprehensive getting started guide. This free resource covers everything you need to know about our platform, including how to navigate courses, track your progress, and make the most of your learning experience."
    },
    {
        "id": 2,
        "name": "Python Mastery Course",
        "description": "Complete Python programming course from beginner to advanced",
        "price": 49.99,
        "image": "https://images.unsplash.com/photo-1649180556628-9ba704115795?q=80&w=1162&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Programming",
        "features": ["42 video lessons", "Hands-on projects", "Certificate of completion", "Lifetime access"],
        "long_description": "Master Python programming from scratch with our comprehensive course. Learn variables, functions, OOP, web scraping, data analysis, and more through practical projects."
    },
    {
        "id": 3,
        "name": "Web Development Bootcamp",
        "description": "Learn HTML, CSS, JavaScript, and modern frameworks",
        "price": 79.99,
        "image": "https://images.unsplash.com/photo-1593720213428-28a5b9e94613?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Web Development",
        "features": ["68 video lessons", "10 projects", "Certificate", "Lifetime access"],
        "long_description": "Become a full-stack web developer with our comprehensive bootcamp covering HTML, CSS, JavaScript, React, Node.js, and more."
    },
    {
        "id": 4,
        "name": "Data Science Fundamentals",
        "description": "Master data analysis, visualization, and machine learning",
        "price": 99.99,
        "image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Data Science",
        "features": ["55 video lessons", "Real datasets", "Certificate", "Lifetime access"],
        "long_description": "Learn data analysis, visualization, and machine learning with Python, pandas, matplotlib, and scikit-learn."
    },
    {
        "id": 5,
        "name": "Mobile App Development",
        "description": "Build iOS and Android apps with React Native",
        "price": 89.99,
        "image": "https://images.unsplash.com/photo-1630442923896-244dd3717b35?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Mobile",
        "features": ["48 video lessons", "5 apps", "Certificate", "Lifetime access"],
        "long_description": "Build cross-platform mobile apps for iOS and Android using React Native and modern development tools."
    },
    {
        "id": 6,
        "name": "UI/UX Design Masterclass",
        "description": "Learn professional design principles and tools",
        "price": 69.99,
        "image": "https://images.unsplash.com/photo-1680016661694-1cd3faf31c3a?q=80&w=1074&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Design",
        "features": ["35 video lessons", "Design projects", "Certificate", "Lifetime access"],
        "long_description": "Master UI/UX design principles, Figma, user research, wireframing, prototyping, and design systems."
    },
    {
        "id": 7,
        "name": "DevOps Engineering",
        "description": "Master CI/CD, Docker, Kubernetes, and cloud deployment",
        "price": 109.99,
        "image": "https://plus.unsplash.com/premium_photo-1733306493254-52b143296396?q=80&w=1693&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "DevOps",
        "features": ["60 video lessons", "Cloud projects", "Certificate", "Lifetime access"],
        "long_description": "Learn DevOps practices, CI/CD pipelines, Docker, Kubernetes, AWS, and infrastructure as code."
    }
]


def create_eshop_app():
    """Create and configure the e-shop example app"""
    
    # Initialize services
    db_service = DBService()
    auth_service = AuthService(db_service)
    
    # Create FastHTML app
    app = FastHTML(hdrs=[*Theme.slate.headers()])
    
    # In-memory cart storage (in production, use database)
    cart_storage = {}
    
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
    
    @app.get("/")
    async def shop_home(request: Request):
        """Main shop page"""
        user = await get_current_user(request)
        
        # Get cart items
        cart_items = []
        cart_total = 0
        if user:
            user_cart = cart_storage.get(user.get("_id"), [])
            for product_id in user_cart:
                product = next((p for p in PRODUCTS if p["id"] == product_id), None)
                if product:
                    cart_items.append(product)
                    cart_total += product["price"]
        
        content = Div(
            # Header
            Div(
                H1("🛍️ E-Shop Example", cls="text-4xl font-bold mb-2"),
                P("Demonstrating auth-protected commerce features", cls="text-xl text-gray-500 mb-4"),
                Div(
                    Span("✓ Public browsing", cls="badge badge-success mr-2"),
                    Span("✓ Auth-protected cart", cls="badge badge-info mr-2"),
                    Span("✓ Secure checkout", cls="badge badge-primary"),
                    cls="mb-8"
                ),
                cls="text-center mb-12"
            ),
            
            # User Status
            Div(
                (Div(
                    Span(f"👤 Logged in as: {user.get('username')}", cls="font-semibold mr-4"),
                    A("Logout", href="/auth/logout", cls="link link-primary"),
                    cls="flex items-center justify-center mb-8"
                ) if user else Div(
                    Span("👋 Not logged in", cls="text-gray-500 mr-4"),
                    A("Sign In", href="/auth/login?redirect=/eshop-example", cls="btn btn-sm btn-primary mr-2"),
                    A("Register", href="/auth/register?redirect=/eshop-example", cls="btn btn-sm btn-outline"),
                    cls="flex items-center justify-center mb-8"
                ))
            ),
            
            # Products Grid
            Div(
                H2("Featured Products", cls="text-2xl font-bold mb-6"),
                Div(
                    *[ProductCard(product, user) for product in PRODUCTS],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
                ),
            ),
            
            # Cart Section
            Div(
                H2("Shopping Cart", cls="text-2xl font-bold mb-6"),
                (Div(
                    Div(
                        *[CartItem(item) for item in cart_items] if cart_items else [
                            P("Your cart is empty", cls="text-gray-500 text-center py-8")
                        ],
                        id="cart-items",
                        cls="space-y-4 mb-6"
                    ),
                    Div(
                        Div(
                            Span("Total:", cls="text-xl font-bold"),
                            Span(f"${cart_total:.2f}", cls="text-2xl font-bold text-blue-600"),
                            cls="flex justify-between items-center mb-4"
                        ),
                        Button(
                            "Proceed to Checkout",
                            cls="btn btn-primary w-full",
                            disabled=len(cart_items) == 0,
                            onclick="alert('Checkout functionality would go here!')"
                        ),
                        cls="border-t pt-4"
                    ),
                    cls="bg-base-200 p-6 rounded-lg"
                ) if user else Div(
                    Div(
                        UkIcon("lock", width="48", height="48", cls="text-gray-400 mb-4"),
                        H3("Sign in to use cart", cls="text-xl font-semibold mb-2"),
                        P("Create an account or sign in to add items to your cart", cls="text-gray-500 mb-4"),
                        Div(
                            A("Sign In", href="/auth/login?redirect=/eshop-example", cls="btn btn-primary mr-2"),
                            A("Register", href="/auth/register", cls="btn btn-outline"),
                            cls="flex justify-center"
                        ),
                        cls="text-center"
                    ),
                    cls="bg-base-200 p-8 rounded-lg"
                )),
            ),
            
            # Features Section
            Div(
                H2("Example Features", cls="text-2xl font-bold mb-6 text-center"),
                Div(
                    FeatureCard("🌐", "Public Browsing", "Anyone can view products without authentication"),
                    FeatureCard("🔒", "Auth-Protected Cart", "Must be logged in to add items to cart"),
                    FeatureCard("💳", "Secure Checkout", "Authentication required for payment processing"),
                    FeatureCard("🎨", "Modern UI", "Built with MonsterUI and Tailwind CSS"),
                    FeatureCard("⚡", "HTMX Integration", "Dynamic updates without page reload"),
                    FeatureCard("🔧", "Easy Customization", "Template ready for client projects"),
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8"
                ),
                cls="mt-16 mb-8"
            )
        )
        
        return Layout(content, title="E-Shop Example | FastApp")
    
    @app.get("/product/{product_id}")
    async def product_detail(request: Request, product_id: int):
        """Product detail page"""
        user = await get_current_user(request)
        
        # Find product
        product = next((p for p in PRODUCTS if p["id"] == product_id), None)
        if not product:
            return Layout(
                Div(
                    H1("Product Not Found", cls="text-3xl font-bold mb-4"),
                    A("← Back to Shop", href="/eshop-example", cls="btn btn-primary"),
                    cls="text-center py-16"
                ),
                title="Product Not Found"
            )
        
        # Check if in cart
        in_cart = False
        if user:
            user_cart = cart_storage.get(user.get("_id"), [])
            in_cart = product_id in user_cart
        
        content = Div(
            # Back button
            A(
                UkIcon("arrow-left", width="20", height="20", cls="mr-2"),
                "Back to Shop",
                href="/eshop-example",
                cls="btn btn-ghost mb-6"
            ),
            
            # Product detail
            Div(
                # Product image
                Div(
                    Img(
                        src=product["image"],
                        alt=product["name"],
                        cls="w-full h-96 object-cover rounded-lg shadow-lg"
                    ),
                    cls="lg:col-span-1"
                ),
                
                # Product info
                Div(
                    # Category badge
                    Span(product["category"], cls="badge badge-primary mb-4"),
                    
                    # Title
                    H1(product["name"], cls="text-4xl font-bold mb-4"),
                    
                    # Price
                    Div(
                        (Span("FREE", cls="text-4xl font-bold text-green-600") if product["price"] == 0 
                         else Span(f"${product['price']}", cls="text-4xl font-bold text-blue-600")),
                        cls="mb-6"
                    ),
                    
                    # Description
                    P(product.get("long_description", product["description"]), cls="text-lg text-gray-600 mb-6"),
                    
                    # Features
                    (Div(
                        H3("What's Included:", cls="text-xl font-semibold mb-3"),
                        Ul(
                            *[Li(
                                UkIcon("check", width="20", height="20", cls="inline mr-2 text-green-500"),
                                feature,
                                cls="mb-2"
                            ) for feature in product.get("features", [])],
                            cls="space-y-2 mb-6"
                        )
                    ) if product.get("features") else None),
                    
                    # Add to cart button
                    Div(id="cart-action", cls="mb-4"),
                    (Div(
                        Span("✓ In Cart", cls="badge badge-success badge-lg py-4 px-6"),
                        A("View Cart", href="/eshop-example#cart", cls="btn btn-primary btn-lg ml-4"),
                        cls="flex items-center"
                    ) if in_cart else (
                        Button(
                            UkIcon("shopping-cart", width="20", height="20", cls="mr-2"),
                            "Add to Cart" if product["price"] > 0 else "Get Free Access",
                            cls="btn btn-primary btn-lg",
                            hx_post=f"/eshop-example/cart/add/{product_id}",
                            hx_target="#cart-action",
                            hx_swap="innerHTML"
                        ) if user else A(
                            UkIcon("lock", width="20", height="20", cls="mr-2"),
                            "Sign in to get this product",
                            href=f"/auth/login?redirect=/eshop-example/product/{product_id}",
                            cls="btn btn-primary btn-lg"
                        )
                    )),
                    
                    cls="lg:col-span-1"
                ),
                
                cls="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12"
            )
        )
        
        return Layout(content, title=f"{product['name']} | E-Shop")
    
    @app.post("/cart/add/{product_id}")
    async def add_to_cart(request: Request, product_id: int):
        """Add product to cart (requires auth)"""
        user = await get_current_user(request)
        
        if not user:
            return Div(
                P("⚠️ Please sign in to add items to cart", cls="text-warning"),
                A("Sign In", href="/auth/login?redirect=/eshop-example", cls="btn btn-sm btn-primary mt-2"),
                cls="alert alert-warning"
            )
        
        # Find product
        product = next((p for p in PRODUCTS if p["id"] == product_id), None)
        if not product:
            return Div(
                P("❌ Product not found", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Add to cart
        user_id = user.get("_id")
        if user_id not in cart_storage:
            cart_storage[user_id] = []
        
        if product_id not in cart_storage[user_id]:
            cart_storage[user_id].append(product_id)
            logger.info(f"User {user_id} added product {product_id} to cart")
        
        # Return updated cart
        cart_items = []
        cart_total = 0
        for pid in cart_storage[user_id]:
            p = next((pr for pr in PRODUCTS if pr["id"] == pid), None)
            if p:
                cart_items.append(p)
                cart_total += p["price"]
        
        return Div(
            *[CartItem(item) for item in cart_items],
            Script(f"""
                document.getElementById('cart-total').textContent = '${cart_total:.2f}';
            """)
        )
    
    def ProductCard(product: dict, user: dict = None):
        """Product card component"""
        is_free = product["price"] == 0
        
        return Card(
            Div(
                # Product image - clickable
                A(
                    Img(
                        src=product["image"],
                        alt=product["name"],
                        cls="w-full h-48 object-cover rounded-t-lg hover:opacity-90 transition-opacity"
                    ),
                    href=f"/eshop-example/product/{product['id']}"
                ),
                # Product info
                Div(
                    Span(product["category"], cls=f"badge badge-sm {'badge-success' if is_free else 'badge-outline'} mb-2"),
                    A(
                        H3(product["name"], cls="text-lg font-semibold mb-2 hover:text-blue-600 transition-colors"),
                        href=f"/eshop-example/product/{product['id']}"
                    ),
                    P(product["description"], cls="text-sm text-gray-500 mb-4 line-clamp-2"),
                    Div(
                        (Span("FREE", cls="text-2xl font-bold text-green-600") if is_free 
                         else Span(f"${product['price']}", cls="text-2xl font-bold text-blue-600")),
                        cls="mb-4"
                    ),
                    # View details button
                    A(
                        UkIcon("eye", width="16", height="16", cls="mr-2"),
                        "View Details",
                        href=f"/eshop-example/product/{product['id']}",
                        cls="btn btn-primary btn-sm w-full"
                    ),
                    cls="p-4"
                ),
                cls="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow"
            )
        )
    
    def CartItem(product: dict):
        """Cart item component"""
        return Div(
            Div(
                Img(src=product["image"], alt=product["name"], cls="w-16 h-16 object-cover rounded"),
                Div(
                    H4(product["name"], cls="font-semibold"),
                    P(product["category"], cls="text-sm text-gray-500"),
                    cls="flex-1 ml-4"
                ),
                Span(f"${product['price']}", cls="text-lg font-bold text-blue-600"),
                cls="flex items-center"
            ),
            cls="border-b pb-4"
        )
    
    def FeatureCard(icon: str, title: str, description: str):
        """Feature card component"""
        return Card(
            Div(
                Div(icon, cls="text-4xl mb-3 text-center"),
                H3(title, cls="text-lg font-semibold mb-2 text-center"),
                P(description, cls="text-sm text-gray-500 text-center"),
                cls="p-6 text-center"
            ),
            cls="hover:shadow-lg transition-shadow"
        )
    
    return app

#serve(port = 8000)