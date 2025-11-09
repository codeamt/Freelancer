from fastapi import APIRouter, Request
from app.core.ui.layout import Layout
from app.core.ui.pages import HomePage, AboutPage, ContactPage

router_main = APIRouter(tags=["main"])

@router_main.get("/")
async def home_page():
    content = HomePage()
    return Layout(content, title="Home | FastApp")

@router_main.get("/about")
async def about_page():
    content = AboutPage()
    return Layout(content, title="About | FastApp")

@router_main.get("/contact")
async def contact_page():
    content = ContactPage()
    return Layout(content, title="Contact | FastApp")
