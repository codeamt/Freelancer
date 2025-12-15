"""Blog Routes Package"""

from fasthtml.common import *

from .posts import router_posts

router_blog = APIRouter()
router_blog.routes.extend(router_posts.routes)

__all__ = ["router_blog"]
