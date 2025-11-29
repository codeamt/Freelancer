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


# ------------------------------------------------------------------------------
# Landing Page Components - Phase 1
# ------------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Hero Sections
# -----------------------------------------------------------------------------

def HeroSection(
    title: str,
    subtitle: str = None,
    tagline: str = None,
    cta_text: str = None,
    cta_link: str = "#",
    background_image: str = None,
    background_color: str = None,
    text_color: str = "#FFFFFF"
):
    """
    Full-width hero section with optional background image
    Perfect for landing page headers
    """
    bg_style = ""
    if background_image:
        bg_style = f"background-image:url('{background_image}');background-size:cover;background-position:center;"
    elif background_color:
        bg_style = f"background:{background_color};"
    else:
        bg_style = f"background:linear-gradient(135deg, {themed_color('primary')} 0%, {themed_color('secondary')} 100%);"
    
    content = [
        H1(title, style=f"font-size:3rem;font-weight:800;color:{text_color};margin-bottom:1rem;text-align:center;line-height:1.2;")
    ]
    
    if subtitle:
        content.append(
            H2(subtitle, style=f"font-size:1.5rem;font-weight:400;color:{text_color};margin-bottom:1rem;text-align:center;opacity:0.95;")
        )
    
    if tagline:
        content.append(
            P(tagline, style=f"font-size:1.1rem;color:{text_color};margin-bottom:2rem;text-align:center;opacity:0.9;")
        )
    
    if cta_text:
        content.append(
            Div(
                A(
                    cta_text,
                    href=cta_link,
                    style=f"background:{themed_color('accent')};color:#FFFFFF;padding:1rem 2.5rem;border-radius:50px;text-decoration:none;font-weight:700;font-size:1.2rem;display:inline-block;box-shadow:0 4px 15px rgba(0,0,0,0.2);transition:transform 0.2s,box-shadow 0.2s;",
                    onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 20px rgba(0,0,0,0.3)'",
                    onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 4px 15px rgba(0,0,0,0.2)'"
                ),
                style="text-align:center;"
            )
        )
    
    return Div(
        Container(content, padding="6rem 2rem"),
        style=f"{bg_style}min-height:500px;display:flex;align-items:center;justify-content:center;position:relative;"
    )


def HeroWithVideo(
    title: str,
    subtitle: str = None,
    video_url: str = None,
    cta_text: str = None,
    cta_link: str = "#"
):
    """Hero section with video background"""
    return Div(
        [
            # Video background
            Div(
                Video(
                    Source(src=video_url, type="video/mp4"),
                    autoplay=True,
                    muted=True,
                    loop=True,
                    style="width:100%;height:100%;object-fit:cover;"
                ) if video_url else None,
                style="position:absolute;top:0;left:0;width:100%;height:100%;z-index:0;overflow:hidden;"
            ),
            # Overlay
            Div(style="position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:1;"),
            # Content
            Container(
                [
                    H1(title, style="font-size:3rem;font-weight:800;color:#FFFFFF;margin-bottom:1rem;text-align:center;z-index:2;position:relative;"),
                    H2(subtitle, style="font-size:1.5rem;color:#FFFFFF;margin-bottom:2rem;text-align:center;z-index:2;position:relative;") if subtitle else None,
                    Div(
                        A(cta_text, href=cta_link, style=f"background:{themed_color('accent')};color:#FFFFFF;padding:1rem 2.5rem;border-radius:50px;text-decoration:none;font-weight:700;font-size:1.2rem;"),
                        style="text-align:center;z-index:2;position:relative;"
                    ) if cta_text else None
                ],
                padding="6rem 2rem"
            )
        ],
        style="position:relative;min-height:600px;display:flex;align-items:center;justify-content:center;overflow:hidden;"
    )


# -----------------------------------------------------------------------------
# Pricing Components
# -----------------------------------------------------------------------------

