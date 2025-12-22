"""
Social Service - Adapted for FastHTML
Handles posts, comments, likes, and follows
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from add_ons.domains.social.models import Post, Comment, Follow, Like
from core.utils.logger import get_logger

logger = get_logger(__name__)


class SocialService:
    """Social networking service"""
    
    def __init__(self, db: AsyncSession, current_user_id: int):
        self.db = db
        self.user_id = current_user_id

    async def create_post(self, content: Optional[str] = None, media_url: Optional[str] = None, 
                         is_public: bool = False) -> Post:
        """Create a new post"""
        post = Post(
            user_id=self.user_id,
            content=content,
            media_url=media_url,
            is_public=is_public
        )
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        
        logger.info(f"User {self.user_id} created post {post.id}")
        return post

    async def get_feed(self, limit: int = 20, offset: int = 0) -> List[Post]:
        """Get personalized feed for current user"""
        # Get users that current user follows
        following_query = select(Follow.followee_id).where(Follow.follower_id == self.user_id)
        
        # Posts from self OR users I follow OR public posts
        stmt = (
            select(Post)
            .options(selectinload(Post.comments), selectinload(Post.likes))
            .where(
                or_(
                    Post.is_public == True,
                    Post.user_id == self.user_id,
                    Post.user_id.in_(following_query)
                )
            )
            .order_by(desc(Post.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        posts = result.scalars().all()
        
        logger.info(f"User {self.user_id} retrieved feed with {len(posts)} posts")
        return posts

    async def get_post(self, post_id: int) -> Optional[Post]:
        """Get specific post with visibility check"""
        stmt = (
            select(Post)
            .options(selectinload(Post.comments), selectinload(Post.likes))
            .where(Post.id == post_id)
        )
        
        result = await self.db.execute(stmt)
        post = result.scalar_one_or_none()
        
        if post and await self.is_post_visible(post):
            return post
        return None

    async def is_post_visible(self, post: Post) -> bool:
        """Check if post is visible to current user"""
        if post.is_public or post.user_id == self.user_id:
            return True
        
        # Check if current user follows the post author
        follow_query = select(Follow).where(
            and_(
                Follow.follower_id == self.user_id,
                Follow.followee_id == post.user_id
            )
        )
        result = await self.db.execute(follow_query)
        return result.scalar_one_or_none() is not None

    async def update_post(self, post_id: int, content: Optional[str] = None, 
                         media_url: Optional[str] = None, is_public: Optional[bool] = None) -> Optional[Post]:
        """Update post (only by owner)"""
        stmt = select(Post).where(and_(Post.id == post_id, Post.user_id == self.user_id))
        result = await self.db.execute(stmt)
        post = result.scalar_one_or_none()
        
        if not post:
            return None
        
        if content is not None:
            post.content = content
        if media_url is not None:
            post.media_url = media_url
        if is_public is not None:
            post.is_public = is_public
        
        await self.db.commit()
        await self.db.refresh(post)
        
        logger.info(f"User {self.user_id} updated post {post_id}")
        return post

    async def delete_post(self, post_id: int) -> bool:
        """Delete post (only by owner)"""
        stmt = select(Post).where(and_(Post.id == post_id, Post.user_id == self.user_id))
        result = await self.db.execute(stmt)
        post = result.scalar_one_or_none()
        
        if not post:
            return False
        
        await self.db.delete(post)
        await self.db.commit()
        
        logger.info(f"User {self.user_id} deleted post {post_id}")
        return True

    async def add_comment(self, post_id: int, content: str, parent_id: Optional[int] = None) -> Optional[Comment]:
        """Add comment to post"""
        # Check if post is visible
        post = await self.get_post(post_id)
        if not post:
            return None
        
        comment = Comment(
            post_id=post_id,
            user_id=self.user_id,
            content=content,
            parent_id=parent_id
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        
        logger.info(f"User {self.user_id} commented on post {post_id}")
        return comment

    async def get_comments(self, post_id: int, limit: int = 50, offset: int = 0) -> List[Comment]:
        """Get comments for post with visibility check"""
        if not await self.is_post_visible_by_id(post_id):
            return []
        
        stmt = (
            select(Comment)
            .where(and_(Comment.post_id == post_id, Comment.parent_id.is_(None)))
            .order_by(Comment.created_at)
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_comment_replies(self, comment_id: int, limit: int = 20) -> List[Comment]:
        """Get replies to a comment"""
        stmt = (
            select(Comment)
            .where(Comment.parent_id == comment_id)
            .order_by(Comment.created_at)
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_comment(self, comment_id: int, content: str) -> Optional[Comment]:
        """Update comment (only by owner)"""
        stmt = select(Comment).where(and_(Comment.id == comment_id, Comment.user_id == self.user_id))
        result = await self.db.execute(stmt)
        comment = result.scalar_one_or_none()
        
        if not comment:
            return None
        
        comment.content = content
        await self.db.commit()
        await self.db.refresh(comment)
        
        logger.info(f"User {self.user_id} updated comment {comment_id}")
        return comment

    async def delete_comment(self, comment_id: int) -> bool:
        """Delete comment (only by owner or post owner)"""
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(stmt)
        comment = result.scalar_one_or_none()
        
        if not comment:
            return False
        
        # Check if user owns comment or the post
        if comment.user_id != self.user_id:
            post = await self.get_post(comment.post_id)
            if not post or post.user_id != self.user_id:
                return False
        
        await self.db.delete(comment)
        await self.db.commit()
        
        logger.info(f"User {self.user_id} deleted comment {comment_id}")
        return True

    async def like_post(self, post_id: int) -> bool:
        """Like a post"""
        # Check if post is visible
        if not await self.is_post_visible_by_id(post_id):
            return False
        
        # Check if already liked
        existing = await self.db.execute(
            select(Like).where(and_(Like.post_id == post_id, Like.user_id == self.user_id))
        )
        if existing.scalar_one_or_none():
            return True  # Already liked
        
        like = Like(post_id=post_id, user_id=self.user_id)
        self.db.add(like)
        await self.db.commit()
        
        logger.info(f"User {self.user_id} liked post {post_id}")
        return True

    async def unlike_post(self, post_id: int) -> bool:
        """Unlike a post"""
        stmt = select(Like).where(and_(Like.post_id == post_id, Like.user_id == self.user_id))
        result = await self.db.execute(stmt)
        like = result.scalar_one_or_none()
        
        if not like:
            return False  # Not liked
        
        await self.db.delete(like)
        await self.db.commit()
        
        logger.info(f"User {self.user_id} unliked post {post_id}")
        return True

    async def get_like_count(self, post_id: int) -> int:
        """Get number of likes for a post"""
        stmt = select(func.count(Like.id)).where(Like.post_id == post_id)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def is_post_liked_by_user(self, post_id: int) -> bool:
        """Check if current user liked the post"""
        stmt = select(Like).where(and_(Like.post_id == post_id, Like.user_id == self.user_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def follow_user(self, followee_id: int) -> bool:
        """Follow a user"""
        if followee_id == self.user_id:
            return False  # Can't follow yourself
        
        # Check if already following
        existing = await self.db.execute(
            select(Follow).where(and_(
                Follow.follower_id == self.user_id,
                Follow.followee_id == followee_id
            ))
        )
        if existing.scalar_one_or_none():
            return True  # Already following
        
        follow = Follow(follower_id=self.user_id, followee_id=followee_id)
        self.db.add(follow)
        await self.db.commit()
        
        logger.info(f"User {self.user_id} followed user {followee_id}")
        return True

    async def unfollow_user(self, followee_id: int) -> bool:
        """Unfollow a user"""
        stmt = select(Follow).where(and_(
            Follow.follower_id == self.user_id,
            Follow.followee_id == followee_id
        ))
        result = await self.db.execute(stmt)
        follow = result.scalar_one_or_none()
        
        if not follow:
            return False  # Not following
        
        await self.db.delete(follow)
        await self.db.commit()
        
        logger.info(f"User {self.user_id} unfollowed user {followee_id}")
        return True

    async def get_followers(self, user_id: int, limit: int = 50) -> List[int]:
        """Get list of user's followers"""
        stmt = (
            select(Follow.follower_id)
            .where(Follow.followee_id == user_id)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_following(self, user_id: int, limit: int = 50) -> List[int]:
        """Get list of users that user follows"""
        stmt = (
            select(Follow.followee_id)
            .where(Follow.follower_id == user_id)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]

    async def is_following(self, followee_id: int) -> bool:
        """Check if current user follows the target user"""
        stmt = select(Follow).where(and_(
            Follow.follower_id == self.user_id,
            Follow.followee_id == followee_id
        ))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_follow_count(self, user_id: int) -> Dict[str, int]:
        """Get follower and following counts for user"""
        followers_query = select(func.count(Follow.id)).where(Follow.followee_id == user_id)
        following_query = select(func.count(Follow.id)).where(Follow.follower_id == user_id)
        
        followers_result = await self.db.execute(followers_query)
        following_result = await self.db.execute(following_query)
        
        return {
            "followers": followers_result.scalar() or 0,
            "following": following_result.scalar() or 0
        }

    async def is_post_visible_by_id(self, post_id: int) -> bool:
        """Check if post is visible by ID (helper method)"""
        stmt = select(Post).where(Post.id == post_id)
        result = await self.db.execute(stmt)
        post = result.scalar_one_or_none()
        
        return post is not None and await self.is_post_visible(post)

    async def get_user_posts(self, user_id: int, limit: int = 20, offset: int = 0) -> List[Post]:
        """Get posts by specific user with visibility check"""
        stmt = (
            select(Post)
            .options(selectinload(Post.comments), selectinload(Post.likes))
            .where(Post.user_id == user_id)
            .order_by(desc(Post.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        posts = result.scalars().all()
        
        # Filter visible posts
        visible_posts = []
        for post in posts:
            if await self.is_post_visible(post):
                visible_posts.append(post)
        
        return visible_posts
