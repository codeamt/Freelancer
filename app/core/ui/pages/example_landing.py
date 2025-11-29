"""
Example: Doodle Institute Summer Art Camp Landing Page
Demonstrates all Phase 1 landing page components
"""
from fasthtml.common import *
from app.core.ui.components import (
    HeroSection, PricingCard, PricingTable, TestimonialCarousel,
    FAQAccordion, CTABanner, CountdownTimer, FeatureGrid,
    EmailCaptureForm, Container, Div
)


def ExamplePage():
    """
    Complete landing page example mimicking Doodle Institute Summer Art Camp
    Uses all new Phase 1 components
    """
    
    return Div(
        # Hero Section
        HeroSection(
            title="SUMMER DOODLE CAMP 2026",
            subtitle="A Summer of Creativity, Confidence & Color • Live on Zoom with Diane Bleck!",
            tagline="Perfect for Families • $99 per week • Monday–Friday • 1 hour per day",
            cta_text="Choose Your Week & Register",
            cta_link="#schedule",
            background_color="#FF6B6B",  # Playful red
            text_color="#FFFFFF"
        ),
        
        # Promotional Banner with Countdown
        Container(
            [
                H2("Black Friday Special OFFER!", 
                   style="font-size:2.5rem;font-weight:800;text-align:center;color:#E53E3E;margin-bottom:1rem;"),
                P("Use code BLACK and save 40% — this weekend only!",
                  style="font-size:1.3rem;text-align:center;color:#2D3748;margin-bottom:2rem;"),
                CountdownTimer(
                    end_date="2026-11-30T23:59:59",
                    message="⏰ Offer ends in:"
                )
            ],
            padding="3rem 2rem"
        ),
        
        # How It Works
        FeatureGrid(
            title="How Summer Doodle Camp Works",
            features=[
                {
                    "icon": "🎨",
                    "title": "Live on Zoom",
                    "description": "1 hour of drawing each day for 5 days a week with live instruction"
                },
                {
                    "icon": "👨‍👩‍👧‍👦",
                    "title": "Perfect for Families",
                    "description": "Ages 6-14 welcome! Parents and grandparents can join the fun too"
                },
                {
                    "icon": "✏️",
                    "title": "All Materials Included",
                    "description": "Simple supplies you already have at home - no special equipment needed"
                },
                {
                    "icon": "🏆",
                    "title": "Build Confidence",
                    "description": "Watch your child's creativity and confidence grow with each session"
                }
            ],
            columns=2
        ),
        
        # Testimonials
        TestimonialCarousel(
            title="Why Parents Love Summer Doodle Camp",
            testimonials=[
                {
                    "quote": "My daughter loved every minute! She can't wait for next summer.",
                    "author": "Sarah M.",
                    "role": "Parent of 9-year-old",
                    "rating": 5
                },
                {
                    "quote": "The perfect blend of structure and creativity. Diane is an amazing teacher!",
                    "author": "Michael T.",
                    "role": "Parent of 7 and 11-year-olds",
                    "rating": 5
                },
                {
                    "quote": "My son who 'hates art' actually asked to sign up for another week!",
                    "author": "Jennifer L.",
                    "role": "Parent of 12-year-old",
                    "rating": 5
                }
            ]
        ),
        
        # Schedule Section
        Container(
            [
                H2("Summer 2026 Camp Schedule",
                   style="font-size:2.5rem;font-weight:700;text-align:center;margin-bottom:1rem;color:#2D3748;"),
                P("Explore all six weekly themes and choose the creative adventures your child will love most!",
                  style="font-size:1.2rem;text-align:center;color:#718096;margin-bottom:3rem;"),
                
                # Week cards
                Div(
                    [
                        Div(
                            [
                                H3("Week 1: Ocean Adventures", style="font-weight:700;color:#2D3748;margin-bottom:0.5rem;"),
                                P("June 1-5, 2026", style="color:#718096;margin-bottom:0.5rem;"),
                                P("Dive into underwater creativity with dolphins, sea turtles, and coral reefs!",
                                  style="color:#4A5568;line-height:1.6;")
                            ],
                            style="background:#FFFFFF;padding:2rem;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.08);"
                        ),
                        Div(
                            [
                                H3("Week 2: World Travel", style="font-weight:700;color:#2D3748;margin-bottom:0.5rem;"),
                                P("June 8-12, 2026", style="color:#718096;margin-bottom:0.5rem;"),
                                P("Journey around the globe drawing landmarks, animals, and cultures!",
                                  style="color:#4A5568;line-height:1.6;")
                            ],
                            style="background:#FFFFFF;padding:2rem;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.08);"
                        ),
                        Div(
                            [
                                H3("Week 3: Magical Creatures", style="font-weight:700;color:#2D3748;margin-bottom:0.5rem;"),
                                P("June 15-19, 2026", style="color:#718096;margin-bottom:0.5rem;"),
                                P("Create dragons, unicorns, and fantastical beasts from your imagination!",
                                  style="color:#4A5568;line-height:1.6;")
                            ],
                            style="background:#FFFFFF;padding:2rem;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.08);"
                        ),
                        Div(
                            [
                                H3("Week 4: Comic Book Heroes", style="font-weight:700;color:#2D3748;margin-bottom:0.5rem;"),
                                P("June 22-26, 2026", style="color:#718096;margin-bottom:0.5rem;"),
                                P("Design your own superheroes and create amazing comic book adventures!",
                                  style="color:#4A5568;line-height:1.6;")
                            ],
                            style="background:#FFFFFF;padding:2rem;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.08);"
                        ),
                        Div(
                            [
                                H3("Week 5: Nature & Wildlife", style="font-weight:700;color:#2D3748;margin-bottom:0.5rem;"),
                                P("June 29 - July 3, 2026", style="color:#718096;margin-bottom:0.5rem;"),
                                P("Explore forests, jungles, and savannas while drawing amazing animals!",
                                  style="color:#4A5568;line-height:1.6;")
                            ],
                            style="background:#FFFFFF;padding:2rem;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.08);"
                        ),
                        Div(
                            [
                                H3("Week 6: Space & Planets", style="font-weight:700;color:#2D3748;margin-bottom:0.5rem;"),
                                P("July 6-10, 2026", style="color:#718096;margin-bottom:0.5rem;"),
                                P("Blast off to outer space and draw planets, rockets, and alien worlds!",
                                  style="color:#4A5568;line-height:1.6;")
                            ],
                            style="background:#FFFFFF;padding:2rem;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.08);"
                        )
                    ],
                    style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:2rem;",
                    id="schedule"
                )
            ],
            padding="4rem 2rem"
        ),
        
        # Pricing
        PricingTable(
            plans=[
                {
                    "title": "Single Week",
                    "price": 99,
                    "period": "per week",
                    "features": [
                        "5 days of LIVE Zoom instruction",
                        "1 hour per day (Monday-Friday)",
                        "All ages 6-14 welcome",
                        "Parents welcome to join",
                        "Supply list provided",
                        "Lifetime access to recordings"
                    ],
                    "cta_text": "Register for One Week",
                    "cta_link": "/register",
                    "badge": "40% OFF with code BLACK"
                },
                {
                    "title": "Multi-Week Package",
                    "price": 89,
                    "period": "per week",
                    "features": [
                        "Everything in Single Week",
                        "Save $10 per week",
                        "Choose any 3+ weeks",
                        "Priority support",
                        "Bonus art resources",
                        "Certificate of completion"
                    ],
                    "cta_text": "Register for Multiple Weeks",
                    "cta_link": "/register",
                    "featured": True,
                    "badge": "BEST VALUE"
                }
            ],
            columns=2
        ),
        
        # FAQ
        FAQAccordion(
            title="Frequently Asked Questions",
            faqs=[
                {
                    "question": "What ages can participate?",
                    "answer": "Students ages 8–14 are welcome to join independently. Children ages 6–7 may also participate with the support of an adult nearby. Parents and grandparents are always welcome to join in the fun!"
                },
                {
                    "question": "What supplies do we need?",
                    "answer": "Just basic supplies you likely already have: paper, pencils, markers or crayons, and an eraser. A detailed supply list will be sent upon registration."
                },
                {
                    "question": "What if we miss a session?",
                    "answer": "All sessions are recorded and you'll have lifetime access to the recordings, so you can catch up anytime!"
                },
                {
                    "question": "Can siblings share one registration?",
                    "answer": "Yes! The $99 per week is per family, so all your children can participate together."
                },
                {
                    "question": "What is the refund policy?",
                    "answer": "We offer a full refund if you cancel at least 48 hours before the first session of your registered week."
                },
                {
                    "question": "Do you offer payment plans?",
                    "answer": "Yes! For multi-week packages, we offer flexible payment plans. Contact us for details."
                }
            ]
        ),
        
        # Instructor Bio
        Container(
            [
                H2("Meet Your Instructor",
                   style="font-size:2.5rem;font-weight:700;text-align:center;margin-bottom:3rem;color:#2D3748;"),
                Div(
                    [
                        # Photo placeholder
                        Div(
                            "👩‍🎨",
                            style="font-size:8rem;text-align:center;margin-bottom:2rem;"
                        ),
                        # Bio
                        Div(
                            [
                                H3("Diane Bleck", style="font-size:2rem;font-weight:700;color:#2D3748;margin-bottom:0.5rem;text-align:center;"),
                                P("Artist, Author & Creativity Guide Around the World",
                                  style="font-size:1.2rem;color:#718096;margin-bottom:2rem;text-align:center;"),
                                P("Diane has been teaching art for over 20 years and has inspired thousands of students worldwide. She's the author of multiple art instruction books and believes that everyone can draw with the right guidance and encouragement.",
                                  style="color:#4A5568;line-height:1.8;text-align:center;max-width:700px;margin:auto;")
                            ]
                        )
                    ]
                )
            ],
            padding="4rem 2rem"
        ),
        
        # Email Capture
        EmailCaptureForm(
            title="Stay Updated on Future Camps!",
            description="Get notified about new themes, special offers, and early bird registration.",
            placeholder="Enter your email address",
            button_text="Keep Me Posted",
            action="/subscribe"
        ),
        
        # Final CTA
        CTABanner(
            title="Ready to Join the Fun?",
            description="Save your spot in Summer Doodle Camp 2026 and give your child an unforgettable creative summer!",
            button_text="Register Now",
            button_link="/register",
            background_color="#4ECDC4"  # Teal
        )
    )
