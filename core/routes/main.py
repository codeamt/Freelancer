from fasthtml.common import *
from core.ui.layout import Layout
from core.ui.pages import HomePage, AboutPage, ContactPage, ExamplePage, TestPage, DocsPage
from core.services.auth.helpers import get_current_user
from core.ui.components.role_based_components import RoleBasedDashboard, RoleBasedNav
from core.services.auth.role_hierarchy import RoleHierarchy
from core.ui.pages.role_ui_demo import RoleUIDemoPage

router_main = APIRouter()


@router_main.get("/")
async def home_page(request: Request):
    demo = getattr(request.app.state, 'demo', False)
    auth_service = request.app.state.auth_service
    user = await get_current_user(request, auth_service)
    home_page = HomePage()
    return home_page.render(request=request)

@router_main.get("/dashboard")
async def dashboard_page(request: Request):
    """Role-based dashboard that adapts to user roles"""
    auth_service = request.app.state.auth_service
    user = await get_current_user(request, auth_service)
    
    if not user:
        return RedirectResponse("/auth?redirect=/dashboard", status_code=303)
    
    user_roles = getattr(user, 'roles', [])
    
    return Title("Dashboard"), Main(
        Header(RoleBasedNav.render(user_roles)),
        Container(
            H1("Dashboard"),
            P(f"Welcome, {user.email}!"),
            RoleBasedDashboard.render(user_roles)
        )
    )

@router_main.get("/role-ui-demo")
async def role_ui_demo_page(request: Request):
    """Demo page showing role-based UI components"""
    demo_page = RoleUIDemoPage()
    return demo_page.render(request)

@router_main.get("/docs")
def docs_page(request: Request):
    """Documentation page"""
    demo = getattr(request.app.state, 'demo', False)
    content = DocsPage()
    return Layout(content, title="Documentation | FastApp", demo=demo)

@router_main.get("/test")
def test_page(request: Request):
    """Test page for MonsterUI components"""
    demo = getattr(request.app.state, 'demo', False)
    content = TestPage()
    return Layout(content, title="MonsterUI Test | FastApp", demo=demo)
    
@router_main.get("/about")
def about_page(request: Request):
    demo = getattr(request.app.state, 'demo', False)
    content = AboutPage()
    return Layout(content, title="About | FastApp", demo=demo)
    
@router_main.get("/contact")
def contact_page(request: Request):
    demo = getattr(request.app.state, 'demo', False)
    content = ContactPage()
    return Layout(content, title="Contact | FastApp", demo=demo)
    
@router_main.get("/example")
def example_landing_page(request: Request):
        """Example landing page demonstrating Phase 1 components"""
        demo = getattr(request.app.state, 'demo', False)
        content = ExamplePage()
        return Layout(content, title="Summer Doodle Camp 2026 | Doodle Institute", demo=demo)
