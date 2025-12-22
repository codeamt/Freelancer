"""
Shared UI Components for Example Applications

Common components used across social, streaming, and other example apps
with proper MonsterUI styling and theming.
"""

from fasthtml.common import *
from monsterui.all import *


# Social Components
def PostComposer(placeholder: str = "What's on your mind?", action_url: str = "/posts"):
    """Post composer component"""
    return Card(
        Div(
            H3("Create Post", cls="text-lg font-semibold mb-4"),
            Form(
                Textarea(
                    name="content",
                    placeholder=placeholder,
                    cls="w-full p-3 border rounded-lg resize-none",
                    rows=3
                ),
                Button("Post", type="submit", cls="btn btn-primary mt-2"),
                method="post",
                action=action_url,
                cls="space-y-2"
            ),
            cls="p-6"
        )
    )


def PostCard(post_data: dict, current_user_id: int):
    """Individual post card component"""
    
    post_id = post_data.get("id")
    user_id = post_data.get("user_id")
    content = post_data.get("content", "")
    is_public = post_data.get("is_public", False)
    like_count = post_data.get("like_count", 0)
    
    return Card(
        Div(
            Div(
                B(f"User {user_id}"),
                Span(" • "),
                Span("Public" if is_public else "Followers", cls="text-xs px-2 py-1 rounded bg-gray-100"),
                cls="mb-2"
            ),
            P(content or "No content", cls="mb-3"),
            Div(
                Button(f"❤️ {like_count}", cls="btn btn-sm btn-outline-secondary"),
                Button("💬 Comment", cls="btn btn-sm btn-outline-secondary ml-2"),
                cls="flex gap-2"
            ),
            cls="p-4"
        )
    )


def UserCard(user_data: dict, current_user_id: int):
    """User profile card component"""
    
    user_id = user_data.get("id")
    username = user_data.get("username", f"User {user_id}")
    followers_count = user_data.get("followers_count", 0)
    following_count = user_data.get("following_count", 0)
    is_following = user_data.get("is_following", False)
    
    return Card(
        Div(
            H3(username, cls="font-bold text-lg"),
            P(f"{followers_count} followers • {following_count} following", cls="text-sm text-gray-600"),
            Button(
                "Unfollow" if is_following else "Follow", 
                cls="btn btn-sm " + ("btn-secondary" if is_following else "btn-primary mt-2")
            ),
            cls="space-y-2 p-4"
        )
    )


def SocialFeed(posts: list, current_user_id: int, base_path: str = ""):
    """Complete social feed component"""
    
    return Div(
        PostComposer(action_url=f"{base_path}/posts"),
        Div(
            *[PostCard(post, current_user_id) for post in posts],
            cls="space-y-4 mt-4"
        ) if posts else P("No posts yet.", cls="text-center text-gray-500 py-8"),
        cls="max-w-2xl mx-auto"
    )


# Streaming Components
def LiveStreamCard(title: str, description: str, stream_url: str, snapshot_url: str):
    """Live streaming card component"""
    return Card(
        Div(
            H3(title, cls="text-xl font-semibold mb-2"),
            P(description, cls="text-gray-600 mb-4"),
            Div(
                # Placeholder for live stream
                Div(
                    "📹 Live Stream Placeholder", 
                    cls="w-full h-48 bg-gray-900 rounded-lg flex items-center justify-center text-white mb-4"
                ),
                Div(
                    A("📸 Take Snapshot", href=snapshot_url, cls="btn btn-primary mr-2", target="_blank"),
                    A("🔄 Refresh", href="#", cls="btn btn-outline-secondary", onclick="window.location.reload()"),
                    cls="flex gap-2"
                ),
                cls="p-6"
            )
        )
    )


def VideoUploadCard(title: str, description: str, upload_url: str):
    """Video upload card component"""
    return Card(
        Div(
            H3(title, cls="text-xl font-semibold mb-2"),
            P(description, cls="text-gray-600 mb-4"),
            Form(
                Input(type="file", accept="video/*", name="video", cls="mb-4"),
                Button("Upload & Stream", cls="btn btn-primary"),
                method="post",
                action=upload_url,
                enctype="multipart/form-data",
                cls="space-y-4"
            ),
            cls="p-6"
        )
    )


