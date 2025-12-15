"""Blog UI Pages"""

from fasthtml.common import *

from core.ui.layout import Layout
from add_ons.domains.blog.ui.components import PostCard


def blog_list_page(posts: list[dict]):
    content = Div(
        Div(
            H1("Blog", cls="text-4xl font-bold mb-2"),
            P("Posts", cls="text-gray-500 mb-6"),
            Div(
                A("New Post", href="/blog/new", cls="btn btn-primary"),
                cls="mb-8",
            ),
            cls="mb-8",
        ),
        (Div(*[PostCard(p) for p in posts], cls="grid grid-cols-1 gap-4") if posts else Div(P("No posts yet"))),
        cls="container mx-auto px-4 py-8",
    )
    return Layout(content, title="Blog")


def blog_new_page():
    content = Div(
        H1("New Post", cls="text-3xl font-bold mb-6"),
        Form(
            Div(
                Label("Title", cls="block text-sm font-medium mb-2"),
                Input(name="title", type="text", cls="input input-bordered w-full", required=True),
                cls="mb-4",
            ),
            Div(
                Label("Body", cls="block text-sm font-medium mb-2"),
                Textarea(name="body", cls="textarea textarea-bordered w-full", rows=10),
                cls="mb-4",
            ),
            Button("Publish", type="submit", cls="btn btn-primary"),
            hx_post="/blog/posts",
            hx_target="#blog-result",
        ),
        Div(id="blog-result", cls="mt-4"),
        cls="container mx-auto px-4 py-8",
    )
    return Layout(content, title="New Post")


def blog_detail_page(post: dict):
    content = Div(
        Div(
            A("← Back", href="/blog", cls="link"),
            cls="mb-6",
        ),
        H1(post.get("title", "Untitled"), cls="text-4xl font-bold mb-4"),
        P(post.get("body", ""), cls="prose max-w-none"),
        cls="container mx-auto px-4 py-8",
    )
    return Layout(content, title=post.get("title", "Post"))
