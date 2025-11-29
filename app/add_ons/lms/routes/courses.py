"""Course routes for LMS add-on"""
from fasthtml.common import *
from typing import Optional
from app.core.db.base_class import get_session
from app.add_ons.lms.services import CourseService
from app.add_ons.lms.schemas import CourseCreate, CourseUpdate, CourseStatus
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

router_courses = FastHTML()


@router_courses.get("/courses")
async def list_courses(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """List all published courses"""
    async for db in get_session():
        try:
            course_status = CourseStatus(status) if status else CourseStatus.PUBLISHED
            courses, total = await CourseService.get_courses(
                db=db,
                page=page,
                page_size=page_size,
                status=course_status,
                category=category,
                search=search
            )
            
            total_pages = (total + page_size - 1) // page_size
            
            return {
                "courses": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "description": c.description,
                        "thumbnail_url": c.thumbnail_url,
                        "price": c.price,
                        "currency": c.currency,
                        "difficulty": c.difficulty.value,
                        "category": c.category,
                        "instructor_id": c.instructor_id,
                    }
                    for c in courses
                ],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        except Exception as e:
            logger.error(f"Error listing courses: {e}")
            raise HTTPException(status_code=500, detail="Failed to list courses")


@router_courses.get("/courses/{course_id}")
async def get_course(course_id: int):
    """Get course details"""
    async for db in get_session():
        try:
            course = await CourseService.get_course(db, course_id, include_instructor=True)
            
            if not course:
                raise HTTPException(status_code=404, detail="Course not found")
            
            stats = await CourseService.get_course_stats(db, course_id)
            
            return {
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "thumbnail_url": course.thumbnail_url,
                "price": course.price,
                "currency": course.currency,
                "duration_hours": course.duration_hours,
                "difficulty": course.difficulty.value,
                "status": course.status.value,
                "category": course.category,
                "tags": course.tags,
                "requirements": course.requirements,
                "learning_objectives": course.learning_objectives,
                "instructor": {
                    "id": course.instructor.id,
                    "email": course.instructor.email
                } if course.instructor else None,
                "stats": stats,
                "created_at": course.created_at.isoformat(),
                "updated_at": course.updated_at.isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting course {course_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get course")


@router_courses.post("/courses")
async def create_course(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    price: float = Form(0.0),
    category: str = Form(None)
):
    """Create a new course (instructor only)"""
    # TODO: Get user_id from session/auth
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    async for db in get_session():
        try:
            course_data = CourseCreate(
                title=title,
                description=description,
                price=price,
                category=category
            )
            
            course = await CourseService.create_course(db, course_data, user_id)
            
            return RedirectResponse(f"/lms/courses/{course.id}", status_code=303)
        except Exception as e:
            logger.error(f"Error creating course: {e}")
            raise HTTPException(status_code=500, detail="Failed to create course")


@router_courses.put("/courses/{course_id}")
async def update_course(
    request: Request,
    course_id: int,
    title: str = Form(None),
    description: str = Form(None),
    price: float = Form(None),
    status: str = Form(None)
):
    """Update a course (instructor only)"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    async for db in get_session():
        try:
            course_data = CourseUpdate(
                title=title,
                description=description,
                price=price,
                status=CourseStatus(status) if status else None
            )
            
            course = await CourseService.update_course(db, course_id, course_data, user_id)
            
            if not course:
                raise HTTPException(status_code=404, detail="Course not found or unauthorized")
            
            return RedirectResponse(f"/lms/courses/{course.id}", status_code=303)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating course {course_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update course")


@router_courses.delete("/courses/{course_id}")
async def delete_course(request: Request, course_id: int):
    """Delete a course (instructor only)"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    async for db in get_session():
        try:
            success = await CourseService.delete_course(db, course_id, user_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Course not found or unauthorized")
            
            return {"message": "Course deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting course {course_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete course")


@router_courses.post("/courses/{course_id}/publish")
async def publish_course(request: Request, course_id: int):
    """Publish a course"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    async for db in get_session():
        try:
            course = await CourseService.publish_course(db, course_id, user_id)
            
            if not course:
                raise HTTPException(status_code=404, detail="Course not found or unauthorized")
            
            return {"message": "Course published successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error publishing course {course_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to publish course")
