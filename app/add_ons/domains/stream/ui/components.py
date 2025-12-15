"""Stream UI Components - FastHTML style"""
from fasthtml.common import *
from enum import Enum
from datetime import datetime
from typing import List


"""Updated StreamCard with paywall integration"""

def StreamCard(stream: dict, user: dict = None, access_badge: str = None):
    """Stream card with membership/purchase indicators"""
    is_live = stream.get('is_live', False)
    visibility = stream.get('visibility', 'public')
    price = stream.get('price', 0.00)
    required_tier = stream.get('required_tier', 'basic')
    if required_tier is None:
        required_tier = 'basic'
    if isinstance(required_tier, Enum):
        required_tier = required_tier.value
    viewer_count = stream.get('viewer_count', 0)
    scheduled_start = stream.get('scheduled_start')
    attendee_count = stream.get('attendee_count')
    attend_action = stream.get('attend_action')

    if isinstance(scheduled_start, datetime):
        scheduled_start = scheduled_start.strftime("%Y-%m-%d %H:%M")
    
    # Access indicators
    if visibility == 'member':
        access_indicator = Span(
            f"⭐ {required_tier.title()} Members",
            cls="badge badge-primary"
        )
    elif price > 0:
        access_indicator = Span(
            f"💳 ${price}",
            cls="badge badge-secondary"
        )
    else:
        access_indicator = Span(
            "🆓 FREE",
            cls="badge badge-success"
        )
    
    # User's access badge (if they have access)
    user_badge = MemberBadge(access_badge) if access_badge else None
    
    return Div(
        # Thumbnail with overlays
        Div(
            Img(
                src=stream['thumbnail'],
                alt=stream['title'],
                cls="w-full h-40 object-cover"
            ),
            
            # Top left: Live/Offline + Viewers
            Div(
                (Span("🔴 LIVE", cls="badge badge-error text-white") if is_live else 
                 Span("OFFLINE", cls="badge badge-ghost")),
                (Span(f"👁 {viewer_count}", cls="badge badge-neutral ml-2") if is_live else None),
                cls="absolute top-2 left-2"
            ),
            
            # Top right: Access type
            Div(
                access_indicator,
                cls="absolute top-2 right-2"
            ),
            
            # User's access badge
            user_badge,
            
            cls="relative"
        ),
        
        # Stream info
        Div(
            H3(stream['title'], cls="text-lg font-semibold mb-2"),
            (P(
                f"🗓 {scheduled_start}",
                cls="text-xs text-gray-500 mb-2"
            ) if scheduled_start else None),
            P(
                stream['description'][:80] + ("..." if len(stream['description']) > 80 else ""),
                cls="text-sm text-gray-600 mb-3"
            ),
            P(
                f"by {stream.get('owner_name', 'Unknown')}",
                cls="text-xs text-gray-500 mb-4"
            ),
            (P(
                f"👥 {attendee_count} attending" if attendee_count is not None else "",
                cls="text-xs text-gray-500 mb-3"
            ) if attendee_count is not None else None),
            
            # Action button
            (Form(
                Button(
                    "Attend",
                    type="submit",
                    cls="btn btn-primary btn-sm w-full"
                ),
                method="post",
                action=f"/stream/attend/{stream['id']}",
                hx_post=f"/stream/attend/{stream['id']}",
                hx_target="body",
            ) if attend_action == "attend" else (
                A(
                    "Sign in to attend",
                    href=f"/auth/login?redirect=/stream/checkout/{stream['id']}",
                    cls="btn btn-outline btn-sm w-full"
                ) if attend_action == "login" else (
                A(
                    "Checkout",
                    href=f"/stream/checkout/{stream['id']}",
                    cls="btn btn-secondary btn-sm w-full"
                ) if attend_action == "checkout" else A(
                    "Watch Now" if is_live else "View Stream",
                    href=f"/stream/watch/{stream['id']}",
                    cls="btn btn-primary btn-sm w-full"
                )
            ))),
            
            cls="p-4"
        ),
        
        cls="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow"
    )


def VideoPlayer(stream: dict, ice_servers: List[dict] = None):
    """Video player component for watching streams"""
    is_live = stream.get('is_live', False)
    
    return Div(
        # Video element
        Div(
            Video(
                id="stream-video",
                cls="w-full aspect-video bg-black rounded-lg",
                controls=True,
                autoplay=is_live,
                playsinline=True
            ),
            cls="mb-4"
        ),
        
        # Stream info bar
        Div(
            Div(
                H2(stream['title'], cls="text-2xl font-bold"),
                P(f"by {stream.get('owner_name', 'Unknown')}", cls="text-gray-600"),
                cls="flex-1"
            ),
            Div(
                Span(
                    f"👁 {stream.get('viewer_count', 0)} watching",
                    cls="badge badge-lg"
                ) if is_live else None,
                cls="flex items-center gap-2"
            ),
            cls="flex items-center justify-between p-4 bg-base-200 rounded-lg"
        ),
        
        # Description
        P(
            stream['description'],
            cls="mt-4 text-gray-700"
        ),
        
        # WebRTC initialization script
        Script(
            f"""
            window.streamId = {stream['id']};
            window.iceServers = {ice_servers or []};
            // WebRTC initialization would go here
            """
        ) if is_live else None,
    )


