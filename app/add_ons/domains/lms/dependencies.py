"""Dependencies for LMS add-on"""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db.base_class import get_session
from app.add_ons.lms.services import EnrollmentService
from typing import Optional


async def get_current_user_id(request: Request) -> int:
    """Get current user ID from session"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


async def verify_course_access(
    course_id: int,
    user_id: int,
    db: AsyncSession
) -> bool:
    """Verify user has access to a course"""
    has_access = await EnrollmentService.check_enrollment_access(
        db, user_id, course_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="You must be enrolled in this course to access it"
        )
    
    return True


async def verify_instructor(
    course_id: int,
    user_id: int,
    db: AsyncSession
) -> bool:
    """Verify user is the instructor of a course"""
    from app.add_ons.lms.services import CourseService
    
    course = await CourseService.get_course(db, course_id)
    
    if not course or course.instructor_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You must be the instructor of this course"
        )
    
    return True
