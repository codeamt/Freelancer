"""LMS Course Model"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from core.db.base_class import Base
import enum


class CourseStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CourseDifficulty(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Course(Base):
    """Course model for LMS domain"""
    
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    thumbnail_url = Column(String)
    price = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    duration_hours = Column(Float)
    difficulty = Column(Enum(CourseDifficulty), default=CourseDifficulty.BEGINNER)
    status = Column(Enum(CourseStatus), default=CourseStatus.DRAFT)
    category = Column(String)
    tags = Column(JSONB)
    requirements = Column(JSONB)
    learning_objectives = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    instructor = relationship("User", foreign_keys=[instructor_id])
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="course", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Course(id={self.id}, title={self.title}, status={self.status})>"
