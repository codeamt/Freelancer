"""Assessment service for LMS add-on"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.db.models import Assessment, AssessmentSubmission, Course, Enrollment
from app.add_ons.lms.schemas import AssessmentCreate, AssessmentUpdate


class AssessmentService:
    """Service for managing assessments and grading"""
    
    @staticmethod
    async def create_assessment(
        db: AsyncSession,
        assessment_data: AssessmentCreate,
        instructor_id: int
    ) -> Optional[Assessment]:
        """Create a new assessment (only by course instructor)"""
        # Verify instructor owns the course
        course_query = select(Course).where(Course.id == assessment_data.course_id)
        course_result = await db.execute(course_query)
        course = course_result.scalar_one_or_none()
        
        if not course or course.instructor_id != instructor_id:
            return None
        
        assessment = Assessment(
            course_id=assessment_data.course_id,
            title=assessment_data.title,
            description=assessment_data.description,
            assessment_type=assessment_data.assessment_type,
            questions=[q.model_dump() for q in assessment_data.questions],
            passing_score=assessment_data.passing_score,
            time_limit_minutes=assessment_data.time_limit_minutes,
            max_attempts=assessment_data.max_attempts
        )
        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)
        return assessment
    
    @staticmethod
    async def get_assessment(
        db: AsyncSession,
        assessment_id: int,
        include_answers: bool = False
    ) -> Optional[Assessment]:
        """Get an assessment by ID"""
        query = select(Assessment).where(Assessment.id == assessment_id)
        result = await db.execute(query)
        assessment = result.scalar_one_or_none()
        
        if assessment and not include_answers:
            # Remove correct answers from questions for students
            questions = assessment.questions.copy() if assessment.questions else []
            for question in questions:
                question.pop('correct_answer', None)
            assessment.questions = questions
        
        return assessment
    
    @staticmethod
    async def get_course_assessments(
        db: AsyncSession,
        course_id: int
    ) -> List[Assessment]:
        """Get all assessments for a course"""
        query = select(Assessment).where(Assessment.course_id == course_id)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def submit_assessment(
        db: AsyncSession,
        assessment_id: int,
        user_id: int,
        answers: Dict[str, str]
    ) -> Optional[AssessmentSubmission]:
        """Submit an assessment and grade it"""
        # Get assessment
        assessment_query = select(Assessment).where(Assessment.id == assessment_id)
        assessment_result = await db.execute(assessment_query)
        assessment = assessment_result.scalar_one_or_none()
        
        if not assessment:
            return None
        
        # Check enrollment
        enrollment_query = select(Enrollment).where(
            and_(
                Enrollment.user_id == user_id,
                Enrollment.course_id == assessment.course_id
            )
        )
        enrollment_result = await db.execute(enrollment_query)
        enrollment = enrollment_result.scalar_one_or_none()
        
        if not enrollment:
            return None
        
        # Check attempt count
        attempt_query = select(AssessmentSubmission).where(
            and_(
                AssessmentSubmission.assessment_id == assessment_id,
                AssessmentSubmission.user_id == user_id
            )
        )
        attempt_result = await db.execute(attempt_query)
        attempts = attempt_result.scalars().all()
        
        if len(attempts) >= assessment.max_attempts:
            return None  # Max attempts reached
        
        # Grade the assessment
        score, correct_count = AssessmentService._grade_assessment(
            assessment.questions, answers
        )
        
        passed = score >= assessment.passing_score
        
        # Create submission
        submission = AssessmentSubmission(
            assessment_id=assessment_id,
            user_id=user_id,
            answers=answers,
            score=score,
            passed=passed,
            attempt_number=len(attempts) + 1,
            graded_at=datetime.utcnow()
        )
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        return submission
    
    @staticmethod
    def _grade_assessment(
        questions: List[Dict[str, Any]],
        answers: Dict[str, str]
    ) -> tuple[float, int]:
        """Grade an assessment and return score and correct count"""
        if not questions:
            return 0.0, 0
        
        total_points = sum(q.get('points', 1.0) for q in questions)
        earned_points = 0.0
        correct_count = 0
        
        for question in questions:
            question_id = question.get('id')
            correct_answer = question.get('correct_answer')
            user_answer = answers.get(question_id)
            
            if user_answer and correct_answer:
                # Simple string comparison (case-insensitive)
                if user_answer.strip().lower() == correct_answer.strip().lower():
                    earned_points += question.get('points', 1.0)
                    correct_count += 1
        
        score = (earned_points / total_points * 100) if total_points > 0 else 0
        return round(score, 2), correct_count
    
    @staticmethod
    async def get_user_submissions(
        db: AsyncSession,
        user_id: int,
        assessment_id: Optional[int] = None
    ) -> List[AssessmentSubmission]:
        """Get all submissions for a user"""
        query = select(AssessmentSubmission).where(
            AssessmentSubmission.user_id == user_id
        )
        
        if assessment_id:
            query = query.where(AssessmentSubmission.assessment_id == assessment_id)
        
        query = query.order_by(AssessmentSubmission.submitted_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_best_submission(
        db: AsyncSession,
        user_id: int,
        assessment_id: int
    ) -> Optional[AssessmentSubmission]:
        """Get the best submission for a user on an assessment"""
        query = select(AssessmentSubmission).where(
            and_(
                AssessmentSubmission.user_id == user_id,
                AssessmentSubmission.assessment_id == assessment_id
            )
        ).order_by(AssessmentSubmission.score.desc()).limit(1)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
