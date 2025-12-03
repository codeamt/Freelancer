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

from core.services import AuthService, DBService, get_current_user
from .auth_ui import EShopLoginPage, EShopRegisterPage

logger = get_logger(__name__)

# Sample products
PRODUCTS = [
    {
        "id": 1,
        "name": "Low Tops",
        "description": "Example shoes curated for affiliate marketing",
        "price": 89.99,
        "image": "https://images.unsplash.com/photo-1679284392816-191b1c849f76?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Merchandise",
        "features": ["48 video lessons", "5 apps", "Certificate", "Lifetime access"],
        "long_description": "Build cross-platform mobile apps for iOS and Android using React Native and modern development tools."
    },
    {
        "id": 2,
        "name": "Namebrand Camera",
        "description": "Example DSLR camera for photography enthusiasts",
        "price": 150.00,
        "image": "https://images.unsplash.com/photo-1507804935366-720e78633272?q=80&w=1169&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Electronics",
        "features": ["35 video lessons", "Design projects", "Certificate", "Lifetime access"],
        "long_description": "Master UI/UX design principles, Figma, user research, wireframing, prototyping, and design systems."
    },
    {
        "id": 3,
        "name": "Writing Set",
        "description": "A personal moleskine journal and included pen for note-taking",
        "price": 19.99,
        "image": "https://images.unsplash.com/photo-1611571741792-edb58d0ceb67?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Personal",
        "features": ["60 video lessons", "Cloud projects", "Certificate", "Lifetime access"],
        "long_description": "Learn DevOps practices, CI/CD pipelines, Docker, Kubernetes, AWS, and infrastructure as code."
    },
    {
        "id": 4,
        "name": "Plain T-Shirt",
        "description": "High-quality branded t-shirt, ready for our logo",
        "price": 29.99,
        "image": "https://images.unsplash.com/photo-1581655353564-df123a1eb820?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Merchandise",
        "features": ["100% cotton", "Multiple sizes available", "Premium quality print", "Comfortable fit"],
        "long_description": "Show your support with our premium branded t-shirt. Made from 100% soft cotton with a high-quality screen print that won't fade. Available in sizes S-XXL."
    },
    {
        "id": 5,
        "name": "Designer Tote Bag",
        "description": "Eco-friendly canvas tote bag perfect for everyday use",
        "price": 19.99,
        "image": "https://images.unsplash.com/photo-1574365569389-a10d488ca3fb?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "category": "Merchandise",
        "features": ["Eco-friendly canvas", "Spacious design", "Reinforced handles", "Reusable & durable"],
        "long_description": "Carry your essentials in style with our eco-friendly canvas tote bag. Features reinforced handles, spacious interior, and a minimalist design with our logo."
    },
    {
        "id": 6,
        "name": "Unlock Album",
        "description": "Download our free sample music album - 10 tracks included!",
        "price": 0.00,
        "image": "https://images.unsplash.com/photo-1619983081563-430f63602796?q=80&w=1074&auto=format&fit=crop",
        "category": "Media",
        "features": ["10 original tracks", "High-quality MP3", "Instant download", "No DRM"],
        "long_description": "Enjoy our free sample album featuring 10 original tracks. Perfect for discovering new music and experiencing our platform. Download instantly and listen anywhere!"
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
    # Format: {user_id: {product_id: quantity}}
    cart_storage = {}
    
    async def get_user(request: Request):
        """Get current user from request"""
        return await get_current_user(request, auth_service)
    
    # ============================================================================
    # E-Shop Auth Routes
    # ============================================================================
    
    @app.get("/login")
    def eshop_login_page(request: Request):
        """E-Shop login page"""
        redirect_url = request.query_params.get("redirect", "/eshop-example")
        error = request.query_params.get("error")
        return Layout(EShopLoginPage(redirect_url, error), title="Sign In | E-Shop", show_auth=False)
    
    @app.get("/register")
    def eshop_register_page(request: Request):
        """E-Shop registration page"""
        redirect_url = request.query_params.get("redirect", "/eshop-example")
        error = request.query_params.get("error")
        return Layout(EShopRegisterPage(redirect_url, error), title="Create Account | E-Shop", show_auth=False)
    
    @app.post("/auth/login")
    async def eshop_login(request: Request):
        """Handle E-Shop login"""
        form_data = await request.form()
        email = form_data.get("email")
        password = form_data.get("password")
        
        # Get redirect URL
        redirect_url = request.query_params.get("redirect", "/eshop-example")
        
        # Validation
        if not all([email, password]):
            logger.warning("Login failed: Missing credentials")
            return RedirectResponse(f"/eshop-example/login?redirect={redirect_url}&error=missing_fields", status_code=303)
        
        try:
            # Authenticate user
            user = await auth_service.authenticate_user(email, password)
            
            if not user:
                logger.warning(f"Login failed: Invalid credentials for {email}")
                return RedirectResponse(f"/eshop-example/login?redirect={redirect_url}&error=invalid_credentials", status_code=303)
            
            # Create token
            token_data = {
                "sub": str(user.get("_id")),
                "email": email,
                "username": user.get("username"),
                "roles": user.get("roles", ["user"])
            }
            token = auth_service.create_token(token_data)
            
            logger.info(f"E-Shop user {email} logged in, redirecting to {redirect_url}")
            
            # Create response with redirect and set cookie
            response = RedirectResponse(url=redirect_url, status_code=303)
            response.set_cookie(
                key="auth_token",
                value=token,
                max_age=86400,  # 24 hours
                httponly=False,  # Allow JavaScript access
                samesite="lax"
            )
            return response
            
        except Exception as e:
            logger.error(f"E-Shop login error: {e}")
            return RedirectResponse(f"/eshop-example/login?redirect={redirect_url}&error=server_error", status_code=303)
    
    @app.post("/auth/register")
    async def eshop_register(request: Request):
        """Handle E-Shop registration"""
        form_data = await request.form()
        email = form_data.get("email")
        password = form_data.get("password")
        confirm_password = form_data.get("confirm_password")
        
        # Get redirect URL
        redirect_url = request.query_params.get("redirect", "/eshop-example")
        
        # Validation - redirect back with error
        if not all([email, password, confirm_password]):
            logger.warning("Registration failed: Missing fields")
            return RedirectResponse(f"/eshop-example/register?redirect={redirect_url}&error=missing_fields", status_code=303)
        
        if password != confirm_password:
            logger.warning("Registration failed: Passwords don't match")
            return RedirectResponse(f"/eshop-example/register?redirect={redirect_url}&error=password_mismatch", status_code=303)
        
        if len(password) < 8:
            logger.warning("Registration failed: Password too short")
            return RedirectResponse(f"/eshop-example/register?redirect={redirect_url}&error=password_short", status_code=303)
        
        try:
            # Register user with "user" role only (E-Shop specific)
            # Username defaults to email
            user = await auth_service.register_user(
                email=email,
                password=password,
                username=email,  # Use email as username
                roles=["user"]  # E-Shop only has "user" role
            )
            
            if not user:
                logger.warning(f"Registration failed: User {email} already exists")
                return RedirectResponse(f"/eshop-example/register?redirect={redirect_url}&error=user_exists", status_code=303)
            
            logger.info(f"E-Shop user {email} registered successfully")
            
            # Auto-login: Generate token
            token_data = {
                "sub": str(user.get("_id")),
                "email": email,
                "username": user.get("username"),
                "roles": user.get("roles", ["user"])
            }
            token = auth_service.create_token(token_data)
            
            logger.info(f"E-Shop user {email} auto-logged in, redirecting to {redirect_url}")
            
            # Create response with redirect and set cookie
            response = RedirectResponse(url=redirect_url, status_code=303)
            response.set_cookie(
                key="auth_token",
                value=token,
                max_age=86400,  # 24 hours
                httponly=False,  # Allow JavaScript access
                samesite="lax"
            )
            return response
            
        except Exception as e:
            logger.error(f"E-Shop registration error: {e}")
            return RedirectResponse(f"/eshop-example/register?redirect={redirect_url}&error=server_error", status_code=303)
    
    # ============================================================================
    # E-Shop Routes
    # ============================================================================
    
    @app.get("/")
    async def shop_home(request: Request, category: str = None):
        """Main shop page"""
        user = await get_user(request)
        
        # Get cart count
        cart_count = 0
        if user:
            user_cart = cart_storage.get(user.get("_id"), {})
            cart_count = sum(user_cart.values())
        
        # Filter products by category if specified
        filtered_products = PRODUCTS
        if category:
            filtered_products = [p for p in PRODUCTS if p["category"] == category]
        
        # Check if user has seen the newsletter modal
        show_modal = not user and not request.cookies.get("newsletter_shown")
        
        content = Div(
            # Newsletter Modal (only for non-logged-in users who haven't seen it)
            (Div(
                # Backdrop blur
                Div(
                    id="newsletter-backdrop",
                    cls="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-40",
                    onclick="document.getElementById('newsletter-modal').style.display='none'; document.getElementById('newsletter-backdrop').style.display='none';"
                ),
                
                # Modal
                Div(
                    Card(
                        # Close button
                        Button(
                            "✕",
                            cls="btn btn-sm btn-circle btn-ghost absolute right-4 top-4",
                            onclick="document.getElementById('newsletter-modal').style.display='none'; document.getElementById('newsletter-backdrop').style.display='none'; document.cookie='newsletter_shown=true; max-age=86400; path=/eshop-example';"
                        ),
                        
                        # Modal content
                        Div(
                            UkIcon("gift", width="64", height="64", cls="text-primary mb-4"),
                            H2("Sign Up!", cls="text-3xl font-bold mb-3"),
                            P("Get exclusive offers delivered straight to your inbox.", cls="text-lg text-gray-600 mb-6"),
                            
                            # Newsletter form
                            Form(
                                Div(
                                    Input(
                                        type="email",
                                        name="email",
                                        placeholder="Enter your email",
                                        required=True,
                                        cls="input input-bordered input-lg w-full mb-3"
                                    ),
                                    Button(
                                        UkIcon("mail", width="20", height="20", cls="mr-2"),
                                        "Get Exclusive Offers",
                                        type="submit",
                                        cls="btn btn-primary btn-lg w-full"
                                    ),
                                    cls="mb-3"
                                ),
                                method="post",
                                action="/eshop-example/newsletter/subscribe",
                                onsubmit="document.getElementById('newsletter-modal').style.display='none'; document.getElementById('newsletter-backdrop').style.display='none'; document.cookie='newsletter_shown=true; max-age=86400; path=/eshop-example';"
                            ),
                            
                            P("🔒 No spam. Unsubscribe anytime.", cls="text-sm text-gray-400"),
                            
                            cls="text-center p-8"
                        ),
                        
                        cls="relative"
                    ),
                    id="newsletter-modal",
                    cls="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md px-4"
                ),
                
                # Auto-show script
                Script("""
                    // Show modal after 2 seconds
                    setTimeout(() => {
                        const modal = document.getElementById('newsletter-modal');
                        const backdrop = document.getElementById('newsletter-backdrop');
                        if (modal && backdrop) {
                            modal.style.display = 'block';
                            backdrop.style.display = 'block';
                        }
                    }, 2000);
                """)
            ) if show_modal else None),
            
            # Hero Section with Background Image
            Div(
                # Background image with overlay
                Div(
                    # Dark overlay for better text readability
                    Div(cls="absolute inset-0 bg-black bg-opacity-50"),
                    
                    # CTA Panel
                    Div(
                        Card(
                            Div(
                                # Badge
                                Span("🎉 NEW ARRIVALS", cls="badge badge-primary badge-lg mb-4"),
                                
                                # Heading
                                H1("Discover Amazing Products", cls="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 text-white"),
                                P("Shop the latest trends with exclusive deals", cls="text-base md:text-lg lg:text-xl text-gray-200 mb-6"),
                                
                                # Features
                                Div(
                                    Div(
                                        UkIcon("check-circle", width="20", height="20", cls="text-success mr-2"),
                                        Span("Free Shipping", cls="text-white"),
                                        cls="flex items-center mb-2"
                                    ),
                                    Div(
                                        UkIcon("check-circle", width="20", height="20", cls="text-success mr-2"),
                                        Span("Secure Checkout", cls="text-white"),
                                        cls="flex items-center mb-2"
                                    ),
                                    Div(
                                        UkIcon("check-circle", width="20", height="20", cls="text-success mr-2"),
                                        Span("30-Day Returns", cls="text-white"),
                                        cls="flex items-center mb-6"
                                    ),
                                ),
                                
                                # CTA Buttons
                                Div(
                                    (Div(
                                        A(
                                            UkIcon("shopping-cart", width="24", height="24", cls="mr-2"),
                                            f"View Cart ({cart_count})",
                                            href="/eshop-example/cart",
                                            cls="btn btn-primary btn-md md:btn-lg sm:mr-3"
                                        ),
                                        A(
                                            "Browse Products",
                                            href="#products",
                                            cls="btn btn-outline btn-md md:btn-lg"
                                        ),
                                        cls="flex flex-col sm:flex-row gap-3 justify-center"
                                    ) if user else Div(
                                        A(
                                            UkIcon("shopping-bag", width="24", height="24", cls="mr-2"),
                                            "Start Shopping",
                                            href="/eshop-example/register?redirect=/eshop-example",
                                            cls="btn btn-primary btn-md md:btn-lg sm:mr-3"
                                        ),
                                        A(
                                            "Browse Products",
                                            href="#products",
                                            cls="btn btn-outline btn-md md:btn-lg"
                                        ),
                                        cls="flex flex-col sm:flex-row gap-3 justify-center"
                                    )),
                                    cls="mb-4"
                                ),
                                
                                # User status (small)
                                (Div(
                                    Span(f"👤 {user.get('username')}", cls="text-sm text-gray-300 mr-3"),
                                    A("Logout", href="/auth/logout", cls="link link-primary text-sm"),
                                    cls="flex items-center justify-center"
                                ) if user else Div(
                                    A("Already have an account? Sign In", href="/eshop-example/login", cls="link link-primary text-sm"),
                                    cls="text-center"
                                )),
                                
                                cls="text-center p-8"
                            ),
                            cls="bg-base-100 bg-opacity-95 backdrop-blur-sm"
                        ),
                        cls="relative z-10 max-w-3xl mx-auto"
                    ),
                    
                    cls="relative min-h-[600px] flex items-center justify-center px-4",
                    style="background-image: url('https://images.unsplash.com/photo-1605513524006-063ed6ed31e7?q=80&w=1052&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'); background-size: cover; background-position: center;"
                ),
                cls="mb-16 -mx-4"
            ),
            
            # Category Filter
            Div(
                H3("Categories", cls="text-lg font-semibold mb-3"),
                Div(
                    A("All", href="/eshop-example", 
                      cls=f"badge badge-lg {'badge-primary' if not category else 'badge-outline'} mr-2 mb-2"),
                    *[A(cat, href=f"/eshop-example?category={cat}", 
                        cls=f"badge badge-lg {'badge-primary' if category == cat else 'badge-outline'} mr-2 mb-2") 
                      for cat in sorted(set(p["category"] for p in PRODUCTS))],
                    cls="flex flex-wrap mb-8"
                )
            ),
            
            # Products Grid
            Div(
                H2(f"{category if category else 'Storefront'} Products", cls="text-2xl font-bold mb-6"),
                (Div(
                    *[ProductCard(product, user) for product in filtered_products],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
                ) if filtered_products else Div(
                    P(f"No products found in {category} category", cls="text-gray-500 text-center py-8"),
                    A("View All Products", href="/eshop-example", cls="btn btn-primary"),
                    cls="text-center"
                )),
                id="products"
            ),
            
            # Call to action
            Div(
                P("View your cart to checkout", cls="text-center text-gray-500 mb-4"),
                A(
                    "Go to Cart",
                    href="/eshop-example/cart",
                    cls="btn btn-primary btn-lg mx-auto block w-fit"
                ) if user and cart_count > 0 else None,
                cls="text-center mb-12"
            ),
            
            # Upcoming Live Events Section
            Div(
                Div(
                    H2("Upcoming Live Events", cls="text-2xl md:text-3xl text-gray-500 font-bold mb-3 text-center tracking-wide"),
                    P("Join us for exclusive shopping experiences and product launches", cls="text-gray-500 text-center mb-12"),
                    
                    # Events list
                    Div(
                        # Event 1
                        Div(
                            Div(
                                # Date badge
                                Div(
                                    Span("DEC", cls="text-xs font-medium text-gray-500 block"),
                                    Span("15", cls="text-3xl font-light block"),
                                    cls="text-center bg-gray-50 p-4 rounded-lg"
                                ),
                                
                                # Event details
                                Div(
                                    Div(
                                        Span("LIVE EVENT", cls="text-xs tracking-widest text-primary mb-2 block"),
                                        H3("Winter Collection Launch", cls="text-lg md:text-xl font-light mb-2 tracking-wide"),
                                        P("Discover our exclusive winter collection with special launch discounts up to 30% off", cls="text-sm text-gray-500 mb-3 leading-relaxed"),
                                        Div(
                                            Div(
                                                UkIcon("clock", width="16", height="16", cls="mr-2 text-gray-400"),
                                                Span("6:00 PM EST", cls="text-sm text-gray-600"),
                                                cls="flex items-center mr-4"
                                            ),
                                            Div(
                                                UkIcon("map-pin", width="16", height="16", cls="mr-2 text-gray-400"),
                                                Span("Virtual Event", cls="text-sm text-gray-600"),
                                                cls="flex items-center"
                                            ),
                                            cls="flex flex-wrap mb-4"
                                        ),
                                        A("Register Now →", href="#", cls="text-sm font-medium hover:underline underline-offset-4"),
                                    ),
                                    cls="flex-1"
                                ),
                                cls="flex flex-col sm:flex-row gap-4 sm:gap-6"
                            ),
                            cls="bg-white border border-gray-100 p-6 rounded-lg hover:border-gray-200 transition-all"
                        ),
                        
                        # Event 2
                        Div(
                            Div(
                                # Date badge
                                Div(
                                    Span("DEC", cls="text-xs font-medium text-gray-500 block"),
                                    Span("22", cls="text-3xl font-light block"),
                                    cls="text-center bg-gray-50 p-4 rounded-lg"
                                ),
                                
                                # Event details
                                Div(
                                    Div(
                                        Span("WORKSHOP", cls="text-xs tracking-widest text-secondary mb-2 block"),
                                        H3("Holiday Gift Styling Session", cls="text-lg md:text-xl font-light mb-2 tracking-wide"),
                                        P("Join our style experts for a live session on curating the perfect holiday gifts", cls="text-sm text-gray-500 mb-3 leading-relaxed"),
                                        Div(
                                            Div(
                                                UkIcon("clock", width="16", height="16", cls="mr-2 text-gray-400"),
                                                Span("3:00 PM EST", cls="text-sm text-gray-600"),
                                                cls="flex items-center mr-4"
                                            ),
                                            Div(
                                                UkIcon("users", width="16", height="16", cls="mr-2 text-gray-400"),
                                                Span("Limited to 50 guests", cls="text-sm text-gray-600"),
                                                cls="flex items-center"
                                            ),
                                            cls="flex flex-wrap mb-4"
                                        ),
                                        A("Reserve Spot →", href="#", cls="text-sm font-medium hover:underline underline-offset-4"),
                                    ),
                                    cls="flex-1"
                                ),
                                cls="flex flex-col sm:flex-row gap-4 sm:gap-6"
                            ),
                            cls="bg-white border border-gray-100 p-6 rounded-lg hover:border-gray-200 transition-all"
                        ),
                        
                        # Event 3
                        Div(
                            Div(
                                # Date badge
                                Div(
                                    Span("JAN", cls="text-xs font-medium text-gray-500 block"),
                                    Span("05", cls="text-3xl font-light block"),
                                    cls="text-center bg-gray-50 p-4 rounded-lg"
                                ),
                                
                                # Event details
                                Div(
                                    Div(
                                        Span("EXCLUSIVE", cls="text-xs tracking-widest text-accent mb-2 block"),
                                        H3("VIP Early Access Sale", cls="text-lg md:text-xl font-light mb-2 tracking-wide"),
                                        P("Get first access to our new year collection before anyone else. VIP members only", cls="text-sm text-gray-500 mb-3 leading-relaxed"),
                                        Div(
                                            Div(
                                                UkIcon("clock", width="16", height="16", cls="mr-2 text-gray-400"),
                                                Span("12:00 PM EST", cls="text-sm text-gray-600"),
                                                cls="flex items-center mr-4"
                                            ),
                                            Div(
                                                UkIcon("star", width="16", height="16", cls="mr-2 text-gray-400"),
                                                Span("VIP Members", cls="text-sm text-gray-600"),
                                                cls="flex items-center"
                                            ),
                                            cls="flex flex-wrap mb-4"
                                        ),
                                        A("Join VIP List →", href="#", cls="text-sm font-medium hover:underline underline-offset-4"),
                                    ),
                                    cls="flex-1"
                                ),
                                cls="flex flex-col sm:flex-row gap-4 sm:gap-6"
                            ),
                            cls="bg-white border border-gray-100 p-6 rounded-lg hover:border-gray-200 transition-all"
                        ),
                        
                        cls="space-y-6 max-w-4xl mx-auto"
                    ),
                    
                    # Newsletter CTA
                    Div(
                        Div(
                            # Divider
                            Div(cls="border-t border-gray-200 mb-12 mt-16"),
                            
                            # Newsletter section
                            Div(
                                UkIcon("mail", width="40", height="40", cls="text-gray-400 mb-4 mx-auto"),
                                H3("Stay in the Loop", cls="text-xl md:text-2xl text-black font-bold mb-3 text-center tracking-wide"),
                                P("Subscribe to our newsletter for exclusive event invites, early access, and special offers", 
                                   cls="text-gray-500 text-center mb-8 max-w-xl mx-auto"),
                                
                                # Newsletter form
                                Form(
                                    Div(
                                        Input(
                                            type="email",
                                            name="email",
                                            placeholder="Enter your email address",
                                            required=True,
                                            cls="input input-bordered input-lg w-full max-w-md text-center"
                                        ),
                                        Button(
                                            "Subscribe",
                                            type="submit",
                                            cls="btn btn-primary btn-lg mt-4 px-12"
                                        ),
                                        cls="flex flex-col items-center"
                                    ),
                                    method="post",
                                    action="/eshop-example/newsletter/subscribe",
                                    cls="mb-4"
                                ),
                                
                                P("🔒 We respect your privacy. Unsubscribe anytime.", 
                                   cls="text-xs text-gray-400 text-center"),
                                
                                cls="text-center"
                            ),
                        ),
                        cls="max-w-4xl mx-auto"
                    ),
                ),
                cls="mt-16 mb-8 bg-gray-50 py-16 -mx-4 px-4"
            )
        )
        
        return Layout(content, title="E-Shop Example | FastApp", user=user, cart_count=cart_count, show_auth=True)
    
    @app.get("/product/{product_id}")
    async def product_detail(request: Request, product_id: int):
        """Product detail page"""
        user = await get_user(request)
        
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
        quantity_in_cart = 0
        is_free = product["price"] == 0
        
        if user:
            user_cart = cart_storage.get(user.get("_id"), {})
            in_cart = product_id in user_cart
            quantity_in_cart = user_cart.get(product_id, 0)
        
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
                # Product image and quantity selector
                Div(
                    Img(
                        src=product["image"],
                        alt=product["name"],
                        cls="w-full h-96 object-cover rounded-lg shadow-lg mb-6"
                    ),
                    
                    # Quantity selector (for paid products only)
                    (Div(
                        Div(
                            Label("Quantity:", cls="font-semibold mb-3 block text-sm"),
                            Div(
                                Button(
                                    "-",
                                    cls="btn btn-sm btn-circle btn-outline",
                                    onclick="const input = document.getElementById('qty-input'); if (input.value > 1) input.value = parseInt(input.value) - 1;"
                                ),
                                Input(
                                    type="number",
                                    value="1",
                                    min="1",
                                    max="10",
                                    id="qty-input",
                                    cls="input input-sm input-bordered w-16 mx-2 text-center",
                                    readonly=True,
                                    style="appearance: textfield; -moz-appearance: textfield; -webkit-appearance: none;"
                                ),
                                Button(
                                    "+",
                                    cls="btn btn-sm btn-circle btn-outline",
                                    onclick="const input = document.getElementById('qty-input'); if (input.value < 10) input.value = parseInt(input.value) + 1;"
                                ),
                                cls="flex items-center justify-start"
                            ),
                            Style("""
                                #qty-input::-webkit-outer-spin-button,
                                #qty-input::-webkit-inner-spin-button {
                                    -webkit-appearance: none;
                                    margin: 0;
                                }
                            """)
                        ),
                        cls="p-4 bg-base-200 rounded-lg"
                    ) if not is_free else None),
                    
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
                    
                    # Action buttons
                    Div(id="cart-action", cls="mb-4"),
                    (A(
                        UkIcon("download", width="20", height="20", cls="mr-2"),
                        "Get Free Access",
                        href="#",
                        cls="btn btn-success btn-lg w-full",
                        onclick="alert('Free product downloaded! Check your email for access details.')"
                    ) if is_free else (
                        # Already in cart
                        Div(
                            Span(f"✓ In Cart ({quantity_in_cart})", cls="badge badge-success badge-lg py-4 px-6 mb-4"),
                            A(
                                UkIcon("shopping-cart", width="20", height="20", cls="mr-2"),
                                "View Cart & Checkout",
                                href="/eshop-example/cart",
                                cls="btn btn-primary btn-lg w-full"
                            ),
                        ) if in_cart else (
                            # User is logged in
                            Div(
                                Button(
                                    UkIcon("shopping-cart", width="20", height="20", cls="mr-2"),
                                    "Add to Cart",
                                    cls="btn btn-primary btn-lg w-full mb-3",
                                    hx_post=f"/eshop-example/cart/add/{product_id}",
                                    hx_target="#cart-action",
                                    hx_swap="innerHTML",
                                    hx_vals="js:{quantity: document.getElementById('qty-input')?.value || 1}"
                                ),
                                A(
                                    UkIcon("zap", width="20", height="20", cls="mr-2"),
                                    "Buy Now",
                                    cls="btn btn-success btn-lg w-full",
                                    onclick=f"const qty = document.getElementById('qty-input')?.value || 1; window.location.href = '/eshop-example/cart/add-and-view/{product_id}?quantity=' + qty; return false;"
                                ),
                            ) if user else (
                                # User not logged in - SIMPLE FLOW
                                Div(
                                    A(
                                        UkIcon("zap", width="20", height="20", cls="mr-2"),
                                        "Buy Now",
                                        href=f"/eshop-example/login?redirect=/eshop-example/cart/add-and-view/{product_id}",
                                        cls="btn btn-success btn-lg w-full mb-3"
                                    ),
                                    Div(
                                        Span("or", cls="text-gray-500 text-sm"),
                                        cls="text-center mb-3"
                                    ),
                                    A(
                                        UkIcon("shopping-cart", width="20", height="20", cls="mr-2"),
                                        "Add to Cart",
                                        href=f"/eshop-example/login?redirect=/eshop-example/cart/add-and-view/{product_id}",
                                        cls="btn btn-outline btn-lg w-full"
                                    ),
                                )
                            )
                        )
                    )),
                    
                    cls="lg:col-span-1"
                ),
                
                cls="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12"
            ),
            
            # You might also like section
            Div(
                H2("You Might Also Like", cls="text-2xl md:text-3xl font-bold mb-6 text-center"),
                Div(
                    *[ProductCard(p, user) for p in PRODUCTS 
                      if p["category"] == product["category"] and p["id"] != product_id][:4],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
                ) if any(p["category"] == product["category"] and p["id"] != product_id for p in PRODUCTS) else Div(
                    P("No similar products available at the moment.", cls="text-gray-500 text-center py-8")
                ),
                cls="mb-12"
            )
        )
        
        # Get cart count
        cart_count = 0
        if user:
            user_cart = cart_storage.get(user.get("_id"), {})
            cart_count = sum(user_cart.values())
        
        return Layout(content, title=f"{product['name']} | E-Shop", user=user, cart_count=cart_count, show_auth=True)
    
    # Guest checkout removed - too much friction. Simple flow: Buy Now → Login/Register → Cart → Checkout
    
    @app.get("/checkout/guest/{product_id}")
    async def guest_checkout_redirect(request: Request, product_id: int):
        """Redirect to login - guest checkout removed for simpler flow"""
        return RedirectResponse(f"/eshop-example/login?redirect=/eshop-example/cart/add-and-view/{product_id}")
    
    @app.get("/cart/add-and-view/{product_id}")
    async def add_and_view_cart(request: Request, product_id: int, quantity: int = 1):
        """Add product to cart and redirect to cart page (for post-login flow)"""
        user = await get_user(request)
        
        if not user:
            return RedirectResponse(f"/eshop-example/login?redirect=/eshop-example/cart/add-and-view/{product_id}?quantity={quantity}")
        
        # Find product
        product = next((p for p in PRODUCTS if p["id"] == product_id), None)
        if not product:
            return RedirectResponse("/eshop-example")
        
        # Add to cart with specified quantity
        user_id = user.get("_id")
        if user_id not in cart_storage:
            cart_storage[user_id] = {}
        
        # Update quantity (add to existing or set new)
        current_qty = cart_storage[user_id].get(product_id, 0)
        cart_storage[user_id][product_id] = current_qty + quantity
        
        logger.info(f"User {user_id} added {quantity}x product {product_id} to cart (post-login)")
        
        # Redirect to cart page
        return RedirectResponse("/eshop-example/cart")
    
    @app.get("/cart")
    async def view_cart(request: Request):
        """View shopping cart"""
        user = await get_user(request)
        
        if not user:
            return RedirectResponse("/eshop-example/login?redirect=/eshop-example/cart")
        
        user_cart = cart_storage.get(user.get("_id"), {})
        cart_items = []
        cart_total = 0
        
        for product_id, quantity in user_cart.items():
            product = next((p for p in PRODUCTS if p["id"] == product_id), None)
            if product:
                subtotal = product["price"] * quantity
                cart_items.append({
                    **product,
                    "quantity": quantity,
                    "subtotal": subtotal
                })
                cart_total += subtotal
        
        content = Div(
            Div(
                # Header
                Div(
                    H1("🛒 Shopping Cart", cls="text-3xl font-bold mb-2"),
                    A("← Continue Shopping", href="/eshop-example", cls="btn btn-ghost mb-6"),
                    cls="mb-8"
                ),
            
            # Cart items or empty state (85vh container)
            (Div(
                # Cart items list (scrollable)
                Div(
                    *[Div(
                        # Product image
                        Img(src=item["image"], alt=item["name"], cls="w-24 h-24 object-cover rounded"),
                        
                        # Product info
                        Div(
                            H3(item["name"], cls="font-semibold text-lg"),
                            P(item["category"], cls="text-sm text-gray-500 mb-2"),
                            Span(f"${item['price']:.2f} each", cls="text-sm text-gray-600"),
                            cls="flex-1"
                        ),
                        
                        # Quantity controls
                        Div(
                            Label("Qty:", cls="text-sm font-semibold mr-2"),
                            Div(
                                Button(
                                    "-",
                                    cls="btn btn-xs btn-circle btn-outline",
                                    hx_post=f"/eshop-example/cart/update/{item['id']}",
                                    hx_vals=f'{{"quantity": {max(0, item["quantity"] - 1)}}}',
                                    hx_target="body",
                                    hx_swap="outerHTML"
                                ),
                                Span(str(item["quantity"]), cls="mx-3 font-semibold min-w-[2rem] text-center inline-block"),
                                Button(
                                    "+",
                                    cls="btn btn-xs btn-circle btn-outline",
                                    hx_post=f"/eshop-example/cart/update/{item['id']}",
                                    hx_vals=f'{{"quantity": {min(10, item["quantity"] + 1)}}}',
                                    hx_target="body",
                                    hx_swap="outerHTML"
                                ),
                                cls="flex items-center"
                            ),
                            cls="flex items-center mr-6"
                        ),
                        
                        # Subtotal and remove
                        Div(
                            Span(f"${item['subtotal']:.2f}", cls="font-bold text-lg mb-2 block text-right"),
                            Button(
                                UkIcon("trash-2", width="16", height="16"),
                                cls="btn btn-xs btn-ghost btn-error",
                                hx_delete=f"/eshop-example/cart/remove/{item['id']}",
                                hx_target="body",
                                hx_swap="outerHTML",
                                hx_confirm="Remove this item from cart?"
                            ),
                            cls="text-right"
                        ),
                        
                        cls="flex items-center gap-4 p-4 bg-base-200 rounded-lg"
                    ) for item in cart_items],
                    cls="space-y-4 mb-8 lg:col-span-2 overflow-y-auto pr-2",
                    style="scrollbar-width: thin;"
                ),
                
                # Cart summary
                Div(
                    H3("Order Summary", cls="text-xl font-bold mb-4"),
                    Div(
                        Span("Subtotal:", cls="text-gray-600"),
                        Span(f"${cart_total:.2f}", cls="font-semibold"),
                        cls="flex justify-between mb-2"
                    ),
                    Hr(cls="my-4"),
                    Div(
                        Span("Total:", cls="text-xl font-bold"),
                        Span(f"${cart_total:.2f}", cls="text-2xl font-bold text-blue-600"),
                        cls="flex justify-between mb-6"
                    ),
                    Button(
                        UkIcon("credit-card", width="20", height="20", cls="mr-2"),
                        "Proceed to Checkout",
                        cls="btn btn-primary btn-lg w-full",
                        onclick="alert('Stripe integration would go here! Total: $" + f"{cart_total:.2f}" + "')"
                    ),
                    cls="bg-base-200 p-6 rounded-lg lg:col-span-1"
                ),
                cls="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[85vh] overflow-y-auto"
            ) if cart_items else Div(
                UkIcon("shopping-cart", width="64", height="64", cls="text-gray-300 mb-4"),
                H2("Your cart is empty", cls="text-2xl font-bold mb-2"),
                P("Add some products to get started!", cls="text-gray-500 mb-6"),
                A("Browse Products", href="/eshop-example", cls="btn btn-primary btn-lg"),
                cls="text-center py-16 h-[85vh] flex flex-col items-center justify-center"
            )),
                cls="container mx-auto px-4"
            )
        )
        
        return Layout(content, title="Shopping Cart | E-Shop", user=user, cart_count=len(cart_items), show_auth=True)
    
    @app.post("/cart/add/{product_id}")
    async def add_to_cart(request: Request, product_id: int):
        """Add product to cart with quantity"""
        user = await get_user(request)
        
        # Get quantity from form data
        form_data = await request.form()
        quantity = int(form_data.get("quantity", 1))
        
        if not user:
            return Div(
                P("⚠️ Please sign in to add items to cart", cls="text-warning"),
                A("Sign In", href="/eshop-example/login?redirect=/eshop-example", cls="btn btn-sm btn-primary mt-2"),
                cls="alert alert-warning"
            )
        
        product = next((p for p in PRODUCTS if p["id"] == product_id), None)
        if not product:
            return Div(P("❌ Product not found", cls="text-error"), cls="alert alert-error")
        
        # Add to cart with quantity
        user_id = user.get("_id")
        if user_id not in cart_storage:
            cart_storage[user_id] = {}
        
        # Update quantity (add to existing or set new)
        current_qty = cart_storage[user_id].get(product_id, 0)
        cart_storage[user_id][product_id] = current_qty + quantity
        
        logger.info(f"User {user_id} added {quantity}x product {product_id} to cart")
        
        return Div(
            Span("✓ Added to Cart", cls="badge badge-success badge-lg py-4 px-6"),
            A("View Cart", href="/eshop-example/cart", cls="btn btn-primary btn-lg ml-4"),
            cls="flex items-center"
        )
    
    @app.post("/cart/update/{product_id}")
    async def update_cart_quantity(request: Request, product_id: int):
        """Update cart item quantity"""
        user = await get_user(request)
        
        if not user:
            return RedirectResponse("/eshop-example/login?redirect=/eshop-example/cart")
        
        # Get quantity from form data
        form_data = await request.form()
        quantity = int(form_data.get("quantity", 1))
        
        user_id = user.get("_id")
        
        # Update or remove item
        if quantity <= 0:
            # Remove item if quantity is 0
            if user_id in cart_storage and product_id in cart_storage[user_id]:
                del cart_storage[user_id][product_id]
                logger.info(f"User {user_id} removed product {product_id} from cart")
        else:
            # Update quantity
            if user_id not in cart_storage:
                cart_storage[user_id] = {}
            cart_storage[user_id][product_id] = min(quantity, 10)  # Max 10
            logger.info(f"User {user_id} updated product {product_id} quantity to {quantity}")
        
        # Redirect to refresh cart page
        return RedirectResponse("/eshop-example/cart", status_code=303)
    
    @app.delete("/cart/remove/{product_id}")
    async def remove_from_cart(request: Request, product_id: int):
        """Remove item from cart"""
        user = await get_user(request)
        
        if not user:
            return RedirectResponse("/eshop-example/login?redirect=/eshop-example/cart")
        
        user_id = user.get("_id")
        
        # Remove item
        if user_id in cart_storage and product_id in cart_storage[user_id]:
            del cart_storage[user_id][product_id]
            logger.info(f"User {user_id} removed product {product_id} from cart")
        
        # Redirect to refresh cart page
        return RedirectResponse("/eshop-example/cart", status_code=303)
    
    def ProductCard(product: dict, user: dict = None):
        """Boutique-style product card component"""
        is_free = product["price"] == 0
        
        return Div(
            # Card container with elegant styling
            Div(
                # Image container with overlay on hover
                Div(
                    A(
                        Img(
                            src=product["image"],
                            alt=product["name"],
                            cls="w-full h-80 object-cover transition-transform duration-500 hover:scale-105"
                        ),
                        # Hover overlay
                        Div(
                            Div(
                                UkIcon("eye", width="24", height="24", cls="mb-2"),
                                Span("Quick View", cls="text-sm font-medium"),
                                cls="flex flex-col items-center"
                            ),
                            cls="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-40 flex items-center justify-center transition-all duration-300 opacity-0 hover:opacity-100"
                        ),
                        href=f"/eshop-example/product/{product['id']}",
                        cls="block"
                    ),
                    cls="relative overflow-hidden group"
                ),
                
                # Product info with elegant spacing
                Div(
                    # Category badge - minimal
                    Span(
                        product["category"].upper(),
                        cls="text-xs tracking-widest text-gray-400 mb-2 block font-light"
                    ),
                    
                    # Product name
                    A(
                        H3(
                            product["name"],
                            cls="text-xl font-light mb-3 hover:text-gray-600 transition-colors tracking-wide"
                        ),
                        href=f"/eshop-example/product/{product['id']}"
                    ),
                    
                    # Description
                    P(
                        product["description"],
                        cls="text-sm text-gray-500 mb-4 line-clamp-2 font-light leading-relaxed"
                    ),
                    
                    # Price and button row
                    Div(
                        # Price
                        Div(
                            (Span("COMPLIMENTARY", cls="text-sm font-medium text-emerald-600 tracking-wide") if is_free 
                             else Span(f"${product['price']}", cls="text-2xl font-light tracking-tight")),
                        ),
                        
                        # Add to cart button - minimal
                        A(
                            "Shop Now",
                            href=f"/eshop-example/product/{product['id']}",
                            cls="text-sm font-medium tracking-wide hover:underline underline-offset-4 transition-all"
                        ),
                        
                        cls="flex items-center justify-between"
                    ),
                    
                    cls="p-6 bg-white"
                ),
                
                cls="bg-white border border-gray-100 hover:border-gray-200 transition-all duration-300 hover:shadow-2xl group"
            ),
            cls="transform transition-transform duration-300 hover:-translate-y-1"
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
    
    @app.post("/newsletter/subscribe")
    async def subscribe_newsletter(request: Request):
        """Handle newsletter subscription"""
        form_data = await request.form()
        email = form_data.get("email")
        
        if email:
            logger.info(f"E-Shop newsletter subscription: {email}")
            # In production: save to database, send to Mailgun, etc.
            
            return Div(
                Div(
                    P(f"✓ Success! Exclusive offers will be sent to {email}", cls="text-success"),
                    cls="alert alert-success max-w-2xl mx-auto mt-8"
                ),
                Script("""
                    setTimeout(() => {
                        window.location.href = '/eshop-example';
                    }, 3000);
                """)
            )
        
        return RedirectResponse("/eshop-example")
    
    return app

#serve(port = 8000)