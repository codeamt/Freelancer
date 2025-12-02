from fasthtml.common import *
from core.ui.layout import Layout
from core.ui.pages import HomePage, AboutPage, ContactPage, ExamplePage, TestPage, DocsPage

router_main = APIRouter()


@router_main.get("/")
def home_page():
    content = HomePage()
    return Layout(content, title="Home | FastApp")

@router_main.get("/docs")
def docs_page():
    """Documentation page"""
    content = DocsPage()
    return Layout(content, title="Documentation | FastApp")

@router_main.get("/test")
def test_page():
    """Test page for MonsterUI components"""
    content = TestPage()
    return Layout(content, title="MonsterUI Test | FastApp")
    
@router_main.get("/about")
def about_page():
    content = AboutPage()
    return Layout(content, title="About | FastApp")
    
@router_main.get("/contact")
def contact_page():
    content = ContactPage()
    return Layout(content, title="Contact | FastApp")
    
@router_main.get("/example")
def example_landing_page():
        """Example landing page demonstrating Phase 1 components"""
        content = ExamplePage()
        return Layout(content, title="Summer Doodle Camp 2026 | Doodle Institute")
