"""Paywall UI components"""
from fasthtml.common import *
from app.add_ons.domains.stream.models.membership import MembershipTier


def MembershipPaywall(stream: dict, paywall_data: dict):
    """Membership paywall - subscribe to access"""
    tiers = paywall_data.get('tiers', [])
    channel_owner_id = paywall_data.get('channel_owner_id')
    
    return Div(
        # Paywall overlay
        Div(
            Div(
                # Header
                Div(
                    H2("🔒 Member-Only Content", cls="text-3xl font-bold mb-2"),
                    P(
                        paywall_data.get('message', 'Subscribe to access this stream'),
                        cls="text-lg text-gray-600 mb-8"
                    ),
                    cls="text-center"
                ),
                
                # Membership tiers
                Div(
                    *[MembershipTierCard(tier, channel_owner_id) for tier in tiers],
                    cls="grid grid-cols-1 md:grid-cols-3 gap-6"
                ),
                
                cls="max-w-6xl mx-auto"
            ),
            cls="bg-base-100 p-8 rounded-lg shadow-2xl"
        ),
        cls="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
    )


def MembershipTierCard(tier: dict, channel_owner_id: int):
    """Individual membership tier option"""
    is_recommended = tier.get('recommended', False)
    
    return Div(
        # Recommended badge
        (Div(
            "⭐ RECOMMENDED",
            cls="badge badge-primary absolute -top-3 left-1/2 -translate-x-1/2"
        ) if is_recommended else None),
        
        # Tier name
        H3(tier['name'], cls="text-2xl font-bold mb-2"),
        
        # Price
        Div(
            Span(f"${tier['price']}", cls="text-4xl font-bold"),
            Span("/month", cls="text-gray-600"),
            cls="mb-6"
        ),
        
        # Perks
        Div(
            H4("Includes:", cls="font-semibold mb-3"),
            Ul(
                *[Li(
                    Span("✓ ", cls="text-success font-bold"),
                    Span(perk),
                    cls="mb-2"
                ) for perk in tier.get('perks', [])],
                cls="space-y-2"
            ),
            cls="mb-6 text-left"
        ),
        
        # Subscribe button
        Button(
            "Subscribe Now",
            cls=f"btn btn-primary w-full {'btn-lg' if is_recommended else ''}",
            hx_post=f"/stream/membership/subscribe",
            hx_vals=f'{{"tier": "{tier["tier"]}", "channel_owner_id": {channel_owner_id}}}',
            hx_target="body"
        ),
        
        cls=f"card bg-base-200 shadow-xl p-6 text-center relative {'ring-2 ring-primary' if is_recommended else ''}"
    )


def PPVPaywall(stream: dict, paywall_data: dict):
    """Pay-per-view paywall - purchase to access"""
    options = paywall_data.get('options', [])
    stream_id = paywall_data.get('stream_id')
    
    return Div(
        Div(
            Div(
                # Header
                Div(
                    H2("💳 Purchase Access", cls="text-3xl font-bold mb-2"),
                    P(
                        paywall_data.get('message', 'Purchase this stream to watch'),
                        cls="text-lg text-gray-600 mb-8"
                    ),
                    cls="text-center"
                ),
                
                # Purchase options
                Div(
                    *[PPVOptionCard(option, stream_id) for option in options],
                    cls="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto"
                ),
                
                # Back button
                Div(
                    A(
                        "← Back to Streams",
                        href="/stream",
                        cls="btn btn-ghost"
                    ),
                    cls="text-center mt-8"
                ),
                
                cls="max-w-6xl mx-auto"
            ),
            cls="bg-base-100 p-8 rounded-lg shadow-2xl"
        ),
        cls="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
    )


def PPVOptionCard(option: dict, stream_id: int):
    """Individual PPV purchase option"""
    is_lifetime = option.get('type') == 'lifetime'
    
    return Div(
        # Option type badge
        Div(
            "🌟 BEST VALUE" if is_lifetime else "⏱ SHORT TERM",
            cls=f"badge {'badge-primary' if is_lifetime else 'badge-secondary'} mb-4"
        ),
        
        # Duration
        H3(option['duration'], cls="text-2xl font-bold mb-2"),
        
        # Price
        Div(
            Span(f"${option['price']}", cls="text-4xl font-bold"),
            cls="mb-6"
        ),
        
        # Description
        P(
            "Watch anytime, forever" if is_lifetime else "48 hours of access",
            cls="text-gray-600 mb-6"
        ),
        
        # Purchase button
        Button(
            "Purchase Now",
            cls=f"btn btn-primary w-full {'btn-lg' if is_lifetime else ''}",
            hx_post=f"/stream/payment/purchase",
            hx_vals=f'{{"stream_id": {stream_id}, "amount": {option["price"]}, "rental": {"true" if not is_lifetime else "false"}}}',
            hx_target="body"
        ),
        
        cls=f"card bg-base-200 shadow-xl p-6 text-center {'ring-2 ring-primary' if is_lifetime else ''}"
    )


def MemberBadge(badge_text: str):
    """Member badge to show on stream cards"""
    if not badge_text:
        return None
    
    return Div(
        badge_text,
        cls="badge badge-primary absolute top-2 left-2 z-10"
    )


def AccessDeniedOverlay(message: str = "Access Denied"):
    """Simple access denied overlay"""
    return Div(
        Div(
            Div(
                H2("🔒", cls="text-6xl mb-4"),
                H3(message, cls="text-2xl font-bold mb-4"),
                P("You don't have access to this content", cls="text-gray-600 mb-6"),
                A(
                    "Browse Streams",
                    href="/stream",
                    cls="btn btn-primary"
                ),
                cls="text-center"
            ),
            cls="bg-base-100 p-12 rounded-lg shadow-2xl max-w-md"
        ),
        cls="fixed inset-0 bg-black/80 flex items-center justify-center z-50"
    )