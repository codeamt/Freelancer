"""Auth Routes"""
from fasthtml.common import *
from monsterui.all import *
from starlette.responses import RedirectResponse
import json
from core.services.auth.decorators import require_auth
from core.services.admin.decorators import require_role
from core.services.auth.helpers import get_current_user_from_request, get_current_user
from core.ui.layout import Layout
from core.ui.pages import AuthPage, AuthTabContent, WebAdminAuthPage, WebAdminDashboard
import os

router_auth = APIRouter()

@router_auth.get("/auth")
async def auth_page(request: Request, tab: str = "login", redirect: str = None, error: str = None, success: str = None):
    """Unified auth page with tabs for login/register"""
    demo = getattr(request.app.state, 'demo', False)
    
    # Create custom navbar with Web Admin button
    nav_items = [
        A("Home", href='/'),
        A(
            UkIcon("shield", cls="mr-1"),
            "Web Admin",
            href='/admin/login',
            cls="flex items-center gap-1 btn btn-ghost btn-sm"
        ),
    ]
    
    content = AuthPage(
        error=error,
        success=success,
        default_tab=tab,
        show_role_selector=True,
        redirect_url=redirect
    )
    
    # Use custom layout with simplified nav
    return (
        Title("Sign In | FastApp"),
        NavBar(*nav_items, brand=H3('FastApp')),
        content,
        Footer(
            Div(
                P("© 2025 FastApp. Built with FastHTML + MonsterUI.", cls=TextT.muted),
                cls="text-center py-4"
            ),
            cls="fixed bottom-0 left-0 right-0 border-t bg-base-100 z-10"
        )
    )

@router_auth.get("/auth/page")
async def auth_tab_content(request: Request, tab: str = "login", redirect: str = None):
    """Return just the tab content for HTMX swapping"""
    return AuthTabContent(tab=tab, redirect_url=redirect, show_role_selector=True)

@router_auth.get("/login")
async def login_redirect(request: Request, redirect: str = None):
    """Redirect old login route to new unified auth page"""
    redirect_url = f"/auth?tab=login" + (f"&redirect={redirect}" if redirect else "")
    return RedirectResponse(redirect_url, status_code=303)

@router_auth.get("/register")
async def register_redirect(request: Request, redirect: str = None):
    """Redirect old register route to new unified auth page"""
    redirect_url = f"/auth?tab=register" + (f"&redirect={redirect}" if redirect else "")
    return RedirectResponse(redirect_url, status_code=303)

@router_auth.post("/auth/login")
async def login(request: Request):
    """Handle login with device tracking"""
    auth_service = request.app.state.auth_service
    
    # Use sanitized form data from security middleware
    form = getattr(request.state, 'sanitized_form', {})
    email = form.get("email")
    password = form.get("password")
    remember_me = form.get("remember_me") == "on"
    redirect_url = form.get("redirect") or "/"
    
    from core.services.auth.auth_service import LoginRequest
    try:
        # Get device info
        user_agent = request.headers.get("User-Agent", "")
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        # Try device-aware login first
        if hasattr(auth_service, 'login_with_device'):
            login_result = await auth_service.login_with_device(
                LoginRequest(username=email, password=password),
                user_agent=user_agent,
                ip_address=client_ip,
                remember_me=remember_me
            )
            
            if login_result and login_result.get("access_token"):
                response = RedirectResponse(redirect_url, status_code=303)
                response.set_cookie(
                    "auth_token",
                    login_result["access_token"],
                    httponly=True,
                    secure=os.getenv("ENVIRONMENT") == "production",
                    samesite="lax",
                    max_age=86400  # 24 hours
                )
                
                # Set refresh token cookie if available
                if login_result.get("refresh_token"):
                    response.set_cookie(
                        "refresh_token",
                        login_result["refresh_token"],
                        httponly=True,
                        secure=os.getenv("ENVIRONMENT") == "production",
                        samesite="lax",
                        max_age=86400 * 30  # 30 days
                    )
                
                return response
        else:
            # Fallback to regular login
            result = await auth_service.login(LoginRequest(username=email, password=password))
            
            if result:
                response = RedirectResponse(redirect_url, status_code=303)
                response.set_cookie(
                    "auth_token",
                    result.access_token,
                    httponly=True,
                    secure=os.getenv("ENVIRONMENT") == "production",
                    samesite="lax",
                    max_age=86400  # 24 hours
                )
                return response
                
    except Exception as e:
        logger.error(f"Login error: {e}")
        pass
    
    # Login failed - redirect back to auth page with error
    return RedirectResponse(f"/auth?tab=login&error=Invalid+credentials" + (f"&redirect={redirect_url}" if redirect_url != "/" else ""), status_code=303)