def PricingCard(
    title: str,
    price: float,
    period: str = "per week",
    features: list = None,
    cta_text: str = "Get Started",
    cta_link: str = "#",
    badge: str = None,
    currency: str = "$",
    featured: bool = False
):
    """
    Pricing card with optional promotional badge
    Perfect for course pricing, product pricing, etc.
    """
    card_style = f"background:#FFFFFF;border-radius:12px;padding:2rem;box-shadow:0 4px 20px rgba(0,0,0,0.1);position:relative;transition:transform 0.3s,box-shadow 0.3s;border:2px solid {'#FFD700' if featured else 'transparent'};"
    
    content = []
    
    # Badge (e.g., "40% OFF")
    if badge:
        content.append(
            Div(
                badge,
                style="position:absolute;top:-15px;right:20px;background:#FF4444;color:#FFFFFF;padding:0.5rem 1rem;border-radius:20px;font-weight:700;font-size:0.9rem;box-shadow:0 2px 10px rgba(255,68,68,0.3);"
            )
        )
    
    # Title
    content.append(
        H3(title, style="font-size:1.5rem;font-weight:700;margin-bottom:1rem;text-align:center;color:#2D3748;")
    )
    
    # Price
    content.append(
        Div(
            [
                Span(currency, style="font-size:1.5rem;font-weight:600;color:#4A5568;vertical-align:top;"),
                Span(str(int(price)) if price == int(price) else str(price), style="font-size:3.5rem;font-weight:800;color:#2D3748;"),
                Span(f" {period}", style="font-size:1rem;color:#718096;margin-left:0.5rem;")
            ],
            style="text-align:center;margin-bottom:1.5rem;"
        )
    )
    
    # Features
    if features:
        feature_items = [
            Div(
                [
                    Span("✓", style="color:#48BB78;font-weight:700;margin-right:0.5rem;"),
                    Span(feature, style="color:#4A5568;")
                ],
                style="margin-bottom:0.75rem;"
            )
            for feature in features
        ]
        content.append(
            Div(feature_items, style="margin-bottom:2rem;")
        )
    
    # CTA Button
    content.append(
        A(
            cta_text,
            href=cta_link,
            style=f"display:block;background:{themed_color('primary')};color:#FFFFFF;padding:1rem 2rem;border-radius:8px;text-decoration:none;font-weight:700;text-align:center;transition:background 0.2s;",
            onmouseover=f"this.style.background='{themed_color('secondary')}'",
            onmouseout=f"this.style.background='{themed_color('primary')}'"
        )
    )
    
    return Div(
        content,
        style=card_style,
        onmouseover="this.style.transform='translateY(-5px)';this.style.boxShadow='0 8px 30px rgba(0,0,0,0.15)'",
        onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 4px 20px rgba(0,0,0,0.1)'"
    )


def PricingTable(plans: list, columns: int = None):
    """
    Display multiple pricing plans in a grid
    plans: list of dicts with keys: title, price, period, features, cta_text, cta_link, badge, featured
    """
    if not columns:
        columns = min(len(plans), 3)
    
    cards = [PricingCard(**plan) for plan in plans]
    
    return Div(
        Container(
            Div(
                cards,
                style=f"display:grid;grid-template-columns:repeat({columns},1fr);gap:2rem;max-width:1200px;margin:auto;"
            ),
            padding="4rem 2rem"
        ),
        style="background:#F7FAFC;"
    )


# -----------------------------------------------------------------------------
# Social Proof Components
# -----------------------------------------------------------------------------

def TestimonialCard(
    quote: str,
    author: str,
    role: str = None,
    photo: str = None,
    rating: int = 5
):
    """Single testimonial card"""
    stars = "⭐" * rating
    
    return Div(
        [
            # Quote
            P(
                f'"{quote}"',
                style="font-size:1.1rem;font-style:italic;color:#2D3748;margin-bottom:1.5rem;line-height:1.6;"
            ),
            # Stars
            Div(stars, style="color:#FFD700;font-size:1.2rem;margin-bottom:1rem;"),
            # Author info
            Div(
                [
                    Img(src=photo, alt=author, style="width:50px;height:50px;border-radius:50%;margin-right:1rem;object-fit:cover;") if photo else None,
                    Div(
                        [
                            Div(author, style="font-weight:700;color:#2D3748;"),
                            Div(role, style="color:#718096;font-size:0.9rem;") if role else None
                        ]
                    )
                ],
                style="display:flex;align-items:center;"
            )
        ],
        style="background:#FFFFFF;padding:2rem;border-radius:12px;box-shadow:0 2px 15px rgba(0,0,0,0.08);"
    )


