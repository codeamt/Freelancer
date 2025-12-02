"""
LMS Example - Learning Management System Application

A complete example of a learning platform with:
- Course catalog (public browsing)
- Student enrollment (requires auth)
- Instructor dashboard (requires instructor role)
- Course management
- Progress tracking

Perfect template for freelance education/training projects.
"""
from .app import create_lms_app

__all__ = ["create_lms_app"]
