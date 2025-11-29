# Landing Page Components - Quick Reference

## 🚀 Quick Start

```python
from app.core.ui.components import (
    HeroSection, PricingCard, TestimonialCarousel,
    FAQAccordion, CTABanner, CountdownTimer
)
```

---

## 📋 Component Cheat Sheet

### Hero Section
```python
HeroSection(
    title="Your Amazing Title",
    subtitle="Compelling subtitle here",
    tagline="Additional info",
    cta_text="Get Started",
    cta_link="/signup",
    background_image="/path/to/image.jpg",  # or background_color="#FF6B6B"
    text_color="#FFFFFF"
)
```

### Pricing Card
```python
PricingCard(
    title="Basic Plan",
    price=99,
    period="per month",
    features=["Feature 1", "Feature 2", "Feature 3"],
    cta_text="Buy Now",
    cta_link="/checkout",
    badge="POPULAR",  # Optional promotional badge
    currency="$",
    featured=True  # Highlights the card
)
```

### Pricing Table (Multiple Plans)
```python
PricingTable(
    plans=[
        {
            "title": "Basic",
            "price": 29,
            "features": ["Feature 1", "Feature 2"],
            "cta_text": "Start Basic",
            "cta_link": "/signup/basic"
        },
        {
            "title": "Pro",
            "price": 99,
            "features": ["All Basic", "Feature 3", "Feature 4"],
            "cta_text": "Start Pro",
            "cta_link": "/signup/pro",
            "featured": True,
            "badge": "BEST VALUE"
        }
    ],
    columns=2
)
```

### Testimonial Card
```python
TestimonialCard(
    quote="This product changed my life!",
    author="Jane Doe",
    role="CEO, Company Inc",
    photo="/path/to/photo.jpg",  # Optional
    rating=5
)
```

### Testimonial Carousel
```python
TestimonialCarousel(
    title="What Our Customers Say",
    testimonials=[
        {
            "quote": "Amazing service!",
            "author": "John Smith",
            "role": "Customer",
            "rating": 5
        },
        {
            "quote": "Highly recommend!",
            "author": "Sarah Johnson",
            "role": "User",
            "rating": 5
        }
    ]
)
```

### FAQ Accordion
```python
FAQAccordion(
    title="Frequently Asked Questions",
    faqs=[
        {
            "question": "How does it work?",
            "answer": "It's simple! Just sign up and start using..."
        },
        {
            "question": "What's the refund policy?",
            "answer": "We offer a 30-day money-back guarantee..."
        },
        {
            "question": "Is support included?",
            "answer": "Yes! 24/7 support is included with all plans."
        }
    ]
)
```

### Countdown Timer
```python
CountdownTimer(
    end_date="2026-12-31T23:59:59",  # ISO format
    message="⏰ Sale ends in:"
)
```

### Feature Grid
```python
FeatureGrid(
    title="Why Choose Us",
    features=[
        {
            "icon": "🚀",
            "title": "Fast Performance",
            "description": "Lightning-fast load times"
        },
        {
            "icon": "🔒",
            "title": "Secure",
            "description": "Bank-level security"
        },
        {
            "icon": "💰",
            "title": "Affordable",
            "description": "Best prices guaranteed"
        }
    ],
    columns=3
)
```

### Email Capture Form
```python
EmailCaptureForm(
    title="Join Our Newsletter",
    description="Get weekly tips and exclusive offers",
    placeholder="Enter your email",
    button_text="Subscribe",
    action="/subscribe"
)
```

### CTA Banner
```python
CTABanner(
    title="Ready to Get Started?",
    description="Join thousands of happy customers today!",
    button_text="Sign Up Now",
    button_link="/signup",
    background_color="#4ECDC4"  # Optional custom color
)
```

---

## 🎨 Common Patterns

### Full Landing Page Template
```python
from fasthtml.common import *
from app.core.ui.components import *

def MyLandingPage():
    return Div(
        # Hero
        HeroSection(
            title="Welcome to Our Product",
            subtitle="The best solution for your needs",
            cta_text="Get Started Free",
            cta_link="/signup"
        ),
        
        # Features
        FeatureGrid(
            title="Why Choose Us",
            features=[
                {"icon": "⚡", "title": "Fast", "description": "Lightning speed"},
                {"icon": "🎯", "title": "Accurate", "description": "Precise results"},
                {"icon": "💪", "title": "Powerful", "description": "Advanced features"}
            ]
        ),
        
        # Social Proof
        TestimonialCarousel(
            title="Customer Reviews",
            testimonials=[
                {"quote": "Great!", "author": "User 1", "rating": 5},
                {"quote": "Love it!", "author": "User 2", "rating": 5}
            ]
        ),
        
        # Pricing
        PricingTable(
            plans=[
                {"title": "Basic", "price": 29, "features": ["Feature 1"]},
                {"title": "Pro", "price": 99, "features": ["All Basic", "Feature 2"], "featured": True}
            ]
        ),
        
        # FAQ
        FAQAccordion(
            faqs=[
                {"question": "Q1?", "answer": "A1"},
                {"question": "Q2?", "answer": "A2"}
            ]
        ),
        
        # Final CTA
        CTABanner(
            title="Start Your Free Trial",
            button_text="Sign Up Now",
            button_link="/signup"
        )
    )
```

