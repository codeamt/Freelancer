"""LMS (Learning Management System) add-on for Freelancer platform"""
from fasthtml.common import *
from .routes.courses import router_courses
from .routes.enrollments import router_enrollments

# Create main LMS router
router_lms = FastHTML()

# Mount sub-routers
router_lms.mount("/", router_courses)
router_lms.mount("/", router_enrollments)

__all__ = ["router_lms"]
