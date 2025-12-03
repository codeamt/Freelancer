"""Lesson schemas for LMS add-on"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class LessonType(str, Enum):
    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"


class LessonBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    order: int = Field(..., ge=1)
    lesson_type: LessonType = LessonType.VIDEO
    is_preview: bool = False
    resources: Optional[List[Dict[str, Any]]] = None


class LessonCreate(LessonBase):
    """Schema for creating a new lesson"""
    course_id: int


class LessonUpdate(BaseModel):
    """Schema for updating a lesson (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    order: Optional[int] = Field(None, ge=1)
    lesson_type: Optional[LessonType] = None
    is_preview: Optional[bool] = None
    resources: Optional[List[Dict[str, Any]]] = None


class LessonResponse(LessonBase):
    """Schema for lesson response"""
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime
    is_completed: Optional[bool] = False
    
    class Config:
        from_attributes = True


class LessonListResponse(BaseModel):
    """Schema for lesson list"""
    lessons: List[LessonResponse]
    total: int