def StreamingHomePage(base_path: str, user=None, demo=False):
    """Streaming platform home page with proper MonsterUI styling"""
    
    # Demo live streams
    demo_streams = [
        {"title": "Live Coding Session", "description": "Building cool stuff with FastHTML"},
        {"title": "Tech Talk", "description": "Latest trends in web development"},
        {"title": "Music Stream", "description": "Relaxing background music"}
    ]
    
    return Div(
        # Header
        Div(
            H1("📺 Streaming Platform", cls="text-4xl font-bold text-center mb-4"),
            P("Live Video Streaming & Content Platform", cls="text-xl text-gray-600 text-center mb-8"),
            cls="mb-8"
        ),
        
        # Main Content
        Div(
            # Live Streaming Section
            Div(
                H2("🔴 Live Streaming", cls="text-2xl font-bold mb-6"),
                Div(
                    *[LiveStreamCard(
                        stream["title"], 
                        stream["description"], 
                        f"{base_path}/stream/{i}", 
                        f"{base_path}/stream/{i}/snapshot"
                    ) for i, stream in enumerate(demo_streams)],
                    cls="grid grid-cols-1 lg:grid-cols-2 gap-6"
                ),
                cls="mb-8"
            ),
            
            # Upload Section
            Div(
                H2("🎬 Upload Content", cls="text-2xl font-bold mb-6"),
                Div(
                    VideoUploadCard(
                        "Upload Video", 
                        "Share your content with our community", 
                        f"{base_path}/stream/upload"
                    ),
                    cls="max-w-2xl mx-auto"
                ),
                cls="mb-8"
            ),
            
            # Features Section
            Div(
                H2("🚀 Features", cls="text-2xl font-bold mb-6"),
                Div(
                    Div(
                        H3("⚡ Optimized Streaming", cls="font-semibold mb-2"),
                        P("Range header support for efficient video streaming with minimal bandwidth usage.", cls="text-sm text-gray-600"),
                        cls="p-4"
                    ),
                    Div(
                        H3("🎥 Camera Integration", cls="font-semibold mb-2"),
                        P("Thread-safe camera access with real-time video capture capabilities.", cls="text-sm text-gray-600"),
                        cls="p-4"
                    ),
                    Div(
                        H3("📱 Responsive Design", cls="font-semibold mb-2"),
                        P("Mobile-friendly interface that works seamlessly across all devices.", cls="text-sm text-gray-600"),
                        cls="p-4"
                    ),
                    cls="grid grid-cols-1 md:grid-cols-3 gap-6"
                ),
                cls="mb-8"
            ),
            
            # Navigation
            Div(
                A("← Back to Home", href="/", cls="btn btn-outline mx-auto"),
                cls="text-center"
            ),
            
            cls="max-w-6xl mx-auto px-4"
        )
    )


# Common Layout Components
def ExampleHeader(title: str, subtitle: str, icon: str = ""):
    """Standard header for example applications"""
    return Div(
        H1(f"{icon} {title}" if icon else title, cls="text-4xl font-bold text-center mb-4"),
        P(subtitle, cls="text-xl text-gray-600 text-center mb-8"),
        cls="mb-8"
    )


def ExampleNavigation(base_path: str, current_page: str = "home", nav_items: list = None):
    """Standard navigation for example applications"""
    if nav_items is None:
        nav_items = [
            ("📝 Feed", f"{base_path}/", "feed"),
            ("👥 Profiles", f"{base_path}/profiles", "profiles"),
            ("💬 Messages", f"{base_path}/messages", "messages")
        ]
    
    return Div(
        Div(
            *[
                A(
                    label,
                    href=url,
                    cls="btn " + ("btn-primary" if page == current_page else "btn-outline-secondary") + " mr-2"
                )
                for label, url, page in nav_items
            ],
            cls="flex justify-center gap-2 mb-8 border-b pb-4"
        )
    )


def ExampleBackLink():
    """Standard back to home link"""
    return Nav(
        A("← Back to Home", href="/", cls="btn btn-outline mb-4"),
        cls="mb-4"
    )
