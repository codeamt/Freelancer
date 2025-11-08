# UI Components with FastHTML
from fasthtml.common import *
from app.core.ui.theme.context import ThemeContext
from starlette.responses import HTMLResponse

# Initialize theme context (for unified styles)
theme_context = ThemeContext()

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def style_merge(base: str, custom: str = "") -> str:
    return f"{base};{custom}" if custom else base

def themed_color(key: str) -> str:
    return theme_context.tokens["color"].get(key, "#000000")

# -----------------------------------------------------------------------------
# HTMX Helpers
# -----------------------------------------------------------------------------

def HTMXRefresh(url: str, target_id: str, interval: int = 5000):
    return Script(f"setInterval(()=>htmx.ajax('GET','{url}',{{target:'#{target_id}',swap:'innerHTML'}}), {interval});")

def ToastAutoHide(timeout: int = 4000):
    return Script(f"setTimeout(()=>{{document.querySelectorAll('.animate-fade-in').forEach(t=>t.remove())}}, {timeout});")


# ------------------------------------------------------------------------------
# Layout Primitives
# ------------------------------------------------------------------------------

def Container(content, max_width="1200px", padding="2rem"):
    return Div(
        content,
        style=f"max-width:{max_width};margin:auto;padding:{padding};display:flex;flex-direction:column;gap:2rem;"
    )

def Section(content, background: str = None, padding="4rem 0"):
    bg = background or themed_color("surface")
    return Div(
        content,
        style=f"background:{bg};padding:{padding};display:flex;flex-direction:column;align-items:center;gap:2rem;"
    )

def Card(content, title: str = None, width="300px", height="auto"):
    return Div(
        [
            Text(title, style=f"font-weight:700;font-size:1.25rem;color:{themed_color('text')};margin-bottom:0.5rem;") if title else None,
            Div(content),
        ],
        style=f"background:{themed_color('surface')};box-shadow:{theme_context.aesthetic.get('shadow')};border-radius:{theme_context.aesthetic.get('radius')};{theme_context.aesthetic.get('border')};padding:1.5rem;width:{width};height:{height};display:flex;flex-direction:column;gap:1rem;justify-content:flex-start;",
    )

def CardGrid(cards: list, columns: int = 3):
    return Div(
        cards,
        style=f"display:grid;grid-template-columns:repeat({columns},1fr);gap:1.5rem;width:100%;max-width:1200px;margin:auto;"
    )

# ------------------------------------------------------------------------------
# Navigation Components
# ------------------------------------------------------------------------------

def NavBar(links: list, logo_text: str = "FastApp", sticky: bool = True):
    position = "sticky;top:0;z-index:1000;" if sticky else ""
    nav_links = [
        Link(text, href=url, style=f"color:{themed_color('text')};text-decoration:none;font-weight:500;margin:0 1rem;")
        for text, url in links
    ]
    return Div(
        [
            Text(logo_text, style=f"font-size:1.5rem;font-weight:700;color:{themed_color('primary')};"),
            Div(nav_links, style="display:flex;align-items:center;gap:1rem;"),
            Div([ToggleThemeButton(), AestheticSwitcher()], style="display:flex;align-items:center;gap:0.5rem;")
        ],
        style=f"display:flex;justify-content:space-between;align-items:center;padding:1rem 2rem;background:{themed_color('surface')};box-shadow:{theme_context.aesthetic.get('shadow')};{position}"
    )

def SideBar(links: list, title: str = "Menu"):
    items = [
        Link(text, href=url, style=f"display:block;padding:0.75rem 1rem;color:{themed_color('text')};text-decoration:none;border-radius:{theme_context.tokens['radius']['sm']};transition:{theme_context.tokens['motion']['hover']};")
        for text, url in links
    ]
    return Div(
        [
            Text(title, style=f"font-weight:700;color:{themed_color('primary')};margin-bottom:1rem;"),
            Div(items, style="display:flex;flex-direction:column;gap:0.25rem;"),
        ],
        style=f"background:{themed_color('surface')};padding:1rem;width:220px;box-shadow:{theme_context.aesthetic.get('shadow')};border-radius:{theme_context.aesthetic.get('radius')};{theme_context.aesthetic.get('border')};height:100%;overflow-y:auto;"
    )

