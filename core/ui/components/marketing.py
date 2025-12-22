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


def NewsletterSignup(
    title: str = "Stay Updated",
    subtitle: str = "Get the latest news and updates delivered to your inbox",
    placeholder: str = "Enter your email address",
    button_text: str = "Subscribe",
    action_url: str = "#",
    description: str = None,
    show_privacy: bool = True,
    theme: str = "light"  # "light" or "dark"
):
    """Newsletter signup section component"""
    
    # Theme-specific styling
    if theme == "dark":
        bg_cls = "bg-gray-900"
        title_cls = "text-white"
        subtitle_cls = "text-gray-300"
        description_cls = "text-gray-400"
        input_cls = "bg-gray-800 text-white border-gray-700 placeholder-gray-400"
        button_cls = "bg-blue-600 hover:bg-blue-700 text-white"
        privacy_cls = "text-gray-400"
    else:
        bg_cls = "bg-gradient-to-r from-blue-50 to-indigo-50"
        title_cls = "text-gray-900"
        subtitle_cls = "text-gray-600"
        description_cls = "text-gray-500"
        input_cls = "bg-white text-gray-900 border-gray-300 placeholder-gray-500"
        button_cls = "bg-blue-600 hover:bg-blue-700 text-white"
        privacy_cls = "text-gray-500"
    
    return Section(
        Div(
            # Header content
            Div(
                Div(
                    H2(title, cls=f"text-3xl font-bold mb-4 text-center {title_cls}"),
                    P(subtitle, cls=f"text-lg text-center mb-8 {subtitle_cls}"),
                    
                    # Optional description
                    P(description, cls=f"text-sm text-center mb-8 {description_cls}") if description else None,
                    
                    # Newsletter form
                    Form(
                        Div(
                            # Email input
                            Input(
                                type="email",
                                name="email",
                                placeholder=placeholder,
                                required=True,
                                cls=f"flex-1 px-4 py-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 {input_cls}"
                            ),
                            
                            # Subscribe button
                            Button(
                                button_text,
                                type="submit",
                                cls=f"px-6 py-3 rounded-lg font-semibold transition-colors duration-200 {button_cls}"
                            ),
                            
                            cls="flex flex-col sm:flex-row gap-4 max-w-md mx-auto"
                        ),
                        method="post",
                        action=action_url,
                        cls="mb-6"
                    ),
                    
                    # Privacy notice
                    P(
                        "We respect your privacy. Unsubscribe at any time.",
                        cls=f"text-xs text-center {privacy_cls}"
                    ) if show_privacy else None,
                    
                    cls="max-w-2xl mx-auto text-center"
                ),
                cls="container mx-auto px-4 py-16"
            ),
            cls=f"w-full {bg_cls}"
        )
    )


def NewsletterCard(
    title: str = "Subscribe to Our Newsletter",
    description: str = "Join our community and get exclusive content delivered to your inbox.",
    placeholder: str = "Your email address",
    button_text: str = "Subscribe",
    action_url: str = "#",
    compact: bool = False,
    theme: str = "light"
):
    """Compact newsletter signup card component"""
    
    # Theme-specific styling
    if theme == "dark":
        bg_cls = "bg-gray-800 border-gray-700"
        title_cls = "text-white"
        description_cls = "text-gray-300"
        input_cls = "bg-gray-700 text-white border-gray-600 placeholder-gray-400"
        button_cls = "bg-blue-600 hover:bg-blue-700 text-white"
    else:
        bg_cls = "bg-white border-gray-200"
        title_cls = "text-gray-900"
        description_cls = "text-gray-600"
        input_cls = "bg-white text-gray-900 border-gray-300 placeholder-gray-500"
        button_cls = "bg-blue-600 hover:bg-blue-700 text-white"
    
    size_cls = "p-6" if compact else "p-8"
    
    return Div(
        Div(
            # Icon or decorative element
            Div(
                Div(
                    "📧",
                    cls="text-3xl mb-4 text-center"
                ),
                cls="flex justify-center"
            ) if not compact else None,
            
            # Content
            H3(title, cls=f"text-xl font-bold mb-3 text-center {title_cls}"),
            P(description, cls=f"text-sm text-center mb-6 {description_cls}"),
            
            # Signup form
            Form(
                Div(
                    Input(
                        type="email",
                        name="email",
                        placeholder=placeholder,
                        required=True,
                        cls=f"w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 mb-3 {input_cls}"
                    ),
                    Button(
                        button_text,
                        type="submit",
                        cls=f"w-full px-4 py-2 rounded-lg font-semibold transition-colors duration-200 {button_cls}"
                    ),
                    cls="space-y-3"
                ),
                method="post",
                action=action_url
            ),
            
            cls=f"{size_cls} rounded-lg border shadow-sm"
        ),
        cls="max-w-md mx-auto"
    )


def NewsletterInline(
    title: str = "Get Updates",
    placeholder: str = "Enter your email",
    button_text: str = "Subscribe",
    action_url: str = "#",
    theme: str = "light"
):
    """Inline newsletter signup component for footers or sidebars"""
    
    # Theme-specific styling
    if theme == "dark":
        title_cls = "text-white"
        input_cls = "bg-gray-800 text-white border-gray-700 placeholder-gray-400"
        button_cls = "bg-blue-600 hover:bg-blue-700 text-white"
    else:
        title_cls = "text-gray-900"
        input_cls = "bg-white text-gray-900 border-gray-300 placeholder-gray-500"
        button_cls = "bg-blue-600 hover:bg-blue-700 text-white"
    
    return Div(
        Div(
            H4(title, cls=f"text-lg font-semibold mb-3 {title_cls}"),
            Form(
                Div(
                    Input(
                        type="email",
                        name="email",
                        placeholder=placeholder,
                        required=True,
                        cls=f"flex-1 px-3 py-2 rounded-l-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 {input_cls}"
                    ),
                    Button(
                        button_text,
                        type="submit",
                        cls=f"px-4 py-2 rounded-r-lg font-semibold transition-colors duration-200 {button_cls}"
                    ),
                    cls="flex"
                ),
                method="post",
                action=action_url
            )
        ),
        cls="w-full max-w-sm"
    )