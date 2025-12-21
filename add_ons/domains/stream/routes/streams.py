"""Stream Routes - Following FastHTML pattern"""
from fasthtml.common import *
import os
from core.ui.layout import Layout
from core.utils.logger import get_logger
from core.services.auth import get_current_user_from_context
from add_ons.domains.stream.services.stream_service import StreamService
from add_ons.domains.stream.ui.pages import streams_list_page, watch_page, broadcast_page
from add_ons.domains.stream.ui.components import StreamCard
from add_ons.domains.stream.services.paywall_service import PaywallService
from add_ons.domains.stream.services.purchase_service import PurchaseService
from add_ons.domains.stream.services.signaling_service import SignalingService
from add_ons.domains.stream.services.chat_service import ChatService
from add_ons.domains.stream.services.youtube_service import YouTubeService
from add_ons.domains.stream.services.membership_service import MembershipService
from add_ons.domains.stream.services.attendance_service import AttendanceService
from core.integrations.storage.s3_client import StorageService
from core.integrations.storage.models import UploadUrlRequest


logger = get_logger(__name__)

# Initialize router
router_streams = APIRouter()

# Ice servers config (move to settings in production)
def _get_ice_servers() -> list[dict]:
    stun_list = os.getenv("STUN_SERVERS", "stun:stun.l.google.com:19302").split(",")
    ice = [{"urls": s.strip()} for s in stun_list if s.strip()]

    turn_url = os.getenv("TURN_URL")
    turn_user = os.getenv("TURN_USERNAME")
    turn_pass = os.getenv("TURN_PASSWORD")
    if turn_url and turn_user and turn_pass:
        ice.append(
            {
                "urls": turn_url,
                "username": turn_user,
                "credential": turn_pass,
            }
        )
    return ice


def _use_db(request: Request) -> bool:
    return not getattr(request.app.state, "demo", False)


def _require_stream_manager(user: dict):
    if not user:
        return False
    role = user.get("role")
    return role in {"stream_admin", "streamer", "admin", "super_admin"}


@router_streams.get("/stream/webrtc/config")
async def webrtc_config(request: Request):
    """Return ICE server configuration for WebRTC clients."""
    return JSONResponse({"iceServers": _get_ice_servers()})


@router_streams.post("/stream/webrtc/{room}/offer")
async def webrtc_post_offer(request: Request, room: str):
    payload = await request.json()
    svc = SignalingService()
    await svc.set_offer(room, payload)
    return JSONResponse({"status": "ok"})


@router_streams.post("/stream/webrtc/{room}/offer/{viewer_id}")
async def webrtc_post_offer_viewer(request: Request, room: str, viewer_id: str):
    """Viewer posts an offer for broadcaster to answer (multi-viewer)."""
    payload = await request.json()
    svc = SignalingService()
    await svc.set_viewer_offer(room, viewer_id, payload)
    return JSONResponse({"status": "ok"})


@router_streams.get("/stream/webrtc/{room}/offers/next")
async def webrtc_next_offer(request: Request, room: str):
    """Broadcaster pops next pending viewer offer (multi-viewer)."""
    svc = SignalingService()
    nxt = await svc.pop_next_offer(room)
    return JSONResponse(nxt or {})


@router_streams.get("/stream/webrtc/{room}/offer")
async def webrtc_get_offer(request: Request, room: str):
    svc = SignalingService()
    offer = await svc.get_offer(room)
    return JSONResponse(offer or {})


@router_streams.post("/stream/webrtc/{room}/answer")
async def webrtc_post_answer(request: Request, room: str):
    payload = await request.json()
    svc = SignalingService()
    await svc.set_answer(room, payload)
    return JSONResponse({"status": "ok"})


@router_streams.post("/stream/webrtc/{room}/answer/{viewer_id}")
async def webrtc_post_answer_viewer(request: Request, room: str, viewer_id: str):
    """Broadcaster posts an answer for a specific viewer (multi-viewer)."""
    payload = await request.json()
    svc = SignalingService()
    await svc.set_viewer_answer(room, viewer_id, payload)
    return JSONResponse({"status": "ok"})


