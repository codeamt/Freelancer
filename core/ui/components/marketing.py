"""Clean UI Components using FastHTML and MonsterUI"""
from fasthtml.common import *
from monsterui.all import *

# ------------------------------------------------------------------------------
# Landing Page Components
# ------------------------------------------------------------------------------

def HeroSection(title: str, subtitle: str, cta_text: str = "Get Started", cta_href: str = "#"):
    """Hero section with title, subtitle, and CTA button"""
    return Div(
        Div(
            H1(title, cls="text-5xl font-bold text-center mb-4"),
            P(subtitle, cls="text-xl text-center mb-8 text-gray-600"),
            Div(
                A(cta_text, href=cta_href, cls="btn btn-primary btn-lg"),
                cls="text-center"
            ),
            cls="py-12"
        ),
        cls="container mx-auto px-4"
    )

def CTABanner(title: str, subtitle: str, cta_text: str = "Get Started", cta_href: str = "#"):
    """Call-to-action banner"""
    return Div(
        Div(
            H2(title, cls="text-white text-3xl font-bold mb-4"),
            P(subtitle, cls="text-blue-100 text-lg mb-6"),
            A(cta_text, href=cta_href, cls="btn btn-lg bg-white text-blue-600 hover:bg-gray-100"),
            cls="text-center py-16"
        ),
        cls="bg-blue-600 w-full"
    )

def CTAButton(label: str, href: str = "#"):
    """Call-to-action button"""
    return A(label, href=href, cls="btn btn-primary")