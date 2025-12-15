"""Membership and subscription routes"""
from fasthtml.common import *
from core.ui.layout import Layout
from core.utils.logger import get_logger
from core.services.auth import get_current_user_from_context
from app.add_ons.domains.stream.services.membership_service import MembershipService
from app.add_ons.domains.stream.models.membership import MembershipTier

logger = get_logger(__name__)

router_membership = APIRouter()


@router_membership.get("/stream/membership")
async def membership_page(request: Request):
    """Membership management page"""
    user = get_current_user_from_context()
    
    if not user:
        return RedirectResponse("/auth/login?redirect=/stream/membership")
    
    use_db = not getattr(request.app.state, "demo", False)
    service = MembershipService(use_db=use_db)
    memberships = await service.get_user_memberships(user['id'])
    
    content = Div(
        H1("My Memberships", cls="text-3xl font-bold mb-8"),
        
        # Active memberships
        (Div(
            H2("Active Subscriptions", cls="text-2xl font-bold mb-4"),
            Div(
                *[MembershipCard(m) for m in memberships],
                cls="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8"
            ),
        ) if memberships else Div(
            H2("No Active Memberships", cls="text-2xl font-bold mb-4"),
            P("Subscribe to channels to support creators and access exclusive content", cls="text-gray-600 mb-4"),
            A("Browse Streams", href="/stream", cls="btn btn-primary"),
            cls="text-center py-12 bg-base-200 rounded-lg"
        )),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="My Memberships | FastApp")


def MembershipCard(membership):
    """Display active membership"""
    return Div(
        Div(
            H3(f"{membership.tier.value.title()} Member", cls="text-xl font-bold mb-2"),
            P(f"Channel: {membership.channel_owner_id}", cls="text-gray-600 mb-4"),
            
            # Status
            Div(
                Span(membership.status.upper(), cls=f"badge badge-{'success' if membership.is_active() else 'error'}"),
                Span(f"{membership.days_remaining()} days left", cls="badge badge-ghost ml-2"),
                cls="mb-4"
            ),
            
            # Actions
            Div(
                A("View Channel", href=f"/stream/channel/{membership.channel_owner_id}", cls="btn btn-sm btn-primary mr-2"),
                Button(
                    "Cancel",
                    cls="btn btn-sm btn-error",
                    hx_post=f"/stream/membership/cancel/{membership.id}",
                    hx_confirm="Are you sure? Access will continue until period end.",
                    hx_target="closest .card"
                ),
                cls="flex gap-2"
            ),
        ),
        cls="card bg-base-100 shadow-lg p-6"
    )


@router_membership.post("/stream/membership/subscribe")
async def subscribe(
    request: Request,
    tier: str = Form(...),
    channel_owner_id: int = Form(...)
):
    """Subscribe to a channel (MVP: direct DB write; Stripe integration comes later)."""
    user = get_current_user_from_context()
    
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    use_db = not getattr(request.app.state, "demo", False)
    service = MembershipService(use_db=use_db)

    try:
        tier_enum = MembershipTier(tier)
    except Exception:
        tier_enum = MembershipTier.BASIC

    membership = await service.create_membership(
        user_id=user['id'],
        channel_owner_id=channel_owner_id,
        tier=tier_enum,
    )

    return Response(
        status_code=303,
        headers={"HX-Redirect": f"/stream/membership/success?id={membership.id}"},
    )


@router_membership.post("/stream/membership/cancel/{membership_id}")
async def cancel_membership(request: Request, membership_id: int):
    """Cancel membership (MVP: mark canceled)."""
    user = get_current_user_from_context()
    
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    use_db = not getattr(request.app.state, "demo", False)
    service = MembershipService(use_db=use_db)

    membership = await service.get_membership_by_id(membership_id)
    if not membership:
        return Div("Membership not found", cls="alert alert-error")
    if membership.user_id != user['id']:
        return Div("Permission denied", cls="alert alert-error")

    ok = await service.cancel_membership(membership_id)
    if not ok:
        return Div("Failed to cancel membership", cls="alert alert-error")

    return Div(
        "Membership canceled. Access continues until period end.",
        cls="alert alert-info",
    )


@router_membership.get("/stream/membership/success")
async def subscription_success(request: Request, id: int):
    """Subscription success page"""
    user = get_current_user_from_context()
    
    content = Div(
        Div(
            H1("🎉 Subscription Successful!", cls="text-4xl font-bold mb-4"),
            P("Thank you for subscribing! You now have access to exclusive content.", cls="text-xl text-gray-600 mb-8"),
            
            Div(
                A("View My Memberships", href="/stream/membership", cls="btn btn-primary mr-2"),
                A("Browse Streams", href="/stream", cls="btn btn-outline"),
                cls="flex gap-2 justify-center"
            ),
            
            cls="text-center py-12"
        ),
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="Subscription Successful | FastApp")