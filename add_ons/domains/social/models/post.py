"""
Social Post Model
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from core.db.base import Base


class Post(Base):
    """Social post model"""
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=True)
    media_url = Column(String(1024), nullable=True)  # S3 or YouTube
    is_public = Column(Boolean, default=False)  # default private; visible to followers/mutuals only
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post(id={self.id}, user_id={self.user_id}, public={self.is_public})>"
