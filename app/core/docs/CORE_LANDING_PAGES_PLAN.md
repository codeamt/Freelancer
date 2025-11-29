# Core Landing Pages Implementation Plan

## Vision
**Core = Landing Page Foundation**  
**Add-ons = Functional Extensions**

Core provides all the marketing, presentation, and content management capabilities.
Add-ons (LMS, Commerce, etc.) use core's landing page system to present their functionality.

---

## Phase 1: Enhance Core UI Components (Week 1)

### 1.1 Add Landing Page Components to `app/core/ui/components.py`

**Hero Sections**
- [ ] `HeroSection()` - Full-width hero with background image
- [ ] `HeroWithVideo()` - Hero with video background
- [ ] `HeroSplit()` - Split layout (text + image)
- [ ] `HeroMinimal()` - Simple centered hero

**Social Proof**
- [ ] `TestimonialCard()` - Single testimonial
- [ ] `TestimonialCarousel()` - Rotating testimonials
- [ ] `ReviewStars()` - Star rating display
- [ ] `TrustBadges()` - Certification/partner badges
- [ ] `SocialProofBar()` - "Join 10,000+ students"

**Pricing**
- [ ] `PricingCard()` - Single pricing plan
- [ ] `PricingTable()` - Multiple plans comparison
- [ ] `PricingToggle()` - Monthly/yearly toggle
- [ ] `PromotionalBadge()` - "40% OFF" badge

**Content Sections**
- [ ] `FeatureGrid()` - Grid of features
- [ ] `FeatureHighlight()` - Large feature showcase
- [ ] `StatsSection()` - Key statistics
- [ ] `TimelineSection()` - Process/schedule timeline
- [ ] `LogoCloud()` - Partner logos

**Engagement**
- [ ] `FAQAccordion()` - Collapsible FAQ
- [ ] `CountdownTimer()` - Promotional countdown
- [ ] `EmailCaptureForm()` - Email signup
- [ ] `NewsletterSignup()` - Newsletter subscription
- [ ] `WaitlistForm()` - Waitlist signup

**Media**
- [ ] `VideoEmbed()` - YouTube/Vimeo embed
- [ ] `ImageGallery()` - Photo gallery
- [ ] `BeforeAfter()` - Before/after slider
- [ ] `ImageCarousel()` - Image slideshow

**Call to Action**
- [ ] `CTABanner()` - Full-width CTA
- [ ] `StickyFooterCTA()` - Sticky bottom CTA
- [ ] `InlineCTA()` - Inline CTA button
- [ ] `FloatingCTA()` - Floating action button

---

## Phase 2: Page Builder System (Week 2)

### 2.1 Create `app/core/page_builder/`

**Files to Create**
```
app/core/page_builder/
├── __init__.py
├── builder.py          # PageBuilder class
├── sections.py         # Section registry
├── renderer.py         # JSON to HTML renderer
└── templates.py        # Pre-built page templates
```

**PageBuilder Features**
- [ ] Fluent API for building pages
- [ ] Section ordering and arrangement
- [ ] Theme application
- [ ] SEO meta tags
- [ ] JSON export/import
- [ ] Preview mode

**Example Usage**
```python
page = PageBuilder("Summer Art Camp")
page.add_hero(...)
page.add_features(...)
page.add_pricing(...)
page.build()
```

---

## Phase 3: Content Management (Week 3)

### 3.1 Create `app/core/content/`

**Database Models**
- [ ] `LandingPage` - Store landing pages
- [ ] `ContentBlock` - Reusable content blocks
- [ ] `PageSection` - Individual page sections
- [ ] `MediaAsset` - Images, videos for pages

**Services**
- [ ] `ContentService` - CRUD for pages
- [ ] `BlockService` - Manage content blocks
- [ ] `TemplateService` - Page templates

**Routes**
- [ ] `GET /pages/{slug}` - View landing page
- [ ] `POST /admin/pages` - Create page
- [ ] `PUT /admin/pages/{id}` - Update page
- [ ] `DELETE /admin/pages/{id}` - Delete page

**Migration**
```bash
alembic revision -m "add_landing_pages_tables"
```

---

## Phase 4: Theme System Enhancement (Week 4)

### 4.1 Add Landing Page Themes

**Theme Presets**
- [ ] Doodle Institute (playful, colorful)
- [ ] Professional (clean, corporate)
- [ ] Minimal (simple, elegant)
- [ ] Bold (high contrast, modern)