def TestimonialCarousel(title: str = None, testimonials: list = None):
    """
    Carousel of testimonials
    testimonials: list of dicts with keys: quote, author, role, photo, rating
    """
    if not testimonials:
        testimonials = []
    
    cards = [TestimonialCard(**t) for t in testimonials]
    
    return Div(
        Container(
            [
                H2(title, style="font-size:2.5rem;font-weight:700;text-align:center;margin-bottom:3rem;color:#2D3748;") if title else None,
                Div(
                    cards,
                    style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:2rem;"
                )
            ],
            padding="4rem 2rem"
        ),
        style="background:#F7FAFC;"
    )


# -----------------------------------------------------------------------------
# FAQ Component
# -----------------------------------------------------------------------------

def FAQAccordion(title: str = "Frequently Asked Questions", faqs: list = None):
    """
    Collapsible FAQ section
    faqs: list of dicts with keys: question, answer
    """
    if not faqs:
        faqs = []
    
    faq_items = []
    for i, faq in enumerate(faqs):
        faq_id = f"faq-{i}"
        faq_items.append(
            Div(
                [
                    # Question (clickable)
                    Div(
                        [
                            Span(faq['question'], style="font-weight:600;color:#2D3748;flex:1;"),
                            Span("▼", id=f"{faq_id}-icon", style="color:#718096;transition:transform 0.3s;")
                        ],
                        style="display:flex;align-items:center;justify-content:space-between;padding:1.5rem;cursor:pointer;background:#FFFFFF;border-radius:8px;margin-bottom:0.5rem;",
                        onclick=f"""
                            const answer = document.getElementById('{faq_id}-answer');
                            const icon = document.getElementById('{faq_id}-icon');
                            if (answer.style.display === 'none' || answer.style.display === '') {{
                                answer.style.display = 'block';
                                icon.style.transform = 'rotate(180deg)';
                            }} else {{
                                answer.style.display = 'none';
                                icon.style.transform = 'rotate(0deg)';
                            }}
                        """
                    ),
                    # Answer (collapsible)
                    Div(
                        P(faq['answer'], style="color:#4A5568;line-height:1.6;"),
                        id=f"{faq_id}-answer",
                        style="display:none;padding:1rem 1.5rem;background:#F7FAFC;border-radius:8px;margin-bottom:1rem;"
                    )
                ]
            )
        )
    
    return Div(
        Container(
            [
                H2(title, style="font-size:2.5rem;font-weight:700;text-align:center;margin-bottom:3rem;color:#2D3748;"),
                Div(faq_items, style="max-width:800px;margin:auto;")
            ],
            padding="4rem 2rem"
        )
    )


# -----------------------------------------------------------------------------
# CTA Components
# -----------------------------------------------------------------------------

def CTABanner(
    title: str,
    description: str = None,
    button_text: str = "Get Started",
    button_link: str = "#",
    background_color: str = None
):
    """Full-width call-to-action banner"""
    bg = background_color or themed_color('primary')
    
    return Div(
        Container(
            [
                H2(title, style="font-size:2.5rem;font-weight:700;color:#FFFFFF;text-align:center;margin-bottom:1rem;"),
                P(description, style="font-size:1.2rem;color:#FFFFFF;text-align:center;margin-bottom:2rem;opacity:0.95;") if description else None,
                Div(
                    A(
                        button_text,
                        href=button_link,
                        style="background:#FFFFFF;color:#2D3748;padding:1rem 2.5rem;border-radius:50px;text-decoration:none;font-weight:700;font-size:1.1rem;display:inline-block;box-shadow:0 4px 15px rgba(0,0,0,0.2);transition:transform 0.2s;",
                        onmouseover="this.style.transform='scale(1.05)'",
                        onmouseout="this.style.transform='scale(1)'"
                    ),
                    style="text-align:center;"
                )
            ],
            padding="4rem 2rem"
        ),
        style=f"background:{bg};"
    )


