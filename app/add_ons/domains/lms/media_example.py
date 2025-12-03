"""
Example: LMS Domain Media Upload

Shows how LMS domain implements its own media upload routes.
Uses the universal StorageService for S3/MinIO operations.
"""

from fasthtml.common import *
from add_ons.services.storage import StorageService
from add_ons.services.auth import get_current_user
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Module name for this domain
MODULE = "lms"


# -----------------------------------------------------------------------------
# Course Material Upload
# -----------------------------------------------------------------------------

async def upload_course_material(request: Request, course_id: str, file: UploadFile):
    """
    Upload course materials (PDFs, videos, etc.).
    
    Domain-specific logic:
    - Validates user is instructor of the course
    - Supports multiple file types
    - Stores metadata in course database
    """
    # Get current user
    user = await get_current_user(request)
    if not user:
        return {"error": "Not authenticated"}, 401
    
    # Check if user is instructor
    if "instructor" not in user.get("roles", []):
        return {"error": "Only instructors can upload course materials"}, 403
    
    # TODO: Validate user owns this course
    # course = await db.find_one("courses", {"_id": course_id, "instructor_id": user["_id"]})
    # if not course:
    #     return {"error": "Course not found or unauthorized"}, 404
    
    # Validate file type
    allowed_types = [
        "application/pdf",
        "video/mp4",
        "video/webm",
        "application/zip",
        "text/plain",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ]
    if file.content_type not in allowed_types:
        return {"error": "Invalid file type"}, 400
    
    # Initialize storage service
    storage = StorageService()
    
    try:
        # Generate presigned upload URL
        upload_info = storage.generate_upload_url(
            module=MODULE,
            user_id=int(user["_id"]),
            filename=f"courses/{course_id}/materials/{file.filename}",
            content_type=file.content_type,
            expires_in=7200  # 2 hours for large video files
        )
        
        logger.info(f"Generated course material upload URL for course {course_id}: {file.filename}")
        
        # TODO: Store metadata in database
        # await db.insert_one("course_materials", {
        #     "course_id": course_id,
        #     "instructor_id": user["_id"],
        #     "filename": file.filename,
        #     "content_type": file.content_type,
        #     "uploaded_at": datetime.utcnow()
        # })
        
        return {
            "message": "Upload URL generated successfully",
            "upload_info": upload_info,
            "course_id": course_id,
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Failed to generate upload URL: {e}")
        return {"error": "Failed to generate upload URL"}, 500


# -----------------------------------------------------------------------------
# Student Assignment Upload
# -----------------------------------------------------------------------------

async def upload_student_assignment(request: Request, course_id: str, assignment_id: str, file: UploadFile):
    """
    Upload student assignment submission.
    
    Domain-specific logic:
    - Validates student is enrolled in course
    - Checks assignment deadline
    - Stores submission metadata
    """
    # Get current user
    user = await get_current_user(request)
    if not user:
        return {"error": "Not authenticated"}, 401
    
    # TODO: Validate student is enrolled
    # enrollment = await db.find_one("enrollments", {"course_id": course_id, "user_id": user["_id"]})
    # if not enrollment:
    #     return {"error": "Not enrolled in this course"}, 403
    
    # TODO: Check assignment deadline
    # assignment = await db.find_one("assignments", {"_id": assignment_id})
    # if datetime.utcnow() > assignment["deadline"]:
    #     return {"error": "Assignment deadline has passed"}, 400
    
    # Validate file size (max 10MB for assignments)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        return {"error": "File too large. Maximum 10MB."}, 400
    
    # Initialize storage service
    storage = StorageService()
    
    try:
        # Upload directly (secure, encrypted)
        success = storage.upload_secure_object(
            module=MODULE,
            user_id=int(user["_id"]),
            filename=f"assignments/{course_id}/{assignment_id}/{file.filename}",
            data=file_content,
            content_type=file.content_type
        )
        
        if success:
            logger.info(f"Student {user['_id']} uploaded assignment for {course_id}/{assignment_id}")
            
            # TODO: Store submission in database
            # await db.insert_one("submissions", {
            #     "course_id": course_id,
            #     "assignment_id": assignment_id,
            #     "student_id": user["_id"],
            #     "filename": file.filename,
            #     "submitted_at": datetime.utcnow()
            # })
            
            return {
                "message": "Assignment uploaded successfully",
                "filename": file.filename
            }
        else:
            return {"error": "Failed to upload assignment"}, 500
            
    except Exception as e:
        logger.error(f"Failed to upload assignment: {e}")
        return {"error": "Failed to upload assignment"}, 500


# -----------------------------------------------------------------------------
# Course Thumbnail Upload
# -----------------------------------------------------------------------------

async def upload_course_thumbnail(request: Request, course_id: str, file: UploadFile):
    """
    Upload course thumbnail image.
    
    Domain-specific logic:
    - Validates user is instructor
    - Only allows images
    - Optimizes for web display
    """
    # Get current user
    user = await get_current_user(request)
    if not user:
        return {"error": "Not authenticated"}, 401
    
    # Check if user is instructor
    if "instructor" not in user.get("roles", []):
        return {"error": "Only instructors can upload course thumbnails"}, 403
    
    # Validate file type (images only)
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        return {"error": "Invalid file type. Only JPEG, PNG, and WebP allowed."}, 400
    
    # Validate file size (max 2MB for thumbnails)
    file_content = await file.read()
    if len(file_content) > 2 * 1024 * 1024:
        return {"error": "File too large. Maximum 2MB."}, 400
    
    # Initialize storage service
    storage = StorageService()
    
    try:
        # Generate presigned upload URL
        upload_info = storage.generate_upload_url(
            module=MODULE,
            user_id=int(user["_id"]),
            filename=f"courses/{course_id}/thumbnail.{file.filename.split('.')[-1]}",
            content_type=file.content_type,
            expires_in=3600
        )
        
        logger.info(f"Generated course thumbnail upload URL for course {course_id}")
        
        # TODO: Update course thumbnail in database
        # await db.update_one("courses", {"_id": course_id}, {
        #     "thumbnail_url": f"courses/{course_id}/thumbnail.{file.filename.split('.')[-1]}"
        # })
        
        return {
            "message": "Upload URL generated successfully",
            "upload_info": upload_info,
            "course_id": course_id
        }
        
    except Exception as e:
        logger.error(f"Failed to generate upload URL: {e}")
        return {"error": "Failed to generate upload URL"}, 500


# -----------------------------------------------------------------------------
# Download Course Material
# -----------------------------------------------------------------------------

async def download_course_material(request: Request, course_id: str, filename: str):
    """
    Download course material.
    
    Domain-specific logic:
    - Validates student is enrolled
    - Generates time-limited download URL
    - Logs access for analytics
    """
    # Get current user
    user = await get_current_user(request)
    if not user:
        return {"error": "Not authenticated"}, 401
    
    # TODO: Validate student is enrolled or is instructor
    # enrollment = await db.find_one("enrollments", {"course_id": course_id, "user_id": user["_id"]})
    # course = await db.find_one("courses", {"_id": course_id, "instructor_id": user["_id"]})
    # if not enrollment and not course:
    #     return {"error": "Not authorized to access this course"}, 403
    
    # Initialize storage service
    storage = StorageService()
    
    try:
        # Generate presigned download URL
        download_url = storage.generate_download_url(
            module=MODULE,
            user_id=int(user["_id"]),
            filename=f"courses/{course_id}/materials/{filename}",
            expires_in=3600  # 1 hour
        )
        
        logger.info(f"Generated course material download URL for user {user['_id']}: {filename}")
        
        # TODO: Log access for analytics
        # await db.insert_one("material_access_log", {
        #     "user_id": user["_id"],
        #     "course_id": course_id,
        #     "filename": filename,
        #     "accessed_at": datetime.utcnow()
        # })
        
        return {
            "download_url": download_url,
            "filename": filename
        }
        
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        return {"error": "Failed to generate download URL"}, 500


# -----------------------------------------------------------------------------
# Routes Registration (Example)
# -----------------------------------------------------------------------------

def register_lms_media_routes(app):
    """
    Register LMS media routes with the app.
    
    Usage:
        from .media_example import register_lms_media_routes
        register_lms_media_routes(app)
    """
    
    @app.post("/lms/media/upload/course-material/{course_id}")
    async def _upload_course_material(request: Request, course_id: str, file: UploadFile):
        return await upload_course_material(request, course_id, file)
    
    @app.post("/lms/media/upload/assignment/{course_id}/{assignment_id}")
    async def _upload_assignment(request: Request, course_id: str, assignment_id: str, file: UploadFile):
        return await upload_student_assignment(request, course_id, assignment_id, file)
    
    @app.post("/lms/media/upload/course-thumbnail/{course_id}")
    async def _upload_thumbnail(request: Request, course_id: str, file: UploadFile):
        return await upload_course_thumbnail(request, course_id, file)
    
    @app.get("/lms/media/download/course-material/{course_id}/{filename}")
    async def _download_material(request: Request, course_id: str, filename: str):
        return await download_course_material(request, course_id, filename)
    
    logger.info("LMS media routes registered")


# Usage in LMS app:
# from .media_example import register_lms_media_routes
# register_lms_media_routes(app)
