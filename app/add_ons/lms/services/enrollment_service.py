"""Enrollment service for LMS add-on"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from app.core.db.models import Enrollment, Course, Progress, User
from app.add_ons.lms.schemas import EnrollmentCreate, EnrollmentStatus


class EnrollmentService:
    """Service for managing course enrollments"""
    
    @staticmethod
    async def enroll_user(
        db: AsyncSession,
        user_id: int,
        enrollment_data: EnrollmentCreate
    ) -> Optional[Enrollment]:
        """Enroll a user in a course"""
        # Check if already enrolled
        existing = await EnrollmentService.get_enrollment(
            db, user_id, enrollment_data.course_id
        )
        
        if existing:
            return None  # Already enrolled
        
        # Verify course exists
        course_query = select(Course).where(Course.id == enrollment_data.course_id)
        course_result = await db.execute(course_query)
        course = course_result.scalar_one_or_none()
        
        if not course:
            return None
        
        # Create enrollment
        enrollment = Enrollment(
            user_id=user_id,
            course_id=enrollment_data.course_id,
            payment_id=enrollment_data.payment_id,
            status=EnrollmentStatus.ACTIVE
        )
        db.add(enrollment)
        await db.flush()
        
        # Create initial progress record
        progress = Progress(
            enrollment_id=enrollment.id,
            completed_lessons=[],
            progress_percent=0.0,
            time_spent_minutes=0
        )
        db.add(progress)
        
        await db.commit()
        await db.refresh(enrollment)
        return enrollment
    
    @staticmethod
    async def get_enrollment(
        db: AsyncSession,
        user_id: int,
        course_id: int
    ) -> Optional[Enrollment]:
        """Get a specific enrollment"""
        query = select(Enrollment).where(
            and_(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id
            )
        ).options(selectinload(Enrollment.progress))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_enrollment_by_id(
        db: AsyncSession,
        enrollment_id: int
    ) -> Optional[Enrollment]:
        """Get enrollment by ID"""
        query = select(Enrollment).where(Enrollment.id == enrollment_id)
        query = query.options(selectinload(Enrollment.progress))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_enrollments(
        db: AsyncSession,
        user_id: int,
        status: Optional[EnrollmentStatus] = None
    ) -> List[Enrollment]:
        """Get all enrollments for a user"""
        query = select(Enrollment).where(Enrollment.user_id == user_id)
        
        if status:
            query = query.where(Enrollment.status == status)
        
        query = query.options(
            selectinload(Enrollment.course),
            selectinload(Enrollment.progress)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_course_enrollments(
        db: AsyncSession,
        course_id: int,
        status: Optional[EnrollmentStatus] = None
    ) -> List[Enrollment]:
        """Get all enrollments for a course"""
        query = select(Enrollment).where(Enrollment.course_id == course_id)
        
        if status:
            query = query.where(Enrollment.status == status)
        
        query = query.options(
            selectinload(Enrollment.user),
            selectinload(Enrollment.progress)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_enrollment_status(
        db: AsyncSession,
        enrollment_id: int,
        user_id: int,
        status: EnrollmentStatus
    ) -> Optional[Enrollment]:
        """Update enrollment status"""
        enrollment = await EnrollmentService.get_enrollment_by_id(db, enrollment_id)
        
        if not enrollment or enrollment.user_id != user_id:
            return None
        
        enrollment.status = status
        
        if status == EnrollmentStatus.COMPLETED:
            enrollment.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(enrollment)
        return enrollment
    
    @staticmethod
    async def drop_enrollment(
        db: AsyncSession,
        enrollment_id: int,
        user_id: int
    ) -> bool:
        """Drop/cancel an enrollment"""
        enrollment = await EnrollmentService.get_enrollment_by_id(db, enrollment_id)
        
        if not enrollment or enrollment.user_id != user_id:
            return False
        
        enrollment.status = EnrollmentStatus.DROPPED
        await db.commit()
        return True
    
    @staticmethod
    async def check_enrollment_access(
        db: AsyncSession,
        user_id: int,
        course_id: int
    ) -> bool:
        """Check if user has access to a course"""
        enrollment = await EnrollmentService.get_enrollment(db, user_id, course_id)
        
        if not enrollment:
            return False
        
        # Check if enrollment is active and not expired
        if enrollment.status != EnrollmentStatus.ACTIVE:
            return False
        
        if enrollment.expires_at and enrollment.expires_at < datetime.utcnow():
            # Mark as expired
            enrollment.status = EnrollmentStatus.EXPIRED
            await db.commit()
            return False
        
        return True