@router_auth.post("/auth/register")
async def register(request: Request):
    """Handle registration"""
    user_service = request.app.state.user_service
    auth_service = request.app.state.auth_service
    
    # Use sanitized form data from security middleware
    form = getattr(request.state, 'sanitized_form', {})
    email = form.get("email")
    password = form.get("password")
    confirm_password = form.get("confirm_password")
    role = form.get("role") or "user"
    redirect_url = form.get("redirect") or "/"
    
    # Validate required fields
    if not email or not password:
        return RedirectResponse(f"/auth?tab=register&error=Email+and+password+are+required" + (f"&redirect={redirect_url}" if redirect_url != "/" else ""), status_code=303)
    
    # Validate passwords match
    if password != confirm_password:
        return RedirectResponse(f"/auth?tab=register&error=Passwords+do+not+match" + (f"&redirect={redirect_url}" if redirect_url != "/" else ""), status_code=303)
    
    try:
        # Create user with selected role (using create_user instead of register to support custom roles)
        user_id = await user_service.create_user(
            email=email,
            password=password,
            role=role,
            profile_data=None
        )
        
        if not user_id:
            return RedirectResponse(f"/auth?tab=register&error=Registration+failed" + (f"&redirect={redirect_url}" if redirect_url != "/" else ""), status_code=303)
        
        # Auto-login after registration
        from core.services.auth.auth_service import LoginRequest
        result = await auth_service.login(LoginRequest(username=email, password=password))
        
        if result:
            response = RedirectResponse(redirect_url, status_code=303)
            response.set_cookie(
                "auth_token",
                result.access_token,
                httponly=True,
                secure=os.getenv("ENVIRONMENT") == "production",
                samesite="lax",
                max_age=86400
            )
            return response
        else:
            # Registration succeeded but login failed - redirect to login tab
            return RedirectResponse(f"/auth?tab=login&success=Account+created+successfully" + (f"&redirect={redirect_url}" if redirect_url != "/" else ""), status_code=303)
            
    except Exception as e:
        error_msg = str(e).replace(" ", "+")
        return RedirectResponse(f"/auth?tab=register&error={error_msg}" + (f"&redirect={redirect_url}" if redirect_url != "/" else ""), status_code=303)

@router_auth.post("/auth/logout")
async def logout(request: Request):
    """Handle logout"""
    auth_service = request.app.state.auth_service
    
    token = request.cookies.get("auth_token")
    if token:
        try:
            await auth_service.logout(token)
        except:
            pass  # Ignore errors if token is invalid
    
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


# =============================================================================
# Web Admin Routes
# =============================================================================

@router_auth.get("/admin/login")
async def web_admin_login_page(request: Request, error: str = None, success: str = None):
    """Web Admin login page - separate from regular user auth"""
    demo = getattr(request.app.state, 'demo', False)
    
    content = WebAdminAuthPage(error=error, success=success)
    
    return (
        Title("Web Admin Login | FastApp"),
        NavBar(
            A("Home", href='/'),
            A("User Login", href='/auth'),
            brand=H3('FastApp Admin')
        ),
        content,
        Footer(
            Div(
                P("© 2025 FastApp. Web Admin Portal.", cls=TextT.muted),
                cls="text-center py-4"
            ),
            cls="fixed bottom-0 left-0 right-0 border-t bg-base-100 z-10"
        )
    )


