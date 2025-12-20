# ==============================================================

# FILE: app/add_ons/social/__init__.py

# ==============================================================

"""Social Networking Add-on
Features: posts (text/media), comments, likes, follows, private feeds (mutual/follow-only),
direct messaging, S3 uploads, HTMX UI, analytics adapter auto-registered.
"""

from app.add_ons.social import models, schemas, services, routes, ui, graphql  # noqa: F401

__all__ = ["models", "schemas", "services", "routes", "ui", "graphql"]

# ==============================================================

# FILE: app/add_ons/social/models/__init__.py

# ==============================================================

from .post import Post
from .comment import Comment
from .follow import Follow
from .like import Like
from .dm import DirectMessage, Conversation

__all__ = ["Post", "Comment", "Follow", "Like", "DirectMessage", "Conversation"]

# ==============================================================

# FILE: app/add_ons/social/models/post.py

# ==============================================================

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.db import Base

class Post(Base):
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)
    media_url = Column(String(1024), nullable=True)  # S3 or YouTube
    is_public = Column(Boolean, default=False)  # default private; visible to followers/mutuals only
    created_at = Column(DateTime, default=datetime.utcnow)

    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

# ==============================================================

# FILE: app/add_ons/social/models/comment.py

# ==============================================================

from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base

class Comment(Base):
    __tablename__ = "social_comments"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("social_posts.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("social_comments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")

# ==============================================================

# FILE: app/add_ons/social/models/follow.py

# ==============================================================

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, UniqueConstraint
from app.core.db import Base

class Follow(Base):
    __tablename__ = "social_follows"

    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, nullable=False)
    followee_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("follower_id", "followee_id", name="uq_follow_pair"),
    )

# ==============================================================

# FILE: app/add_ons/social/models/like.py

# ==============================================================

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, UniqueConstraint
from app.core.db import Base

class Like(Base):
    __tablename__ = "social_likes"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_like_post_user"),
    )

# ==============================================================

# FILE: app/add_ons/social/models/dm.py

# ==============================================================

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Text, UniqueConstraint
from app.core.db import Base

class Conversation(Base):
    __tablename__ = "social_conversations"

    id = Column(Integer, primary_key=True)
    user_a = Column(Integer, nullable=False)
    user_b = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_a", "user_b", name="uq_conversation_pair"),
    )

class DirectMessage(Base):
    __tablename__ = "social_direct_messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, nullable=False)
    sender_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)
    media_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==============================================================

# FILE: app/add_ons/social/schemas/__init__.py

# ==============================================================

from .post_schema import PostCreate, PostOut
from .comment_schema import CommentCreate, CommentOut
from .follow_schema import FollowIn, FollowOut

__all__ = ["PostCreate", "PostOut", "CommentCreate", "CommentOut", "FollowIn", "FollowOut"]

# ==============================================================

# FILE: app/add_ons/social/schemas/post_schema.py

# ==============================================================

from pydantic import BaseModel
from typing import Optional

class PostCreate(BaseModel):
    content: Optional[str] = None
    media_url: Optional[str] = None
    is_public: bool = False

class PostOut(BaseModel):
    id: int
    user_id: int
    content: Optional[str]
    media_url: Optional[str]
    is_public: bool

    class Config:
        from_attributes = True

# ==============================================================

# FILE: app/add_ons/social/schemas/comment_schema.py

# ==============================================================

from pydantic import BaseModel
from typing import Optional

class CommentCreate(BaseModel):
    post_id: int
    content: str
    parent_id: Optional[int] = None

class CommentOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str

    class Config:
        from_attributes = True

# ==============================================================

# FILE: app/add_ons/social/schemas/follow_schema.py

# ==============================================================

from pydantic import BaseModel

class FollowIn(BaseModel):
    followee_id: int

class FollowOut(BaseModel):
    follower_id: int
    followee_id: int

    class Config:
        from_attributes = True

# ==============================================================

# FILE: app/add_ons/social/services/__init__.py

# ==============================================================

from .social_service import SocialService
from .notification_service import NotificationService
from .dm_service import DirectMessageService

__all__ = ["SocialService", "NotificationService", "DirectMessageService"]

# ==============================================================

# FILE: app/add_ons/social/services/social_service.py

# ==============================================================

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.add_ons.social.models import Post, Comment, Follow, Like
from app.add_ons.social.schemas import PostCreate, CommentCreate
from app.core.utils import get_logger
from app.core.services.s3_service import s3

logger = get_logger("social.service")

