# UI Theme Routes for HTMX Interactions
from fastapi import APIRouter
from app.core.ui.theme.context import ThemeContext
from app.core.ui.theme.utils import ThemeUtils

# Use the singleton theme context instance
theme_context = ThemeContext()

router = APIRouter(prefix="/theme")

@router.get("/switch-mode")
async def switch_theme_mode():
    """Switch between light and dark mode"""
    return ThemeUtils.switch_theme_mode(theme_context)

@router.get("/aesthetic/{mode}")
async def switch_aesthetic_mode(mode: str):
    """Switch between different aesthetic modes (soft, flat, rough, glass)"""
    return ThemeUtils.switch_aesthetic_mode(theme_context, mode)

@router.get("/css")
async def get_theme_css():
    """Get the current theme CSS variables"""
    return ThemeUtils.get_css(theme_context)

@router.get("/preview")
async def preview_theme():
    """Preview the current theme colors"""
    return ThemeUtils.preview_theme(theme_context)
