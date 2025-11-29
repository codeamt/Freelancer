"""Enrollment schemas for LMS add-on"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class EnrollmentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    EXPIRED = "expired"


class EnrollmentCreate(BaseModel):
    """Schema for creating a new enrollment"""
    course_id: int
    payment_id: Optional[str] = None


class EnrollmentUpdate(BaseModel):
    """Schema for updating an enrollment"""
    status: Optional[EnrollmentStatus] = None
    expires_at: Optional[datetime] = None


class EnrollmentResponse(BaseModel):
    """Schema for enrollment response"""
    id: int
    user_id: int
    course_id: int
    status: EnrollmentStatus
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    payment_id: Optional[str] = None
    progress_percent: Optional[float] = 0.0
    
    class Config:
        from_attributes = True


class EnrollmentWithCourse(EnrollmentResponse):
    """Schema for enrollment with course details"""
    course_title: str
    course_thumbnail: Optional[str] = None
    instructor_name: str