### Promotional Landing Page
```python
def PromoPage():
    return Div(
        # Hero with promo
        HeroSection(
            title="BLACK FRIDAY SALE",
            subtitle="50% OFF Everything",
            cta_text="Shop Now",
            cta_link="/shop",
            background_color="#E53E3E"
        ),
        
        # Countdown
        CountdownTimer(
            end_date="2026-11-30T23:59:59",
            message="⏰ Sale ends in:"
        ),
        
        # Pricing with badges
        PricingTable(
            plans=[
                {
                    "title": "Premium",
                    "price": 49,
                    "period": "was $99",
                    "badge": "50% OFF",
                    "features": ["All features"],
                    "cta_text": "Buy Now"
                }
            ]
        ),
        
        # Email capture
        EmailCaptureForm(
            title="Don't Miss Out!",
            description="Get notified of future sales",
            button_text="Notify Me"
        )
    )
```

### Course/Event Landing Page
```python
def CoursePage():
    return Div(
        # Hero
        HeroSection(
            title="Master Python in 30 Days",
            subtitle="Live online course with expert instructor",
            tagline="Next cohort starts Jan 15, 2026",
            cta_text="Enroll Now",
            cta_link="/enroll"
        ),
        
        # What you'll learn
        FeatureGrid(
            title="What You'll Learn",
            features=[
                {"icon": "📚", "title": "Basics", "description": "Python fundamentals"},
                {"icon": "🔧", "title": "Projects", "description": "Real-world apps"},
                {"icon": "🎓", "title": "Certificate", "description": "Completion cert"}
            ]
        ),
        
        # Testimonials
        TestimonialCarousel(
            title="Student Success Stories",
            testimonials=[...]
        ),
        
        # Pricing
        PricingCard(
            title="Course Access",
            price=299,
            period="one-time",
            features=[
                "30 live sessions",
                "Lifetime access to recordings",
                "Certificate of completion",
                "Private Discord community"
            ],
            cta_text="Enroll Now",
            badge="LIMITED SPOTS"
        ),
        
        # FAQ
        FAQAccordion(
            title="Common Questions",
            faqs=[...]
        )
    )
```

---

## 🎯 Tips & Best Practices

### Color Schemes
```python
# Use theme colors for consistency
from app.core.ui.theme.context import ThemeContext
theme = ThemeContext()

# Access theme colors
primary = theme.tokens["color"]["primary"]
secondary = theme.tokens["color"]["secondary"]

# Or use custom colors
background_color="#FF6B6B"  # Playful red
background_color="#4ECDC4"  # Teal
background_color="#FFE66D"  # Yellow
```

### Responsive Design
All components are responsive by default:
- Hero sections adapt to mobile
- Pricing tables stack on small screens
- Feature grids adjust columns automatically
- Forms resize appropriately

### Accessibility
- Use descriptive text for CTAs
- Provide alt text for images
- Ensure good color contrast
- Use semantic HTML (built-in)

### Performance
- Optimize images before using
- Use appropriate image sizes
- Lazy load images when possible
- Minimize inline styles (components handle this)

---

## 🔧 Customization

### Inline Styling
```python
# Add custom styles to any component
HeroSection(
    title="My Title",
    # Components return Div() which accepts style
)

# Wrap in custom container
Div(
    HeroSection(...),
    style="margin-top:2rem;"
)
```

### Layout Helpers
```python
from app.core.ui.components import Container, Section

# Use Container for consistent width
Container(
    your_content,
    max_width="1200px",
    padding="2rem"
)

# Use Section for full-width backgrounds
Section(
    your_content,
    background="#F7FAFC",
    padding="4rem 0"
)
```

---

## 📱 Mobile Considerations

All components are mobile-responsive, but consider:

1. **Hero Text**: Keep titles concise for mobile
2. **Pricing**: 2-3 plans max for mobile readability
3. **Features**: Use 1-2 columns on mobile
4. **Forms**: Full-width on mobile
5. **CTAs**: Large touch targets (built-in)

---

## 🎨 Example Color Palettes

### Playful (Doodle Institute)
```python
primary = "#FF6B6B"    # Red
secondary = "#4ECDC4"  # Teal
accent = "#FFE66D"     # Yellow
```

### Professional
```python
primary = "#2563EB"    # Blue
secondary = "#64748B"  # Gray
accent = "#F59E0B"     # Orange
```

### Minimal
```python
primary = "#000000"    # Black
secondary = "#FFFFFF"  # White
accent = "#3B82F6"     # Blue
```

---

## 🚀 Quick Deploy Checklist

- [ ] Create landing page function
- [ ] Import components
- [ ] Add route in `main.py`
- [ ] Test on desktop
- [ ] Test on mobile
- [ ] Check all links work
- [ ] Verify forms submit
- [ ] Test countdown timer
- [ ] Check FAQ accordion
- [ ] Deploy!

---

## 📚 More Resources

- **Full Documentation**: [PHASE_1_COMPLETE.md](PHASE_1_COMPLETE.md)
- **Example Page**: [app/core/ui/pages/doodle_example.py](app/core/ui/pages/doodle_example.py)
- **Components Source**: [app/core/ui/components.py](app/core/ui/components.py)
- **Implementation Plan**: [CORE_LANDING_PAGES_PLAN.md](CORE_LANDING_PAGES_PLAN.md)

---

**Happy Building! 🎉**
