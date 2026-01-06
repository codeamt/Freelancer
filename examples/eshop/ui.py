"""E-Shop Specific Auth UI - Simple user registration"""
from fasthtml.common import *
from monsterui.all import *

# Import core marketing components
from core.ui.components.marketing import NewsletterSignup


# ============================================================================
# Helper Components
# ============================================================================

def EShopSubNav(user, base_path: str, cart_count: int = 0):
    """E-Shop specific sub-navigation with hamburger menu and cart."""
    return Nav(
        # Main navigation container
        Div(
            # Logo/Brand
            Div(
                A(
                    Div(
                        UkIcon("shopping-bag", width="24", height="24", cls="text-blue-400 mr-2"),
                        Span("E-Shop", cls="text-xl font-bold text-white"),
                        cls="flex items-center"
                    ),
                    href=base_path,
                    cls="flex items-center"
                ),
                cls="flex items-center"
            ),
            
            # Desktop navigation links
            Div(
                A("Home", href=base_path, cls="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"),
                A("Products", href=f"{base_path}/#products", cls="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"),
                A("About", href=f"{base_path}/about", cls="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"),
                A("Contact", href=f"{base_path}/contact", cls="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"),
                cls="hidden md:flex space-x-4"
            ),
            
            # Right side actions
            Div(
                # Shopping cart button (desktop)
                Button(
                    Div(
                        UkIcon("shopping-cart", width="20", height="20", cls="text-white"),
                        Span(
                            str(cart_count) if cart_count > 0 else "",
                            cls="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center" if cart_count > 0 else ""
                        ),
                        cls="relative"
                    ),
                    onclick="toggleCartDrawer()",
                    cls="relative p-2 text-gray-300 hover:text-white hidden md:block"
                ),
                
                # Hamburger menu button (mobile)
                Button(
                    UkIcon("menu", width="24", height="24", cls="text-white"),
                    onclick="toggleSideDrawer()",
                    cls="md:hidden p-2 text-gray-300 hover:text-white"
                ),
                
                cls="flex items-center space-x-4"
            ),
            
            cls="flex items-center justify-between px-4 py-3 bg-gray-900 border-b border-gray-800"
        ),
        
        # Side drawer for mobile and auth
        Div(
            # Close button
            Button(
                UkIcon("x", width="24", height="24", cls="text-gray-400 hover:text-white"),
                onclick="toggleSideDrawer()",
                cls="absolute top-4 right-4 p-2"
            ),
            
            # Drawer content
            Div(
                # Auth section
                Div(
                    H3("Account", cls="text-lg font-semibold text-white mb-4"),
                    Div(
                        A("Login", href=f"{base_path}/login", cls="block w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-800 rounded"),
                        A("Register", href=f"{base_path}/register", cls="block w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-800 rounded"),
                        A("Profile", href=f"{base_path}/profile", cls="block w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-800 rounded"),
                        A("Orders", href=f"{base_path}/orders", cls="block w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-800 rounded"),
                        cls="space-y-2 mb-6"
                    ),
                    cls="border-b border-gray-700 pb-6"
                ),
                
                # Navigation links
                Div(
                    H3("Navigation", cls="text-lg font-semibold text-white mb-4"),
                    Div(
                        A("Home", href=base_path, cls="block w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-800 rounded"),
                        A("Products", href=f"{base_path}/#products", cls="block w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-800 rounded"),
                        A("About", href=f"{base_path}/about", cls="block w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-800 rounded"),
                        A("Contact", href=f"{base_path}/contact", cls="block w-full text-left px-4 py-2 text-gray-300 hover:bg-gray-800 rounded"),
                        cls="space-y-2"
                    ),
                    cls="mb-6"
                ),
                
                # Mobile cart button
                Div(
                    Button(
                        Div(
                            UkIcon("shopping-cart", width="20", height="20", cls="text-white mr-2"),
                            Span("Shopping Cart"),
                            Span(
                                str(cart_count) if cart_count > 0 else "",
                                cls="ml-2 bg-red-500 text-white text-xs rounded-full px-2 py-1" if cart_count > 0 else ""
                            ),
                            cls="flex items-center"
                        ),
                        onclick="toggleSideDrawer(); toggleCartDrawer()",
                        cls="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
                    ),
                    cls="border-t border-gray-700 pt-6"
                ),
                
                cls="p-6"
            ),
            
            # Drawer styling
            cls="fixed top-0 right-0 h-full w-80 bg-gray-900 shadow-2xl transform translate-x-full transition-transform duration-300 ease-in-out z-50",
            id="side-drawer"
        ),
        
        # Cart drawer
        Div(
            # Cart header
            Div(
                Div(
                    H3("Shopping Cart", cls="text-lg font-semibold text-white"),
                    Button(
                        UkIcon("x", width="20", height="20", cls="text-gray-400 hover:text-white"),
                        onclick="toggleCartDrawer()",
                        cls="p-1"
                    ),
                    cls="flex items-center justify-between"
                ),
                cls="flex items-center justify-between p-4 border-b border-gray-700"
            ),
            
            # Cart content
            Div(
                Div(id="cart-items", cls="p-4 space-y-4"),
                
                # Cart footer
                Div(
                    Div(
                        Div(
                            Span("Total:", cls="text-gray-300"),
                            Span("$0.00", id="cart-total", cls="text-xl font-bold text-white"),
                            cls="flex justify-between items-center"
                        ),
                        Button(
                            "Checkout",
                            cls="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-lg font-semibold"
                        ),
                        cls="space-y-4"
                    ),
                    cls="p-4 border-t border-gray-700"
                ),
                
                cls="flex flex-col h-full"
            ),
            
            # Cart drawer styling
            cls="fixed top-0 right-0 h-full w-80 bg-gray-900 shadow-2xl transform translate-x-full transition-transform duration-300 ease-in-out z-50",
            id="cart-drawer"
        ),
        
        # JavaScript for drawer functionality
        Script("""
            function toggleSideDrawer() {
                const drawer = document.getElementById('side-drawer');
                drawer.classList.toggle('translate-x-full');
            }
            
            function toggleCartDrawer() {
                const drawer = document.getElementById('cart-drawer');
                drawer.classList.toggle('translate-x-full');
            }
            
            // Close drawers when clicking outside
            document.addEventListener('click', function(e) {
                const sideDrawer = document.getElementById('side-drawer');
                const cartDrawer = document.getElementById('cart-drawer');
                
                if (!sideDrawer.contains(e.target) && !e.target.closest('button[onclick*="toggleSideDrawer"]')) {
                    sideDrawer.classList.add('translate-x-full');
                }
                
                if (!cartDrawer.contains(e.target) && !e.target.closest('button[onclick*="toggleCartDrawer"]')) {
                    cartDrawer.classList.add('translate-x-full');
                }
            });
        """),
        
        cls="bg-gray-900"
    )


