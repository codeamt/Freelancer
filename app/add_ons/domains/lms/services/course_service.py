"""Course service for LMS add-on"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional, TYPE_CHECKING
import math

from app.add_ons.domains.lms.models.sql.course import Course
from app.add_ons.domains.lms.models.sql.lesson import Lesson
from app.add_ons.domains.lms.models.sql.enrollment import Enrollment
from core.db.models import User
from app.add_ons.domains.lms.schemas import CourseCreate, CourseUpdate, CourseStatus


class CourseService:
    """Service for managing courses"""
    
    @staticmethod
    async def create_course(
        db: AsyncSession,
        course_data: CourseCreate,
        instructor_id: int
    ) -> Course:
        """Create a new course"""
        course = Course(
            **course_data.model_dump(),
            instructor_id=instructor_id
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course
    
    @staticmethod
    async def get_course(
        db: AsyncSession,
        course_id: int,
        include_instructor: bool = False
    ) -> Optional[Course]:
        """Get a course by ID"""
        query = select(Course).where(Course.id == course_id)
        
        if include_instructor:
            query = query.options(selectinload(Course.instructor))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_courses(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status: Optional[CourseStatus] = None,
        category: Optional[str] = None,
        instructor_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> tuple[List[Course], int]:
        """Get paginated list of courses with filters"""
        query = select(Course)
        count_query = select(func.count(Course.id))
        
        # Apply filters
        filters = []
        if status:
            filters.append(Course.status == status)
        if category:
            filters.append(Course.category == category)
        if instructor_id:
            filters.append(Course.instructor_id == instructor_id)
        if search:
            filters.append(Course.title.ilike(f"%{search}%"))
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        query = query.options(selectinload(Course.instructor))
        
        result = await db.execute(query)
        courses = result.scalars().all()
        
        return list(courses), total
    
    @staticmethod
    async def update_course(
        db: AsyncSession,
        course_id: int,
        course_data: CourseUpdate,
        instructor_id: int
    ) -> Optional[Course]:
        """Update a course (only by instructor)"""
        course = await CourseService.get_course(db, course_id)
        
        if not course or course.instructor_id != instructor_id:
            return None
        
        # Update only provided fields
        update_data = course_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(course, field, value)
        
        await db.commit()
        await db.refresh(course)
        return course
    
    @staticmethod
    async def delete_course(
        db: AsyncSession,
        course_id: int,
        instructor_id: int
    ) -> bool:
        """Delete a course (only by instructor)"""
        course = await CourseService.get_course(db, course_id)
        
        if not course or course.instructor_id != instructor_id:
            return False
        
        await db.delete(course)
        await db.commit()
        return True
    
    @staticmethod
    async def get_course_stats(
        db: AsyncSession,
        course_id: int
    ) -> dict:
        """Get statistics for a course"""
        # Get lesson count
        lesson_count_query = select(func.count(Lesson.id)).where(Lesson.course_id == course_id)
        lesson_result = await db.execute(lesson_count_query)
        lesson_count = lesson_result.scalar()
        
        # Get enrollment count
        enrollment_count_query = select(func.count(Enrollment.id)).where(
            Enrollment.course_id == course_id
        )
        enrollment_result = await db.execute(enrollment_count_query)
        enrollment_count = enrollment_result.scalar()
        
        # Get completion rate
        completed_count_query = select(func.count(Enrollment.id)).where(
            and_(
                Enrollment.course_id == course_id,
                Enrollment.status == "completed"
            )
        )
        completed_result = await db.execute(completed_count_query)
        completed_count = completed_result.scalar()
        
        completion_rate = (completed_count / enrollment_count * 100) if enrollment_count > 0 else 0
        
        return {
            "lesson_count": lesson_count,
            "enrollment_count": enrollment_count,
            "completed_count": completed_count,
            "completion_rate": round(completion_rate, 2)
        }
    
    @staticmethod
    async def publish_course(
        db: AsyncSession,
        course_id: int,
        instructor_id: int
    ) -> Optional[Course]:
        """Publish a course"""
        course = await CourseService.get_course(db, course_id)
        
        if not course or course.instructor_id != instructor_id:
            return None
        
        course.status = CourseStatus.PUBLISHED
        await db.commit()
        await db.refresh(course)
        return course
    
    @staticmethod
    async def archive_course(
        db: AsyncSession,
        course_id: int,
        instructor_id: int
    ) -> Optional[Course]:
        """Archive a course"""
        course = await CourseService.get_course(db, course_id)
        
        if not course or course.instructor_id != instructor_id:
            return None
        
        course.status = CourseStatus.ARCHIVED
        await db.commit()
        await db.refresh(course)
        return course