@router_auth.post("/admin/auth/login")
async def web_admin_login(request: Request):
    """Handle Web Admin login - validates admin role"""
    auth_service = request.app.state.auth_service
    
    # Try sanitized form first (from security middleware), fallback to raw form
    form = getattr(request.state, 'sanitized_form', None) or await request.form()
    email = form.get("email")
    password = form.get("password")
    redirect_url = form.get("redirect") or "/admin/dashboard"
    
    if not email or not password:
        return RedirectResponse("/admin/login?error=Email+and+password+required", status_code=303)
    
    try:
        from core.services.auth.auth_service import LoginRequest
        result = await auth_service.login(LoginRequest(username=email, password=password))
        
        if result:
            # Verify user has admin role
            user = await auth_service.get_current_user(result.access_token)
            if user:
                user_role = user.get("role", "user") if isinstance(user, dict) else getattr(user, "role", "user")
                if user_role in ["admin", "super_admin"]:
                    response = RedirectResponse(redirect_url, status_code=303)
                    response.set_cookie(
                        "auth_token",
                        result.access_token,
                        httponly=True,
                        secure=os.getenv("ENVIRONMENT") == "production",
                        samesite="lax",
                        max_age=86400
                    )
                    return response
                else:
                    return RedirectResponse("/admin/login?error=Admin+access+required", status_code=303)
    except Exception as e:
        import logging
        logging.error(f"Admin login error: {e}")
    
    return RedirectResponse("/admin/login?error=Invalid+credentials", status_code=303)


@router_auth.get("/admin/dashboard")
async def web_admin_dashboard(request: Request):
    """Web Admin Dashboard with site/theme editor links"""
    demo = getattr(request.app.state, 'demo', False)
    auth_service = request.app.state.auth_service
    
    # Get current user from token
    user = await get_current_user_from_request(request, auth_service)
    if not user:
        return RedirectResponse("/admin/login?error=Please+login+first", status_code=303)
    
    # Check admin role
    user_role = user.get("role", "user") if isinstance(user, dict) else getattr(user, "role", "user")
    if user_role not in ["admin", "super_admin"]:
        return RedirectResponse("/admin/login?error=Admin+access+required", status_code=303)
    
    # Convert user to dict if needed
    user_dict = user if isinstance(user, dict) else {
        "email": getattr(user, "email", "Admin"),
        "role": getattr(user, "role", "admin"),
        "_id": getattr(user, "id", None)
    }
    
    # Get metrics (placeholder - would come from analytics service)
    metrics = {
        "total_users": 0,
        "active_sessions": 0,
        "page_views_today": 0,
        "pending_updates": 0
    }
    
    # Try to get real user count
    try:
        user_service = request.app.state.user_service
        users_data = await user_service.list_users()
        metrics["total_users"] = users_data.get("total", 0)
    except:
        pass
    
    content = WebAdminDashboard(user_dict, metrics)
    
    return Layout(
        content,
        title="Web Admin Dashboard | FastApp",
        user=user_dict,
        show_auth=True,
        demo=demo
    )


# Refresh Token Endpoints

@router_auth.post("/auth/refresh")
async def refresh_token(request: Request):
    """Refresh access token using refresh token"""
    auth_service = request.app.state.auth_service
    
    # Get refresh token from request body
    try:
        import json
        body = json.loads(await request.body())
        refresh_token = body.get("refresh_token")
    except:
        # Fallback to form data
        form = getattr(request.state, 'sanitized_form', {})
        refresh_token = form.get("refresh_token")
    
    if not refresh_token:
        return Response(
            json.dumps({"error": "Refresh token required"}),
            status_code=400,
            media_type="application/json"
        )
    
    # Validate refresh token and get new access token
    result = await auth_service.refresh_token(refresh_token)
    
    if not result:
        return Response(
            json.dumps({"error": "Invalid or expired refresh token"}),
            status_code=401,
            media_type="application/json"
        )
    
    return Response(
        json.dumps({
            "access_token": result["access_token"],
            "token_type": "Bearer"
        }),
        media_type="application/json"
    )


