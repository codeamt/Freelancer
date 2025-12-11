"""LMS Progress Model"""

from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from core.db.base_class import Base


class Progress(Base):
    """Progress tracking model for LMS domain"""
    
    __tablename__ = "progress"
    
    id = Column(Integer, primary_key=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, unique=True)
    completed_lessons = Column(JSONB, default=list)
    progress_percent = Column(Float, default=0.0)
    last_lesson_id = Column(Integer, ForeignKey("lessons.id"))
    time_spent_minutes = Column(Integer, default=0)
    last_accessed = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="progress")
    last_lesson = relationship("Lesson", foreign_keys=[last_lesson_id])
    
    def __repr__(self):
        return f"<Progress(enrollment_id={self.enrollment_id}, progress={self.progress_percent}%)>"