class SocialService:
    def __init__(self, db: AsyncSession, current_user_id: int):
        self.db = db
        self.user_id = current_user_id

    async def create_post(self, data: PostCreate) -> Post:
        post = Post(user_id=self.user_id, **data.model_dump())
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def presign_post_upload(self, filename: str, content_type: str) -> dict:
        return s3.presign_put_url(key=f"social/posts/{self.user_id}/{filename}", content_type=content_type)

    async def feed(self, limit: int = 20, offset: int = 0) -> List[Post]:
        # posts from self OR users I follow OR mutuals; include public posts always
        # visible if is_public or author in follows; for private (is_public=False) require follower relationship
        following = select(Follow.followee_id).where(Follow.follower_id == self.user_id)
        stmt = (
            select(Post)
            .where(
                or_(
                    Post.is_public == True,
                    Post.user_id == self.user_id,
                    Post.user_id.in_(following),
                )
            )
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def post_visible_to_user(self, post: Post) -> bool:
        if post.is_public or post.user_id == self.user_id:
            return True
        # follower-only visibility
        res = await self.db.execute(
            select(Follow).where(and_(Follow.follower_id == self.user_id, Follow.followee_id == post.user_id))
        )
        return res.scalars().first() is not None

    async def add_comment(self, data: CommentCreate) -> Comment:
        c = Comment(user_id=self.user_id, **data.model_dump())
        self.db.add(c)
        await self.db.commit()
        await self.db.refresh(c)
        return c

    async def like_post(self, post_id: int) -> bool:
        existing = await self.db.execute(select(Like).where(Like.post_id == post_id, Like.user_id == self.user_id))
        if existing.scalars().first():
            return True
        like = Like(post_id=post_id, user_id=self.user_id)
        self.db.add(like)
        await self.db.commit()
        return True

    async def follow(self, followee_id: int) -> bool:
        if followee_id == self.user_id:
            return True
        exists = await self.db.execute(
            select(Follow).where(Follow.follower_id == self.user_id, Follow.followee_id == followee_id)
        )
        if exists.scalars().first():
            return True
        f = Follow(follower_id=self.user_id, followee_id=followee_id)
        self.db.add(f)
        await self.db.commit()
        return True

# ==============================================================

# FILE: app/add_ons/social/services/dm_service.py

# ==============================================================

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from app.add_ons.social.models import Conversation, DirectMessage
from app.core.services.s3_service import s3

class DirectMessageService:
    def __init__(self, db: AsyncSession, current_user_id: int):
        self.db = db
        self.user_id = current_user_id

    async def get_or_create_conversation(self, peer_id: int) -> Conversation:
        a, b = sorted([self.user_id, peer_id])
        res = await self.db.execute(select(Conversation).where(and_(Conversation.user_a == a, Conversation.user_b == b)))
        conv = res.scalars().first()
        if conv:
            return conv
        conv = Conversation(user_a=a, user_b=b)
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def send_message(self, conversation_id: int, content: str | None = None, media_filename: str | None = None, content_type: str | None = None):
        media_url = None
        if media_filename and content_type:
            presigned = s3.presign_put_url(key=f"social/dm/{conversation_id}/{media_filename}", content_type=content_type)
            media_url = presigned["url"]  # client uploads then persists the key in message
        msg = DirectMessage(conversation_id=conversation_id, sender_id=self.user_id, content=content, media_url=media_url)
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def list_messages(self, conversation_id: int, limit: int = 50, offset: int = 0):
        res = await self.db.execute(
            select(DirectMessage).where(DirectMessage.conversation_id == conversation_id).order_by(DirectMessage.created_at.desc()).limit(limit).offset(offset)
        )
        return res.scalars().all()

# ==============================================================

# FILE: app/add_ons/social/services/notification_service.py

# ==============================================================

class NotificationService:
    """Stub for future WS/email/push notifications."""
    pass

# ==============================================================

# FILE: app/add_ons/social/routes/__init__.py

# ==============================================================

from fastapi import APIRouter
from .social_routes import router as social_router
from .comment_routes import router as comment_router
from .follow_routes import router as follow_router
from .dm_routes import router as dm_router

router = APIRouter(prefix="/social", tags=["Social"])
router.include_router(social_router)
router.include_router(comment_router)
router.include_router(follow_router)
router.include_router(dm_router)

# ==============================================================

# FILE: app/add_ons/social/routes/social_routes.py

# ==============================================================

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.add_ons.social.schemas import PostCreate
from app.add_ons.social.services import SocialService
from app.add_ons.social.ui.components.post_card import render_post_card
from app.add_ons.social.ui.pages.feed import render_feed

# NOTE: Replace with your real auth dependency

async def get_current_user_id() -> int:
    return 1  # stub; integrate SecurityWrapper/session

router = APIRouter()

@router.get("/feed", response_class=HTMLResponse)
async def feed(page: int = Query(1, ge=1), db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    svc = SocialService(db, user_id)
    posts = await svc.feed(limit=20, offset=(page - 1) * 20)
    return HTMLResponse(render_feed([p.__dict__ for p in posts]).render())

@router.post("/posts")
async def create_post(content: str = Form(""), is_public: bool = Form(False), media_url: str = Form(None), db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    svc = SocialService(db, user_id)
    post = await svc.create_post(PostCreate(content=content or None, is_public=is_public, media_url=media_url))
    return JSONResponse({"id": post.id, "content": post.content})

@router.get("/posts/{post_id}", response_class=HTMLResponse)
async def view_post(post_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    svc = SocialService(db, user_id)
    posts = await svc.feed(limit=1, offset=0)  # simplified; replace with direct fetch & visibility check
    for p in posts:
        if p.id == post_id:
            return HTMLResponse(render_post_card(p.__dict__).render())
    raise HTTPException(404, "Post not found or not visible")

@router.get("/uploads/presign")
async def presign_upload(filename: str, content_type: str, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    svc = SocialService(db, user_id)
    return JSONResponse(await svc.presign_post_upload(filename, content_type))

# ==============================================================

# FILE: app/add_ons/social/routes/comment_routes.py

# ==============================================================

from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.add_ons.social.schemas import CommentCreate
from app.add_ons.social.services import SocialService
from app.add_ons.social.ui.components.comment_section import render_comment

# NOTE: Replace with real auth dependency

async def get_current_user_id() -> int:
    return 1

router = APIRouter(prefix="/comments")

@router.post("")
async def create_comment(post_id: int = Form(...), content: str = Form(...), parent_id: int | None = Form(None), db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    svc = SocialService(db, user_id)
    c = await svc.add_comment(CommentCreate(post_id=post_id, content=content, parent_id=parent_id))
    return {"id": c.id}

# ==============================================================

# FILE: app/add_ons/social/routes/follow_routes.py

# ==============================================================

from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.add_ons.social.services import SocialService

# NOTE: Replace with real auth dependency

async def get_current_user_id() -> int:
    return 1

router = APIRERouter = APIRouter(prefix="/follow")

@router.post("")
async def follow(followee_id: int = Form(...), db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    svc = SocialService(db, user_id)
    await svc.follow(followee_id)
    return {"status": "ok"}

# ==============================================================

# FILE: app/add_ons/social/routes/dm_routes.py

# ==============================================================

from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.add_ons.social.services import DirectMessageService

# NOTE: Replace with real auth dependency

async def get_current_user_id() -> int:
    return 1

router = APIRouter(prefix="/dm")

@router.post("/start")
async def start_conversation(peer_id: int = Form(...), db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    svc = DirectMessageService(db, user_id)
    conv = await svc.get_or_create_conversation(peer_id)
    return {"conversation_id": conv.id}

@router.post("/send")
async def send_message(conversation_id: int = Form(...), content: str | None = Form(None), media_filename: str | None = Form(None), content_type: str | None = Form(None), db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    svc = DirectMessageService(db, user_id)
    msg = await svc.send_message(conversation_id, content, media_filename, content_type)
    return JSONResponse({"id": msg.id, "content": msg.content, "media_url": msg.media_url})

# ==============================================================

# FILE: app/add_ons/social/ui/pages/feed.py

# ==============================================================

from fasthtml.common import *
from app.add_ons.social.ui.components.post_card import render_post_card
from app.core.ui import app_layout

def render(posts: list[dict]):
    return app_layout(
        Div(
            H1("My Feed", cls="text-2xl font-bold mb-4"),
            Div(*[render_post_card(p) for p in posts], cls="flex flex-col gap-4"),
        )
    )

# ==============================================================

# FILE: app/add_ons/social/ui/components/post_card.py

# ==============================================================

from fasthtml.common import *

def _yt_id(url: str) -> str:
    try:
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
        parts = url.rstrip("/").split("/")
        return parts[-1]
    except Exception:
        return url

def render_post_card(post: dict):
    media = None
    url = (post.get("media_url") or "").strip()
    if url:
        if "youtube.com" in url or "youtu.be" in url:
            media = Iframe(src=f"https://www.youtube.com/embed/{_yt_id(url)}?enablejsapi=1", allowfullscreen=True, cls="w-full aspect-video rounded")
        else:
            media = Video(src=url, controls=True, cls="w-full rounded")

    return Div(
        Div(
            B(f"User {post['user_id']}"), Span(" • "), Span(str(post.get("created_at", "")), cls="text-gray-500 text-sm")
        ),
        P(post.get("content", ""), cls="mt-2"),
        media,
        cls="p-4 border rounded bg-white"
    )

# ==============================================================

# FILE: app/add_ons/social/ui/components/comment_section.py

# ==============================================================

from fasthtml.common import *

def render_comment(comment: dict):
    return Div(
        B(f"User {comment['user_id']}:"), Span(" "), Span(comment["content"]),
        cls="p-2 border rounded bg-gray-50"
    )

# ==============================================================

# FILE: app/add_ons/social/analytics_adapter.py

# ==============================================================

from app.core.services.duckdb_service import analytics, BaseAnalyticsAdapter
import json

class SocialAnalyticsAdapter(BaseAnalyticsAdapter):
    TABLE_NAME = "social_events"

    def _ensure_table(self):
        analytics.query(
            f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                id UUID DEFAULT uuid(),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event TEXT,
                user_id INTEGER,
                post_id INTEGER,
                peer_id INTEGER,
                metadata JSON
            );
            """
        )

    def log(self, event: str, user_id: int | None = None, post_id: int | None = None, peer_id: int | None = None, metadata: dict | None = None):
        analytics.query(
            f"INSERT INTO {self.TABLE_NAME} (event, user_id, post_id, peer_id, metadata) VALUES (?, ?, ?, ?, ?)",
            [event, user_id, post_id, peer_id, json.dumps(metadata or {})],
        )

    def top_authors(self, limit: int = 5):
        sql = f"""
            SELECT user_id, COUNT(*) as posts
            FROM {self.TABLE_NAME}
            WHERE event = 'post_created'
            GROUP BY user_id
            ORDER BY posts DESC
            LIMIT {limit}
        """
        return analytics.query(sql)

# Auto-register

SocialAnalyticsAdapter(analytics)

# ==============================================================

# FILE: app/add_ons/social/graphql/schema.py (stub)

# ==============================================================

import strawberry

@strawberry.type
class PostType:
    id: int
    user_id: int
    content: str | None
    media_url: str | None
    is_public: bool

@strawberry.type
class SocialQuery:
    hello: str = strawberry.field(resolver=lambda: "social-graphql-ready")

schema = strawberry.Schema(query=SocialQuery)

# ==============================================================

# FILE: app/add_ons/social/README.md

# ==============================================================

# Social Add-on (FastApp)

- Private-first social network with follows/mutuals and optional public posts
- Posts with S3/YouTube media, comments, likes, follows
- Direct messaging with media
- HTMX/FastHTML UI
- Analytics adapter auto-registered into DuckDB

## Quick API Notes

- `GET /social/feed` — personalized feed (requires auth)
- `POST /social/posts` — create post (content/media)
- `GET /social/uploads/presign?filename=...&content_type=...` — presigned PUT URL to S3
- `POST /social/dm/start` — start conversation
- `POST /social/dm/send` — send message

> Replace `get_current_user_id()` with your real auth dependency (SecurityWrapper/session).
>
>
> # ==============================================================
>
> # FILE: app/add_ons/social/services/group_service.py (UPDATED WITH LEAVE GROUP)
>
> # ==============================================================
>
> from sqlalchemy.ext.asyncio import AsyncSession
> from sqlalchemy import select, delete
> from app.add_ons.social.models.group import Group, GroupMember
> from app.add_ons.social.schemas.group_schema import GroupCreate
>
> class GroupService:
>     def __init__(self, db: AsyncSession, user_id: int):
>         self.db = db
>         self.user_id = user_id
>
>     async def create_group(self, data: GroupCreate) -> Group:
>         g = Group(owner_id=self.user_id, **data.model_dump())
>         self.db.add(g)
>         await self.db.commit()
>         await self.db.refresh(g)
>         self.db.add(GroupMember(group_id=g.id, user_id=self.user_id))
>         await self.db.commit()
>         return g
>
>     async def join_group(self, group_id: int):
>         exists = await self.db.execute(
>             select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == self.user_id)
>         )
>         if not exists.scalars().first():
>             self.db.add(GroupMember(group_id=group_id, user_id=self.user_id))
>             await self.db.commit()
>
>     async def leave_group(self, group_id: int):
>         await self.db.execute(
>             delete(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == self.user_id)
>         )
>         await self.db.commit()
>
>     async def is_member(self, group_id: int) -> bool:
>         res = await self.db.execute(
>             select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == self.user_id)
>         )
>         return res.scalars().first() is not None
>
> # ==============================================================
>
> # FILE: app/add_ons/social/routes/group_routes.py (UPDATED WITH LEAVE ENDPOINT)
>
> # ==============================================================
>
> from fastapi import APIRouter, Depends, Form
> from sqlalchemy.ext.asyncio import AsyncSession
> from app.core.db import get_db
> from app.add_ons.social.services.group_service import GroupService
> from app.add_ons.social.schemas.group_schema import GroupCreate
>
> # NOTE: Replace with real auth
>
> aSync def get_current_user_id() -> int:
>     return 1
>
> router = APIRouter(prefix="/groups", tags=["Groups"])
>
> @router.post("")
> aSync def create_group(
>     name: str = Form(...),
>     description: str | None = Form(None),
>     is_public: bool = Form(True),
>     db: AsyncSession = Depends(get_db),
>     user_id: int = Depends(get_current_user_id),
> ):
>     svc = GroupService(db, user_id)
>     g = await svc.create_group(GroupCreate(name=name, description=description, is_public=is_public))
>     return {"id": g.id, "name": g.name}
>
> @router.post("/{group_id}/join")
> aSync def join_group(group_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
>     svc = GroupService(db, user_id)
>     await svc.join_group(group_id)
>     return {"status": "ok", "group_id": group_id}
>
> @router.post("/{group_id}/leave")
> aSync def leave_group(group_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
>     svc = GroupService(db, user_id)
>     await svc.leave_group(group_id)
>     return {"status": "ok", "group_id": group_id}
>
> # ==============================================================
>
> # FILE: app/add_ons/social/ui/pages/group_page.py (UPDATED WITH LEAVE ACTION)
>
> # ==============================================================
>
> from fasthtml.common import *
> from app.add_ons.social.ui.components.post_card import render_post_card
> from app.core.ui import app_layout
>
> def render(group: dict, posts: list[dict], is_member: bool):
>     join_btn = (
>         Button(
>             "Join Group",
>             hx_post=f"/groups/{group['id']}/join",
>             hx_swap="outerHTML",
>             hx_target="this",
>             hx_on="afterRequest: htmx.trigger('#group-members', 'refresh')",
>             cls="btn btn-primary",
>         )
>         if not is_member
>         else Button(
>             "Leave Group",
>             hx_post=f"/groups/{group['id']}/leave",
>             hx_swap="outerHTML",
>             hx_target="this",
>             hx_on="afterRequest: htmx.trigger('#group-members', 'refresh')",
>             cls="btn btn-secondary",
>         )
>     )
>
>     return app_layout(
>         Div(
>             H2(group["name"], cls="text-2xl font-bold mb-2"),
>             P(group.get("description", ""), cls="text-gray-600 mb-4"),
>             join_btn,
>             Hr(),
>             Div(
>                 H3("Members", cls="text-lg font-semibold mt-6 mb-2"),
>                 Div(
>                     hx_get=f"/groups/{group['id']}/members",
>                     hx_trigger="load, refresh from:body",
>                     hx_target="#group-members",
>                     id="group-members",
>                 ),
>                 cls="border-t pt-4"
>             ),
>             Hr(),
>             Div(*[render_post_card(p) for p in posts], cls="flex flex-col gap-4 mt-4"),
>         )
>     )



# ==============================================================

# FILE: app/add_ons/social/analytics/group_events_adapter.py (EXTENDED WITH METRICS)

# ==============================================================

from app.core.services.duckdb_service import analytics

def log_group_event(event: str, group_id: int, user_id: int):
    """Log high-level group membership and engagement events."""
    analytics.query(
        "INSERT INTO social_events (event, user_id, peer_id, metadata) VALUES (?, ?, ?, ?)",
        [event, user_id, group_id, "{}"],
    )

def log_group_created(group_id: int, user_id: int):
    log_group_event("group_created", group_id, user_id)

def log_group_joined(group_id: int, user_id: int):
    log_group_event("group_joined", group_id, user_id)

def log_group_left(group_id: int, user_id: int):
    log_group_event("group_left", group_id, user_id)

def log_group_post_created(group_id: int, user_id: int):
    log_group_event("group_post_created", group_id, user_id)

# ==============================================================

# FILE: app/add_ons/social/analytics/group_metrics_service.py (NEW)

# ==============================================================

import duckdb
from datetime import datetime, timedelta
from app.core.services.duckdb_service import analytics

class GroupMetricsService:
    """Aggregates group-level engagement metrics from social_events."""

    @staticmethod
    def _run_query(sql: str, params=None):
        return analytics.query(sql, params or [])

    @classmethod
    def total_groups(cls):
        return cls._run_query("SELECT COUNT(DISTINCT peer_id) FROM social_events WHERE event = 'group_created'")[0][0]

    @classmethod
    def member_count(cls, group_id: int):
        return cls._run_query(
            "SELECT COUNT(DISTINCT user_id) FROM social_events WHERE event = 'group_joined' AND peer_id = ?",
            [group_id],
        )[0][0]

    @classmethod
    def post_count(cls, group_id: int):
        return cls._run_query(
            "SELECT COUNT(*) FROM social_events WHERE event = 'group_post_created' AND peer_id = ?",
            [group_id],
        )[0][0]

    @classmethod
    def active_groups(cls, days: int = 7):
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        return cls._run_query(
            """
            SELECT peer_id, COUNT(*) AS activity_count
            FROM social_events
            WHERE event IN ('group_post_created', 'group_joined', 'group_left')
              AND timestamp > ?
            GROUP BY peer_id
            ORDER BY activity_count DESC
            LIMIT 20;
            """,
            [cutoff],
        )

    @classmethod
    def engagement_rate(cls, group_id: int):
        joined = cls.member_count(group_id)
        posts = cls.post_count(group_id)
        return 0 if joined == 0 else round(posts / joined, 2)

    @classmethod
    def summary(cls, group_id: int):
        return {
            "group_id": group_id,
            "members": cls.member_count(group_id),
            "posts": cls.post_count(group_id),
            "engagement_rate": cls.engagement_rate(group_id),
        }



# ==============================================================

# FILE: app/add_ons/social/leaderboard/base.py

# ==============================================================

from abc import ABC, abstractmethod
from typing import Any, List, Dict

class BaseLeaderboard(ABC):
    """Abstract base class for all leaderboard types."""

    name: str = "base"
    description: str = "Base leaderboard type"

    @abstractmethod
    def get_rankings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return a list of ranked entities."""
        raise NotImplementedError

# ==============================================================

# FILE: app/add_ons/social/leaderboard/engagement_leaderboard.py

# ==============================================================

from typing import List, Dict
from app.core.services.duckdb_service import analytics
from .base import BaseLeaderboard

class EngagementLeaderboard(BaseLeaderboard):
    name = "engagement"
    description = "Ranks users by total engagement (posts, comments, likes)."

    def get_rankings(self, limit: int = 10) -> List[Dict]:
        query = """
        SELECT user_id,
               COUNT(CASE WHEN event = 'post_created' THEN 1 END) AS posts,
               COUNT(CASE WHEN event = 'comment_created' THEN 1 END) AS comments,
               COUNT(CASE WHEN event = 'like_created' THEN 1 END) AS likes,
               COALESCE(COUNT(*),0) AS total
        FROM social_events
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT ?;
        """
        rows = analytics.query(query, [limit])
        return [
            {"user_id": r[0], "posts": r[1] or 0, "comments": r[2] or 0, "likes": r[3] or 0, "total": r[4] or 0}
            for r in rows
        ]

# ==============================================================

# FILE: app/add_ons/social/leaderboard/scoring_leaderboard.py

# ==============================================================

from typing import List, Dict
from app.core.services.duckdb_service import analytics
from .base import BaseLeaderboard

class ScoringLeaderboard(BaseLeaderboard):
    name = "scoring"
    description = "Ranks participants based on judged scores (e.g., competitions)."

    def get_rankings(self, limit: int = 10) -> List[Dict]:
        query = """
        SELECT user_id,
               AVG(CAST(metadata->>'score' AS DOUBLE)) AS avg_score,
               COUNT(*) AS votes
        FROM social_events
        WHERE event = 'content_scored'
        GROUP BY user_id
        ORDER BY avg_score DESC NULLS LAST, votes DESC
        LIMIT ?;
        """
        rows = analytics.query(query, [limit])
        return [
            {"user_id": r[0], "avg_score": round(r[1] or 0.0, 2), "votes": r[2] or 0}
            for r in rows
        ]

# ==============================================================

# FILE: app/add_ons/social/leaderboard/service.py

# ==============================================================

from typing import List, Dict
from .engagement_leaderboard import EngagementLeaderboard
from .scoring_leaderboard import ScoringLeaderboard

# Registry of available leaderboard modes

LEADERBOARD_TYPES = {
    "engagement": EngagementLeaderboard(),
    "scoring": ScoringLeaderboard(),
}

def get_leaderboard(mode: str = "engagement", limit: int = 10) -> List[Dict]:
    lb = LEADERBOARD_TYPES.get(mode, LEADERBOARD_TYPES["engagement"])  # default to engagement
    return lb.get_rankings(limit=limit)

# ==============================================================

# FILE: app/add_ons/social/leaderboard/routes.py

# ==============================================================

from fastapi import APIRouter, Query
from .service import get_leaderboard

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

@router.get("")
async def api_leaderboard(mode: str = Query("engagement"), limit: int = Query(10, ge=1, le=100)):
    data = get_leaderboard(mode=mode, limit=limit)
    return {"mode": mode, "leaderboard": data}

# ==============================================================

# FILE: app/add_ons/social/leaderboard/ui/leaderboard_page.py

# ==============================================================

from fasthtml.common import *
from app.core.ui import app_layout

def render_leaderboard(mode: str, leaderboard: list[dict]):
    def row(idx: int, entry: dict):
        return Tr(
            Td(str(idx + 1), cls="px-3 py-2"),
            Td(str(entry.get("user_id", "-")), cls="px-3 py-2"),
            Td(str(entry.get("total", entry.get("avg_score", "-"))), cls="px-3 py-2"),
            Td(str(entry.get("votes", entry.get("comments", entry.get("likes", "-")))), cls="px-3 py-2"),
        )

    table = Table(
        Thead(Tr(Th("#"), Th("User ID"), Th("Score / Total"), Th("Votes / Comments"))),
        Tbody(*[row(i, e) for i, e in enumerate(leaderboard)], id="leaderboard-table"),
        cls="min-w-full bg-white border rounded shadow"
    )

    return app_layout(
        Div(
            H2("Leaderboard", cls="text-2xl font-bold mb-4"),
            Div(
                Label("Mode:", cls="mr-2 text-sm text-gray-700"),
                Select(
                    Option("Engagement", value="engagement", selected=mode == "engagement"),
                    Option("Scoring", value="scoring", selected=mode == "scoring"),
                    name="mode",
                    hx_get="/leaderboard",
                    hx_target="#leaderboard-container",
                    hx_trigger="change",
                    cls="border rounded p-1",
                ),
                cls="mb-4"
            ),
            Div(table, id="leaderboard-container"),
        )
    )

# ==============================================================

# FILE: app/add_ons/social/leaderboard/routes_ui.py

# ==============================================================

from fastapi import APIRouter, Query
from .service import get_leaderboard
from .ui.leaderboard_page import render_leaderboard

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard UI"])

@router.get("/view")
async def leaderboard_view(mode: str = Query("engagement"), limit: int = Query(10, ge=1, le=100)):
    data = get_leaderboard(mode=mode, limit=limit)
    return render_leaderboard(mode, data)

# ==============================================================

# FILE: app/add_ons/social/routes/__init__.py (INTEGRATION SNIPPET)

# ==============================================================

"""

# In `app/add_ons/social/routes/__init__.py`, include leaderboard routes:

from app.add_ons.social.leaderboard.routes import router as leaderboard_api_router
from app.add_ons.social.leaderboard.routes_ui import router as leaderboard_ui_router
router.include_router(leaderboard_api_router)
router.include_router(leaderboard_ui_router)
"""

# ==============================================================

# FILE: app/add_ons/social/leaderboard/upvote_leaderboard.py

# ==============================================================

from typing import List, Dict
from app.core.services.duckdb_service import analytics
from .base import BaseLeaderboard

class UpvoteLeaderboard(BaseLeaderboard):
    name = "upvote"
    description = "Ranks media by community voting (upvotes/downvotes)."

    def get_rankings(self, limit: int = 10) -> List[Dict]:
        query = """
        SELECT peer_id AS media_id,
               SUM(CASE WHEN event = 'media_upvoted' THEN 1 ELSE 0 END) AS upvotes,
               SUM(CASE WHEN event = 'media_downvoted' THEN 1 ELSE 0 END) AS downvotes,
               (SUM(CASE WHEN event = 'media_upvoted' THEN 1 ELSE 0 END) -
                SUM(CASE WHEN event = 'media_downvoted' THEN 1 ELSE 0 END)) AS score,
               COUNT(DISTINCT user_id) AS voters
        FROM social_events
        WHERE event IN ('media_upvoted', 'media_downvoted')
        GROUP BY media_id
        ORDER BY score DESC, upvotes DESC
        LIMIT ?;
        """
        rows = analytics.query(query, [limit])
        return [
            {
                "media_id": r[0],
                "upvotes": r[1] or 0,
                "downvotes": r[2] or 0,
                "score": r[3] or 0,
                "voters": r[4] or 0,
            }
            for r in rows
        ]

# ==============================================================

# FILE: app/add_ons/social/leaderboard/service.py (UPDATED)

# ==============================================================

from typing import List, Dict
from .engagement_leaderboard import EngagementLeaderboard
from .scoring_leaderboard import ScoringLeaderboard
from .upvote_leaderboard import UpvoteLeaderboard

LEADERBOARD_TYPES = {
    "engagement": EngagementLeaderboard(),
    "scoring": ScoringLeaderboard(),
    "upvote": UpvoteLeaderboard(),
}

def get_leaderboard(mode: str = "engagement", limit: int = 10) -> List[Dict]:
    lb = LEADERBOARD_TYPES.get(mode, LEADERBOARD_TYPES["engagement"])
    return lb.get_rankings(limit=limit)

# ==============================================================

# FILE: app/add_ons/social/services/feed_service.py

# ==============================================================

import math
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.add_ons.social.models import Post

DECAY_FACTOR = 1.8  # Controls how fast older posts lose rank

def compute_hot_score(upvotes: int, downvotes: int, created_at: datetime) -> float:
    """Calculate post hotness using a simplified Reddit-style formula."""
    score = upvotes - downvotes
    order = max(abs(score), 1)
    seconds = (created_at - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds()
    return round(math.log(order, 10) + seconds / 45000, 6)

async def get_ranked_feed(db: AsyncSession, limit: int = 20):
    """Retrieve posts and rank them by hotness score using upvotes/downvotes and recency."""
    res = await db.execute(select(Post))
    posts = res.scalars().all()

    scored_posts = []
    for p in posts:
        up = getattr(p, "upvotes", 0)
        down = getattr(p, "downvotes", 0)
        hot = compute_hot_score(up, down, p.created_at)
        scored_posts.append((p, hot))

    scored_posts.sort(key=lambda x: x[1], reverse=True)
    return [p for p, _ in scored_posts[:limit]]

# ==============================================================

# FILE: app/add_ons/social/models/events_example.py (REFERENCE)

# ==============================================================

"""Example event schema entries for DuckDB analytics events table:

social_events table columns:
    event TEXT -- e.g., 'media_upvoted', 'media_downvoted'
    user_id INTEGER
    peer_id INTEGER  # media_id or post_id
    metadata JSON  # optional context {"reason": "great quality"}

Example rows:
    ('media_upvoted', 12, 204, '{}')
    ('media_downvoted', 23, 205, '{"reason": "spam"}')
"""

# ==============================================================

# FILE: app/add_ons/social/leaderboard/ui/leaderboard_page.py (UPDATED SNIPPET)

# ==============================================================

Select(
    Option("Engagement", value="engagement"),
    Option("Scoring", value="scoring"),
    Option("Upvote/Downvote", value="upvote"),
    hx_get="/leaderboard",
    hx_target="#leaderboard-container",
    hx_trigger="change",
    cls="border rounded p-1",
)

# ==============================================================

# FILE: app/add_ons/social/leaderboard/upvote_leaderboard.py

# ==============================================================

from typing import List, Dict
from app.core.services.duckdb_service import analytics
from .base import BaseLeaderboard

class UpvoteLeaderboard(BaseLeaderboard):
    name = "upvote"
    description = "Ranks media by community voting (upvotes/downvotes)."

    def get_rankings(self, limit: int = 10) -> List[Dict]:
        query = """
        SELECT peer_id AS media_id,
               SUM(CASE WHEN event = 'media_upvoted' THEN 1 ELSE 0 END) AS upvotes,
               SUM(CASE WHEN event = 'media_downvoted' THEN 1 ELSE 0 END) AS downvotes,
               (SUM(CASE WHEN event = 'media_upvoted' THEN 1 ELSE 0 END) -
                SUM(CASE WHEN event = 'media_downvoted' THEN 1 ELSE 0 END)) AS score,
               COUNT(DISTINCT user_id) AS voters
        FROM social_events
        WHERE event IN ('media_upvoted', 'media_downvoted')
        GROUP BY media_id
        ORDER BY score DESC, upvotes DESC
        LIMIT ?;
        """
        rows = analytics.query(query, [limit])
        return [
            {
                "media_id": r[0],
                "upvotes": r[1] or 0,
                "downvotes": r[2] or 0,
                "score": r[3] or 0,
                "voters": r[4] or 0,
            }
            for r in rows
        ]

# ==============================================================

# FILE: app/add_ons/social/leaderboard/service.py (UPDATED)

# ==============================================================

from typing import List, Dict
from .engagement_leaderboard import EngagementLeaderboard
from .scoring_leaderboard import ScoringLeaderboard
from .upvote_leaderboard import UpvoteLeaderboard

LEADERBOARD_TYPES = {
    "engagement": EngagementLeaderboard(),
    "scoring": ScoringLeaderboard(),
    "upvote": UpvoteLeaderboard(),
}

def get_leaderboard(mode: str = "engagement", limit: int = 10) -> List[Dict]:
    lb = LEADERBOARD_TYPES.get(mode, LEADERBOARD_TYPES["engagement"])
    return lb.get_rankings(limit=limit)

# ==============================================================

# FILE: app/add_ons/social/services/feed_service.py

# ==============================================================

import math
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.add_ons.social.models import Post

DECAY_FACTOR = 1.8  # Controls how fast older posts lose rank

def compute_hot_score(upvotes: int, downvotes: int, created_at: datetime) -> float:
    """Calculate post hotness using a simplified Reddit-style formula."""
    score = upvotes - downvotes
    order = max(abs(score), 1)
    seconds = (created_at - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds()
    return round(math.log(order, 10) + seconds / 45000, 6)

async def get_ranked_feed(db: AsyncSession, limit: int = 20):
    """Retrieve posts and rank them by hotness score using upvotes/downvotes and recency."""
    res = await db.execute(select(Post))
    posts = res.scalars().all()

    scored_posts = []
    for p in posts:
        up = getattr(p, "upvotes", 0)
        down = getattr(p, "downvotes", 0)
        hot = compute_hot_score(up, down, p.created_at)
        scored_posts.append((p, hot))

    scored_posts.sort(key=lambda x: x[1], reverse=True)
    return [p for p, _ in scored_posts[:limit]]

# ==============================================================

# FILE: app/add_ons/social/models/events_example.py (REFERENCE)

# ==============================================================

"""Example event schema entries for DuckDB analytics events table:

social_events table columns:
    event TEXT -- e.g., 'media_upvoted', 'media_downvoted'
    user_id INTEGER
    peer_id INTEGER  # media_id or post_id
    metadata JSON  # optional context {"reason": "great quality"}

Example rows:
    ('media_upvoted', 12, 204, '{}')
    ('media_downvoted', 23, 205, '{"reason": "spam"}')
"""

# ==============================================================

# FILE: app/add_ons/social/leaderboard/ui/leaderboard_page.py (UPDATED SNIPPET)

# ==============================================================

Select(
    Option("Engagement", value="engagement"),
    Option("Scoring", value="scoring"),
    Option("Upvote/Downvote", value="upvote"),
    hx_get="/leaderboard",
    hx_target="#leaderboard-container",
    hx_trigger="change",
    cls="border rounded p-1",
)



# ==============================================================

# FILE: app/add_ons/social/leaderboard/upvote_leaderboard.py

# ==============================================================

from typing import List, Dict
from app.core.services.duckdb_service import analytics
from .base import BaseLeaderboard

class UpvoteLeaderboard(BaseLeaderboard):
    name = "upvote"
    description = "Ranks media by community voting (upvotes/downvotes)."

    def get_rankings(self, limit: int = 10) -> List[Dict]:
        query = """
        SELECT peer_id AS media_id,
               SUM(CASE WHEN event = 'media_upvoted' THEN 1 ELSE 0 END) AS upvotes,
               SUM(CASE WHEN event = 'media_downvoted' THEN 1 ELSE 0 END) AS downvotes,
               (SUM(CASE WHEN event = 'media_upvoted' THEN 1 ELSE 0 END) -
                SUM(CASE WHEN event = 'media_downvoted' THEN 1 ELSE 0 END)) AS score,
               COUNT(DISTINCT user_id) AS voters
        FROM social_events
        WHERE event IN ('media_upvoted', 'media_downvoted')
        GROUP BY media_id
        ORDER BY score DESC, upvotes DESC
        LIMIT ?;
        """
        rows = analytics.query(query, [limit])
        return [
            {
                "media_id": r[0],
                "upvotes": r[1] or 0,
                "downvotes": r[2] or 0,
                "score": r[3] or 0,
                "voters": r[4] or 0,
            }
            for r in rows
        ]

# ==============================================================

# FILE: app/add_ons/social/leaderboard/service.py (UPDATED)

# ==============================================================

from typing import List, Dict
from .engagement_leaderboard import EngagementLeaderboard
from .scoring_leaderboard import ScoringLeaderboard
from .upvote_leaderboard import UpvoteLeaderboard

LEADERBOARD_TYPES = {
    "engagement": EngagementLeaderboard(),
    "scoring": ScoringLeaderboard(),
    "upvote": UpvoteLeaderboard(),
}

def get_leaderboard(mode: str = "engagement", limit: int = 10) -> List[Dict]:
    lb = LEADERBOARD_TYPES.get(mode, LEADERBOARD_TYPES["engagement"])
    return lb.get_rankings(limit=limit)

# ==============================================================

# FILE: app/add_ons/social/services/feed_service.py

# ==============================================================

import math
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.add_ons.social.models import Post

DECAY_FACTOR = 1.8  # Controls how fast older posts lose rank

def compute_hot_score(upvotes: int, downvotes: int, created_at: datetime) -> float:
    """Calculate post hotness using a simplified Reddit-style formula."""
    score = upvotes - downvotes
    order = max(abs(score), 1)
    seconds = (created_at - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds()
    return round(math.log(order, 10) + seconds / 45000, 6)

async def get_ranked_feed(db: AsyncSession, limit: int = 20):
    """Retrieve posts and rank them by hotness score using upvotes/downvotes and recency."""
    res = await db.execute(select(Post))
    posts = res.scalars().all()

    scored_posts = []
    for p in posts:
        up = getattr(p, "upvotes", 0)
        down = getattr(p, "downvotes", 0)
        hot = compute_hot_score(up, down, p.created_at)
        scored_posts.append((p, hot))

    scored_posts.sort(key=lambda x: x[1], reverse=True)
    return [p for p, _ in scored_posts[:limit]]

# ==============================================================

# FILE: app/add_ons/social/models/events_example.py (REFERENCE)

# ==============================================================

"""Example event schema entries for DuckDB analytics events table:

social_events table columns:
    event TEXT -- e.g., 'media_upvoted', 'media_downvoted'
    user_id INTEGER
    peer_id INTEGER  # media_id or post_id
    metadata JSON  # optional context {"reason": "great quality"}

Example rows:
    ('media_upvoted', 12, 204, '{}')
    ('media_downvoted', 23, 205, '{"reason": "spam"}')
"""

# ==============================================================

# FILE: app/add_ons/social/leaderboard/ui/leaderboard_page.py (UPDATED SNIPPET)

# ==============================================================

Select(
    Option("Engagement", value="engagement"),
    Option("Scoring", value="scoring"),
    Option("Upvote/Downvote", value="upvote"),
    hx_get="/leaderboard",
    hx_target="#leaderboard-container",
    hx_trigger="change",
    cls="border rounded p-1",
)
