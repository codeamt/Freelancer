"""LMS Assessment Models"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from core.db.base_class import Base
import enum


class AssessmentType(enum.Enum):
    QUIZ = "quiz"
    EXAM = "exam"
    ASSIGNMENT = "assignment"


class Assessment(Base):
    """Assessment model for LMS domain"""
    
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    assessment_type = Column(Enum(AssessmentType), default=AssessmentType.QUIZ)
    questions = Column(JSONB)
    passing_score = Column(Float, default=70.0)
    time_limit_minutes = Column(Integer)
    max_attempts = Column(Integer, default=3)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="assessments")
    submissions = relationship("AssessmentSubmission", back_populates="assessment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Assessment(id={self.id}, title={self.title}, type={self.assessment_type})>"


class AssessmentSubmission(Base):
    """Assessment submission model for LMS domain"""
    
    __tablename__ = "assessment_submissions"
    
    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    answers = Column(JSONB)
    score = Column(Float)
    passed = Column(Boolean, default=False)
    attempt_number = Column(Integer, default=1)
    submitted_at = Column(DateTime, server_default=func.now())
    graded_at = Column(DateTime)
    feedback = Column(Text)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="submissions")
    user = relationship("User")
    
    def __repr__(self):
        return f"<AssessmentSubmission(id={self.id}, user_id={self.user_id}, score={self.score}, passed={self.passed})>"
