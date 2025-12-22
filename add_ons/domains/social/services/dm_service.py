"""
Direct Message Service - Adapted for FastHTML
Handles private conversations and direct messaging
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func

from add_ons.domains.social.models import Conversation, DirectMessage
from core.utils.logger import get_logger

logger = get_logger(__name__)


class DirectMessageService:
    """Direct messaging service"""
    
    def __init__(self, db: AsyncSession, current_user_id: int):
        self.db = db
        self.user_id = current_user_id

    async def get_or_create_conversation(self, peer_id: int) -> Conversation:
        """Get existing conversation or create new one"""
        if peer_id == self.user_id:
            raise ValueError("Cannot start conversation with yourself")
        
        # Sort user IDs to ensure consistent conversation identification
        user_a, user_b = sorted([self.user_id, peer_id])
        
        # Look for existing conversation
        stmt = select(Conversation).where(
            and_(Conversation.user_a == user_a, Conversation.user_b == user_b)
        )
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        if conversation:
            return conversation
        
        # Create new conversation
        conversation = Conversation(user_a=user_a, user_b=user_b)
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        
        logger.info(f"User {self.user_id} started conversation with user {peer_id}")
        return conversation

    async def send_message(self, conversation_id: int, content: Optional[str] = None, 
                          media_url: Optional[str] = None) -> Optional[DirectMessage]:
        """Send a message in a conversation"""
        # Verify user is part of conversation
        conv_stmt = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                or_(Conversation.user_a == self.user_id, Conversation.user_b == self.user_id)
            )
        )
        conv_result = await self.db.execute(conv_stmt)
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            return None
        
        if not content and not media_url:
            raise ValueError("Message must have content or media")
        
        # Create message
        message = DirectMessage(
            conversation_id=conversation_id,
            sender_id=self.user_id,
            content=content,
            media_url=media_url
        )
        self.db.add(message)
        
        # Update conversation timestamp
        conversation.updated_at = message.created_at
        
        await self.db.commit()
        await self.db.refresh(message)
        
        logger.info(f"User {self.user_id} sent message in conversation {conversation_id}")
        return message

    async def get_messages(self, conversation_id: int, limit: int = 50, 
                          offset: int = 0) -> List[DirectMessage]:
        """Get messages from conversation"""
        # Verify user is part of conversation
        conv_stmt = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                or_(Conversation.user_a == self.user_id, Conversation.user_b == self.user_id)
            )
        )
        conv_result = await self.db.execute(conv_stmt)
        if not conv_result.scalar_one_or_none():
            return []
        
        # Get messages
        stmt = (
            select(DirectMessage)
            .where(DirectMessage.conversation_id == conversation_id)
            .order_by(desc(DirectMessage.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        messages = result.scalars().all()
        
        # Return in chronological order (oldest first)
        return list(reversed(messages))

    async def get_conversations(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's conversations with last message info"""
        stmt = (
            select(Conversation)
            .where(
                or_(Conversation.user_a == self.user_id, Conversation.user_b == self.user_id)
            )
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        conversations = result.scalars().all()
        
        conversation_data = []
        for conv in conversations:
            # Get other participant
            peer_id = conv.user_b if conv.user_a == self.user_id else conv.user_a
            
            # Get last message
            last_msg_stmt = (
                select(DirectMessage)
                .where(DirectMessage.conversation_id == conv.id)
                .order_by(desc(DirectMessage.created_at))
                .limit(1)
            )
            last_msg_result = await self.db.execute(last_msg_stmt)
            last_message = last_msg_result.scalar_one_or_none()
            
            # Get unread count
            unread_stmt = select(func.count(DirectMessage.id)).where(
                and_(
                    DirectMessage.conversation_id == conv.id,
                    DirectMessage.sender_id != self.user_id,
                    # Note: You would add read status tracking here in a real implementation
                )
            )
            unread_result = await self.db.execute(unread_stmt)
            unread_count = unread_result.scalar() or 0
            
            conversation_data.append({
                "id": conv.id,
                "peer_id": peer_id,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "last_message": last_message,
                "unread_count": unread_count
            })
        
        return conversation_data

    async def delete_message(self, message_id: int) -> bool:
        """Delete a message (only by sender)"""
        stmt = select(DirectMessage).where(
            and_(DirectMessage.id == message_id, DirectMessage.sender_id == self.user_id)
        )
        result = await self.db.execute(stmt)
        message = result.scalar_one_or_none()
        
        if not message:
            return False
        
        await self.db.delete(message)
        await self.db.commit()
        
        logger.info(f"User {self.user_id} deleted message {message_id}")
        return True

    async def edit_message(self, message_id: int, content: str) -> Optional[DirectMessage]:
        """Edit a message (only by sender, only text messages)"""
        stmt = select(DirectMessage).where(
            and_(
                DirectMessage.id == message_id, 
                DirectMessage.sender_id == self.user_id,
                DirectMessage.media_url.is_(None)  # Can only edit text messages
            )
        )
        result = await self.db.execute(stmt)
        message = result.scalar_one_or_none()
        
        if not message:
            return None
        
        message.content = content
        await self.db.commit()
        await self.db.refresh(message)
        
        logger.info(f"User {self.user_id} edited message {message_id}")
        return message

    async def mark_conversation_read(self, conversation_id: int) -> bool:
        """Mark all messages in conversation as read"""
        # Verify user is part of conversation
        conv_stmt = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                or_(Conversation.user_a == self.user_id, Conversation.user_b == self.user_id)
            )
        )
        conv_result = await self.db.execute(conv_stmt)
        if not conv_result.scalar_one_or_none():
            return False
        
        # Note: In a real implementation, you would add a read_at timestamp
        # to messages and update them here. For now, this is a placeholder.
        
        logger.info(f"User {self.user_id} marked conversation {conversation_id} as read")
        return True

    async def get_message_count(self, conversation_id: int) -> int:
        """Get total message count for conversation"""
        # Verify user is part of conversation
        conv_stmt = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                or_(Conversation.user_a == self.user_id, Conversation.user_b == self.user_id)
            )
        )
        conv_result = await self.db.execute(conv_stmt)
        if not conv_result.scalar_one_or_none():
            return 0
        
        stmt = select(func.count(DirectMessage.id)).where(
            DirectMessage.conversation_id == conversation_id
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def search_messages(self, conversation_id: int, query: str, 
                             limit: int = 20) -> List[DirectMessage]:
        """Search messages in conversation"""
        # Verify user is part of conversation
        conv_stmt = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                or_(Conversation.user_a == self.user_id, Conversation.user_b == self.user_id)
            )
        )
        conv_result = await self.db.execute(conv_stmt)
        if not conv_result.scalar_one_or_none():
            return []
        
        # Search in content (case-insensitive)
        stmt = (
            select(DirectMessage)
            .where(
                and_(
                    DirectMessage.conversation_id == conversation_id,
                    DirectMessage.content.ilike(f"%{query}%")
                )
            )
            .order_by(desc(DirectMessage.created_at))
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def block_user(self, peer_id: int) -> bool:
        """Block a user (placeholder for future implementation)"""
        # In a real implementation, you would add a blocked_users table
        # and prevent messaging between blocked users
        logger.info(f"User {self.user_id} blocked user {peer_id}")
        return True

    async def unblock_user(self, peer_id: int) -> bool:
        """Unblock a user (placeholder for future implementation)"""
        # In a real implementation, you would remove the block from blocked_users table
        logger.info(f"User {self.user_id} unblocked user {peer_id}")
        return True

    async def is_user_blocked(self, peer_id: int) -> bool:
        """Check if user is blocked (placeholder for future implementation)"""
        # In a real implementation, you would check the blocked_users table
        return False
