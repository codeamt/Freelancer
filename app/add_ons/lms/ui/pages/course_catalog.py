"""Course Catalog Page"""
from fasthtml.common import *
from monsterui.all import *

def CourseCatalog(courses: list = None, user: dict = None):
    """
    Public course catalog page.
    Shows all available courses with option to enroll (requires auth).
    
    Args:
        courses: List of available courses
        user: Current user (optional - None if not logged in)
    """
    courses = courses or []
    
    return Div(
        # Header
        Div(
            H1("Course Catalog", cls="text-4xl font-bold mb-4"),
            P("Explore our courses and start learning today", cls="text-xl text-gray-500 mb-8"),
            cls="text-center mb-12"
        ),
        
        # Filters (placeholder for now)
        Div(
            Div(
                Input(
                    type="text",
                    placeholder="Search courses...",
                    cls="input input-bordered w-full",
                    hx_get="/lms/courses",
                    hx_trigger="keyup changed delay:500ms",
                    hx_target="#course-grid",
                    name="search"
                ),
                cls="mb-6"
            ),
        ),
        
        # Course Grid
        Div(
            *[CourseCardPublic(course, user) for course in courses] if courses else [
                Card(
                    Div(
                        UkIcon("book", width="48", height="48", cls="text-gray-400 mb-4"),
                        H3("No courses available", cls="text-xl font-semibold mb-2"),
                        P("Check back soon for new courses!", cls="text-gray-500"),
                        cls="text-center p-12"
                    )
                )
            ],
            id="course-grid",
            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        ),
        
        cls="container mx-auto px-4 py-8"
    )


def CourseCardPublic(course: dict, user: dict = None):
    """
    Public course card with enroll button.
    Shows login prompt if user not authenticated.
    """
    is_enrolled = False  # TODO: Check if user is enrolled
    
    return Card(
        Div(
            # Course thumbnail
            Div(
                Img(
                    src=course.get("thumbnail_url", "/static/placeholder.jpg"),
                    alt=course.get("title"),
                    cls="w-full h-48 object-cover"
                ),
                # Price badge
                Span(
                    f"${course.get('price', 0)}" if course.get('price', 0) > 0 else "Free",
                    cls="badge badge-primary absolute top-2 right-2"
                ),
                cls="relative mb-4"
            ),
            
            # Course info
            H3(course.get("title", "Untitled Course"), cls="text-lg font-semibold mb-2"),
            P(
                course.get("description", "")[:120] + ("..." if len(course.get("description", "")) > 120 else ""),
                cls="text-sm text-gray-500 mb-4"
            ),
            
            # Course meta
            Div(
                Div(
                    UkIcon("user", width="16", height="16", cls="inline mr-1"),
                    Span(course.get("instructor_name", "Instructor"), cls="text-sm"),
                    cls="mr-4"
                ),
                Div(
                    UkIcon("clock", width="16", height="16", cls="inline mr-1"),
                    Span(f"{course.get('duration', 0)}h", cls="text-sm"),
                ),
                cls="flex items-center text-gray-600 mb-4"
            ),
            
            # Action button
            Div(
                A(
                    "View Course",
                    href=f"/lms/courses/{course.get('id')}",
                    cls="btn btn-outline btn-sm mr-2"
                ),
                (
                    Span("Enrolled", cls="badge badge-success") if is_enrolled else
                    A(
                        "Enroll Now",
                        href=f"/lms/courses/{course.get('id')}/enroll" if user else "/auth/login?redirect=/lms/courses",
                        cls="btn btn-primary btn-sm"
                    )
                ),
                cls="flex justify-between items-center"
            ),
            
            cls="p-4"
        ),
        cls="hover:shadow-lg transition-shadow"
    )
