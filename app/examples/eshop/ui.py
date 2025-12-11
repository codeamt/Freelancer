"""E-Shop Specific Auth UI - Simple user registration"""
from fasthtml.common import *
from monsterui.all import *


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
                action=f"{base_path}/auth/login?redirect={base_pathl}"
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
