from fasthtml.common import *
from monsterui.all import *

def FeatureCard(icon: str, title: str, description: str):
    """Feature card with icon, title, and description"""
    return Card(
        Div(
            Div(
                UkIcon(icon, width="64", height="64", cls="text-blue-600"),
                cls="flex justify-center mb-6"
            ),
            H5(title, cls="text-xl font-semibold mb-3"),
            P(description, cls="text-gray-400 text-sm"),
            cls="text-center p-8"
        ),
        cls="shadow-sm hover:shadow-md transition-shadow h-full"
    )


def FeatureCard(icon: str, title: str, description: str):
    """Feature card with icon, title, and description"""
    return Card(
        Div(
            Div(
                UkIcon(icon, width="64", height="64", cls="text-blue-600"),
                cls="flex justify-center mb-6"
            ),
            H5(title, cls="text-xl font-semibold mb-3"),
            P(description, cls="text-gray-400 text-sm"),
            cls="text-center p-8"
        ),
        cls="shadow-sm hover:shadow-md transition-shadow h-full"
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

def FeatureCarousel(features: list, autoplay: bool = True):
    """Carousel/slider of feature cards with autoplay
    
    Args:
        features: List of dicts with keys: icon, title, description
        autoplay: Whether to autoplay the carousel
    """
    carousel_id = "addon-carousel"
    
    return Div(
        # Carousel container with DaisyUI carousel
        Div(
            *[Div(
                Card(
                    Div(
                        Div(
                            UkIcon(f["icon"], width="64", height="64", cls="text-blue-600"),
                            cls="flex justify-center mb-6"
                        ),
                        H5(f["title"], cls="text-xl font-semibold mb-3"),
                        P(f["description"], cls="text-gray-400 text-sm"),
                        cls="text-center p-8"
                    ),
                    cls="shadow-lg hover:shadow-xl transition-shadow bg-base-200 min-h-[300px] flex items-center"
                ),
                id=f"slide{i}",
                cls="carousel-item relative w-full md:w-1/3 px-2"
            ) for i, f in enumerate(features)],
            id=carousel_id,
            cls="carousel carousel-center w-full space-x-4 p-4 bg-base-100 rounded-box"
        ),
        # Navigation dots
        Div(
            *[A(f"❯", href=f"#slide{i}", cls="btn btn-xs") for i in range(len(features))],
            cls="flex justify-center gap-2 py-4"
        ),
        # Auto-scroll script
        Script(f"""
            let currentSlide = 0;
            const totalSlides = {len(features)};
            
            setInterval(() => {{
                currentSlide = (currentSlide + 1) % totalSlides;
                document.getElementById('slide' + currentSlide).scrollIntoView({{
                    behavior: 'smooth',
                    block: 'nearest',
                    inline: 'center'
                }});
            }}, 4000); // Change slide every 4 seconds
        """) if autoplay else None,
        cls="container mx-auto px-4 py-8"
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

def FAQAccordion(faqs: list):
    """FAQ accordion using MonsterUI
    
    Args:
        faqs: List of dicts with keys: question, answer
    """
    return Div(
        Accordion(
            *[AccordionItem(
                faq["question"],
                P(faq["answer"], cls="text-gray-400")
            ) for faq in faqs],
            multiple=False,
            animation=True,
        ),
        cls="max-w-4xl mx-auto py-8"
    )

def CTABanner(title: str, description: str, cta_text: str = "Get Started", cta_href: str = "#", secondary_text: str = None, secondary_href: str = None):
    """Call-to-action banner with title, description, and buttons"""
    return Div(
        Container(
            Div(
                H2(title, cls="text-3xl md:text-4xl font-bold mb-4 text-white"),
                P(description, cls="text-xl mb-6 text-gray-200"),
                Div(
                    A(cta_text, href=cta_href, cls="btn btn-primary btn-lg mr-3"),
                    A(secondary_text, href=secondary_href, cls="btn btn-outline btn-lg") if secondary_text else None,
                    cls="flex gap-4"
                ),
                cls="text-center max-w-4xl mx-auto"
            ),
            cls="py-16"
        ),
        cls="bg-gradient-to-r from-blue-600 to-purple-600"
    )

def EmailCaptureForm(title: str = "Stay Updated", description: str = "Get the latest updates delivered to your inbox.", button_text: str = "Subscribe", placeholder: str = "Enter your email"):
    """Email capture form with title and description"""
    return Div(
        Container(
            Div(
                H3(title, cls="text-2xl font-bold mb-2"),
                P(description, cls="text-gray-400 mb-6"),
                Form(
                    Div(
                        Input(
                            type="email",
                            placeholder=placeholder,
                            required=True,
                            cls="input input-bordered w-full"
                        ),
                        Button(button_text, type="submit", cls="btn btn-primary"),
                        cls="flex gap-2"
                    ),
                    method="POST",
                    action="/subscribe",
                    cls="max-w-md mx-auto"
                ),
                cls="text-center"
            ),
            cls="py-12"
        ),
        cls="bg-base-200"
    )