def ChatWidget(stream_id: int):
    """Live chat widget"""
    return Div(
        # Chat header
        Div(
            H3("Live Chat", cls="text-lg font-bold"),
            Span(
                "🟢 Online",
                cls="badge badge-sm badge-success"
            ),
            cls="flex items-center justify-between mb-4 pb-2 border-b"
        ),
        
        # Chat messages container
        Div(
            id=f"chat-{stream_id}",
            cls="h-96 overflow-y-auto mb-4 p-2 bg-base-200 rounded",
            hx_get=f"/stream/chat/{stream_id}",
            hx_trigger="load, every 2s",
            hx_swap="innerHTML",
        ),
        
        # Chat input
        Form(
            Input(
                type="text",
                name="message",
                placeholder="Type a message...",
                cls="input input-bordered w-full",
                required=True
            ),
            Button(
                "Send",
                type="submit",
                cls="btn btn-primary mt-2"
            ),
            hx_post=f"/stream/chat/{stream_id}/send",
            hx_target=f"#chat-{stream_id}",
            hx_swap="beforeend",
            cls="flex flex-col gap-2"
        ),
        
        cls="card bg-base-100 shadow-lg p-4"
    )


def BroadcastControls(stream: dict):
    """Broadcast control panel for streamers"""
    is_live = stream.get('is_live', False)
    
    return Div(
        H3("Broadcast Controls", cls="text-xl font-bold mb-4"),
        
        # Preview
        Div(
            Video(
                id="preview-video",
                cls="w-full aspect-video bg-black rounded-lg mb-4",
                autoplay=True,
                muted=True,
                playsinline=True
            ),
        ),
        
        # Control buttons
        Div(
            Button(
                "🎥 Go Live (WebRTC)" if not is_live else "⏹ Stop Stream",
                id="btn-go-live",
                cls=f"btn {'btn-error' if is_live else 'btn-primary'} flex-1",
                hx_post=f"/stream/api/{'stop' if is_live else 'start'}/{stream['id']}",
                hx_swap="outerHTML",
                hx_target="#broadcast-status"
            ),
            Button(
                "📺 Broadcast on YouTube",
                id="btn-youtube",
                cls="btn btn-secondary flex-1",
                hx_post=f"/stream/youtube/create/{stream['id']}",
                hx_target="#youtube-info",
                hx_swap="outerHTML",
            ),
            cls="flex gap-2 mb-4"
        ),
        
        # Status
        Div(
            id="broadcast-status",
            cls="alert alert-info"
        ),
        
        # YouTube info (if integrated)
        Div(
            H4("YouTube Live", cls="font-semibold mb-2"),
            Div(
                Button(
                    "Start",
                    cls="btn btn-sm btn-primary",
                    hx_post=f"/stream/youtube/start/{stream['id']}",
                    hx_target="#youtube-status",
                    hx_swap="outerHTML",
                ),
                Button(
                    "End",
                    cls="btn btn-sm btn-error",
                    hx_post=f"/stream/youtube/end/{stream['id']}",
                    hx_target="#youtube-status",
                    hx_swap="outerHTML",
                ),
                cls="flex gap-2 mb-3",
            ),
            Div(id="youtube-status", cls="alert alert-info"),
            Div(
                P("RTMP URL: ", Span(id="yt-ingest", cls="font-mono text-sm")),
                P("Stream Key: ", Span(id="yt-key", cls="font-mono text-sm")),
                P("Watch URL: ", A(id="yt-watch", href="#", children=["(pending)"])),
                cls="text-sm"
            ),
            cls="card bg-base-200 p-4 mt-4",
            id="youtube-info",
            style=""
        ),
        
        cls="card bg-base-100 shadow-lg p-6"
    )


def StreamAnalytics(metrics: dict):
    """Stream analytics widget"""
    return Div(
        H3("Live Analytics", cls="text-lg font-bold mb-4"),
        
        # Metrics grid
        Div(
            # Viewers
            Div(
                Div("👁", cls="text-3xl mb-2"),
                Div(str(metrics.get('viewers', 0)), cls="text-2xl font-bold"),
                Div("Viewers", cls="text-sm text-gray-600"),
                cls="stat bg-base-200 rounded-lg p-4 text-center"
            ),
            
            # Likes
            Div(
                Div("❤️", cls="text-3xl mb-2"),
                Div(str(metrics.get('likes', 0)), cls="text-2xl font-bold"),
                Div("Likes", cls="text-sm text-gray-600"),
                cls="stat bg-base-200 rounded-lg p-4 text-center"
            ),
            
            # Chat messages
            Div(
                Div("💬", cls="text-3xl mb-2"),
                Div(str(metrics.get('chat_messages', 0)), cls="text-2xl font-bold"),
                Div("Messages", cls="text-sm text-gray-600"),
                cls="stat bg-base-200 rounded-lg p-4 text-center"
            ),
            
            # Watch time
            Div(
                Div("⏱", cls="text-3xl mb-2"),
                Div(f"{metrics.get('avg_watch_duration', 0) // 60}m", cls="text-2xl font-bold"),
                Div("Avg Watch", cls="text-sm text-gray-600"),
                cls="stat bg-base-200 rounded-lg p-4 text-center"
            ),
            
            cls="grid grid-cols-2 md:grid-cols-4 gap-4"
        ),
        
        cls="card bg-base-100 shadow-lg p-6",
        id="stream-analytics",
        hx_get=f"/stream/api/analytics",
        hx_trigger="every 5s",
        hx_swap="outerHTML"
    )