@router_streams.get("/stream/webrtc/{room}/answer")
async def webrtc_get_answer(request: Request, room: str):
    svc = SignalingService()
    answer = await svc.get_answer(room)
    return JSONResponse(answer or {})


@router_streams.get("/stream/webrtc/{room}/answer/{viewer_id}")
async def webrtc_get_answer_viewer(request: Request, room: str, viewer_id: str):
    """Viewer polls for their answer (multi-viewer)."""
    svc = SignalingService()
    answer = await svc.get_viewer_answer(room, viewer_id)
    return JSONResponse(answer or {})


@router_streams.post("/stream/webrtc/{room}/candidates/from-viewer/{viewer_id}")
async def webrtc_post_candidate_from_viewer(request: Request, room: str, viewer_id: str):
    """Viewer trickles ICE candidates to broadcaster."""
    payload = await request.json()
    svc = SignalingService()
    await svc.push_viewer_candidate(room, viewer_id, payload)
    return JSONResponse({"status": "ok"})


@router_streams.get("/stream/webrtc/{room}/candidates/from-viewer/{viewer_id}")
async def webrtc_get_candidates_from_viewer(request: Request, room: str, viewer_id: str):
    """Broadcaster polls ICE candidates from a specific viewer."""
    max_items = int(request.query_params.get("max", "50"))
    svc = SignalingService()
    cands = await svc.pop_viewer_candidates(room, viewer_id, max_items=max_items)
    return JSONResponse({"candidates": cands})


@router_streams.post("/stream/webrtc/{room}/candidates/from-broadcaster/{viewer_id}")
async def webrtc_post_candidate_from_broadcaster(request: Request, room: str, viewer_id: str):
    """Broadcaster trickles ICE candidates to a specific viewer."""
    payload = await request.json()
    svc = SignalingService()
    await svc.push_broadcaster_candidate(room, viewer_id, payload)
    return JSONResponse({"status": "ok"})


@router_streams.get("/stream/webrtc/{room}/candidates/from-broadcaster/{viewer_id}")
async def webrtc_get_candidates_from_broadcaster(request: Request, room: str, viewer_id: str):
    """Viewer polls ICE candidates from broadcaster."""
    max_items = int(request.query_params.get("max", "50"))
    svc = SignalingService()
    cands = await svc.pop_broadcaster_candidates(room, viewer_id, max_items=max_items)
    return JSONResponse({"candidates": cands})


@router_streams.post("/stream/webrtc/{room}/disconnect/{viewer_id}")
async def webrtc_disconnect(request: Request, room: str, viewer_id: str):
    """Cleanup viewer-specific signaling keys in Redis."""
    svc = SignalingService()
    await svc.cleanup_viewer(room, viewer_id)
    return JSONResponse({"status": "ok"})


@router_streams.get("/stream/upload-url")
async def get_presigned_upload_url(
    request: Request,
    filename: str,
    content_type: str = "application/octet-stream",
    level: str = "app",
):
    """Generate a presigned upload URL for stream recordings/assets."""
    user = get_current_user_from_context()

    storage = StorageService()
    req = UploadUrlRequest(
        domain="stream",
        level=level,
        filename=filename,
        content_type=content_type,
        user_id=str(user["id"]) if (user and level == "user") else None,
        expires_in=900,
    )
    resp = storage.generate_upload_url(req)
    return JSONResponse(resp.dict())


