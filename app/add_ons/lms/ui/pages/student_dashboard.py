"""Student Dashboard Page"""
from fasthtml.common import *
from monsterui.all import *

def StudentDashboard(user: dict, enrolled_courses: list = None):
    """
    Student dashboard showing enrolled courses and progress.
    
    Args:
        user: Current user dict
        enrolled_courses: List of courses student is enrolled in
    """
    enrolled_courses = enrolled_courses or []
    
    return Div(
        # Welcome Header
        Div(
            H1(f"Welcome back, {user.get('username', 'Student')}!", cls="text-3xl font-bold mb-2"),
            P("Continue your learning journey", cls="text-gray-500"),
            cls="mb-8"
        ),
        
        # Stats Cards
        Div(
            # Enrolled Courses
            Card(
                Div(
                    Div(
                        UkIcon("book", width="32", height="32", cls="text-blue-600"),
                        cls="mb-2"
                    ),
                    H3(str(len(enrolled_courses)), cls="text-3xl font-bold mb-1"),
                    P("Enrolled Courses", cls="text-sm text-gray-500"),
                    cls="text-center p-6"
                )
            ),
            # Completed
            Card(
                Div(
                    Div(
                        UkIcon("check-circle", width="32", height="32", cls="text-green-600"),
                        cls="mb-2"
                    ),
                    H3("0", cls="text-3xl font-bold mb-1"),
                    P("Completed", cls="text-sm text-gray-500"),
                    cls="text-center p-6"
                )
            ),
            # In Progress
            Card(
                Div(
                    Div(
                        UkIcon("play-circle", width="32", height="32", cls="text-orange-600"),
                        cls="mb-2"
                    ),
                    H3(str(len(enrolled_courses)), cls="text-3xl font-bold mb-1"),
                    P("In Progress", cls="text-sm text-gray-500"),
                    cls="text-center p-6"
                )
            ),
            cls="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
        ),
        
        # My Courses Section
        Div(
            H2("My Courses", cls="text-2xl font-bold mb-6"),
            Div(
                *[CourseCard(course) for course in enrolled_courses] if enrolled_courses else [
                    Card(
                        Div(
                            Div(
                                UkIcon("book", width="48", height="48", cls="text-gray-400 mb-4"),
                                cls="flex justify-center"
                            ),
                            H3("No courses yet", cls="text-xl font-semibold mb-2 text-center"),
                            P("Browse the course catalog to get started", cls="text-gray-500 text-center mb-4"),
                            A("Browse Courses", href="/lms/courses", cls="btn btn-primary"),
                            cls="text-center p-8"
                        )
                    )
                ],
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            ),
            cls="mb-8"
        ),
        
        # Quick Actions
        Div(
            H2("Quick Actions", cls="text-2xl font-bold mb-6"),
            Div(
                A(
                    Card(
                        Div(
                            UkIcon("search", width="24", height="24", cls="text-blue-600 mb-2"),
                            H3("Browse Courses", cls="font-semibold"),
                            P("Explore available courses", cls="text-sm text-gray-500"),
                            cls="text-center p-6"
                        )
                    ),
                    href="/lms/courses"
                ),
                A(
                    Card(
                        Div(
                            UkIcon("user", width="24", height="24", cls="text-blue-600 mb-2"),
                            H3("My Profile", cls="font-semibold"),
                            P("View and edit your profile", cls="text-sm text-gray-500"),
                            cls="text-center p-6"
                        )
                    ),
                    href="/auth/profile"
                ),
                A(
                    Card(
                        Div(
                            UkIcon("settings", width="24", height="24", cls="text-blue-600 mb-2"),
                            H3("Settings", cls="font-semibold"),
                            P("Manage your account", cls="text-sm text-gray-500"),
                            cls="text-center p-6"
                        )
                    ),
                    href="/auth/settings"
                ),
                cls="grid grid-cols-1 md:grid-cols-3 gap-6"
            ),
        ),
        
        cls="container mx-auto px-4 py-8"
    )


def CourseCard(course: dict):
    """Individual course card for dashboard"""
    return Card(
        Div(
            # Course thumbnail
            Div(
                Img(src=course.get("thumbnail_url", "/static/placeholder.jpg"), 
                    alt=course.get("title"),
                    cls="w-full h-48 object-cover"),
                cls="mb-4"
            ),
            # Course info
            H3(course.get("title", "Untitled Course"), cls="text-lg font-semibold mb-2"),
            P(course.get("description", "")[:100] + "...", cls="text-sm text-gray-500 mb-4"),
            # Progress bar
            Div(
                Div(
                    Div(cls="h-2 bg-blue-600 rounded", style=f"width: {course.get('progress', 0)}%"),
                    cls="w-full bg-gray-200 rounded h-2 mb-2"
                ),
                P(f"{course.get('progress', 0)}% Complete", cls="text-xs text-gray-500"),
                cls="mb-4"
            ),
            # Action button
            A("Continue Learning", 
              href=f"/lms/courses/{course.get('id')}", 
              cls="btn btn-primary btn-sm w-full"),
            cls="p-4"
        ),
        cls="hover:shadow-lg transition-shadow"
    )
