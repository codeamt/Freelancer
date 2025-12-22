"""
Social Network Example Application

Complete social networking features with posts, comments, likes, follows, and messaging.
"""

from fasthtml.common import *
from monsterui.all import *
import os
from core.ui.layout import Layout
from core.utils.logger import get_logger
from core.services.auth.helpers import get_current_user
from core.services.auth.context import set_user_context
from core.services.auth.context import create_user_context
from datetime import datetime

# Import UI components from examples/social/ui/components.py
from examples.social.ui.components import (
    PostComposer, PostCard, UserCard, SocialFeed, ExampleHeader, ExampleNavigation, ExampleBackLink,
    StreamingHomePage, LiveStreamCard, VideoUploadCard
)

logger = get_logger(__name__)


def create_social_app(auth_service=None, user_service=None, postgres=None, mongodb=None, redis=None, demo=False):
    """
    Create and configure the social network example app
    
    Args:
        auth_service: Injected authentication service
        user_service: Injected user management service
        postgres: PostgreSQL adapter (optional)
        mongodb: MongoDB adapter (optional)
        redis: Redis adapter (optional)
        demo: Whether to run in demo mode (uses mock data, limited features)
    """
    
    logger.info(f"Initializing Social example app (demo={demo})...")
    
    app = FastHTML(hdrs=[*Theme.violet.headers(mode="light")])
    
    # Store demo flag in app state
    app.state.demo = demo
    
    # Base path
    BASE = "/social-example"
    
    async def get_user_with_context(request: Request):
        """Get current user from request and set context."""
        user = await get_current_user(request, auth_service)
        if user:
            # Set user context for state system using factory
            class SimpleUser:
                def __init__(self, user_dict):
                    self.id = user_dict.get("id") or int(user_dict.get("_id", 0))
                    self.role = user_dict.get("role", "user")
                    self.email = user_dict.get("email", "")
            
            user_obj = SimpleUser(user)
            user_context = create_user_context(user_obj, request)
            set_user_context(user_context)
        return user
    
    @app.get("/")
    async def social_home(request: Request):
        """Social network home with enhanced feed showcasing add_ons/domains/social features"""
        user = await get_user_with_context(request)
        
        # Get demo posts
        demo_posts = get_demo_posts()
        current_user_id = user.id if user else 1
        
        content = Div(
            # Enhanced Header with Features Overview
            Div(
                Div(
                    H1("🌐 Social Network", cls="text-4xl font-bold text-center mb-4"),
                    P("Connect, Share, and Engage with your community", cls="text-xl text-gray-600 text-center mb-8"),
                    
                    # Feature badges
                    Div(
                        Span("📝 Posts", cls="badge badge-primary mr-2 mb-2"),
                        Span("💬 Comments", cls="badge badge-secondary mr-2 mb-2"),
                        Span("❤️ Likes", cls="badge badge-accent mr-2 mb-2"),
                        Span("👥 Follows", cls="badge badge-info mr-2 mb-2"),
                        Span("📩 Direct Messages", cls="badge badge-success mr-2 mb-2"),
                        cls="flex flex-wrap justify-center gap-2 mb-8"
                    ),
                    
                    # Quick stats
                    Div(
                        Div(
                            H4("1,234", cls="text-2xl font-bold text-blue-600"),
                            P("Active Users", cls="text-sm text-gray-600"),
                            cls="text-center"
                        ),
                        Div(
                            H4("5,678", cls="text-2xl font-bold text-green-600"),
                            P("Posts Today", cls="text-sm text-gray-600"),
                            cls="text-center"
                        ),
                        Div(
                            H4("892", cls="text-2xl font-bold text-purple-600"),
                            P("Online Now", cls="text-sm text-gray-600"),
                            cls="text-center"
                        ),
                        cls="grid grid-cols-3 gap-4 max-w-md mx-auto mb-8"
                    ),
                    
                    cls="mb-8"
                ),
                cls="bg-gradient-to-r from-blue-50 to-purple-50 py-8 px-4 rounded-lg mb-6"
            ),
            
            # Navigation
            ExampleNavigation(BASE, "feed"),
            
            # Post Composer
            Div(
                PostComposer(action_url=f"{BASE}/posts"),
                cls="max-w-2xl mx-auto mb-8"
            ),
            
            # Social Feed with Enhanced Posts
            Div(
                H3("📝 Your Feed", cls="text-2xl font-bold mb-6"),
                *[Div(
                    # Post header with user info
                    Div(
                        Div(
                            Div(
                                B(post["username"]),
                                Span(" ✓", cls="text-blue-500") if post.get("is_verified") else None,
                                Span(" • "),
                                Span(post["created_at"].strftime("%I:%M %p"), cls="text-sm text-gray-500"),
                                Span(" • "),
                                Span("Public" if post["is_public"] else "Followers", 
                                     cls="text-xs px-2 py-1 rounded " + 
                                     ("bg-green-100 text-green-800" if post["is_public"] else "bg-gray-100 text-gray-800")),
                                cls="flex items-center gap-2"
                            ),
                            Button("⋯", cls="btn btn-ghost btn-sm"),
                            cls="flex justify-between items-center"
                        ),
                        cls="mb-3"
                    ),
                    
                    # Post content
                    Div(
                        P(post["content"], cls="text-gray-800 mb-4"),
                        cls="mb-4"
                    ),
                    
                    # Engagement bar
                    Div(
                        Div(
                            Button(
                                f"❤️ {post['like_count']}", 
                                cls=("btn btn-sm " + ("btn-primary" if post["is_liked"] else "btn-outline-secondary"))
                            ),
                            Button(f"💬 {post['comment_count']}", cls="btn btn-sm btn-outline-secondary ml-2"),
                            Button("🔄 Share", cls="btn btn-sm btn-outline-secondary ml-2"),
                            cls="flex gap-2"
                        ),
                        cls="border-t pt-3"
                    ),
                    
                    # Comments preview (show first 2)
                    Div(
                        H5("Comments", cls="font-semibold mb-3"),
                        *[Div(
                            Div(
                                B(comment["username"], cls="text-sm"),
                                Span(comment["created_at"].strftime("%I:%M %p"), cls="text-xs text-gray-500"),
                                cls="mb-1"
                            ),
                            P(comment["content"], cls="text-sm text-gray-700"),
                            cls="border-l-2 border-gray-200 pl-3 mb-2"
                        ) for comment in post.get("comments", [])[:2]],
                        
                        Button("View all comments", cls="btn btn-link btn-sm p-0"),
                        cls="mt-4 bg-gray-50 p-3 rounded-lg"
                    ),
                    
                    cls="p-6 bg-white border rounded-lg shadow-sm hover:shadow-md transition-shadow"
                ) for post in demo_posts],
                cls="max-w-2xl mx-auto space-y-6"
            ),
            
            # Features Showcase
            Div(
                H3("🚀 Social Network Features", cls="text-2xl font-bold mb-6 text-center"),
                Div(
                    Div(
                        H4("📝 Rich Posts", cls="font-semibold mb-2"),
                        P("Create posts with text, hashtags, and privacy controls", cls="text-sm text-gray-600"),
                        cls="p-4 bg-blue-50 rounded-lg"
                    ),
                    Div(
                        H4("💬 Real-time Comments", cls="font-semibold mb-2"),
                        P("Engage with threaded conversations on posts", cls="text-sm text-gray-600"),
                        cls="p-4 bg-green-50 rounded-lg"
                    ),
                    Div(
                        H4("❤️ Like System", cls="font-semibold mb-2"),
                        P("Show appreciation with interactive like functionality", cls="text-sm text-gray-600"),
                        cls="p-4 bg-red-50 rounded-lg"
                    ),
                    Div(
                        H4("👥 Follow System", cls="font-semibold mb-2"),
                        P("Build your network with follow/unfollow capabilities", cls="text-sm text-gray-600"),
                        cls="p-4 bg-purple-50 rounded-lg"
                    ),
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
                ),
                cls="max-w-4xl mx-auto mt-8"
            ),
            
            ExampleBackLink(),
            cls="min-h-screen bg-gray-50"
        )
        
        return Layout(content, title="Social Network | FastApp", current_path=f"{BASE}/", user=user, show_auth=True, demo=demo)
    
    @app.get("/streaming")
    async def streaming_page(request: Request):
        """Streaming platform page using StreamingHomePage component"""
        user = await get_user_with_context(request)
        
        # Use StreamingHomePage component as content for Layout
        content = StreamingHomePage(BASE, user, demo)
        
        return Layout(content, title="Streaming Platform | FastApp", current_path=f"{BASE}/streaming", user=user, show_auth=True, demo=demo)
    
    @app.get("/profiles")
    async def profiles_page(request: Request):
        """User profiles page"""
        user = await get_user_with_context(request)
        current_user_id = user.id if user else 1
        
        # Get demo users
        demo_users = get_demo_users()
        
        content = Div(
            ExampleHeader("👥 User Profiles", "Discover and connect with our community"),
            ExampleNavigation(BASE, "profiles"),
            
            Div(
                *[UserCard(user_data, current_user_id) for user_data in demo_users],
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto"
            ),
            
            ExampleBackLink(),
            cls="min-h-screen bg-gray-50"
        )
        
        return Layout(content, title="Profiles | Social Network", current_path=f"{BASE}/profiles", user=user, show_auth=True, demo=demo)
    
    @app.get("/messages")
    async def messages_page(request: Request):
        """Direct messages page - showcasing DM service from add_ons/domains/social"""
        user = await get_user_with_context(request)
        
        # Get demo conversations
        conversations = get_demo_conversations()
        
        content = Div(
            ExampleHeader("💬 Messages", "Private conversations with your network"),
            ExampleNavigation(BASE, "messages"),
            
            # Conversations List
            Div(
                H3("Recent Conversations", cls="text-2xl font-bold mb-6"),
                Div(
                    *[Div(
                        # Online indicator
                        Div(
                            Div(
                                cls="w-3 h-3 rounded-full " + ("bg-green-500" if conv["is_online"] else "bg-gray-400"),
                                title="Online" if conv["is_online"] else "Offline"
                            ),
                            cls="mr-3"
                        ),
                        
                        # Conversation content
                        Div(
                            Div(
                                Div(
                                    B(conv["participant"]["username"]),
                                    Span(
                                        f" • {conv['last_message_time'].strftime('%H:%M')}",
                                        cls="text-sm text-gray-500"
                                    ),
                                    cls="flex justify-between items-center"
                                ),
                                P(conv["last_message"], cls="text-sm text-gray-600 truncate"),
                                cls="flex-1"
                            ),
                            
                            # Unread count badge
                            Div(
                                Span(str(conv["unread_count"]), cls="badge badge-primary") if conv["unread_count"] > 0 else None,
                                cls="ml-3"
                            ),
                            cls="flex items-center"
                        ),
                        
                        cls="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors",
                        onclick=f"window.location.href='{BASE}/messages/{conv['id']}'"
                    ) for conv in conversations],
                    cls="space-y-2 max-w-2xl mx-auto"
                ),
                
                # Features showcase
                Div(
                    H4("Direct Messaging Features", cls="text-lg font-semibold mb-4 mt-8"),
                    Div(
                        Div(
                            H5("🔒 Private Conversations", cls="font-medium mb-1"),
                            P("Secure one-on-one messaging with end-to-end encryption", cls="text-sm text-gray-600"),
                            cls="p-3 bg-blue-50 rounded-lg"
                        ),
                        Div(
                            H5("📱 Real-time Chat", cls="font-medium mb-1"),
                            P("Instant message delivery with online status indicators", cls="text-sm text-gray-600"),
                            cls="p-3 bg-green-50 rounded-lg"
                        ),
                        Div(
                            H5("💾 Message History", cls="font-medium mb-1"),
                            P("Persistent conversation storage with search capabilities", cls="text-sm text-gray-600"),
                            cls="p-3 bg-purple-50 rounded-lg"
                        ),
                        cls="grid grid-cols-1 md:grid-cols-3 gap-3"
                    ),
                    cls="max-w-2xl mx-auto"
                ),
                
                cls="max-w-4xl mx-auto"
            ),
            
            ExampleBackLink(),
            cls="min-h-screen bg-gray-50"
        )
        
        return Layout(content, title="Messages | Social Network", current_path=f"{BASE}/messages", user=user, show_auth=True, demo=demo)
    
    @app.get("/messages/{conversation_id}")
    async def conversation_page(request: Request, conversation_id: int):
        """Individual conversation page"""
        user = await get_user_with_context(request)
        
        # Get specific conversation
        conversations = get_demo_conversations()
        conv = next((c for c in conversations if c["id"] == conversation_id), None)
        
        if not conv:
            return RedirectResponse(f"{BASE}/messages")
        
        # Get demo messages for this conversation
        demo_messages = [
            {"id": 1, "sender_id": conv["participant"]["id"], "content": "Hey! How's your project going?", "time": datetime.now().replace(hour=16, minute=0)},
            {"id": 2, "sender_id": user.id if user else 1, "content": "Going great! Just finished the main features.", "time": datetime.now().replace(hour=16, minute=15)},
            {"id": 3, "sender_id": conv["participant"]["id"], "content": "Awesome! Would love to see it when you're ready.", "time": datetime.now().replace(hour=16, minute=20)},
            {"id": 4, "sender_id": conv["participant"]["id"], "content": "Hey! Are you free to collaborate on that project?", "time": datetime.now().replace(hour=16, minute=30)},
        ]
        
        content = Div(
            # Conversation header
            Div(
                Div(
                    A("← Back to Messages", href=f"{BASE}/messages", cls="btn btn-outline-secondary mb-4"),
                    Div(
                        Div(
                            Div(
                                cls="w-3 h-3 rounded-full " + ("bg-green-500" if conv["is_online"] else "bg-gray-400")
                            ),
                            H4(conv["participant"]["username"], cls="font-semibold"),
                            Span("Online" if conv["is_online"] else "Offline", cls="text-sm text-gray-500"),
                            cls="flex items-center gap-2"
                        ),
                        cls="border-b pb-4"
                    ),
                    cls="max-w-2xl mx-auto"
                ),
                cls="mb-6"
            ),
            
            # Messages
            Div(
                *[Div(
                    Div(
                        P(msg["content"], cls="mb-1"),
                        Span(msg["time"].strftime("%H:%M"), cls="text-xs text-gray-500"),
                        cls="inline-block"
                    ),
                    cls=("text-right" if msg["sender_id"] == (user.id if user else 1) else "text-left") + " mb-4 w-full"
                ) for msg in demo_messages],
                cls="max-w-2xl mx-auto mb-6"
            ),
            
            # Message input
            Div(
                Form(
                    Div(
                        Input(
                            type="text",
                            name="message",
                            placeholder="Type your message...",
                            cls="flex-1 p-3 border rounded-l-lg",
                            required=True
                        ),
                        Button("Send", cls="btn btn-primary rounded-r-lg"),
                        cls="flex gap-0"
                    ),
                    method="post",
                    action=f"{BASE}/messages/{conversation_id}/send"
                ),
                cls="max-w-2xl mx-auto border-t pt-4"
            ),
            
            cls="min-h-screen bg-gray-50"
        )
        
        return Layout(content, title=f"Chat with {conv['participant']['username']} | Social Network", current_path=f"{BASE}/messages/{conversation_id}", user=user, show_auth=True, demo=demo)
    
    @app.post("/posts")
    async def create_post(request: Request, content: str = ""):
        """Create new post (demo implementation)"""
        user = await get_user_with_context(request)
        current_user_id = user.id if user else 1
        
        # In demo mode, just return a success response
        new_post = {
            "id": len(get_demo_posts()) + 1,
            "user_id": current_user_id,
            "content": content,
            "is_public": True,
            "created_at": datetime.now(),
            "like_count": 0,
            "comment_count": 0,
            "is_liked": False
        }
        
        return PostCard(new_post, current_user_id)
    
    return app


