"""Example Landing Page - Doodle Institute Style"""
from fasthtml.common import *
from monsterui.all import *
from core.ui.components import (
    HeroSection, PricingCard, PricingTable, TestimonialCarousel,
    FAQAccordion, CTABanner, EmailCaptureForm, FeatureGrid
)

def ExamplePage():
    """Example landing page demonstrating all Phase 1 components"""
    
    # Pricing plans
    plans = [
        {
            "title": "Early Bird",
            "price": "$299",
            "features": [
                "Full 8-week program",
                "All materials included",
                "Portfolio review",
                "Certificate of completion"
            ],
            "cta_text": "Register Now",
            "cta_href": "/auth/register",
            "highlighted": True
        },
        {
            "title": "Standard",
            "price": "$399",
            "features": [
                "Full 8-week program",
                "All materials included",
                "Portfolio review",
                "Certificate of completion",
                "1-on-1 mentorship session"
            ],
            "cta_text": "Register Now",
            "cta_href": "/auth/register",
            "highlighted": False
        },
        {
            "title": "Premium",
            "price": "$599",
            "features": [
                "Full 8-week program",
                "Premium materials kit",
                "Portfolio review",
                "Certificate of completion",
                "3 mentorship sessions",
                "Exhibition opportunity"
            ],
            "cta_text": "Register Now",
            "cta_href": "/auth/register",
            "highlighted": False
        }
    ]
    
    # Testimonials
    testimonials = [
        {
            "quote": "My daughter absolutely loved the summer camp! She learned so much and made great friends.",
            "author": "Sarah M.",
            "role": "Parent"
        },
        {
            "quote": "The instructors were amazing and really helped me develop my artistic skills.",
            "author": "Alex T.",
            "role": "Student, Age 14"
        },
        {
            "quote": "Best investment we made for our son's creative development this summer!",
            "author": "Michael R.",
            "role": "Parent"
        }
    ]
    
    # FAQs
    faqs = [
        {
            "question": "What age groups is this camp for?",
            "answer": "Our Summer Doodle Camp is designed for students ages 10-16 of all skill levels."
        },
        {
            "question": "What materials do students need to bring?",
            "answer": "All materials are provided! Students just need to bring their creativity and enthusiasm."
        },
        {
            "question": "What is the daily schedule?",
            "answer": "Camp runs Monday-Friday, 9 AM - 3 PM, with breaks for snacks and lunch."
        },
        {
            "question": "Is there a refund policy?",
            "answer": "Yes! Full refunds are available up to 2 weeks before camp starts. After that, 50% refunds are available up to 1 week before."
        }
    ]
    
    # Features
    features = [
        {
            "icon": "palette",
            "title": "Expert Instruction",
            "description": "Learn from professional artists with years of teaching experience"
        },
        {
            "icon": "people",
            "title": "Small Class Sizes",
            "description": "Maximum 12 students per class for personalized attention"
        },
        {
            "icon": "award",
            "title": "Certificate Program",
            "description": "Receive a certificate of completion and portfolio review"
        }
    ]
    
    return Div(
        # Hero Section
        HeroSection(
            title="Summer Doodle Camp 2026",
            subtitle="Unleash your creativity this summer! Join us for 8 weeks of artistic exploration, skill-building, and fun.",
            cta_text="Register Now - Early Bird Special!",
            cta_href="/auth/register"
        ),
        
        # Features
        FeatureGrid(features),
        
        # Pricing Section
        Container(
            H2("Choose Your Plan", cls="text-center display-5 mb-5"),
            PricingTable(plans),
            cls="py-5"
        ),
        
        # Testimonials
        Container(
            H2("What Parents & Students Say", cls="text-center display-5 mb-5"),
            TestimonialCarousel(testimonials),
            cls="py-5"
        ),
        
        # FAQ Section
        Container(
            H2("Frequently Asked Questions", cls="text-center display-5 mb-5"),
            FAQAccordion(faqs),
            cls="py-5"
        ),
        
        # Email Capture
        Div(
            Container(
                H2("Stay Updated!", cls="text-center text-white mb-4"),
                P("Get early access to next year's camp dates and special offers", cls="text-center text-white-50 mb-4"),
                EmailCaptureForm(action="/subscribe", placeholder="Enter your email for updates")
            ),
            cls="bg-primary py-5"
        ),
        
        # Final CTA
        CTABanner(
            title="Ready to Join the Fun?",
            subtitle="Limited spots available - register today!",
            cta_text="Register Now",
            cta_href="/auth/register"
        )
    )
