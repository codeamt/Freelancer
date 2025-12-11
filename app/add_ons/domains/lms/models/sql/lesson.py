"""LMS Lesson Model"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from core.db.base_class import Base
import enum


class LessonType(enum.Enum):
    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"


class Lesson(Base):
    """Lesson model for LMS domain"""
    
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    content = Column(Text)
    video_url = Column(String)
    duration_minutes = Column(Integer)
    order = Column(Integer, nullable=False)
    lesson_type = Column(Enum(LessonType), default=LessonType.VIDEO)
    is_preview = Column(Boolean, default=False)
    resources = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="lessons")
    
    def __repr__(self):
        return f"<Lesson(id={self.id}, title={self.title}, type={self.lesson_type})>"
