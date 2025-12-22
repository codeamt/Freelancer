"""
Social Direct Message Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Text, UniqueConstraint, Index, ForeignKey
from sqlalchemy.orm import relationship
from core.db.base import Base


class Conversation(Base):
    """Social conversation model"""
    __tablename__ = "social_conversations"

    id = Column(Integer, primary_key=True)
    user_a = Column(Integer, nullable=False, index=True)
    user_b = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("DirectMessage", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_a", "user_b", name="uq_conversation_pair"),
        Index("idx_conversation_users", "user_a", "user_b"),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, user_a={self.user_a}, user_b={self.user_b})>"


class DirectMessage(Base):
    """Social direct message model"""
    __tablename__ = "social_direct_messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("social_conversations.id"), nullable=False, index=True)
    sender_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=True)
    media_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<DirectMessage(id={self.id}, conversation_id={self.conversation_id}, sender_id={self.sender_id})>"
