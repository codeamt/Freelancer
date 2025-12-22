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
    
    app = FastHTML(hdrs=[*Theme.slate.headers()])
    
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
        """Social network home with feed"""
        user = await get_user_with_context(request)
        
        # Get demo posts
        demo_posts = get_demo_posts()
        current_user_id = user.id if user else 1
        
        content = Div(
            # Use shared components with proper MonsterUI styling
            ExampleHeader("🌐 Social Network", "Connect, Share, Engage"),
            ExampleNavigation(BASE, "feed"),
            
            # Use proper SocialFeed component from shared components
            SocialFeed(demo_posts, current_user_id, BASE),
            
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
        """Messages page"""
        user = await get_user_with_context(request)
        
        content = Div(
            ExampleHeader("💬 Messages", "Connect with your network"),
            ExampleNavigation(BASE, "messages"),
            
            Div(
                H3("Messages", cls="text-2xl font-bold mb-6"),
                P("Messaging functionality coming soon!", cls="text-gray-600 mb-4"),
                P("This will integrate with the social domain services.", cls="text-gray-600"),
                cls="max-w-2xl mx-auto p-6"
            ),
            
            ExampleBackLink(),
            cls="min-h-screen bg-gray-50"
        )
        
        return Layout(content, title="Messages | Social Network", current_path=f"{BASE}/messages", user=user, show_auth=True, demo=demo)
    
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
    """Get demo posts for the social feed"""
    return [
        {
            "id": 1,
            "user_id": 2,
            "username": "Alice Johnson",
            "content": "Just launched my new project! 🚀 Check it out and let me know what you think. Building in public has been such an amazing journey!",
            "is_public": True,
            "created_at": datetime.now().replace(hour=10, minute=30),
            "like_count": 42,
            "comment_count": 8,
            "is_liked": False
        },
        {
            "id": 2,
            "user_id": 3,
            "username": "Bob Smith",
            "content": "Beautiful sunset today! Sometimes it's important to step away from the keyboard and appreciate the little things. 🌅",
            "is_public": True,
            "created_at": datetime.now().replace(hour=14, minute=15),
            "like_count": 28,
            "comment_count": 5,
            "is_liked": True
        },
        {
            "id": 3,
            "user_id": 4,
            "username": "Carol Davis",
            "content": "Hot take: Python is the best language for web development in 2024. The ecosystem is just unmatched! What do you think? 🐍",
            "is_public": False,
            "created_at": datetime.now().replace(hour=9, minute=45),
            "like_count": 15,
            "comment_count": 12,
            "is_liked": False
        }
    ]


def get_demo_users():
    """Get demo user profiles"""
    return [
        {
            "id": 2,
            "username": "Alice Johnson",
            "bio": "Full-stack developer | Open source enthusiast | Building cool stuff 🚀",
            "followers_count": 1234,
            "following_count": 567,
            "is_following": False
        },
        {
            "id": 3,
            "username": "Bob Smith",
            "bio": "Designer & photographer | Coffee addict ☕ | Capturing moments",
            "followers_count": 892,
            "following_count": 234,
            "is_following": True
        },
        {
            "id": 4,
            "username": "Carol Davis",
            "bio": "Data scientist | ML engineer | Making sense of data 📊",
            "followers_count": 2156,
            "following_count": 189,
            "is_following": False
        }
    ]
