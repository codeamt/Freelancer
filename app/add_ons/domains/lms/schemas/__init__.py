"""LMS schemas package"""
from .course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseListResponse,
    CourseStatus,
    CourseDifficulty,
)
from .lesson import (
    LessonCreate,
    LessonUpdate,
    LessonResponse,
    LessonListResponse,
    LessonType,
)
from .enrollment import (
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
    EnrollmentWithCourse,
    EnrollmentStatus,
)
from .progress import (
    ProgressUpdate,
    ProgressResponse,
    CourseProgressDetail,
)
from .assessment import (
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentResponse,
    AssessmentSubmit,
    AssessmentSubmissionResponse,
    AssessmentResultDetail,
    AssessmentType,
)

__all__ = [
    # Course
    "CourseCreate",
    "CourseUpdate",
    "CourseResponse",
    "CourseListResponse",
    "CourseStatus",
    "CourseDifficulty",
    # Lesson
    "LessonCreate",
    "LessonUpdate",
    "LessonResponse",
    "LessonListResponse",
    "LessonType",
    # Enrollment
    "EnrollmentCreate",
    "EnrollmentUpdate",
    "EnrollmentResponse",
    "EnrollmentWithCourse",
    "EnrollmentStatus",
    # Progress
    "ProgressUpdate",
    "ProgressResponse",
    "CourseProgressDetail",
    # Assessment
    "AssessmentCreate",
    "AssessmentUpdate",
    "AssessmentResponse",
    "AssessmentSubmit",
    "AssessmentSubmissionResponse",
    "AssessmentResultDetail",
    "AssessmentType",
]
