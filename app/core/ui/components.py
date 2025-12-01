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

def FeatureCard(icon: str, title: str, description: str):
    """Feature card with icon, title, and description"""
    return Card(
        Div(
            I(cls=f"bi bi-{icon} text-4xl text-blue-600 mb-4"),
            H5(title, cls="text-xl font-semibold mb-2"),
            P(description, cls="text-gray-600"),
            cls="text-center p-6"
        ),
        cls="shadow-sm hover:shadow-md transition-shadow"
    )

def FeatureGrid(features: list):
    """Grid of feature cards
    
    Args:
        features: List of dicts with keys: icon, title, description
    """
    return Div(
        Div(
            *[Div(
                FeatureCard(f["icon"], f["title"], f["description"]),
                cls="w-full md:w-1/3 px-4 mb-8"
            ) for f in features],
            cls="flex flex-wrap -mx-4"
        ),
        cls="container mx-auto px-4 py-12"
    )

def PricingCard(title: str, price: str, features: list, cta_text: str = "Choose Plan", cta_href: str = "#", highlighted: bool = False):
    """Pricing card with title, price, features list, and CTA"""
    card_cls = "h-100 shadow-lg border-primary" if highlighted else "h-100 shadow-sm"
    
    return Card(
        CardHeader(
            H4(title, cls="my-0 fw-normal text-center"),
            cls="py-3" + (" bg-primary text-white" if highlighted else "")
        ),
        CardBody(
            H1(price, cls="card-title pricing-card-title text-center mb-4"),
            Ul(
                *[Li(feature, cls="mb-2") for feature in features],
                cls="list-unstyled mt-3 mb-4"
            ),
            Div(
                A(cta_text, href=cta_href, 
                  cls="btn w-100 " + ("btn-primary" if highlighted else "btn-outline-primary")),
                cls="d-grid"
            )
        ),
        cls=card_cls
    )

def PricingTable(plans: list):
    """Grid of pricing cards
    
    Args:
        plans: List of dicts with keys: title, price, features, cta_text, cta_href, highlighted
    """
    return Container(
        Div(
            *[Div(
                PricingCard(
                    p["title"], 
                    p["price"], 
                    p["features"],
                    p.get("cta_text", "Choose Plan"),
                    p.get("cta_href", "#"),
                    p.get("highlighted", False)
                ),
                cls="col-md-4 mb-4"
            ) for p in plans],
            cls="row"
        ),
        cls="py-5"
    )

def TestimonialCard(quote: str, author: str, role: str):
    """Testimonial card with quote, author, and role"""
    return Card(
        CardBody(
            Blockquote(
                P(f'"{quote}"', cls="mb-3"),
                Footer(
                    Strong(author),
                    Br(),
                    Small(role, cls="text-muted"),
                    cls="blockquote-footer mt-2"
                ),
                cls="mb-0"
            )
        ),
        cls="border-0 shadow-sm h-100"
    )

def TestimonialCarousel(testimonials: list):
    """Carousel of testimonials
    
    Args:
        testimonials: List of dicts with keys: quote, author, role
    """
    return Container(
        Div(
            *[Div(
                TestimonialCard(t["quote"], t["author"], t["role"]),
                cls="col-md-4 mb-4"
            ) for t in testimonials],
            cls="row"
        ),
        cls="py-5"
    )

def FAQItem(question: str, answer: str, item_id: str):
    """Single FAQ accordion item"""
    return Div(
        H2(
            Button(
                question,
                cls="accordion-button collapsed",
                type="button",
                data_bs_toggle="collapse",
                data_bs_target=f"#collapse{item_id}"
            ),
            cls="accordion-header"
        ),
        Div(
            Div(P(answer), cls="accordion-body"),
            id=f"collapse{item_id}",
            cls="accordion-collapse collapse"
        ),
        cls="accordion-item"
    )

def FAQAccordion(faqs: list):
    """FAQ accordion
    
    Args:
        faqs: List of dicts with keys: question, answer
    """
    return Container(
        Div(
            *[FAQItem(faq["question"], faq["answer"], f"faq{i}") 
              for i, faq in enumerate(faqs)],
            cls="accordion"
        ),
        cls="py-5"
    )

def CTABanner(title: str, subtitle: str, cta_text: str = "Get Started", cta_href: str = "#"):
    """Call-to-action banner"""
    return Div(
        Container(
            Div(
                H2(title, cls="text-white mb-3"),
                P(subtitle, cls="text-white-50 mb-4"),
                A(cta_text, href=cta_href, cls="btn btn-light btn-lg"),
                cls="text-center py-5"
            )
        ),
        cls="bg-primary"
    )

def EmailCaptureForm(action: str = "/subscribe", placeholder: str = "Enter your email"):
    """Email capture form with HTMX"""
    return Container(
        Div(
            Form(
                Div(
                    Input(type="email", name="email", placeholder=placeholder, required=True, cls="form-control form-control-lg"),
                    Button("Subscribe", type="submit", cls="btn btn-primary btn-lg"),
                    cls="input-group input-group-lg"
                ),
                hx_post=action,
                hx_target="#subscribe-result"
            ),
            Div(id="subscribe-result", cls="mt-3"),
            cls="py-4"
        )
    )

# ------------------------------------------------------------------------------
# Utility Components
# ------------------------------------------------------------------------------

def CTAButton(label: str, href: str = "#"):
    """Call-to-action button"""
    return A(label, href=href, cls="btn btn-primary")