@router_streams.post("/stream/youtube/create/{stream_id}")
async def youtube_create_broadcast(request: Request, stream_id: int):
    user = get_current_user_from_context()
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    if not _require_stream_manager(user):
        return JSONResponse({"error": "Insufficient permissions"}, status_code=403)

    use_db = _use_db(request)
    stream_service = StreamService(use_db=use_db)
    stream = await stream_service.get_stream(stream_id)
    if not stream:
        return Div("Stream not found", cls="alert alert-error")
    if stream.get("owner_id") != user.get("id"):
        return Div("Permission denied", cls="alert alert-error")

    yt = YouTubeService()
    try:
        info = await yt.create_and_bind_broadcast(
            title=stream.get("title") or f"Stream {stream_id}",
            description=stream.get("description") or "",
            privacy_status=os.getenv("YOUTUBE_PRIVACY", "public"),
        )
    except Exception as e:
        return Div(str(e), cls="alert alert-error", id="youtube-info")

    update_fields = {
        "yt_broadcast_id": info.get("broadcast_id"),
        "yt_stream_id": info.get("stream_id"),
        "yt_ingest_url": info.get("ingest_url"),
        "yt_stream_key": info.get("stream_key"),
        "yt_watch_url": info.get("watch_url"),
    }

    if use_db:
        await stream_service.db.update_document(
            "streams",
            {"id": stream_id},
            {"$set": update_fields},
        )
    else:
        stream.update(update_fields)

    return Div(
        H4("YouTube Live", cls="font-semibold mb-2"),
        Div(
            P("RTMP URL: ", Span(update_fields.get("yt_ingest_url") or "", cls="font-mono text-sm")),
            P("Stream Key: ", Span(update_fields.get("yt_stream_key") or "", cls="font-mono text-sm")),
            P(
                "Watch URL: ",
                A(
                    update_fields.get("yt_watch_url") or "",
                    href=update_fields.get("yt_watch_url") or "#",
                    target="_blank",
                    cls="link",
                ),
            ),
            cls="text-sm",
        ),
        id="youtube-info",
        cls="card bg-base-200 p-4 mt-4",
        style="",
    )


@router_streams.post("/stream/youtube/start/{stream_id}")
async def youtube_start_broadcast(request: Request, stream_id: int):
    user = get_current_user_from_context()
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    use_db = _use_db(request)
    stream_service = StreamService(use_db=use_db)
    stream = await stream_service.get_stream(stream_id)
    if not stream:
        return Div("Stream not found", cls="alert alert-error")
    if stream.get("owner_id") != user.get("id"):
        return Div("Permission denied", cls="alert alert-error")

    broadcast_id = stream.get("yt_broadcast_id")
    if not broadcast_id:
        return Div("YouTube broadcast not created", cls="alert alert-error")

    yt = YouTubeService()
    try:
        result = await yt.start_broadcast(str(broadcast_id))
    except Exception as e:
        return Div(str(e), cls="alert alert-error")

    return Div(
        f"YouTube status: {result.get('status')}",
        cls="alert alert-info",
        id="youtube-status",
    )


@router_streams.post("/stream/youtube/end/{stream_id}")
async def youtube_end_broadcast(request: Request, stream_id: int):
    user = get_current_user_from_context()
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    use_db = _use_db(request)
    stream_service = StreamService(use_db=use_db)
    stream = await stream_service.get_stream(stream_id)
    if not stream:
        return Div("Stream not found", cls="alert alert-error")
    if stream.get("owner_id") != user.get("id"):
        return Div("Permission denied", cls="alert alert-error")

    broadcast_id = stream.get("yt_broadcast_id")
    if not broadcast_id:
        return Div("YouTube broadcast not created", cls="alert alert-error")

    yt = YouTubeService()
    try:
        result = await yt.end_broadcast(str(broadcast_id))
    except Exception as e:
        return Div(str(e), cls="alert alert-error", id="youtube-status")

    return Div(
        f"YouTube status: {result.get('status')}",
        cls="alert alert-info",
        id="youtube-status",
    )


