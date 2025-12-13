"""
Social Network Example Application

Social networking features with authentication.
"""
from fasthtml.common import *
from monsterui.all import *
import os
from core.ui.layout import Layout
from core.utils.logger import get_logger

logger = get_logger(__name__)


def create_social_app(auth_service=None, user_service=None, postgres=None, mongodb=None, redis=None, demo=False):
    """
    Create and configure the social network example app
    
    Args:
        auth_service: Injected authentication service
        user_service: Injected user management service
        postgres: PostgreSQL adapter (optional)
        mongodb: MongoDB adapter (optional)
        redis: Redis adapter (optional)
        demo: Whether to run in demo mode (uses mock data, limited features)
    """
    from core.services.auth.helpers import get_current_user
    from core.services.auth.context import set_user_context
    from core.services.auth.context import create_user_context
    
    logger.info(f"Initializing Social example app (demo={demo})...")
    
    app = FastHTML(hdrs=[*Theme.slate.headers()])
    
    # Store demo flag in app state
    app.state.demo = demo
    
    # Base path
    BASE = "/social-example"
    
    async def get_user_with_context(request: Request):
        """Get current user from request and set context."""
        user = await get_current_user(request, auth_service)
        if user:
            # Set user context for state system using factory
            class SimpleUser:
                def __init__(self, user_dict):
                    self.id = user_dict.get("id") or int(user_dict.get("_id", 0))
                    self.role = user_dict.get("role", "user")
                    self.email = user_dict.get("email", "")
            
            user_obj = SimpleUser(user)
            user_context = create_user_context(user_obj, request)
            set_user_context(user_context)
        return user
    
    @app.get("/")
    async def social_home(request: Request):
        """Social network coming soon page"""
        user = await get_user_with_context(request)
        
        content = Div(
            # Hero Section
            Div(
                Div(
                    # Icon
                    Div(
                        UkIcon("users", width="120", height="120", cls="text-blue-500 mb-8"),
                        cls="flex justify-center"
                    ),
                    
                    # Title
                    H1("🌐 Social Network", cls="text-5xl font-bold mb-4 text-center"),
                    P("Connect, Share, Engage", cls="text-2xl text-gray-500 mb-8 text-center"),
                    
                    # Coming Soon Badge
                    Div(
                        Span("🚧 Demo Coming Soon", cls="badge badge-lg badge-warning text-lg px-6 py-4"),
                        cls="flex justify-center mb-12"
                    ),
                    
                    # Features Preview
                    Div(
                        H2("Planned Features", cls="text-3xl font-bold mb-8 text-center"),
                        Div(
                            FeatureCard("👤", "User Profiles", "Customizable profiles with photos, bio, and interests"),
                            FeatureCard("📝", "Posts & Feed", "Share updates, photos, and videos with your network"),
                            FeatureCard("💬", "Messaging", "Real-time chat and direct messaging"),
                            FeatureCard("👥", "Connections", "Follow users and build your network"),
                            FeatureCard("❤️", "Interactions", "Like, comment, and share content"),
                            FeatureCard("🔔", "Notifications", "Stay updated with real-time notifications"),
                            FeatureCard("🔒", "Privacy Controls", "Manage who sees your content"),
                            FeatureCard("📊", "Analytics", "Track engagement and reach"),
                            FeatureCard("🎯", "Groups & Communities", "Create and join interest-based groups"),
                            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
                        ),
                    ),
                    
                    # Tech Stack
                    Div(
                        H3("Tech Stack", cls="text-2xl font-bold mb-6 text-center"),
                        Div(
                            TechBadge("FastHTML", "Web Framework"),
                            TechBadge("WebSockets", "Real-time Chat"),
                            TechBadge("MongoDB", "User Data & Posts"),
                            TechBadge("Redis", "Caching & Sessions"),
                            TechBadge("S3", "Media Storage"),
                            TechBadge("MonsterUI", "UI Components"),
                            cls="flex flex-wrap justify-center gap-3 mb-12"
                        ),
                    ),
                    
                    # CTA
                    Div(
                        A("← Back to Home", href="/", cls="btn btn-primary btn-lg mr-4"),
                        A("View Other Examples", href="#examples", cls="btn btn-outline btn-lg"),
                        cls="flex justify-center gap-4 mb-8"
                    ),
                    
                    # Example Sections
                    Div(
                        H3("Example Use Cases", cls="text-2xl font-bold mb-6 text-center", id="examples"),
                        Div(
                            UseCaseCard(
                                "Professional Network",
                                "LinkedIn-style platform for professionals",
                                ["Job postings", "Skills endorsements", "Company pages", "Professional messaging"]
                            ),
                            UseCaseCard(
                                "Community Platform",
                                "Facebook-style social network",
                                ["Personal profiles", "Photo albums", "Events", "Groups & pages"]
                            ),
                            UseCaseCard(
                                "Niche Social Network",
                                "Specialized community (e.g., artists, gamers, fitness)",
                                ["Interest-based feeds", "Portfolio sharing", "Challenges", "Leaderboards"]
                            ),
                            cls="grid grid-cols-1 md:grid-cols-3 gap-6"
                        ),
                    ),
                    
                    cls="max-w-6xl mx-auto"
                ),
                cls="py-16"
            )
        )
        
        return Layout(content, title="Social Network Example | FastApp", current_path=f"{BASE}/", user=user, show_auth=True, demo=demo)
    
    # ========================================================================
    # Auth Pages
    # ========================================================================
    
    def SocialLoginPage(error: str = None):
        """Simple login page for social app"""
        return Layout(
            Div(
                Card(
                    Div(
                        H1("Sign In", cls="text-3xl font-bold mb-6 text-center"),
                        P("Welcome back to Social Network", cls="text-gray-500 mb-8 text-center"),
                        (Div(P(error, cls="text-error"), cls="alert alert-error mb-4") if error else None),
                        Form(
                            Div(Label("Email", cls="label"), Input(type="email", name="email", placeholder="you@example.com", cls="input input-bordered w-full", required=True), cls="form-control mb-4"),
                            Div(Label("Password", cls="label"), Input(type="password", name="password", placeholder="••••••••", cls="input input-bordered w-full", required=True), cls="form-control mb-6"),
                            Button("Sign In", type="submit", cls="btn btn-primary w-full mb-4"),
                            Div(P("Don't have an account? ", A("Sign up", href="register", cls="link link-primary")), cls="text-center"),
                            action="/auth/login", method="post"
                        ),
                        cls="p-8"
                    ),
                    cls="max-w-md mx-auto"
                ),
                cls="container mx-auto px-4 py-16"
            ),
            title="Sign In | Social Network", show_auth=False, demo=demo
        )
    
    def SocialRegisterPage(error: str = None):
        """Simple register page for social app"""
        return Layout(
            Div(
                Card(
                    Div(
                        H1("Create Account", cls="text-3xl font-bold mb-6 text-center"),
                        P("Join the Social Network community", cls="text-gray-500 mb-8 text-center"),
                        (Div(P(error, cls="text-error"), cls="alert alert-error mb-4") if error else None),
                        Form(
                            Div(Label("Email", cls="label"), Input(type="email", name="email", placeholder="you@example.com", cls="input input-bordered w-full", required=True), cls="form-control mb-4"),
                            Div(Label("Password", cls="label"), Input(type="password", name="password", placeholder="••••••••", cls="input input-bordered w-full", required=True), P("Must be 8+ chars with uppercase, lowercase, and number", cls="text-xs text-gray-500 mt-1"), cls="form-control mb-6"),
                            Button("Create Account", type="submit", cls="btn btn-primary w-full mb-4"),
                            Div(P("Already have an account? ", A("Sign in", href="login", cls="link link-primary")), cls="text-center"),
                            action="/auth/register", method="post"
                        ),
                        cls="p-8"
                    ),
                    cls="max-w-md mx-auto"
                ),
                cls="container mx-auto px-4 py-16"
            ),
            title="Create Account | Social Network", show_auth=False, demo=demo
        )
    
    # ========================================================================
    # Auth Routes
    # ========================================================================
    
    @app.get("/login")
    async def login_page(request: Request):
        return SocialLoginPage()
    
    @app.get("/register")
    async def register_page(request: Request):
        return SocialRegisterPage()
    
    @app.post("/auth/login")
    async def login(request: Request):
        form = getattr(request.state, 'sanitized_form', None) or await request.form()
        email, password = form.get("email"), form.get("password")
        if not email or not password:
            return SocialLoginPage(error="Email and password are required")
        from core.services.auth.models import LoginRequest
        try:
            result = await auth_service.login(LoginRequest(username=email, password=password))
            if result:
                response = RedirectResponse(f"{BASE}/", status_code=303)
                response.set_cookie("auth_token", result.access_token, httponly=True, secure=os.getenv("ENVIRONMENT") == "production", samesite="lax", max_age=result.expires_in)
                return response
        except Exception as e:
            logger.error(f"Login failed: {e}")
        return SocialLoginPage(error="Invalid credentials")
    
    @app.post("/auth/register")
    async def register(request: Request):
        form = getattr(request.state, 'sanitized_form', None) or await request.form()
        email, password = form.get("email"), form.get("password")
        if not email or not password:
            return SocialRegisterPage(error="Email and password are required")
        try:
            user_id = await user_service.register(email, password)
            if not user_id:
                return SocialRegisterPage(error="Registration failed")
            from core.services.auth.models import LoginRequest
            result = await auth_service.login(LoginRequest(username=email, password=password))
            if result:
                response = RedirectResponse(f"{BASE}/", status_code=303)
                response.set_cookie("auth_token", result.access_token, httponly=True, secure=os.getenv("ENVIRONMENT") == "production", samesite="lax", max_age=result.expires_in)
                return response
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return SocialRegisterPage(error=str(e))
        return SocialRegisterPage(error="Registration failed")
    
    @app.post("/auth/logout")
    async def logout(request: Request):
        token = request.cookies.get("auth_token")
        if token:
            try:
                await auth_service.logout(token)
            except:
                pass
        response = RedirectResponse(f"{BASE}/", status_code=303)
        response.delete_cookie("auth_token")
        return response
    
    # ========================================================================
    # Helper Components
    # ========================================================================
    
    def FeatureCard(icon: str, title: str, description: str):
        """Feature card component"""
        return Card(
            Div(
                Div(icon, cls="text-4xl mb-3 text-center"),
                H3(title, cls="text-lg font-semibold mb-2 text-center"),
                P(description, cls="text-sm text-gray-500 text-center"),
                cls="p-6"
            ),
            cls="hover:shadow-lg transition-shadow"
        )
    
    def TechBadge(name: str, description: str):
        """Technology badge"""
        return Div(
            Span(name, cls="font-semibold"),
            Span(f" - {description}", cls="text-sm text-gray-500"),
            cls="badge badge-lg badge-outline"
        )
    
    def UseCaseCard(title: str, description: str, features: list):
        """Use case card"""
        return Card(
            Div(
                H4(title, cls="text-xl font-bold mb-3"),
                P(description, cls="text-gray-600 mb-4"),
                Ul(
                    *[Li(
                        UkIcon("check", width="16", height="16", cls="inline mr-2 text-green-500"),
                        feature,
                        cls="text-sm mb-2"
                    ) for feature in features],
                    cls="space-y-1"
                ),
                cls="p-6"
            ),
            cls="hover:shadow-lg transition-shadow"
        )
    
    return app