**Theme Configuration**
```python
{
    "colors": {...},
    "fonts": {...},
    "spacing": {...},
    "animations": {...},
    "components": {
        "hero": {...},
        "card": {...},
        "button": {...}
    }
}
```

**Features**
- [ ] Per-page theme override
- [ ] Custom CSS injection
- [ ] Google Fonts integration
- [ ] Color palette generator

---

## Phase 5: Forms & Lead Capture (Week 5)

### 5.1 Create `app/core/forms/`

**Form Handlers**
- [ ] Email capture
- [ ] Contact form
- [ ] Registration form
- [ ] Waitlist signup
- [ ] Survey/quiz

**Integrations**
- [ ] Email service (SendGrid/Mailchimp)
- [ ] CRM integration
- [ ] Webhook support
- [ ] Zapier integration

**Validation**
- [ ] Email validation
- [ ] Phone validation
- [ ] Custom field validation
- [ ] Spam protection (honeypot, reCAPTCHA)

---

## Phase 6: Analytics & Tracking (Week 6)

### 6.1 Create `app/core/analytics/`

**Tracking**
- [ ] Page views
- [ ] Unique visitors
- [ ] CTA clicks
- [ ] Form submissions
- [ ] Conversion tracking
- [ ] A/B testing support

**Metrics Dashboard**
- [ ] Real-time analytics
- [ ] Conversion funnel
- [ ] Traffic sources
- [ ] Device breakdown
- [ ] Geographic data

**Integrations**
- [ ] Google Analytics
- [ ] Facebook Pixel
- [ ] Custom event tracking

---

## Phase 7: Promotions System (Week 7)

### 7.1 Create `app/core/promotions/`

**Features**
- [ ] Coupon codes
- [ ] Percentage discounts
- [ ] Fixed amount discounts
- [ ] BOGO offers
- [ ] Time-limited promotions
- [ ] User-specific discounts

**Models**
```python
class Coupon(Base):
    code = Column(String, unique=True)
    discount_type = Column(Enum)  # percentage, fixed
    discount_value = Column(Float)
    expires_at = Column(DateTime)
    max_uses = Column(Integer)
    current_uses = Column(Integer)
```

**Routes**
- [ ] `POST /promotions/validate` - Validate coupon
- [ ] `GET /promotions/active` - Get active promotions
- [ ] `POST /admin/promotions` - Create promotion

---

## Phase 8: Integration with Add-ons (Week 8)

### 8.1 LMS Integration

**Course Landing Pages**
- [ ] Auto-generate landing page for each course
- [ ] Use core components for presentation
- [ ] Integrate enrollment with core forms
- [ ] Apply promotions to course pricing

**Example**
```python
# app/add_ons/lms/landing.py
def create_course_landing(course):
    page = PageBuilder(course.title)
    page.add_hero(title=course.title, ...)
    page.add_pricing(price=course.price, ...)
    return page.build()
```

### 8.2 Commerce Integration

**Product Landing Pages**
- [ ] Product showcase pages
- [ ] Shopping cart integration
- [ ] Checkout flow
- [ ] Upsell/cross-sell sections

### 8.3 Social Integration

**Community Landing Pages**
- [ ] Community overview
- [ ] Member testimonials
- [ ] Join community CTA

---

## Quick Wins (Do First)

### Week 1 Quick Wins
1. **Add 5 Essential Components**
   - HeroSection
   - PricingCard
   - FAQAccordion
   - TestimonialCard
   - CTABanner

2. **Create Doodle Institute Theme**
   - Playful colors
   - Fun fonts
   - Rounded corners

3. **Build Example Landing Page**
   - Use new components
   - Demonstrate capabilities
   - Template for future pages

---

## Success Metrics

### Technical
- [ ] 20+ reusable landing page components
- [ ] Page builder with fluent API
- [ ] 5+ pre-built themes
- [ ] Form handling system
- [ ] Analytics tracking

### Business
- [ ] Can clone Doodle Institute page in < 1 hour
- [ ] Non-technical users can create pages
- [ ] A/B testing capability
- [ ] Conversion tracking working
- [ ] Email capture integrated

---

## File Checklist

