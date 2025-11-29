"""Enrollment routes for LMS add-on"""
from fasthtml.common import *
from app.core.db.base_class import get_session
from app.add_ons.lms.services import EnrollmentService, ProgressService
from app.add_ons.lms.schemas import EnrollmentCreate
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

router_enrollments = FastHTML()


@router_enrollments.post("/enroll")
async def enroll_in_course(
    request: Request,
    course_id: int = Form(...),
    payment_id: str = Form(None)
):
    """Enroll in a course"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    async for db in get_session():
        try:
            enrollment_data = EnrollmentCreate(
                course_id=course_id,
                payment_id=payment_id
            )
            
            enrollment = await EnrollmentService.enroll_user(db, user_id, enrollment_data)
            
            if not enrollment:
                raise HTTPException(status_code=400, detail="Already enrolled or course not found")
            
            return RedirectResponse(f"/lms/courses/{course_id}", status_code=303)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error enrolling in course {course_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to enroll")


@router_enrollments.get("/my-courses")
async def get_my_courses(request: Request):
    """Get user's enrolled courses"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    async for db in get_session():
        try:
            enrollments = await EnrollmentService.get_user_enrollments(db, user_id)
            
            return {
                "enrollments": [
                    {
                        "id": e.id,
                        "course_id": e.course_id,
                        "course_title": e.course.title if e.course else "",
                        "status": e.status.value,
                        "enrolled_at": e.enrolled_at.isoformat(),
                        "progress_percent": e.progress.progress_percent if e.progress else 0.0
                    }
                    for e in enrollments
                ]
            }
        except Exception as e:
            logger.error(f"Error getting user courses: {e}")
            raise HTTPException(status_code=500, detail="Failed to get courses")


@router_enrollments.get("/courses/{course_id}/progress")
async def get_course_progress(request: Request, course_id: int):
    """Get progress for a specific course"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    async for db in get_session():
        try:
            progress_detail = await ProgressService.get_course_progress_detail(
                db, user_id, course_id
            )
            
            if not progress_detail:
                raise HTTPException(status_code=404, detail="Enrollment not found")
            
            return progress_detail
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting course progress: {e}")
            raise HTTPException(status_code=500, detail="Failed to get progress")


@router_enrollments.post("/lessons/{lesson_id}/complete")
async def complete_lesson(
    request: Request,
    lesson_id: int,
    enrollment_id: int = Form(...),
    time_spent: int = Form(0)
):
    """Mark a lesson as complete"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    async for db in get_session():
        try:
            # Verify enrollment belongs to user
            enrollment = await EnrollmentService.get_enrollment_by_id(db, enrollment_id)
            
            if not enrollment or enrollment.user_id != user_id:
                raise HTTPException(status_code=403, detail="Unauthorized")
            
            progress = await ProgressService.mark_lesson_complete(
                db, enrollment_id, lesson_id, time_spent
            )
            
            return {
                "message": "Lesson completed",
                "progress_percent": progress.progress_percent
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error completing lesson {lesson_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to complete lesson")