@router_streams.get("/stream")
async def list_streams(request: Request):
    """List all streams page"""
    user = get_current_user_from_context()
    service = StreamService(use_db=_use_db(request))
    streams = await service.list_all_streams()

    attendee_service = AttendanceService(use_db=_use_db(request))
    counts = await attendee_service.counts_for_stream_ids([int(s.get("id")) for s in streams if s.get("id") is not None])

    # Enrich with attendee counts and attend/checkout actions for upcoming events
    paywall = PaywallService(use_db=_use_db(request))
    enriched = []
    for s in streams:
        s = dict(s)
        sid = int(s.get("id") or 0)
        if sid:
            s["attendee_count"] = counts.get(sid, 0)

        # Determine action for upcoming events
        if not s.get("is_live") and s.get("scheduled_start"):
            if not user:
                s["attend_action"] = "login"
            else:
                has_access, _reason, _data = await paywall.can_access_stream(user["id"], s)
                s["attend_action"] = "attend" if has_access else "checkout"

        enriched.append(s)

    return streams_list_page(enriched, user)


@router_streams.get("/stream/live")
async def list_live(request: Request):
    """List only live streams"""
    user = get_current_user_from_context()
    service = StreamService(use_db=_use_db(request))
    streams = await service.list_live_streams()
    
    return streams_list_page(streams, user)


"""Updated watch route with paywall integration"""

@router_streams.get("/stream/watch/{stream_id}")
async def watch_stream(request: Request, stream_id: int):
    """Watch a stream - with paywall check"""
    user = get_current_user_from_context()
    user_id = user['id'] if user else None
    
    # Get stream
    use_db = _use_db(request)
    stream_service = StreamService(use_db=use_db)
    stream = await stream_service.get_stream(stream_id)
    
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
    paywall_service = PaywallService(use_db=use_db)
    has_access, reason, paywall_data = await paywall_service.can_access_stream(user_id, stream)
    
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
    access_badge = await paywall_service.get_access_badge(user_id, stream)
    return watch_page(stream, _get_ice_servers(), user, access_badge=access_badge)


@router_streams.post("/stream/attend/{stream_id}")
async def attend_stream(request: Request, stream_id: int):
    """Attend an upcoming stream event. Requires access (free or member/ppv)."""
    user = get_current_user_from_context()
    if not user:
        return RedirectResponse(f"/auth/login?redirect=/stream/checkout/{stream_id}")

    use_db = _use_db(request)
    stream_service = StreamService(use_db=use_db)
    stream = await stream_service.get_stream(stream_id)
    if not stream:
        return Div("Stream not found", cls="alert alert-error")

    paywall = PaywallService(use_db=use_db)
    has_access, _reason, _data = await paywall.can_access_stream(user["id"], stream)
    if not has_access:
        return Response(status_code=303, headers={"HX-Redirect": f"/stream/checkout/{stream_id}"})

    attendance = AttendanceService(use_db=use_db)
    await attendance.add_attendee(stream_id=stream_id, user_id=user["id"])
    return Response(status_code=303, headers={"HX-Redirect": f"/stream/my-upcoming"})


@router_streams.get("/stream/checkout/{stream_id}")
async def stream_checkout(request: Request, stream_id: int):
    """Checkout page for stream access (membership or PPV)."""
    user = get_current_user_from_context()
    if not user:
        return RedirectResponse(f"/auth/login?redirect=/stream/checkout/{stream_id}")

    use_db = _use_db(request)
    stream_service = StreamService(use_db=use_db)
    stream = await stream_service.get_stream(stream_id)
    if not stream:
        return Layout(Div("Stream not found", cls="alert alert-error"), title="Not Found")

    paywall = PaywallService(use_db=use_db)
    has_access, reason, paywall_data = await paywall.can_access_stream(user["id"], stream)
    if has_access:
        return Response(status_code=303, headers={"HX-Redirect": f"/stream"})

    from app.add_ons.domains.stream.ui.paywall_components import PPVPaywall, MembershipPaywall

    if reason == "membership_required":
        return Layout(MembershipPaywall(stream, paywall_data), title="Become a Member")
    if reason == "payment_required":
        return Layout(PPVPaywall(stream, paywall_data), title="Purchase Access")

    return Layout(Div(paywall_data.get("message", "Access denied"), cls="alert alert-error"), title="Access Denied")


