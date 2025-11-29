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
from .pages import (
    CourseCatalogPage,
    CourseDetailPage,
    MyCoursesPage,
    LessonViewPage,
    InstructorDashboardPage,
)

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
    "CourseCatalogPage",
    "CourseDetailPage",
    "MyCoursesPage",
    "LessonViewPage",
    "InstructorDashboardPage",
]
