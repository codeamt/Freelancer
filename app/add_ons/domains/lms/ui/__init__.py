"""LMS UI components and pages"""
from .components import (
    CourseCard,
    ProgressBar,
    LessonListItem,
    EnrollmentCard,
    AssessmentCard,
    CourseHeader,
    InstructorInfo,
)
from .pages import CourseCatalog, InstructorDashboard, StudentDashboard

__all__ = [
    # Components
    "CourseCard",
    "ProgressBar",
    "LessonListItem",
    "EnrollmentCard",
    "AssessmentCard",
    "CourseHeader",
    "InstructorInfo",
    # Pages
    "CourseCatalog",
    "InstructorDashboard",
    "StudentDashboard",
]