@router_streams.get("/stream/my-upcoming")
async def my_upcoming(request: Request):
    """List upcoming streams the user is attending."""
    user = get_current_user_from_context()
    if not user:
        return RedirectResponse("/auth/login?redirect=/stream/my-upcoming")

    use_db = _use_db(request)
    attendance = AttendanceService(use_db=use_db)
    attendances = await attendance.list_user_attendances(user_id=user["id"], limit=200)
    stream_ids = [a.stream_id for a in attendances]

    stream_service = StreamService(use_db=use_db)
    streams = await stream_service.get_streams_by_ids(stream_ids)
    by_id = {int(s.get("id") or 0): s for s in streams}

    cards = []
    for sid in stream_ids:
        s = by_id.get(int(sid))
        if not s:
            continue
        s = dict(s)
        s["attend_action"] = None
        cards.append(StreamCard(s, user))

    content = Div(
        H1("My Upcoming Streams", cls="text-3xl font-bold mb-8"),
        Div(*cards, cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6") if cards else Div(
            H2("No upcoming streams", cls="text-2xl font-bold mb-4"),
            A("Browse Streams", href="/stream", cls="btn btn-primary"),
            cls="text-center py-12 bg-base-200 rounded-lg",
        ),
        cls="container mx-auto px-4 py-8",
    )

    return Layout(content, title="My Upcoming Streams | FastApp")


@router_streams.get("/stream/broadcast/new")
async def new_broadcast(request: Request):
    """Create new broadcast"""
    user = get_current_user_from_context()
    
    if not user:
        return RedirectResponse("/auth/login?redirect=/stream/broadcast/new")

    if not _require_stream_manager(user):
        return Layout(
            Div(
                H1("Access Denied", cls="text-3xl font-bold mb-4"),
                P("Only streamers/admins can create live stream events.", cls="text-gray-600"),
                cls="text-center py-12",
            ),
            title="Access Denied",
        )
    
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

            Div(
                Label("Scheduled Start (local time)", cls="label"),
                Input(
                    type="datetime-local",
                    name="scheduled_start",
                    cls="input input-bordered w-full",
                ),
                cls="form-control mb-6",
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

    if not _require_stream_manager(user):
        return Layout(
            Div(
                H1("Access Denied", cls="text-3xl font-bold mb-4"),
                P("Only streamers/admins can manage live stream events.", cls="text-gray-600"),
                cls="text-center py-12",
            ),
            title="Access Denied",
        )
    
    service = StreamService(use_db=_use_db(request))
    stream = await service.get_stream(stream_id)
    
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
    
    return broadcast_page(stream, _get_ice_servers())


@router_streams.get("/stream/my-streams")
async def my_streams(request: Request):
    """User's streams dashboard"""
    user = get_current_user_from_context()
    
    if not user:
        return RedirectResponse("/auth/login?redirect=/stream/my-streams")

    if not _require_stream_manager(user):
        return RedirectResponse("/stream")
    
    service = StreamService(use_db=_use_db(request))
    streams = await service.get_user_streams(user['id'])
    
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
    price: float = Form(0.00),
    scheduled_start: str = Form("")
):
    """Create stream (MVP: direct service call; state machine comes later)."""
    user = get_current_user_from_context()
    
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    if not _require_stream_manager(user):
        return JSONResponse({"error": "Insufficient permissions"}, status_code=403)
    
    if not title or len(title) < 3:
        return Div(P("Title must be at least 3 characters", cls="text-error"), cls="alert alert-error")

    service = StreamService(use_db=_use_db(request))
    stream = await service.create_stream(
        owner_id=user['id'],
        title=title,
        description=description,
        visibility=visibility,
        price=price,
        scheduled_start=scheduled_start,
    )

    stream_id = int(stream.get("id"))
    return Response(
        status_code=303,
        headers={"HX-Redirect": f"/stream/broadcast/{stream_id}"},
    )