def Footer(text: str = "© 2025 FastApp. All rights reserved.", links: list = None):
    footer_links = [
        Link(t, href=u, style=f"color:{themed_color('muted')};margin:0 0.5rem;text-decoration:none;") for t, u in (links or [])
    ]
    return Div(
        [
            Text(text, style=f"color:{themed_color('muted')};font-size:0.9rem;"),
            Div(footer_links, style="display:flex;gap:0.5rem;"),
        ],
        style=f"display:flex;flex-direction:column;align-items:center;gap:0.5rem;padding:2rem;background:{themed_color('surface')};margin-top:2rem;border-top:1px solid {themed_color('accent')};"
    )

# ------------------------------------------------------------------------------
# Aesthetic Switcher (HTMX-powered)
# ------------------------------------------------------------------------------

def ToggleThemeButton():
    base_style = f"background:{themed_color('surface')};border:1px solid {themed_color('accent')};padding:8px 16px;border-radius:{theme_context.aesthetic['radius']};cursor:pointer;transition:{theme_context.tokens['motion']['hover']};"
    return Button(
        "Toggle Theme",
        id="theme-toggle",
        hx_get="/theme/switch-mode",
        hx_swap="outerHTML",
        style=style_merge(base_style, "font-weight:600;"),
    )

def AestheticSwitcher():
    modes = ["soft", "flat", "rough", "glass"]
    buttons = []
    for mode in modes:
        btn_style = (
            f"padding:6px 12px;border-radius:{theme_context.aesthetic['radius']};"
            f"border:1px solid {themed_color('accent')};background:{themed_color('surface')};"
            f"color:{themed_color('text')};cursor:pointer;font-size:0.9rem;"
            f"transition:{theme_context.tokens['motion']['hover']};"
        )
        buttons.append(
            Button(
                mode.capitalize(),
                hx_get=f"/theme/aesthetic/{mode}",
                hx_swap="none",
                style=btn_style,
            )
        )
    return Div(buttons, style="display:flex;align-items:center;gap:0.25rem;")

# ------------------------------------------------------------------------------
# Core UI Components
# ------------------------------------------------------------------------------

def SearchBar(action: str = "/search", placeholder: str = "Search..."):
    return Div(
        [
            Input(
                type="text",
                name="q",
                placeholder=placeholder,
                style=f"flex:1;padding:0.75rem;border:1px solid {themed_color('accent')};border-radius:{theme_context.aesthetic['radius']};font-family:{theme_context.tokens['font']['family']};",
            ),
            Button(
                Icon("search"),
                type="submit",
                style=f"background:{themed_color('primary')};color:white;padding:0.75rem;border:none;border-radius:{theme_context.aesthetic['radius']};cursor:pointer;margin-left:0.5rem;",
            ),
        ],
        style="display:flex;align-items:center;max-width:500px;margin:auto;",
        hx_post=action,
        hx_target="#results",
    )

def NotificationToast(message: str):
    return Div(
        Span(message, cls="block"),
        cls="fixed bottom-4 right-4 bg-primary text-white p-3 rounded-xl shadow-lg animate-fade-in"
    )

def CTAButton(label: str, href: str = "#"):
    return A(label, href=href, cls="mui-btn mui-btn-primary rounded-2xl px-6 py-3 shadow-md")

def AnalyticsWidget(metrics: dict):
    if not metrics:
        return Div(
            P("No metrics available yet.", cls="text-gray-500 italic"),
            cls="p-6 border rounded bg-white text-center"
        )
    
    metric_items = []
    for k, v in metrics.items():
        # Format the value based on its type
        if isinstance(v, float):
            formatted_value = f"{v:.2f}"
        else:
            formatted_value = str(v)
        
        metric_items.append(
            Div(
                Div(k, cls="font-medium text-gray-700"),
                Div(formatted_value, cls="text-2xl font-bold text-blue-600"),
                cls="p-4 border rounded bg-white hover:shadow-md transition-shadow"
            )
        )
    
    return Div(
        H2("Analytics Summary", cls="text-xl font-bold mb-4"),
        Div(
            *metric_items,
            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        ),
        cls="p-6 border rounded bg-gray-50"
    )

def MediaCard(title: str, url: str):
    return Div(
        Img(src=url, alt=title, cls="rounded-xl mb-2"),
        P(title, cls="text-sm text-center"),
        cls="p-2 hover:opacity-90"
    )


def MediaGallery(media_items: list):
    return Section(
        H1("Media Library", cls="text-2xl font-semibold mb-4"),
        Div(*[MediaCard(m['title'], m['url']) for m in media_items], cls="grid grid-cols-2 md:grid-cols-4 gap-4")
    )

