"""
Social UI Components - FastHTML Components
Reusable components for social features
"""

from fasthtml.common import *


def PostComposer(placeholder: str = "What's on your mind?"):
    """Post composer component"""
    return Div(
        Form(
            Textarea(
                name="content",
                placeholder=placeholder,
                cls="w-full p-3 border rounded-lg resize-none",
                rows=3
            ),
            Button("Post", type="submit", cls="btn btn-primary mt-2"),
            cls="space-y-2"
        ),
        cls="p-4 border rounded-lg bg-white shadow-sm"
    )


def PostCard(post_data: dict, current_user_id: int):
    """Individual post card component"""
    
    post_id = post_data.get("id")
    user_id = post_data.get("user_id")
    content = post_data.get("content", "")
    is_public = post_data.get("is_public", False)
    
    return Div(
        Div(
            B(f"User {user_id}"),
            Span(" • "),
            Span("Public" if is_public else "Followers", cls="text-xs px-2 py-1 rounded bg-gray-100"),
            cls="mb-2"
        ),
        P(content or "No content", cls="mb-3"),
        Div(
            Button("❤️ Like", cls="btn btn-sm btn-outline-secondary"),
            Button("💬 Comment", cls="btn btn-sm btn-outline-secondary ml-2"),
            cls="flex gap-2"
        ),
        cls="p-4 border rounded-lg bg-white shadow-sm"
    )


def CommentCard(comment_data: dict, current_user_id: int):
    """Individual comment component"""
    
    user_id = comment_data.get("user_id")
    content = comment_data.get("content", "")
    
    return Div(
        B(f"User {user_id}"),
        P(content, cls="mt-1"),
        cls="p-3 border-l-4 border-gray-200 bg-gray-50 rounded-r-lg"
    )


def FollowButton(user_id: int, is_following: bool = False):
    """Follow/unfollow button component"""
    return Button(
        "Unfollow" if is_following else "Follow",
        cls="btn btn-sm " + ("btn-secondary" if is_following else "btn-primary")
    )


def UserCard(user_data: dict, current_user_id: int):
    """User profile card component"""
    
    user_id = user_data.get("id")
    username = user_data.get("username", f"User {user_id}")
    followers_count = user_data.get("followers_count", 0)
    following_count = user_data.get("following_count", 0)
    
    return Div(
        Div(
            H3(username, cls="font-bold text-lg"),
            P(f"{followers_count} followers • {following_count} following", cls="text-sm text-gray-600"),
            FollowButton(user_id, user_data.get("is_following", False)),
            cls="space-y-2"
        ),
        cls="p-4 border rounded-lg bg-white shadow-sm"
    )


def SocialFeed(posts: list, current_user_id: int):
    """Complete social feed component"""
    
    return Div(
        PostComposer(),
        Div(
            *[PostCard(post, current_user_id) for post in posts],
            cls="space-y-4 mt-4"
        ) if posts else P("No posts yet.", cls="text-center text-gray-500 py-8"),
        cls="max-w-2xl mx-auto"
    )


def UserProfile(user_data: dict, current_user_id: int):
    """Complete user profile component"""
    
    user_id = user_data.get("id")
    username = user_data.get("username", f"User {user_id}")
    followers_count = user_data.get("followers_count", 0)
    following_count = user_data.get("following_count", 0)
    
    return Div(
        Div(
            H2(username, cls="text-2xl font-bold"),
            P(f"{followers_count} followers • {following_count} following", cls="text-gray-600"),
            FollowButton(user_id, user_data.get("is_following", False)),
            cls="space-y-4 text-center"
        ),
        cls="max-w-2xl mx-auto p-6"
    )