@router_streams.post("/stream/api/start/{stream_id}")
async def api_start_stream(request: Request, stream_id: int):
    """Start stream (go live)."""
    user = get_current_user_from_context()
    
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    service = StreamService(use_db=_use_db(request))
    stream = await service.get_stream(stream_id)
    if not stream:
        return JSONResponse({"error": "Stream not found"}, status_code=404)
    if stream.get('owner_id') != user['id']:
        return JSONResponse({"error": "Permission denied"}, status_code=403)

    updated = await service.start_stream(stream_id)
    if updated:
        return Div(
            "🔴 LIVE",
            cls="alert alert-success",
            id="broadcast-status"
        )
    else:
        return Div(
            "Failed to start stream",
            cls="alert alert-error",
            id="broadcast-status"
        )


@router_streams.post("/stream/api/stop/{stream_id}")
async def api_stop_stream(request: Request, stream_id: int):
    """Stop stream."""
    user = get_current_user_from_context()
    
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    service = StreamService(use_db=_use_db(request))
    stream = await service.get_stream(stream_id)
    if not stream:
        return JSONResponse({"error": "Stream not found"}, status_code=404)
    if stream.get('owner_id') != user['id']:
        return JSONResponse({"error": "Permission denied"}, status_code=403)

    updated = await service.stop_stream(stream_id)
    if updated:
        return Div(
            "⏹ Stream ended",
            cls="alert alert-info",
            id="broadcast-status"
        )
    else:
        return Div(
            "Failed to stop stream",
            cls="alert alert-error",
            id="broadcast-status"
        )


@router_streams.post("/stream/payment/purchase")
async def purchase_stream(
    request: Request,
    stream_id: int = Form(...),
    amount: float = Form(...),
    rental: bool = Form(False),
):
    """Purchase access (MVP: record purchase; Stripe integration comes later)."""
    user = get_current_user_from_context()
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    use_db = _use_db(request)
    purchase_service = PurchaseService(use_db=use_db)
    await purchase_service.create_purchase(
        user_id=user['id'],
        stream_id=stream_id,
        amount=amount,
        rental=rental,
    )

    return Response(
        status_code=303,
        headers={"HX-Redirect": f"/stream/watch/{stream_id}"},
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


@router_streams.get("/stream/chat/{stream_id}")
async def get_chat_messages(request: Request, stream_id: int):
    """Render recent chat messages for a stream (HTMX polling target)."""
    use_db = _use_db(request)
    user = get_current_user_from_context()
    stream_service = StreamService(use_db=use_db)
    stream = await stream_service.get_stream(stream_id)
    if not stream:
        return Div()
    paywall = PaywallService(use_db=use_db)
    allowed, _reason, _data = await paywall.can_access_stream(user["id"] if user else None, stream)
    if not allowed:
        return Div()
    service = ChatService(use_db=use_db)
    messages = await service.list_messages(stream_id=stream_id, limit=50)

    return Div(
        *[
            Div(
                Div(
                    Strong(m.username, cls="text-primary"),
                    Span(": "),
                    Span(m.content),
                    cls="mb-1",
                ),
                Div(
                    m.created_at.strftime("%H:%M"),
                    cls="text-xs text-gray-500",
                ),
                cls="chat-message p-2 border-b",
            )
            for m in messages
        ]
    )


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

    use_db = _use_db(request)
    stream_service = StreamService(use_db=use_db)
    stream = await stream_service.get_stream(stream_id)
    if not stream:
        return JSONResponse({"error": "Stream not found"}, status_code=404)
    paywall = PaywallService(use_db=use_db)
    allowed, _reason, _data = await paywall.can_access_stream(user["id"], stream)
    if not allowed:
        return JSONResponse({"error": "Access denied"}, status_code=403)

    service = ChatService(use_db=use_db)
    msg = await service.add_message(
        stream_id=stream_id,
        user_id=int(user.get('id')),
        username=user.get('username', 'User'),
        content=message,
    )

    return Div(
        Div(
            Strong(msg.username, cls="text-primary"),
            Span(": "),
            Span(msg.content),
            cls="mb-1",
        ),
        Div(
            msg.created_at.strftime("%H:%M"),
            cls="text-xs text-gray-500",
        ),
        cls="chat-message p-2 border-b",
    )