"""Stream Routes - Following FastHTML pattern"""
from fasthtml.common import *
from core.ui.layout import Layout
from core.utils.logger import get_logger
from core.services.auth import get_current_user_from_context
from app.add_ons.domains.stream.services.stream_service import StreamService
from app.add_ons.domains.stream.ui.pages import streams_list_page, watch_page, broadcast_page
from app.add_ons.domains.stream.ui.components import StreamCard
from app.add_ons.domains.stream.state.manager import StreamStateManager
from app.add_ons.domains.stream.state.actions import (
    CreateStreamAction, GoLiveAction, EndStreamAction
)
from app.add_ons.domains.stream.services.paywall_service import PaywallService


logger = get_logger(__name__)

# Initialize router
router_streams = APIRouter()

# Ice servers config (move to settings in production)
ICE_SERVERS = [
    {"urls": "stun:stun.l.google.com:19302"}
]

#TODO: Inject settings, integrations, analytics, tasks
# Initialize state manager (inject in app.py in production)
state_manager = StreamStateManager(
    settings=settings,
    integrations=integrations,
    analytics=analytics,
    tasks=tasks
)


@router_streams.get("/stream")
async def list_streams(request: Request):
    """List all streams page"""
    user = get_current_user_from_context()
    service = StreamService()
    streams = service.list_all_streams()
    
    return streams_list_page(streams, user)


@router_streams.get("/stream/live")
async def list_live(request: Request):
    """List only live streams"""
    user = get_current_user_from_context()
    service = StreamService()
    streams = service.list_live_streams()
    
    return streams_list_page(streams, user)


"""Updated watch route with paywall integration"""

@router_streams.get("/stream/watch/{stream_id}")
async def watch_stream(request: Request, stream_id: int):
    """Watch a stream - with paywall check"""
    user = get_current_user_from_context()
    user_id = user['id'] if user else None
    
    # Get stream
    stream_service = StreamService()
    stream = stream_service.get_stream(stream_id)
    
    if not stream:
        return Layout(
            Div(
                H1("Stream Not Found", cls="text-3xl font-bold mb-4"),
                P("The stream you're looking for doesn't exist.", cls="text-gray-600 mb-4"),
                A("Browse Streams", href="/stream", cls="btn btn-primary"),
                cls="text-center py-12"
            ),
            title="Stream Not Found"
        )
    
    # Check access
    paywall_service = PaywallService()
    has_access, reason, paywall_data = paywall_service.can_access_stream(user_id, stream)
    
    # If no access, show appropriate paywall
    if not has_access:
        if reason == "auth_required":
            return RedirectResponse(paywall_data['redirect'])
        
        elif reason == "membership_required":
            from app.add_ons.domains.stream.ui.paywall_components import MembershipPaywall
            content = Div(
                # Blurred video preview
                Div(
                    Img(
                        src=stream['thumbnail'],
                        cls="w-full h-96 object-cover filter blur-xl"
                    ),
                    cls="relative mb-8"
                ),
                
                # Paywall overlay
                MembershipPaywall(stream, paywall_data)
            )
            return Layout(content, title=f"{stream['title']} | FastApp")
        
        elif reason == "payment_required":
            from app.add_ons.domains.stream.ui.paywall_components import PPVPaywall
            content = Div(
                # Blurred video preview
                Div(
                    Img(
                        src=stream['thumbnail'],
                        cls="w-full h-96 object-cover filter blur-xl"
                    ),
                    cls="relative mb-8"
                ),
                
                # Paywall overlay
                PPVPaywall(stream, paywall_data)
            )
            return Layout(content, title=f"{stream['title']} | FastApp")
        
        else:
            from app.add_ons.domains.stream.ui.paywall_components import AccessDeniedOverlay
            return Layout(
                AccessDeniedOverlay(paywall_data.get('message', 'Access Denied')),
                title="Access Denied"
            )
    
    # User has access - show full player
    access_badge = paywall_service.get_access_badge(user_id, stream)
    return watch_page(stream, ICE_SERVERS, user, access_badge=access_badge)


