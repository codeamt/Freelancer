"""Lesson service for LMS add-on"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from app.add_ons.domains.lms.models.sql.lesson import Lesson
from app.add_ons.domains.lms.models.sql.course import Course
from app.add_ons.domains.lms.schemas import LessonCreate, LessonUpdate


class LessonService:
    """Service for managing lessons"""
    
    @staticmethod
    async def create_lesson(
        db: AsyncSession,
        lesson_data: LessonCreate,
        instructor_id: int
    ) -> Optional[Lesson]:
        """Create a new lesson (only by course instructor)"""
        # Verify instructor owns the course
        course_query = select(Course).where(Course.id == lesson_data.course_id)
        course_result = await db.execute(course_query)
        course = course_result.scalar_one_or_none()
        
        if not course or course.instructor_id != instructor_id:
            return None
        
        lesson = Lesson(**lesson_data.model_dump())
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)
        return lesson
    
    @staticmethod
    async def get_lesson(
        db: AsyncSession,
        lesson_id: int
    ) -> Optional[Lesson]:
        """Get a lesson by ID"""
        query = select(Lesson).where(Lesson.id == lesson_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_course_lessons(
        db: AsyncSession,
        course_id: int,
        include_non_preview: bool = True
    ) -> List[Lesson]:
        """Get all lessons for a course, ordered by order field"""
        query = select(Lesson).where(Lesson.course_id == course_id)
        
        if not include_non_preview:
            query = query.where(Lesson.is_preview == True)
        
        query = query.order_by(Lesson.order)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_lesson(
        db: AsyncSession,
        lesson_id: int,
        lesson_data: LessonUpdate,
        instructor_id: int
    ) -> Optional[Lesson]:
        """Update a lesson (only by course instructor)"""
        lesson = await LessonService.get_lesson(db, lesson_id)
        
        if not lesson:
            return None
        
        # Verify instructor owns the course
        course_query = select(Course).where(Course.id == lesson.course_id)
        course_result = await db.execute(course_query)
        course = course_result.scalar_one_or_none()
        
        if not course or course.instructor_id != instructor_id:
            return None
        
        # Update only provided fields
        update_data = lesson_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lesson, field, value)
        
        await db.commit()
        await db.refresh(lesson)
        return lesson
    
    @staticmethod
    async def delete_lesson(
        db: AsyncSession,
        lesson_id: int,
        instructor_id: int
    ) -> bool:
        """Delete a lesson (only by course instructor)"""
        lesson = await LessonService.get_lesson(db, lesson_id)
        
        if not lesson:
            return False
        
        # Verify instructor owns the course
        course_query = select(Course).where(Course.id == lesson.course_id)
        course_result = await db.execute(course_query)
        course = course_result.scalar_one_or_none()
        
        if not course or course.instructor_id != instructor_id:
            return False
        
        await db.delete(lesson)
        await db.commit()
        return True
    
    @staticmethod
    async def reorder_lessons(
        db: AsyncSession,
        course_id: int,
        lesson_orders: dict[int, int],
        instructor_id: int
    ) -> bool:
        """Reorder lessons in a course"""
        # Verify instructor owns the course
        course_query = select(Course).where(Course.id == course_id)
        course_result = await db.execute(course_query)
        course = course_result.scalar_one_or_none()
        
        if not course or course.instructor_id != instructor_id:
            return False
        
        # Update lesson orders
        for lesson_id, new_order in lesson_orders.items():
            lesson = await LessonService.get_lesson(db, lesson_id)
            if lesson and lesson.course_id == course_id:
                lesson.order = new_order
        
        await db.commit()
        return True
    
    @staticmethod
    async def get_next_lesson(
        db: AsyncSession,
        course_id: int,
        current_lesson_id: int
    ) -> Optional[Lesson]:
        """Get the next lesson in the course"""
        current_lesson = await LessonService.get_lesson(db, current_lesson_id)
        
        if not current_lesson:
            return None
        
        query = select(Lesson).where(
            and_(
                Lesson.course_id == course_id,
                Lesson.order > current_lesson.order
            )
        ).order_by(Lesson.order).limit(1)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_previous_lesson(
        db: AsyncSession,
        course_id: int,
        current_lesson_id: int
    ) -> Optional[Lesson]:
        """Get the previous lesson in the course"""
        current_lesson = await LessonService.get_lesson(db, current_lesson_id)
        
        if not current_lesson:
            return None
        
        query = select(Lesson).where(
            and_(
                Lesson.course_id == course_id,
                Lesson.order < current_lesson.order
            )
        ).order_by(Lesson.order.desc()).limit(1)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
