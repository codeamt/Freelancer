"""Blog Routes - Posts"""

from fasthtml.common import *
import os

from core.services.auth import get_current_user_from_context
from core.ui.layout import Layout

from add_ons.domains.blog.services.post_service import PostService
from add_ons.domains.blog.ui.pages import blog_detail_page, blog_list_page, blog_new_page


router_posts = APIRouter()


def _use_db(request: Request) -> bool:
    return os.getenv("USE_DB", "").lower() in {"1", "true", "yes"}


@router_posts.get("/blog")
async def list_posts(request: Request):
    service = PostService(use_db=_use_db(request))
    posts = await service.list_posts()
    return blog_list_page(posts)


@router_posts.get("/blog/new")
async def new_post(request: Request):
    user = get_current_user_from_context()
    if not user:
        return RedirectResponse("/auth/login?redirect=/blog/new")

    return blog_new_page()


@router_posts.post("/blog/posts")
async def create_post(request: Request, title: str = Form(...), body: str = Form("")):
    user = get_current_user_from_context()
    if not user:
        return Div(P("Please sign in", cls="text-error"), cls="alert alert-error")

    if not title or len(title) < 3:
        return Div(P("Title must be at least 3 characters", cls="text-error"), cls="alert alert-error")

    service = PostService(use_db=_use_db(request))
    post = await service.create_post(author_id=user["id"], title=title, body=body)

    return Response(status_code=303, headers={"HX-Redirect": f"/blog/posts/{post['id']}"})


@router_posts.get("/blog/posts/{post_id}")
async def view_post(request: Request, post_id: int):
    service = PostService(use_db=_use_db(request))
    post = await service.get_post(post_id)
    if not post:
        return Layout(Div("Post not found", cls="alert alert-error"), title="Not Found")

    return blog_detail_page(post)
