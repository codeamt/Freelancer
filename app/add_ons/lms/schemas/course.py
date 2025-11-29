"""Course schemas for LMS add-on"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CourseStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CourseDifficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    price: float = Field(default=0.0, ge=0)
    currency: str = Field(default="USD", max_length=3)
    duration_hours: Optional[float] = Field(None, ge=0)
    difficulty: CourseDifficulty = CourseDifficulty.BEGINNER
    status: CourseStatus = CourseStatus.DRAFT
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    requirements: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None


class CourseCreate(CourseBase):
    """Schema for creating a new course"""
    pass


class CourseUpdate(BaseModel):
    """Schema for updating a course (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    duration_hours: Optional[float] = Field(None, ge=0)
    difficulty: Optional[CourseDifficulty] = None
    status: Optional[CourseStatus] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    requirements: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None


class CourseInstructor(BaseModel):
    """Instructor information for course"""
    id: int
    email: str
    
    class Config:
        from_attributes = True


class CourseResponse(CourseBase):
    """Schema for course response"""
    id: int
    instructor_id: int
    instructor: Optional[CourseInstructor] = None
    created_at: datetime
    updated_at: datetime
    lesson_count: Optional[int] = 0
    enrollment_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class CourseListResponse(BaseModel):
    """Schema for paginated course list"""
    courses: List[CourseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
