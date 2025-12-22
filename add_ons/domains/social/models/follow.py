"""
Social Follow Model
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, UniqueConstraint, Index
from core.db.base import Base


class Follow(Base):
    """Social follow relationship model"""
    __tablename__ = "social_follows"

    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, nullable=False, index=True)
    followee_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        UniqueConstraint("follower_id", "followee_id", name="uq_follow_pair"),
        Index("idx_follow_relationship", "follower_id", "followee_id"),
    )

    def __repr__(self):
        return f"<Follow(follower_id={self.follower_id}, followee_id={self.followee_id})>"