### New Files to Create
- [ ] `app/core/ui/components.py` - ENHANCE (add 20+ components)
- [ ] `app/core/page_builder/builder.py`
- [ ] `app/core/page_builder/sections.py`
- [ ] `app/core/page_builder/renderer.py`
- [ ] `app/core/page_builder/templates.py`
- [ ] `app/core/content/models.py`
- [ ] `app/core/content/service.py`
- [ ] `app/core/content/routes.py`
- [ ] `app/core/forms/handlers.py`
- [ ] `app/core/forms/validators.py`
- [ ] `app/core/forms/routes.py`
- [ ] `app/core/analytics/tracker.py`
- [ ] `app/core/analytics/models.py`
- [ ] `app/core/analytics/routes.py`
- [ ] `app/core/promotions/models.py`
- [ ] `app/core/promotions/service.py`
- [ ] `app/core/promotions/routes.py`
- [ ] `app/core/ui/theme/presets.py`

### Migrations to Create
- [ ] `0012_landing_pages_tables.py`
- [ ] `0013_content_blocks.py`
- [ ] `0014_promotions_system.py`
- [ ] `0015_analytics_tracking.py`

---

## Next Steps

1. **Start with Phase 1** - Enhance UI components
2. **Create Doodle Institute example** - Prove the concept
3. **Build page builder** - Enable dynamic pages
4. **Add content management** - Store pages in DB
5. **Integrate with LMS** - Course landing pages

---

## Example: Doodle Institute Landing Page

```python
# app/core/ui/pages/doodle_summer_camp.py
from app.core.page_builder import PageBuilder
from app.core.ui.components import *

def DoodleSummerCampPage():
    page = PageBuilder(
        title="Summer Doodle Camp 2026",
        meta_description="A Summer of Creativity, Confidence & Color"
    )
    
    # Hero
    page.add_section(HeroSection(
        title="SUMMER DOODLE CAMP 2026",
        subtitle="A Summer of Creativity, Confidence & Color • Live on Zoom with Diane Bleck!",
        tagline="Perfect for Families • $99 per week • Monday–Friday • 1 hour per day",
        cta_text="Choose Your Week & Register",
        cta_link="#schedule",
        background_image="/static/summer-camp-hero.jpg"
    ))
    
    # Promotional Banner
    page.add_section(PromotionalBanner(
        title="Black Friday Special OFFER!",
        message="Use code BLACK and save 40% — this weekend only!",
        badge="40% OFF"
    ))
    
    # How It Works
    page.add_section(FeatureHighlight(
        title="How Summer Doodle Camp Works",
        description="✏️ 1 Hour of Drawing Each Day for 5 Days a Week",
        features=[
            "Live on Zoom instruction",
            "Ages 6-14 welcome",
            "Parents can join too!",
            "All materials included"
        ]
    ))
    
    # Testimonials
    page.add_section(TestimonialCarousel(
        title="Why Parents Love Summer Doodle Camp",
        testimonials=[
            {
                "quote": "My daughter loved every minute!",
                "author": "Sarah M.",
                "role": "Parent of 9-year-old"
            },
            # ... more testimonials
        ]
    ))
    
    # Schedule
    page.add_section(TimelineSection(
        title="Summer 2026 Camp Schedule",
        subtitle="Explore all six weekly themes",
        weeks=[
            {"week": 1, "theme": "Ocean Adventures", "dates": "June 1-5"},
            {"week": 2, "theme": "World Travel", "dates": "June 8-12"},
            # ... more weeks
        ]
    ))
    
    # Pricing
    page.add_section(PricingCard(
        title="Registration Details",
        price=99,
        period="per week",
        features=[
            "5 days of LIVE Zoom instruction",
            "1 hour per day",
            "All ages 6-14 welcome",
            "Parents welcome to join"
        ],
        cta_text="Register Now",
        cta_link="/lms/enroll",
        badge="40% OFF with code BLACK"
    ))
    
    # FAQ
    page.add_section(FAQAccordion(
        title="Frequently Asked Questions",
        faqs=[
            {
                "question": "What ages can participate?",
                "answer": "Students ages 8–14 can join independently..."
            },
            # ... more FAQs
        ]
    ))
    
    # Instructor Bio
    page.add_section(InstructorBio(
        name="Diane Bleck",
        title="Artist, Author & Creativity Guide",
        photo="/static/diane-bleck.jpg",
        bio="Diane has been teaching art for over 20 years...",
        credentials=["Published Author", "International Speaker"]
    ))
    
    # Final CTA
    page.add_section(CTABanner(
        title="Ready to Join the Fun?",
        description="Save your spot in Summer Doodle Camp 2026!",
        button_text="Register Now",
        button_link="/lms/enroll"
    ))
    
    return page.build()
```

---

**Status**: Ready to implement Phase 1
**Timeline**: 8 weeks to full implementation
**Priority**: Start with UI components and Doodle Institute example
