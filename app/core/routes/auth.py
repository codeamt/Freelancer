"""Auth Routes"""
from fasthtml.common import *
from starlette.responses import RedirectResponse
from core.services.auth import require_auth, require_role
from core.services.auth.utils import get_current_user_from_request

router_auth = APIRouter()

@router_auth.get("/login")
async def login_page(request: Request):
    """Login page"""
    return Html(
        Head(Title("Login")),
        Body(
            Form(
                Input(name="email", type="email", placeholder="Email", required=True),
                Input(name="password", type="password", placeholder="Password", required=True),
                Button("Login", type="submit"),
                method="post",
                action="/auth/login"
            )
        )
    )

@router_auth.post("/auth/login")
async def login(request: Request):
    """Handle login"""
    auth_service = request.app.state.auth_service
    
    form = await request.form()
    email = form.get("email")
    password = form.get("password")
    
    result = await auth_service.login(email, password)
    
    if result:
        response = RedirectResponse("/dashboard", status_code=303)
        response.set_cookie(
            "auth_token",
            result["token"],
            httponly=True,
            secure=os.getenv("ENVIRONMENT") == "production",
            samesite="lax",
            max_age=86400  # 24 hours
        )
        return response
    
    # Login failed
    return login_page(request, error="Invalid credentials")

@router_auth.post("/auth/logout")
@require_auth()
async def logout(request: Request):
    """Handle logout"""
    auth_service = request.app.state.auth_service
    
    token = request.cookies.get("auth_token")
    if token:
        await auth_service.logout(token)
    
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("auth_token")
    return response

@router_auth.get("/dashboard")
@require_auth()
async def dashboard(request: Request):
    """Protected dashboard"""
    user = request.state.user  # Injected by @require_auth
    
    return Html(
        Head(Title("Dashboard")),
        Body(
            H1(f"Welcome, {user.email}!"),
            P(f"Role: {user.role}")
        )
    )

@router_auth.get("/admin")
@require_role("admin")
async def admin_panel(request: Request):
    """Admin-only route"""
    user = request.state.user
    user_service = request.app.state.user_service
    
    # List all users
    users_data = await user_service.list_users()
    
    return Html(
        Head(Title("Admin Panel")),
        Body(
            H1("Admin Panel"),
            Ul(*[Li(f"{u.email} - {u.role}") for u in users_data["users"]])
        )
    )