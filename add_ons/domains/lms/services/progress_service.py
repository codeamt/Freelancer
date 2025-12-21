"""Progress tracking service for LMS add-on"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime
from add_ons.domains.lms.models.sql.progress import Progress
from add_ons.domains.lms.models.sql.enrollment import Enrollment
from add_ons.domains.lms.models.sql.lesson import Lesson
from add_ons.domains.lms.models.sql.course import Course
from add_ons.domains.lms.schemas import EnrollmentStatus


class ProgressService:
    """Service for tracking student progress"""
    
    @staticmethod
    async def get_progress(
        db: AsyncSession,
        enrollment_id: int
    ) -> Optional[Progress]:
        """Get progress for an enrollment"""
        query = select(Progress).where(Progress.enrollment_id == enrollment_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def mark_lesson_complete(
        db: AsyncSession,
        enrollment_id: int,
        lesson_id: int,
        time_spent_minutes: int = 0
    ) -> Optional[Progress]:
        """Mark a lesson as completed and update progress"""
        # Get or create progress
        progress = await ProgressService.get_progress(db, enrollment_id)
        
        if not progress:
            progress = Progress(
                enrollment_id=enrollment_id,
                completed_lessons=[],
                progress_percent=0.0,
                time_spent_minutes=0
            )
            db.add(progress)
            await db.flush()
        
        # Add lesson to completed if not already there
        if lesson_id not in progress.completed_lessons:
            progress.completed_lessons.append(lesson_id)
        
        # Update time spent
        progress.time_spent_minutes += time_spent_minutes
        progress.last_lesson_id = lesson_id
        progress.last_accessed = datetime.utcnow()
        
        # Calculate progress percentage
        enrollment_query = select(Enrollment).where(Enrollment.id == enrollment_id)
        enrollment_result = await db.execute(enrollment_query)
        enrollment = enrollment_result.scalar_one_or_none()
        
        if enrollment:
            # Get total lessons in course
            lesson_count_query = select(func.count(Lesson.id)).where(
                Lesson.course_id == enrollment.course_id
            )
            lesson_count_result = await db.execute(lesson_count_query)
            total_lessons = lesson_count_result.scalar()
            
            if total_lessons > 0:
                progress.progress_percent = (len(progress.completed_lessons) / total_lessons) * 100
                
                # Check if course is completed
                if progress.progress_percent >= 100:
                    enrollment.status = EnrollmentStatus.COMPLETED
                    enrollment.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(progress)
        return progress
    
    @staticmethod
    async def update_time_spent(
        db: AsyncSession,
        enrollment_id: int,
        lesson_id: int,
        time_spent_minutes: int
    ) -> Optional[Progress]:
        """Update time spent on a lesson without marking as complete"""
        progress = await ProgressService.get_progress(db, enrollment_id)
        
        if not progress:
            return None
        
        progress.time_spent_minutes += time_spent_minutes
        progress.last_lesson_id = lesson_id
        progress.last_accessed = datetime.utcnow()
        
        await db.commit()
        await db.refresh(progress)
        return progress
    
    @staticmethod
    async def reset_progress(
        db: AsyncSession,
        enrollment_id: int
    ) -> Optional[Progress]:
        """Reset progress for an enrollment"""
        progress = await ProgressService.get_progress(db, enrollment_id)
        
        if not progress:
            return None
        
        progress.completed_lessons = []
        progress.progress_percent = 0.0
        progress.last_lesson_id = None
        progress.time_spent_minutes = 0
        progress.last_accessed = datetime.utcnow()
        
        await db.commit()
        await db.refresh(progress)
        return progress
    
    @staticmethod
    async def get_course_progress_detail(
        db: AsyncSession,
        user_id: int,
        course_id: int
    ) -> Optional[dict]:
        """Get detailed progress information for a course"""
        # Get enrollment
        enrollment_query = select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id
        )
        enrollment_result = await db.execute(enrollment_query)
        enrollment = enrollment_result.scalar_one_or_none()
        
        if not enrollment:
            return None
        
        # Get progress
        progress = await ProgressService.get_progress(db, enrollment.id)
        
        if not progress:
            return None
        
        # Get course info
        course_query = select(Course).where(Course.id == course_id)
        course_result = await db.execute(course_query)
        course = course_result.scalar_one_or_none()
        
        # Get total lessons
        lesson_count_query = select(func.count(Lesson.id)).where(
            Lesson.course_id == course_id
        )
        lesson_count_result = await db.execute(lesson_count_query)
        total_lessons = lesson_count_result.scalar()
        
        # Get next lesson
        next_lesson = None
        if progress.last_lesson_id:
            last_lesson_query = select(Lesson).where(Lesson.id == progress.last_lesson_id)
            last_lesson_result = await db.execute(last_lesson_query)
            last_lesson = last_lesson_result.scalar_one_or_none()
            
            if last_lesson:
                next_lesson_query = select(Lesson).where(
                    Lesson.course_id == course_id,
                    Lesson.order > last_lesson.order
                ).order_by(Lesson.order).limit(1)
                next_lesson_result = await db.execute(next_lesson_query)
                next_lesson = next_lesson_result.scalar_one_or_none()
        else:
            # Get first lesson
            first_lesson_query = select(Lesson).where(
                Lesson.course_id == course_id
            ).order_by(Lesson.order).limit(1)
            first_lesson_result = await db.execute(first_lesson_query)
            next_lesson = first_lesson_result.scalar_one_or_none()
        
        return {
            "course_id": course_id,
            "course_title": course.title if course else "",
            "enrollment_id": enrollment.id,
            "progress_percent": progress.progress_percent,
            "completed_lessons": progress.completed_lessons,
            "total_lessons": total_lessons,
            "time_spent_minutes": progress.time_spent_minutes,
            "last_accessed": progress.last_accessed,
            "next_lesson_id": next_lesson.id if next_lesson else None
        }
