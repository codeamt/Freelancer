"""Home Page - Showcasing FastApp Add-ons"""
from fasthtml.common import *
from monsterui.all import *
from core.ui import (
    HeroSection, FeatureCarousel, CTABanner, FAQAccordion
)
from core.ui.pages.landing_page import LandingPage, Section


class HomePage(LandingPage):
    """Home page showcasing the FastApp platform and its add-ons"""
    
    def __init__(self, site_id: str = "main"):
        super().__init__(site_id)
        self._initialize_default_sections()
    
    def get_title(self) -> str:
        """Get the page title."""
        return "FastApp - Build Powerful Web Apps in Minutes"
    
    def get_default_sections(self) -> list[Section]:
        """Get the default sections for the home page."""
        return [
            Section(
                id="hero",
                type="hero",
                title="Hero Section",
                content=self._get_hero_content(),
                order=1
            ),
            Section(
                id="addons",
                type="addons",
                title="Add-ons Section",
                content=self._get_addons_content(),
                order=2
            ),
            Section(
                id="features",
                type="features",
                title="Core Features",
                content=self._get_features_content(),
                order=3
            ),
            Section(
                id="faq",
                type="faq",
                title="FAQ",
                content=self._get_faq_content(),
                order=4
            ),
            Section(
                id="cta",
                type="cta",
                title="Call to Action",
                content=self._get_cta_content(),
                order=5
            )
        ]
    
    def render_content(self) -> Div:
        """Render the main content of the home page."""
        # Render sections in order
        content_parts = []
        for section in self.site_graph.sections:
            if section.visible:
                content_parts.append(section.content)
        
        return Div(*content_parts)
    
    def _initialize_default_sections(self):
        """Initialize the default sections for the home page."""
        default_sections = self.get_default_sections()
        for section in default_sections:
            self.add_section(section)
    
    def _get_hero_content(self) -> Div:
        """Get the hero section content."""
        return HeroSection(
            title="Build Powerful Web Apps in Minutes",
            subtitle="FastApp combines FastHTML + MonsterUI with modular add-ons for LMS, Commerce, and Social features.",
            cta_text="Get Started",
            cta_href="/about"
        )
    
    def _get_addons_content(self) -> Div:
        """Get the add-ons section content."""
        addons = [
            {
                "icon": "book",
                "title": "LMS - Learning Management",
                "description": "Create and manage online courses, track student progress, issue certificates, and build a complete e-learning platform."
            },
            {
                "icon": "shopping-cart",
                "title": "Commerce - Online Store",
                "description": "Sell products and services with built-in payment processing, inventory management, and order fulfillment."
            },
            {
                "icon": "users",
                "title": "Social - Community Platform",
                "description": "Build engaged communities with user profiles, posts, comments, likes, and real-time messaging."
            },
            {
                "icon": "play-circle",
                "title": "Streaming - Live & VOD",
                "description": "Stream live video, host webinars, and deliver on-demand video content with built-in player and analytics."
            }
        ]
        
        return Div(
            H2("Powerful Add-ons", cls="text-center mb-8 text-4xl font-bold"),
            FeatureCarousel(addons, autoplay=True),
            cls="py-12"
        )
    
    def _get_features_content(self) -> Div:
        """Get the core features section content."""
        core_features_steps = [
            {"title": "Lightning Fast", "icon": "zap"},
            {"title": "Secure by Default", "icon": "shield"},
            {"title": "Open Source", "icon": "github"},
            {"title": "AWS & Mailgun Ready", "icon": "cloud"},
            {"title": "Fully Customizable", "icon": "cog"},
            {"title": "Modular Architecture", "icon": "grid"},
        ]
        
        return Div(
            H2("Core Features", cls="text-center mb-12 text-4xl font-bold"),
            Div(
                Steps(
                    *[LiStep(
                        Div(
                            UkIcon(feature["icon"], width="24", height="24", cls="text-blue-600"),
                            Span(feature["title"], cls="ml-3 text-lg"),
                            cls="flex items-center"
                        ),
                        cls="step-neutral"
                    ) for feature in core_features_steps],
                    cls=(StepsT.vertical, "min-h-[400px]")
                ),
                cls="flex justify-center"
            ),
            cls="container mx-auto px-4 py-16"
        )
    
    def _get_faq_content(self) -> Div:
        """Get the FAQ section content."""
        faqs = [
            {
                "question": "What is FastApp?",
                "answer": "FastApp is a modular web application platform built with FastHTML and MonsterUI. It provides a core foundation with optional add-ons for LMS, e-commerce, and social features."
            },
            {
                "question": "How do add-ons work?",
                "answer": "Add-ons are modular extensions that plug into the core FastApp platform. You can enable only the features you need, keeping your application lean and focused."
            },
            {
                "question": "Can I customize the design?",
                "answer": "Absolutely! FastApp uses MonsterUI components which are fully customizable with Bootstrap classes and custom CSS."
            },
            {
                "question": "Is it suitable for production?",
                "answer": "Yes! FastApp includes production-ready features like security middleware, database management, and scalable architecture."
            }
        ]
        
        return Container(
            H2("Frequently Asked Questions", cls="text-center mb-5 display-5"),
            FAQAccordion(faqs),
            cls="py-5"
        )
    
    def _get_cta_content(self) -> Div:
        """Get the call-to-action section content."""
        return CTABanner(
            title="Ready to Build Something Amazing?",
            subtitle="Join thousands of developers building with FastApp",
            cta_text="Start Building",
            cta_href="/contact"
        )


# Backward compatibility function
def HomePage_content():
    """Legacy function for backward compatibility."""
    return HomePage().render_content()