# Demo data functions
def get_demo_posts():
    """Get demo posts for the social feed - reflecting add_ons/domains/social models"""
    return [
        {
            "id": 1,
            "user_id": 2,
            "username": "Alice Johnson",
            "content": "Just launched my new project! 🚀 Check it out and let me know what you think. Building in public has been such an amazing journey! #FastHTML #WebDev",
            "is_public": True,
            "created_at": datetime.now().replace(hour=10, minute=30),
            "like_count": 42,
            "comment_count": 8,
            "is_liked": False,
            "comments": [
                {"id": 1, "user_id": 3, "username": "Bob Smith", "content": "Looks amazing! Great work! 🎉", "created_at": datetime.now().replace(hour=11, minute=15)},
                {"id": 2, "user_id": 4, "username": "Carol Davis", "content": "Love the architecture choices!", "created_at": datetime.now().replace(hour=11, minute=30)}
            ]
        },
        {
            "id": 2,
            "user_id": 3,
            "username": "Bob Smith",
            "content": "Beautiful sunset today! Sometimes it's important to step away from the keyboard and appreciate the little things. 🌅 #Photography #LifeBalance",
            "is_public": True,
            "created_at": datetime.now().replace(hour=14, minute=15),
            "like_count": 28,
            "comment_count": 5,
            "is_liked": True,
            "comments": [
                {"id": 3, "user_id": 2, "username": "Alice Johnson", "content": "Stunning shot! Where was this taken?", "created_at": datetime.now().replace(hour=14, minute=45)}
            ]
        },
        {
            "id": 3,
            "user_id": 4,
            "username": "Carol Davis",
            "content": "Hot take: Python is the best language for web development in 2024. The ecosystem is just unmatched! FastHTML + MonsterUI = 🔥 What do you think? #Python #FastHTML",
            "is_public": False,
            "created_at": datetime.now().replace(hour=9, minute=45),
            "like_count": 15,
            "comment_count": 12,
            "is_liked": False,
            "comments": [
                {"id": 4, "user_id": 2, "username": "Alice Johnson", "content": "Totally agree! The productivity gains are incredible.", "created_at": datetime.now().replace(hour=10, minute=0)},
                {"id": 5, "user_id": 3, "username": "Bob Smith", "content": "FastHTML has been a game changer for me!", "created_at": datetime.now().replace(hour=10, minute=15)}
            ]
        }
    ]


