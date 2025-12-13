from fasthtml.common import *
from core.ui.layout import Layout
from core.ui.pages import HomePage, AboutPage, ContactPage, ExamplePage, TestPage, DocsPage
from core.services.auth.helpers import get_current_user

router_main = APIRouter()


@router_main.get("/")
async def home_page(request: Request):
    demo = getattr(request.app.state, 'demo', False)
    auth_service = request.app.state.auth_service
    user = await get_current_user(request, auth_service)
    content = HomePage()
    return Layout(content, title="Home | FastApp", current_path="/", user=user, demo=demo)

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
