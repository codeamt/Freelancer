"""Progress schemas for LMS add-on"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ProgressUpdate(BaseModel):
    """Schema for updating progress"""
    lesson_id: int
    time_spent_minutes: Optional[int] = Field(None, ge=0)


class ProgressResponse(BaseModel):
    """Schema for progress response"""
    id: int
    enrollment_id: int
    completed_lessons: List[int]
    progress_percent: float
    last_lesson_id: Optional[int] = None
    time_spent_minutes: int
    last_accessed: datetime
    
    class Config:
        from_attributes = True


class CourseProgressDetail(BaseModel):
    """Detailed progress for a course"""
    course_id: int
    course_title: str
    enrollment_id: int
    progress_percent: float
    completed_lessons: List[int]
    total_lessons: int
    time_spent_minutes: int
    last_accessed: datetime
    next_lesson_id: Optional[int] = None