def CountdownTimer(end_date: str, message: str = "Offer ends in:"):
    """
    Countdown timer for promotions
    end_date: ISO format date string (e.g., "2026-11-30T23:59:59")
    """
    timer_id = "countdown-timer"
    
    return Div(
        [
            Div(message, style="font-size:1.2rem;font-weight:600;color:#2D3748;margin-bottom:1rem;text-align:center;"),
            Div(
                id=timer_id,
                style="display:flex;gap:1rem;justify-content:center;font-size:2rem;font-weight:700;color:#E53E3E;"
            ),
            Script(f"""
                const endDate = new Date('{end_date}').getTime();
                const timer = document.getElementById('{timer_id}');
                
                function updateTimer() {{
                    const now = new Date().getTime();
                    const distance = endDate - now;
                    
                    if (distance < 0) {{
                        timer.innerHTML = "Offer Expired";
                        return;
                    }}
                    
                    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                    const seconds = Math.floor((distance % (1000 * 60)) / 1000);
                    
                    timer.innerHTML = `
                        <div style="text-align:center;">
                            <div style="font-size:2.5rem;">${{days}}</div>
                            <div style="font-size:0.8rem;color:#718096;">DAYS</div>
                        </div>
                        <div style="font-size:2.5rem;">:</div>
                        <div style="text-align:center;">
                            <div style="font-size:2.5rem;">${{hours}}</div>
                            <div style="font-size:0.8rem;color:#718096;">HOURS</div>
                        </div>
                        <div style="font-size:2.5rem;">:</div>
                        <div style="text-align:center;">
                            <div style="font-size:2.5rem;">${{minutes}}</div>
                            <div style="font-size:0.8rem;color:#718096;">MINS</div>
                        </div>
                        <div style="font-size:2.5rem;">:</div>
                        <div style="text-align:center;">
                            <div style="font-size:2.5rem;">${{seconds}}</div>
                            <div style="font-size:0.8rem;color:#718096;">SECS</div>
                        </div>
                    `;
                }}
                
                updateTimer();
                setInterval(updateTimer, 1000);
            """)
        ],
        style="background:#FFF5F5;padding:2rem;border-radius:12px;border:2px solid #FEB2B2;margin:2rem 0;"
    )


# -----------------------------------------------------------------------------
# Feature Components
# -----------------------------------------------------------------------------

def FeatureGrid(title: str = None, features: list = None, columns: int = 3):
    """
    Grid of features with icons
    features: list of dicts with keys: icon, title, description
    """
    if not features:
        features = []
    
    feature_cards = []
    for feature in features:
        feature_cards.append(
            Div(
                [
                    Div(feature.get('icon', '✨'), style="font-size:3rem;margin-bottom:1rem;"),
                    H3(feature.get('title', ''), style="font-size:1.3rem;font-weight:700;color:#2D3748;margin-bottom:0.5rem;"),
                    P(feature.get('description', ''), style="color:#718096;line-height:1.6;")
                ],
                style="text-align:center;padding:2rem;background:#FFFFFF;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.05);"
            )
        )
    
    return Div(
        Container(
            [
                H2(title, style="font-size:2.5rem;font-weight:700;text-align:center;margin-bottom:3rem;color:#2D3748;") if title else None,
                Div(
                    feature_cards,
                    style=f"display:grid;grid-template-columns:repeat({columns},1fr);gap:2rem;"
                )
            ],
            padding="4rem 2rem"
        ),
        style="background:#F7FAFC;"
    )


# -----------------------------------------------------------------------------
# Form Components
# -----------------------------------------------------------------------------

def EmailCaptureForm(
    placeholder: str = "Enter your email",
    button_text: str = "Subscribe",
    action: str = "/subscribe",
    title: str = None,
    description: str = None
):
    """Email capture form for lead generation"""
    return Div(
        Container(
            [
                H2(title, style="font-size:2rem;font-weight:700;text-align:center;margin-bottom:1rem;color:#2D3748;") if title else None,
                P(description, style="font-size:1.1rem;text-align:center;margin-bottom:2rem;color:#718096;") if description else None,
                Form(
                    Div(
                        [
                            Input(
                                type="email",
                                name="email",
                                placeholder=placeholder,
                                required=True,
                                style="flex:1;padding:1rem 1.5rem;border:2px solid #E2E8F0;border-radius:8px 0 0 8px;font-size:1rem;outline:none;",
                                onfocus="this.style.borderColor='#4299E1'"
                            ),
                            Button(
                                button_text,
                                type="submit",
                                style=f"background:{themed_color('primary')};color:#FFFFFF;padding:1rem 2rem;border:none;border-radius:0 8px 8px 0;font-weight:700;cursor:pointer;transition:background 0.2s;",
                                onmouseover=f"this.style.background='{themed_color('secondary')}'",
                                onmouseout=f"this.style.background='{themed_color('primary')}'"
                            )
                        ],
                        style="display:flex;max-width:500px;margin:auto;"
                    ),
                    action=action,
                    method="POST"
                )
            ],
            padding="3rem 2rem"
        ),
        style="background:#FFFFFF;"
    )

