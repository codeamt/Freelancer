"""Home Page - Showcasing FastApp Add-ons"""
from fasthtml.common import *
from monsterui.all import *
from core.ui import (
    HeroSection, FeatureCarousel, CTABanner, FAQAccordion
)

def HomePage():
    """Home page showcasing the FastApp platform and its add-ons"""
    
    # Add-on features
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
    
    # Core features - now using Steps component
    core_features_steps = [
        {"title": "Lightning Fast", "icon": "zap"},
        {"title": "Secure by Default", "icon": "shield"},
        {"title": "Open Source", "icon": "github"},
        {"title": "AWS & Mailgun Ready", "icon": "cloud"},
        {"title": "Fully Customizable", "icon": "cog"},
        {"title": "Modular Architecture", "icon": "grid"},
    ]
    
    # Testimonials
    testimonials = [
        {
            "quote": "FastApp helped us launch our online course platform in just 2 weeks!",
            "author": "Sarah Johnson",
            "role": "Education Startup Founder"
        },
        {
            "quote": "The modular design made it easy to add e-commerce to our existing site.",
            "author": "Mike Chen",
            "role": "Small Business Owner"
        },
        {
            "quote": "Best platform for building community-driven applications.",
            "author": "Alex Rivera",
            "role": "Community Manager"
        }
    ]
    
    # FAQs
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
    
    return Div(
        # Hero Section
        HeroSection(
            title="Build Powerful Web Apps in Minutes",
            subtitle="FastApp combines FastHTML + MonsterUI with modular add-ons for LMS, Commerce, and Social features.",
            cta_text="Get Started",
            cta_href="/about"
        ),
        
        # Add-ons Section with Carousel
        Div(
            H2("Powerful Add-ons", cls="text-center mb-8 text-4xl font-bold"),
            FeatureCarousel(addons, autoplay=True),
            cls="py-12"
        ),
        
        # Core Features Section with Steps
        Div(
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
        ),
        
        # FAQ Section
        Container(
            H2("Frequently Asked Questions", cls="text-center mb-5 display-5"),
            FAQAccordion(faqs),
            cls="py-5"
        ),
        
        # CTA Banner
        CTABanner(
            title="Ready to Build Something Amazing?",
            subtitle="Join thousands of developers building with FastApp",
            cta_text="Start Building",
            cta_href="/contact"
        )
    )
