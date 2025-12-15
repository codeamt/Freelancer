"""Blog business logic service"""

from datetime import datetime
from typing import List, Optional

from core.services import get_db_service
from core.utils.logger import get_logger

logger = get_logger(__name__)


_DEMO_POSTS: List[dict] = [
    {
        "id": 1,
        "author_id": 1,
        "title": "Welcome to the Blog",
        "body": "This is your first post.",
        "status": "published",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
]


class PostService:
    """Post service - business logic for blog posts"""

    def __init__(self, use_db: bool = False):
        self.use_db = use_db
        self.db = get_db_service() if use_db else None

    async def list_posts(self) -> List[dict]:
        if self.use_db:
            return await self.db.find_documents("blog_posts", {}, limit=100)

        return list(_DEMO_POSTS)

    async def get_post(self, post_id: int) -> Optional[dict]:
        if self.use_db:
            return await self.db.find_document("blog_posts", {"id": post_id})

        for p in _DEMO_POSTS:
            if int(p.get("id", 0)) == int(post_id):
                return p
        return None

    async def create_post(self, author_id: int, title: str, body: str = "") -> dict:
        now = datetime.utcnow()
        post_data = {
            "author_id": author_id,
            "title": title,
            "body": body,
            "status": "published",
            "created_at": now,
            "updated_at": now,
        }

        if self.use_db:
            existing = await self.db.find_documents("blog_posts", {}, limit=1000)
            new_id = (
                max((int(p.get("id")) for p in existing if p.get("id") is not None), default=0) + 1
            )
            post = await self.db.insert_document("blog_posts", {"id": new_id, **post_data})
            logger.info(f"Created blog post {new_id} in database")
            return post

        new_id = max((int(p.get("id")) for p in _DEMO_POSTS), default=0) + 1
        post = {"id": new_id, **post_data}
        _DEMO_POSTS.append(post)
        logger.info(f"Created blog post: {post['id']} - {title}")
        return post
