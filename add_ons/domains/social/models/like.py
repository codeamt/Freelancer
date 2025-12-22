"""
Social Like Model
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, UniqueConstraint, Index, ForeignKey
from sqlalchemy.orm import relationship
from core.db.base import Base


class Like(Base):
    """Social like model"""
    __tablename__ = "social_likes"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("social_posts.id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    post = relationship("Post", back_populates="likes")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_like_post_user"),
        Index("idx_like_post_user", "post_id", "user_id"),
    )

    def __repr__(self):
        return f"<Like(post_id={self.post_id}, user_id={self.user_id})>"