def get_demo_users():
    """Get demo user profiles - reflecting social domain features"""
    return [
        {
            "id": 2,
            "username": "Alice Johnson",
            "bio": "Full-stack developer | Open source enthusiast | Building cool stuff 🚀",
            "followers_count": 1234,
            "following_count": 567,
            "is_following": False,
            "post_count": 89,
            "is_verified": True
        },
        {
            "id": 3,
            "username": "Bob Smith",
            "bio": "Designer & photographer | Coffee addict ☕ | Capturing moments",
            "followers_count": 892,
            "following_count": 234,
            "is_following": True,
            "post_count": 156,
            "is_verified": False
        },
        {
            "id": 4,
            "username": "Carol Davis",
            "bio": "Data scientist | ML engineer | Making sense of data 📊",
            "followers_count": 2156,
            "following_count": 189,
            "is_following": False,
            "post_count": 234,
            "is_verified": True
        },
        {
            "id": 5,
            "username": "David Wilson",
            "bio": "Backend engineer | Database enthusiast | Performance optimizer",
            "followers_count": 567,
            "following_count": 445,
            "is_following": False,
            "post_count": 78,
            "is_verified": False
        }
    ]


def get_demo_conversations():
    """Get demo direct message conversations - reflecting DM service"""
    return [
        {
            "id": 1,
            "participant": {"id": 3, "username": "Bob Smith"},
            "last_message": "Hey! Are you free to collaborate on that project?",
            "last_message_time": datetime.now().replace(hour=16, minute=30),
            "unread_count": 2,
            "is_online": True
        },
        {
            "id": 2,
            "participant": {"id": 4, "username": "Carol Davis"},
            "last_message": "Thanks for the feedback on my post!",
            "last_message_time": datetime.now().replace(hour=15, minute=45),
            "unread_count": 0,
            "is_online": False
        },
        {
            "id": 3,
            "participant": {"id": 5, "username": "David Wilson"},
            "last_message": "Let's discuss the database optimization tomorrow",
            "last_message_time": datetime.now().replace(hour=14, minute=20),
            "unread_count": 1,
            "is_online": True
        }
    ]
