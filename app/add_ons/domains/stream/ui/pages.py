"""Stream UI Pages - FastHTML style"""
from fasthtml.common import *
from core.ui.layout import Layout
from .components import StreamCard, VideoPlayer, ChatWidget, BroadcastControls, StreamAnalytics


def streams_list_page(streams: List[dict], user: dict = None):
    """List all streams page"""
    content = Div(
        # Header
        Div(
            H1("Live Streams", cls="text-4xl font-bold mb-4"),
            P(
                "Watch live streams or start your own broadcast",
                cls="text-xl text-gray-600 mb-8"
            ),
            Div(
                A(
                    "🎥 Start Broadcasting",
                    href="/stream/broadcast/new",
                    cls="btn btn-primary"
                ) if user else A(
                    "Sign in to broadcast",
                    href="/auth/login?redirect=/stream/broadcast/new",
                    cls="btn btn-outline"
                ),
                cls="flex justify-center"
            ),
            cls="text-center mb-12"
        ),
        
        # Live streams section
        Div(
            H2("🔴 Live Now", cls="text-2xl font-bold mb-6"),
            Div(
                *[StreamCard(stream, user) for stream in streams if stream.get('is_live')],
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
            ) if any(s.get('is_live') for s in streams) else P(
                "No live streams at the moment. Check back soon!",
                cls="text-center text-gray-500 py-8"
            ),
        ),
        
        # Recorded streams section
        Div(
            H2("📼 Recordings", cls="text-2xl font-bold mb-6"),
            Div(
                *[StreamCard(stream, user) for stream in streams if not stream.get('is_live')],
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            ),
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="Live Streams | FastApp")


def watch_page(stream: dict, ice_servers: List[dict], user: dict = None):
    """Watch stream page"""
    content = Div(
        Div(
            # Main video player (left side)
            Div(
                VideoPlayer(stream, ice_servers),
                cls="lg:col-span-3"
            ),
            
            # Chat widget (right side)
            Div(
                ChatWidget(stream['id']) if user else Div(
                    H3("Chat", cls="text-lg font-bold mb-4"),
                    P("Sign in to join the chat", cls="text-center text-gray-500 py-8"),
                    A(
                        "Sign In",
                        href=f"/auth/login?redirect=/stream/watch/{stream['id']}",
                        cls="btn btn-primary w-full"
                    ),
                    cls="card bg-base-100 shadow-lg p-6"
                ),
                cls="lg:col-span-1"
            ),
            
            cls="grid grid-cols-1 lg:grid-cols-4 gap-6"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    # Add WebRTC script
    content = Div(
        content,
        Script(src="/static/js/webrtc-player.js"),
        Script(
            f"""
            window.addEventListener('DOMContentLoaded', () => {{
                initPlayer({stream['id']}, {ice_servers});
            }});
            """
        )
    )
    
    return Layout(content, title=f"{stream['title']} | FastApp")


def broadcast_page(stream: dict, ice_servers: List[dict]):
    """Broadcast control page for streamers"""
    content = Div(
        H1(f"Broadcasting: {stream['title']}", cls="text-3xl font-bold mb-8"),
        
        Div(
            # Broadcast controls (left)
            Div(
                BroadcastControls(stream),
                cls="lg:col-span-2"
            ),
            
            # Analytics (right)
            Div(
                StreamAnalytics({
                    "viewers": stream.get('viewer_count', 0),
                    "likes": 0,
                    "chat_messages": 0,
                    "avg_watch_duration": 0
                }),
                cls="lg:col-span-1"
            ),
            
            cls="grid grid-cols-1 lg:grid-cols-3 gap-6"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    # Add WebRTC broadcast script
    content = Div(
        content,
        Script(src="/static/js/webrtc-broadcast.js"),
        Script(
            f"""
            window.addEventListener('DOMContentLoaded', () => {{
                initBroadcast({stream['id']}, {ice_servers});
            }});
            """
        )
    )
    
    return Layout(content, title=f"Broadcast: {stream['title']} | FastApp")