def NewsletterModal(base_path: str = "/eshop-example"):
    """Newsletter signup modal with delayed appearance and subtle backdrop blur."""
    return Div(
        # Modal dialog element
        Dialog(
            # Backdrop with reduced opacity
            Div(
                # Modal content card (fully visible)
                Div(
                    # Close button
                    Button(
                        "×",
                        cls="absolute top-4 right-4 text-gray-400 hover:text-white text-2xl font-bold",
                        onclick="this.closest('dialog').close()"
                    ),
                    
                    # Modal content
                    Div(
                        Div(
                            # Icon
                            Div(
                                UkIcon("mail", width="48", height="48", cls="text-blue-400 mb-4"),
                                cls="flex justify-center"
                            ),
                            
                            # Title and description
                            H3("🎉 Get Exclusive Discounts!", cls="text-2xl font-bold text-white mb-4 text-center"),
                            P(
                                "Join our newsletter and receive 15% off your first order, plus early access to sales and new products.",
                                cls="text-gray-300 mb-6 text-center"
                            ),
                            
                            # Benefits list
                            Ul(
                                Li("✨ 15% off your first order", cls="text-gray-300 mb-2"),
                                Li("🚀 Early access to new products", cls="text-gray-300 mb-2"),
                                Li("💰 Member-only sales and promotions", cls="text-gray-300 mb-2"),
                                Li("📦 Free shipping on orders over $50", cls="text-gray-300 mb-2"),
                                cls="space-y-2 mb-6"
                            ),
                            
                            # Newsletter form
                            Form(
                                Div(
                                    Input(
                                        type="email",
                                        name="email",
                                        placeholder="Enter your email address",
                                        required=True,
                                        cls="w-full px-4 py-3 rounded-lg bg-gray-800 text-white border-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
                                    ),
                                    
                                    Button(
                                        "Get My 15% Discount",
                                        type="submit",
                                        cls="w-full px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-colors duration-200"
                                    ),
                                    
                                    cls="space-y-4"
                                ),
                                method="post",
                                action=f"{base_path}/newsletter/subscribe",
                                hx_post=f"{base_path}/newsletter/subscribe",
                                hx_target="#newsletter-result",
                                hx_swap="innerHTML"
                            ),
                            
                            # Result message container
                            Div(id="newsletter-result", cls="mt-4"),
                            
                            # Privacy notice
                            P(
                                "We respect your privacy. Unsubscribe at any time.",
                                cls="text-xs text-gray-400 text-center mt-4"
                            ),
                            
                            cls="max-w-md mx-auto"
                        ),
                        cls="p-8"
                    ),
                    
                    # Modal card styling (fully visible)
                    cls="bg-gray-900 rounded-lg shadow-2xl border border-gray-700 max-w-md mx-auto relative",
                    style="opacity: 0; transition: opacity 0.5s ease-in-out;"
                ),
                
                # Backdrop styling with reduced opacity only
                cls="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            ),
            id="newsletter-modal"
        ),
        
        # JavaScript to handle delay and fade-in
        Script("""
            console.log('Newsletter modal script loaded');
            
            // Delay modal appearance and fade in
            setTimeout(function() {
                console.log('Attempting to show modal after delay');
                const modal = document.getElementById('newsletter-modal');
                if (modal) {
                    console.log('Modal found, showing...');
                    // Fade in the modal card only
                    const modalCard = modal.querySelector('.bg-gray-900');
                    if (modalCard) {
                        modalCard.style.opacity = '1';
                    }
                    modal.showModal();
                } else {
                    console.error('Modal not found!');
                }
            }, 3000); // 3 second delay
            
            // Close modal with Escape key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    const modal = document.getElementById('newsletter-modal');
                    if (modal && modal.open) {
                        modal.close();
                    }
                }
            });
        """)
    )


def SocialLinks():
    return Div(
        H3("Follow Us", cls="text-lg font-semibold text-white mb-4 text-center"),
        Div(
            A(
                UkIcon("facebook", width="20", height="20"),
                cls="btn btn-circle btn-outline bg-gray-800 border-gray-600 text-white hover:bg-blue-600 hover:border-blue-600 mr-2",
                href="https://facebook.com",
                target="_blank"
            ),
            A(
                UkIcon("twitter", width="20", height="20"),
                cls="btn btn-circle btn-outline bg-gray-800 border-gray-600 text-white hover:bg-blue-400 hover:border-blue-400 mr-2",
                href="https://twitter.com",
                target="_blank"
            ),
            A(
                UkIcon("instagram", width="20", height="20"),
                cls="btn btn-circle btn-outline bg-gray-800 border-gray-600 text-white hover:bg-pink-600 hover:border-pink-600 mr-2",
                href="https://instagram.com",
                target="_blank"
            ),
            A(
                UkIcon("youtube", width="20", height="20"),
                cls="btn btn-circle btn-outline bg-gray-800 border-gray-600 text-white hover:bg-red-600 hover:border-red-600",
                href="https://youtube.com",
                target="_blank"
            ),
            cls="flex justify-center items-center"
        ),
        cls="py-8"
    )

def ProductCard(product: dict, user, base_path: str):
    """Product card component with dark theme."""
    # Handle free products
    if product["price"] == 0.0:
        price_display = Span("Free (with signup)", cls="text-2xl font-bold text-green-400")
    else:
        price_display = Span(
            f"${product['price']}",
            cls="text-2xl font-bold text-blue-400"
        )
    
    return Div(
        A(
            Div(
                Img(
                    src=product["image"],
                    alt=product["name"],
                    cls="w-full h-48 object-cover"
                ),
                Div(
                    H3(product["name"], cls="text-lg font-semibold mb-2 text-white"),
                    P(product["description"], cls="text-sm text-gray-300 mb-4"),
                    Div(
                        price_display,
                        Span(product["category"], cls="badge badge-outline bg-gray-700 text-gray-300 border-gray-600"),
                        cls="flex justify-between items-center"
                    ),
                    cls="p-4"
                ),
                cls="card bg-gray-900 shadow-xl hover:shadow-2xl transition-all duration-300 border border-gray-700 hover:border-blue-500"
            ),
            href=f"{base_path}/product/{product['id']}"
        )
    )


def CartItem(item: dict, base_path: str):
    """Cart item component with quantity controls."""
    return Div(
        Div(
            # Product image
            A(
                Img(
                    src=item["image"],
                    alt=item["name"],
                    cls="w-24 h-24 object-cover rounded"
                ),
                href=f"{base_path}/product/{item['id']}"
            ),
            
            # Product info
            Div(
                A(
                    H3(item["name"], cls="font-semibold text-lg hover:text-blue-600"),
                    href=f"{base_path}/product/{item['id']}"
                ),
                P(f"${item['price']:.2f} each", cls="text-gray-600 text-sm"),
                
                # Quantity controls
                Div(
                    Button(
                        "−",
                        cls="btn btn-sm btn-outline",
                        hx_post=f"{base_path}/cart/update/{item['id']}?action=decrease",
                        hx_target="#cart-content",
                        hx_swap="innerHTML"
                    ),
                    Span(str(item['quantity']), cls="px-4 font-semibold"),
                    Button(
                        "+",
                        cls="btn btn-sm btn-outline",
                        hx_post=f"{base_path}/cart/update/{item['id']}?action=increase",
                        hx_target="#cart-content",
                        hx_swap="innerHTML"
                    ),
                    cls="flex items-center mt-2"
                ),
                cls="flex-1 ml-4"
            ),
            
            # Price and remove
            Div(
                P(
                    f"${item['price'] * item['quantity']:.2f}",
                    cls="font-bold text-xl text-blue-600"
                ),
                Button(
                    UkIcon("trash-2", width="16", height="16"),
                    " Remove",
                    cls="btn btn-sm btn-ghost text-error mt-2",
                    hx_post=f"{base_path}/cart/remove/{item['id']}",
                    hx_target="#cart-content",
                    hx_swap="innerHTML"
                ),
                cls="text-right"
            ),
            cls="flex items-center gap-4"
        ),
        cls="card bg-base-100 shadow p-4",
        id=f"cart-item-{item['id']}"
    )


def CartSummary(subtotal: float, tax: float, total: float, base_path: str):
    """Cart summary component."""
    return Div(
        H2("Order Summary", cls="text-2xl font-bold mb-4"),
        Div(
            Div(
                Span("Subtotal:", cls="text-gray-600"),
                Span(f"${subtotal:.2f}", cls="font-semibold"),
                cls="flex justify-between mb-2"
            ),
            Div(
                Span("Tax (10%):", cls="text-gray-600"),
                Span(f"${tax:.2f}", cls="font-semibold"),
                cls="flex justify-between mb-2"
            ),
            Div(cls="divider my-2"),
            Div(
                Span("Total:", cls="font-bold text-xl"),
                Span(f"${total:.2f}", cls="font-bold text-xl text-blue-600"),
                cls="flex justify-between mb-6"
            ),
            A(
                "Proceed to Checkout",
                href=f"{base_path}/checkout",
                cls="btn btn-primary btn-lg w-full"
            ),
            A(
                "Continue Shopping",
                href=f"{base_path}/",
                cls="btn btn-ghost btn-sm w-full mt-2"
            ),
            cls="bg-base-200 p-6 rounded-lg"
        )
    )


def EShopLoginPage(base_path: str = "/eshop-example", error: str = None):
    """E-Shop login page - simple and focused"""
    # Error messages
    error_messages = {
        "missing_fields": "Email and password are required",
        "invalid_credentials": "Invalid email or password",
        "server_error": "An error occurred. Please try again."
    }
    
    return Div(
        # Header
        Div(
            H1("🛍️ Welcome Back", cls="text-4xl font-bold mb-2"),
            P("Sign in to access your cart and checkout", cls="text-xl text-gray-500 mb-8"),
            cls="text-center mb-8"
        ),
        
        # Error message
        (Div(
            P(f"⚠️ {error_messages.get(error, 'An error occurred')}", cls="text-error"),
            cls="alert alert-error max-w-md mx-auto mb-4"
        ) if error else None),
        
        # Login Form
        Card(
            Form(
                # Email
                Div(
                    Label("Email", cls="label"),
                    Input(
                        type="email",
                        name="email",
                        placeholder="your@email.com",
                        required=True,
                        cls="input input-bordered w-full"
                    ),
                    cls="form-control mb-4"
                ),
                
                # Password
                Div(
                    Label("Password", cls="label"),
                    Input(
                        type="password",
                        name="password",
                        placeholder="••••••••",
                        required=True,
                        cls="input input-bordered w-full"
                    ),
                    cls="form-control mb-4"
                ),
                
                # Submit
                Button(
                    "Sign In",
                    type="submit",
                    cls="btn btn-primary w-full btn-lg"
                ),
                
                # Register link
                Div(
                    Span("Don't have an account? ", cls="text-gray-500"),
                    A("Create one", href=f"/eshop-example/register?redirect={base_path}", cls="link link-primary"),
                    cls="text-center mt-4"
                ),
                
                method="post",
                action=f"{base_path}/auth/login"
            ),
            cls="max-w-md mx-auto p-8"
        ),
        
        cls="container mx-auto px-4 py-8"
    )


def EShopRegisterPage(base_path: str = "/eshop-example", error: str = None):
    """E-Shop registration page - simple user registration only"""
    # Error messages
    error_messages = {
        "missing_fields": "All fields are required",
        "password_mismatch": "Passwords do not match",
        "password_short": "Password must be at least 8 characters",
        "user_exists": "User already exists. Please sign in instead.",
        "server_error": "An error occurred. Please try again."
    }
    
    return Div(
        # Header
        Div(
            H1("🛍️ Create Account", cls="text-4xl font-bold mb-2"),
            P("Join us to start shopping", cls="text-xl text-gray-500 mb-8"),
            cls="text-center mb-8"
        ),
        
        # Error message
        (Div(
            P(f"⚠️ {error_messages.get(error, 'An error occurred')}", cls="text-error"),
            cls="alert alert-error max-w-md mx-auto mb-4"
        ) if error else None),
        
        # Registration Form
        Card(
            Form(
                # Email
                Div(
                    Label("Email", cls="label"),
                    Input(
                        type="email",
                        name="email",
                        placeholder="your@email.com",
                        required=True,
                        cls="input input-bordered w-full"
                    ),
                    cls="form-control mb-4"
                ),
                
                # Password
                Div(
                    Label("Password", cls="label"),
                    Input(
                        type="password",
                        name="password",
                        placeholder="••••••••",
                        required=True,
                        minlength="8",
                        cls="input input-bordered w-full"
                    ),
                    P("Minimum 8 characters", cls="text-sm text-gray-500 mt-1"),
                    cls="form-control mb-4"
                ),
                
                # Confirm Password
                Div(
                    Label("Confirm Password", cls="label"),
                    Input(
                        type="password",
                        name="confirm_password",
                        placeholder="••••••••",
                        required=True,
                        cls="input input-bordered w-full"
                    ),
                    cls="form-control mb-4"
                ),
                
                # Hidden role field (always "user" for E-Shop)
                Input(type="hidden", name="role", value="user"),
                
                # Submit
                Button(
                    "Create Account",
                    type="submit",
                    cls="btn btn-primary w-full btn-lg"
                ),
                
                # Login link
                Div(
                    Span("Already have an account? ", cls="text-gray-500"),
                    A("Sign in", href=f"/eshop-example/login?redirect={base_path}", cls="link link-primary"),
                    cls="text-center mt-4"
                ),
                
                method="post",
                action=f"{base_path}/auth/register?redirect={base_path}"
            ),
            cls="max-w-md mx-auto p-8"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
