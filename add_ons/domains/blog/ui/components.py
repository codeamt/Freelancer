"""Blog UI Components"""

from fasthtml.common import *


def PostCard(post: dict):
    return Div(
        Div(
            H3(post.get("title", "Untitled"), cls="text-xl font-bold mb-2"),
            P((post.get("body") or "")[:180], cls="text-sm text-gray-600 mb-4"),
            A("Read", href=f"/blog/posts/{post.get('id')}", cls="btn btn-sm btn-outline"),
            cls="card bg-base-100 shadow p-4",
        )
    )
