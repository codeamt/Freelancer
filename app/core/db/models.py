from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from .base_class import Base
import enum

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, server_default=func.now())

    media = relationship("Media", back_populates="user")

class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    url = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="media")

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True)
    name = Column(String)
    price = Column(Float)
    currency = Column(String(3), default="USD")

class CourseStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class CourseDifficulty(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class Course(Base):
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

class LessonType(enum.Enum):
    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"

class Lesson(Base):
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

class EnrollmentStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    EXPIRED = "expired"

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE)
    enrolled_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)
    payment_id = Column(String)
    
    # Relationships
    user = relationship("User")
    course = relationship("Course", back_populates="enrollments")
    progress = relationship("Progress", back_populates="enrollment", uselist=False, cascade="all, delete-orphan")

class Progress(Base):
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

class AssessmentType(enum.Enum):
    QUIZ = "quiz"
    EXAM = "exam"
    ASSIGNMENT = "assignment"

class Assessment(Base):
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

class AssessmentSubmission(Base):
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

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    certificate_url = Column(String)
    issued_at = Column(DateTime, server_default=func.now())
    verification_code = Column(String, unique=True)
    
    # Relationships
    user = relationship("User")
    course = relationship("Course")

class Post(Base):
    __tablename__ = "posts"
    id = Column(String, primary_key=True)
    content = Column(Text)
    like_count = Column(Integer, default=0)