@router_auth.post("/auth/device/revoke")
async def revoke_device(request: Request):
    """Revoke all tokens for a specific device"""
    auth_service = request.app.state.auth_service
    current_user = await get_current_user(request)
    
    if not current_user:
        return Response(
            json.dumps({"error": "Authentication required"}),
            status_code=401,
            media_type="application/json"
        )
    
    # Get device_id from request
    try:
        import json
        body = json.loads(await request.body())
        device_id = body.get("device_id")
    except:
        # Fallback to form data
        form = getattr(request.state, 'sanitized_form', {})
        device_id = form.get("device_id")
    
    if not device_id:
        return Response(
            json.dumps({"error": "Device ID required"}),
            status_code=400,
            media_type="application/json"
        )
    
    # Revoke device tokens
    success = await auth_service.revoke_device(current_user.id, device_id)
    
    if success:
        return Response(
            json.dumps({"success": True, "message": "Device revoked successfully"}),
            media_type="application/json"
        )
    else:
        return Response(
            json.dumps({"error": "Failed to revoke device"}),
            status_code=500,
            media_type="application/json"
        )


@router_auth.get("/auth/devices")
async def list_devices(request: Request):
    """List all devices for the current user"""
    auth_service = request.app.state.auth_service
    current_user = await get_current_user(request)
    
    if not current_user:
        return Response(
            json.dumps({"error": "Authentication required"}),
            status_code=401,
            media_type="application/json"
        )
    
    # Get user devices
    devices = await auth_service.get_user_devices(current_user.id)
    
    return Response(
        json.dumps({"devices": devices}),
        media_type="application/json"
    )


@router_auth.post("/auth/devices/{device_id}/trust")
async def trust_device(request: Request, device_id: str):
    """Mark a device as trusted"""
    auth_service = request.app.state.auth_service
    current_user = await get_current_user(request)
    
    if not current_user:
        return Response(
            json.dumps({"error": "Authentication required"}),
            status_code=401,
            media_type="application/json"
        )
    
    # Trust device
    success = await auth_service.trust_device(current_user.id, device_id)
    
    if success:
        return Response(
            json.dumps({"success": True, "message": "Device marked as trusted"}),
            media_type="application/json"
        )
    else:
        return Response(
            json.dumps({"error": "Failed to trust device"}),
            status_code=500,
            media_type="application/json"
        )


@router_auth.delete("/auth/devices/{device_id}/trust")
async def untrust_device(request: Request, device_id: str):
    """Unmark a device as trusted"""
    auth_service = request.app.state.auth_service
    current_user = await get_current_user(request)
    
    if not current_user:
        return Response(
            json.dumps({"error": "Authentication required"}),
            status_code=401,
            media_type="application/json"
        )
    
    # Untrust device
    success = await auth_service.untrust_device(current_user.id, device_id)
    
    if success:
        return Response(
            json.dumps({"success": True, "message": "Device unmarked as trusted"}),
            media_type="application/json"
        )
    else:
        return Response(
            json.dumps({"error": "Failed to untrust device"}),
            status_code=500,
            media_type="application/json"
        )


@router_auth.get("/auth/token/expiry")
async def check_token_expiry(request: Request):
    """Check if the current token is expiring soon"""
    auth_token = request.cookies.get("auth_token")
    
    if not auth_token:
        return Response(
            json.dumps({"error": "No token found"}),
            status_code=401,
            media_type="application/json"
        )
    
    # Check token expiration
    jwt_provider = auth_service.jwt if hasattr(auth_service, 'jwt') else JWTProvider()
    
    if jwt_provider.is_token_expiring_soon(auth_token, minutes_threshold=5):
        return Response(
            json.dumps({
                "expiring_soon": True,
                "message": "Token expires in less than 5 minutes"
            }),
            media_type="application/json"
        )
    
    # Get actual expiration time
    exp_time = jwt_provider.get_token_expiration(auth_token)
    
    return Response(
        json.dumps({
            "expiring_soon": False,
            "expires_at": exp_time.isoformat() if exp_time else None
        }),
        media_type="application/json"
    )