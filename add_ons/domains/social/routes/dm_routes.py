"""
Direct Message Routes - Adapted for FastHTML
Handles private conversations and messaging
"""

from typing import Optional
from fasthtml.common import *

from add_ons.domains.social.services.dm_service import DirectMessageService
from core.utils.logger import get_logger

logger = get_logger(__name__)


def get_current_user_id(request) -> int:
    """Get current user ID from request (placeholder - integrate with auth)"""
    # TODO: Replace with actual authentication
    return 1


def create_dm_routes():
    """Create and return direct message routes"""
    
    @app.get("/social/messages")
    async def get_conversations(request, page: int = 1):
        """Get user's conversations list"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = DirectMessageService(db, user_id)
            conversations = await service.get_conversations(limit=20, offset=(page - 1) * 20)
            
            return render_conversation_list(conversations, user_id)
    
    @app.get("/social/messages/{conversation_id}")
    async def get_conversation(request, conversation_id: int, page: int = 1):
        """Get specific conversation with messages"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = DirectMessageService(db, user_id)
            
            # Get conversation info and messages
            conversations = await service.get_conversations(limit=100)
            conversation = next((c for c in conversations if c["id"] == conversation_id), None)
            
            if not conversation:
                return Response("Conversation not found", status_code=404)
            
            messages = await service.get_messages(
                conversation_id=conversation_id,
                limit=50,
                offset=(page - 1) * 50
            )
            
            return render_conversation_detail(conversation, messages, user_id)
    
    @app.post("/social/messages")
    async def start_conversation(request, peer_id: int):
        """Start new conversation"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = DirectMessageService(db, user_id)
            
            try:
                conversation = await service.get_or_create_conversation(peer_id)
                return Response(f"/social/messages/{conversation.id}", status_code=201)
            except ValueError as e:
                return Response(str(e), status_code=400)
    
    @app.post("/social/messages/{conversation_id}/send")
    async def send_message(request, conversation_id: int, content: str = "", 
                          media_url: str = ""):
        """Send message in conversation"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = DirectMessageService(db, user_id)
            
            message = await service.send_message(
                conversation_id=conversation_id,
                content=content if content.strip() else None,
                media_url=media_url if media_url.strip() else None
            )
            
            if not message:
                return Response("Conversation not found", status_code=404)
            
            return render_message_card(message, user_id)
    
    @app.get("/social/messages/{conversation_id}/messages")
    async def get_messages(request, conversation_id: int, page: int = 1):
        """Get messages from conversation"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = DirectMessageService(db, user_id)
            messages = await service.get_messages(
                conversation_id=conversation_id,
                limit=20,
                offset=(page - 1) * 20
            )
            
            return render_message_list(messages, user_id)
    
    @app.put("/social/messages/{message_id}")
    async def edit_message(request, message_id: int, content: str):
        """Edit message"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = DirectMessageService(db, user_id)
            message = await service.edit_message(message_id, content)
            
            if not message:
                return Response("Message not found or cannot be edited", status_code=404)
            
            return render_message_card(message, user_id)
    
    @app.delete("/social/messages/{message_id}")
    async def delete_message(request, message_id: int):
        """Delete message"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = DirectMessageService(db, user_id)
            success = await service.delete_message(message_id)
            
            if not success:
                return Response("Message not found or unauthorized", status_code=404)
            
            return Response("Message deleted", status_code=200)
    
    @app.post("/social/messages/{conversation_id}/read")
    async def mark_read(request, conversation_id: int):
        """Mark conversation as read"""
        user_id = get_current_user_id(request)
        
        async with get_db() as db:
            service = DirectMessageService(db, user_id)
            success = await service.mark_conversation_read(conversation_id)
            
            if not success:
                return Response("Conversation not found", status_code=404)
            
            return Response("Conversation marked as read", status_code=200)
    
    @app.get("/social/messages/{conversation_id}/search")
    async def search_messages(request, conversation_id: int, q: str = ""):
        """Search messages in conversation"""
        user_id = get_current_user_id(request)
        
        if not q.strip():
            return Response("Query required", status_code=400)
        
        async with get_db() as db:
            service = DirectMessageService(db, user_id)
            messages = await service.search_messages(conversation_id, q.strip(), limit=20)
            
            return render_message_list(messages, user_id)
    
    return True


# Rendering functions
def render_conversation_list(conversations, current_user_id):
    """Render conversations list"""
    return Div(
        H1("Messages", cls="text-2xl font-bold mb-6"),
        
        # New conversation button
        Div(
            Button(
                "New Message",
                cls="btn btn-primary mb-4",
                onclick="openNewMessageModal()"
            ),
            cls="mb-4"
        ),
        
        # Conversations list
        Div(
            *[render_conversation_item(conv, current_user_id) for conv in conversations],
            cls="space-y-2"
        ) if conversations else P("No conversations yet", cls="text-gray-500"),
        
        cls="max-w-2xl mx-auto p-4"
    )


def render_conversation_item(conversation, current_user_id):
    """Render single conversation item"""
    last_msg = conversation.get("last_message")
    peer_id = conversation.get("peer_id")
    unread_count = conversation.get("unread_count", 0)
    
    return A(
        Div(
            Div(
                Div(
                    B(f"User {peer_id}"),
                    Span(" • "),
                    Span(conversation["updated_at"].strftime("%b %d, %Y"), 
                          cls="text-gray-500 text-sm")
                ),
                Span(
                    f"{unread_count} unread" if unread_count > 0 else "",
                    cls="text-xs px-2 py-1 rounded bg-red-100 text-red-800"
                ) if unread_count > 0 else None,
                cls="flex justify-between items-center"
            ),
            P(
                last_msg.content[:50] + "..." if last_msg and last_msg.content and len(last_msg.content) > 50 
                else (last_msg.content or "Media message") if last_msg else "No messages",
                cls="text-gray-600 text-sm mt-1"
            ),
            cls="p-3 border rounded-lg hover:bg-gray-50"
        ),
        href=f"/social/messages/{conversation['id']}",
        cls="block"
    )


def render_conversation_detail(conversation, messages, current_user_id):
    """Render conversation detail view"""
    peer_id = conversation.get("peer_id")
    
    return Div(
        # Header
        Div(
            Div(
                H3(f"User {peer_id}", cls="font-bold"),
                A("← Back to Messages", href="/social/messages", cls="text-blue-600")
            ),
            cls="flex justify-between items-center mb-4 p-4 border-b"
        ),
        
        # Messages
        Div(
            *[render_message_card(msg, current_user_id) for msg in messages],
            cls="flex-1 overflow-y-auto p-4 space-y-3",
            style="min-height: 400px; max-height: 600px;"
        ),
        
        # Message input
        Div(
            Form(
                Div(
                    Input(
                        type="text",
                        name="content",
                        placeholder="Type a message...",
                        cls="flex-1 px-3 py-2 border rounded-l-lg",
                        required=True
                    ),
                    Button(
                        "Send",
                        type="submit",
                        cls="btn btn-primary rounded-r-l-none"
                    ),
                    cls="flex"
                ),
                hx_post=f"/social/messages/{conversation['id']}/send",
                hx_target="#message-list",
                hx_swap="beforeend"
            ),
            id="message-list",
            cls="border-t p-4"
        ),
        
        cls="max-w-2xl mx-auto border rounded-lg"
    )


def render_message_card(message, current_user_id):
    """Render individual message"""
    is_own = message.sender_id == current_user_id
    
    return Div(
        Div(
            Div(
                Strong("You" if is_own else f"User {message.sender_id}"),
                Span(" • "),
                Span(message.created_at.strftime("%H:%M"), cls="text-gray-500 text-xs")
            ),
            P(message.content or "Media message", cls="mt-1"),
            cls="text-sm"
        ),
        cls=(
            "flex justify-end" if is_own else "flex justify-start"
        )
    )


def render_message_list(messages, current_user_id):
    """Render list of messages"""
    return Div(
        *[render_message_card(msg, current_user_id) for msg in messages],
        cls="space-y-2"
    )
