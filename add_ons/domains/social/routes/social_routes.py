"""
Social Routes - Adapted for FastHTML
Handles posts, comments, likes, and follows
"""

from typing import Optional
from fasthtml.common import *

from add_ons.domains.social.services.social_service import SocialService
from core.utils.logger import get_logger

logger = get_logger(__name__)


def get_current_user_id(request) -> int:
    """Get current user ID from request (placeholder - integrate with auth)"""
    # TODO: Replace with actual authentication
    return 1


def create_social_routes():
    """Create and return social routes router"""
    
    @app.get("/social/feed")
    async def feed(request, page: int = 1):
        """Get user's social feed"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = SocialService(db, user_id)
            posts = await service.get_feed(limit=20, offset=(page - 1) * 20)
            
            # Simple render for now
            return Div(
                H1("Social Feed"),
                P(f"Found {len(posts)} posts"),
                cls="p-4"
            )
    
    @app.post("/social/posts")
    async def create_post(request, content: str = "", is_public: bool = False):
        """Create new post"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = SocialService(db, user_id)
            post = await service.create_post(
                content=content if content.strip() else None,
                is_public=is_public
            )
            
            return P(f"Post created with ID: {post.id}")
    
    @app.get("/social/posts/{post_id}")
    async def get_post(request, post_id: int):
        """Get specific post"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = SocialService(db, user_id)
            post = await service.get_post(post_id)
            
            if not post:
                return Response("Post not found", status_code=404)
            
            return Div(
                H2(f"Post {post.id}"),
                P(post.content or "No content"),
                P(f"Public: {post.is_public}"),
                cls="p-4"
            )
    
    @app.post("/social/posts/{post_id}/like")
    async def like_post(request, post_id: int):
        """Like a post"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = SocialService(db, user_id)
            success = await service.like_post(post_id)
            
            if not success:
                return Response("Post not found", status_code=404)
            
            return P("Post liked")
    
    @app.delete("/social/posts/{post_id}/like")
    async def unlike_post(request, post_id: int):
        """Unlike a post"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = SocialService(db, user_id)
            await service.unlike_post(post_id)
            
            return P("Post unliked")
    
    @app.post("/social/users/{user_id}/follow")
    async def follow_user(request, user_id: int):
        """Follow a user"""
        current_user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = SocialService(db, current_user_id)
            success = await service.follow_user(user_id)
            
            if not success:
                return Response("Cannot follow user", status_code=400)
            
            return P("User followed")
    
    @app.delete("/social/users/{user_id}/follow")
    async def unfollow_user(request, user_id: int):
        """Unfollow a user"""
        current_user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = SocialService(db, current_user_id)
            await service.unfollow_user(user_id)
            
            return P("User unfollowed")
    
    return True