@router_streams.get("/stream/broadcast/new")
async def new_broadcast(request: Request):
    """Create new broadcast"""
    user = get_current_user_from_context()
    
    if not user:
        return RedirectResponse("/auth/login?redirect=/stream/broadcast/new")
    
    # Show create form
    content = Div(
        H1("Start a New Broadcast", cls="text-3xl font-bold mb-8"),
        
        Form(
            Div(
                Label("Stream Title", cls="label"),
                Input(
                    type="text",
                    name="title",
                    placeholder="Enter stream title...",
                    cls="input input-bordered w-full",
                    required=True
                ),
                cls="form-control mb-4"
            ),
            
            Div(
                Label("Description", cls="label"),
                Textarea(
                    name="description",
                    placeholder="Tell viewers what your stream is about...",
                    cls="textarea textarea-bordered w-full",
                    rows=4
                ),
                cls="form-control mb-4"
            ),
            
            Div(
                Label("Visibility", cls="label"),
                Select(
                    Option("Public - Anyone can watch", value="public", selected=True),
                    Option("Private - Invite only", value="private"),
                    Option("Paid - Requires payment", value="paid"),
                    name="visibility",
                    cls="select select-bordered w-full"
                ),
                cls="form-control mb-4"
            ),
            
            Div(
                Label("Price (if paid)", cls="label"),
                Input(
                    type="number",
                    name="price",
                    placeholder="0.00",
                    step="0.01",
                    min="0",
                    value="0.00",
                    cls="input input-bordered w-full"
                ),
                cls="form-control mb-6"
            ),
            
            Button(
                "Create Broadcast",
                type="submit",
                cls="btn btn-primary w-full"
            ),
            
            hx_post="/stream/api/create",
            hx_target="body",
            cls="max-w-2xl mx-auto card bg-base-100 shadow-lg p-8"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="New Broadcast | FastApp")


@router_streams.get("/stream/broadcast/{stream_id}")
async def broadcast_stream(request: Request, stream_id: int):
    """Broadcast control page"""
    user = get_current_user_from_context()
    
    if not user:
        return RedirectResponse(f"/auth/login?redirect=/stream/broadcast/{stream_id}")
    
    service = StreamService()
    stream = service.get_stream(stream_id)
    
    if not stream:
        return Layout(
            Div(
                H1("Stream Not Found", cls="text-3xl font-bold"),
                cls="text-center py-12"
            ),
            title="Stream Not Found"
        )
    
    # Check ownership
    if stream['owner_id'] != user['id']:
        return Layout(
            Div(
                H1("Access Denied", cls="text-3xl font-bold mb-4"),
                P("You don't have permission to broadcast this stream.", cls="text-gray-600"),
                cls="text-center py-12"
            ),
            title="Access Denied"
        )
    
    return broadcast_page(stream, ICE_SERVERS)


@router_streams.get("/stream/my-streams")
async def my_streams(request: Request):
    """User's streams dashboard"""
    user = get_current_user_from_context()
    
    if not user:
        return RedirectResponse("/auth/login?redirect=/stream/my-streams")
    
    service = StreamService()
    streams = service.get_user_streams(user['id'])
    
    content = Div(
        H1("My Streams", cls="text-3xl font-bold mb-8"),
        
        Div(
            A(
                "➕ New Broadcast",
                href="/stream/broadcast/new",
                cls="btn btn-primary"
            ),
            cls="mb-6"
        ),
        
        Div(
            *[StreamCard(stream, user) for stream in streams],
            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        ) if streams else Div(
            H2("No streams yet", cls="text-2xl font-bold mb-4"),
            P("Start your first broadcast to get started!", cls="text-gray-600 mb-4"),
            A("Create Broadcast", href="/stream/broadcast/new", cls="btn btn-primary"),
            cls="text-center py-12 bg-base-200 rounded-lg"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="My Streams | FastApp")


# ============================================================================
# API Routes (for HTMX)
# ============================================================================

@router_streams.post("/stream/api/create")
async def api_create_stream(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    visibility: str = Form("public"),
    price: float = Form(0.00)
):
    """Create stream using state system"""
    user = get_current_user_from_context()
    
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    # Execute action via state manager
    action = CreateStreamAction(
        owner_id=user['id'],
        title=title,
        description=description,
        visibility=visibility,
        price=price
    )
    
    new_state, result = await state_manager.execute(action, user_context=user)
    
    if result.success:
        stream_id = result.data['stream_id']
        return Response(
            status_code=303,
            headers={"HX-Redirect": f"/stream/broadcast/{stream_id}"}
        )
    else:
        # Return validation errors
        return Div(
            *[P(error, cls="text-error") for error in result.errors],
            cls="alert alert-error"
        )

@router_streams.post("/stream/api/start/{stream_id}")
async def api_start_stream(request: Request, stream_id: int):
    """Start stream using state system"""
    user = get_current_user_from_context()
    
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    # Get current state
    service = StreamService()
    stream = service.get_stream(stream_id)
    
    if not stream:
        return JSONResponse({"error": "Stream not found"}, status_code=404)
    
    # Convert to StreamState (in production, load from DB)
    from app.add_ons.domains.stream.state.stream_state import StreamState
    current_state = StreamState(**stream)
    
    # Execute action
    action = GoLiveAction(stream_id=stream_id, user_id=user['id'])
    new_state, result = await state_manager.execute(action, current_state, user_context=user)
    
    if result.success:
        return Div(
            "🔴 LIVE",
            cls="alert alert-success",
            id="broadcast-status"
        )
    else:
        return Div(
            result.message,
            cls="alert alert-error",
            id="broadcast-status"
        )


@router_streams.post("/stream/api/stop/{stream_id}")
async def api_stop_stream(request: Request, stream_id: int):
    """Stop stream using state system"""
    user = get_current_user_from_context()
    
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    # Get current state
    service = StreamService()
    stream = service.get_stream(stream_id)
    
    if not stream:
        return JSONResponse({"error": "Stream not found"}, status_code=404)
    
    from app.add_ons.domains.stream.state.stream_state import StreamState
    current_state = StreamState(**stream)
    
    # Execute action
    action = EndStreamAction(stream_id=stream_id, user_id=user['id'])
    new_state, result = await state_manager.execute(action, current_state, user_context=user)
    
    if result.success:
        return Div(
            "⏹ Stream ended",
            cls="alert alert-info",
            id="broadcast-status"
        )
    else:
        return Div(
            result.message,
            cls="alert alert-error",
            id="broadcast-status"
        )


@router_streams.get("/stream/api/analytics")
async def api_analytics(request: Request):
    """API: Get live analytics (mock for demo)"""
    import random
    
    metrics = {
        "viewers": random.randint(10, 200),
        "likes": random.randint(0, 50),
        "chat_messages": random.randint(0, 100),
        "avg_watch_duration": random.randint(60, 1800)
    }
    
    from app.add_ons.domains.stream.ui.components import StreamAnalytics
    return StreamAnalytics(metrics)


@router_streams.post("/stream/chat/{stream_id}/send")
async def api_send_chat(
    request: Request,
    stream_id: int,
    message: str = Form(...)
):
    """API: Send chat message"""
    user = get_current_user_from_context()
    
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    # In real app: save to DB and broadcast via WebSocket
    # For demo: return the message as HTML
    from datetime import datetime
    
    return Div(
        Div(
            Strong(user.get('username', 'User'), cls="text-primary"),
            Span(": "),
            Span(message),
            cls="mb-1"
        ),
        Div(
            datetime.now().strftime("%H:%M"),
            cls="text-xs text-gray-500"
        ),
        cls="chat-message p-2 border-b"
    )