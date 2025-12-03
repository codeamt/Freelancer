"""Instructor Dashboard Page"""
from fasthtml.common import *
from monsterui.all import *

def InstructorDashboard(user: dict, my_courses: list = None):
    """
    Instructor dashboard showing their courses and stats.
    
    Args:
        user: Current user dict
        my_courses: List of courses created by instructor
    """
    my_courses = my_courses or []
    total_students = sum(course.get("enrolled_count", 0) for course in my_courses)
    
    return Div(
        # Welcome Header
        Div(
            H1(f"Welcome back, {user.get('username', 'Instructor')}!", cls="text-3xl font-bold mb-2"),
            P("Manage your courses and students", cls="text-gray-500"),
            cls="mb-8"
        ),
        
        # Stats Cards
        Div(
            # Total Courses
            Card(
                Div(
                    Div(
                        UkIcon("book", width="32", height="32", cls="text-blue-600"),
                        cls="mb-2"
                    ),
                    H3(str(len(my_courses)), cls="text-3xl font-bold mb-1"),
                    P("My Courses", cls="text-sm text-gray-500"),
                    cls="text-center p-6"
                )
            ),
            # Total Students
            Card(
                Div(
                    Div(
                        UkIcon("users", width="32", height="32", cls="text-green-600"),
                        cls="mb-2"
                    ),
                    H3(str(total_students), cls="text-3xl font-bold mb-1"),
                    P("Total Students", cls="text-sm text-gray-500"),
                    cls="text-center p-6"
                )
            ),
            # Revenue
            Card(
                Div(
                    Div(
                        UkIcon("dollar-sign", width="32", height="32", cls="text-purple-600"),
                        cls="mb-2"
                    ),
                    H3("$0", cls="text-3xl font-bold mb-1"),
                    P("Total Revenue", cls="text-sm text-gray-500"),
                    cls="text-center p-6"
                )
            ),
            cls="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
        ),
        
        # Quick Actions
        Div(
            A(
                Button(
                    UkIcon("plus", width="20", height="20", cls="mr-2"),
                    "Create New Course",
                    cls="btn btn-primary btn-lg"
                ),
                href="/lms/instructor/courses/create"
            ),
            cls="mb-8"
        ),
        
        # My Courses Section
        Div(
            H2("My Courses", cls="text-2xl font-bold mb-6"),
            Div(
                *[InstructorCourseCard(course) for course in my_courses] if my_courses else [
                    Card(
                        Div(
                            Div(
                                UkIcon("book", width="48", height="48", cls="text-gray-400 mb-4"),
                                cls="flex justify-center"
                            ),
                            H3("No courses yet", cls="text-xl font-semibold mb-2 text-center"),
                            P("Create your first course to get started", cls="text-gray-500 text-center mb-4"),
                            A("Create Course", href="/lms/instructor/courses/create", cls="btn btn-primary"),
                            cls="text-center p-8"
                        )
                    )
                ],
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            ),
            cls="mb-8"
        ),
        
        # Recent Activity
        Div(
            H2("Recent Activity", cls="text-2xl font-bold mb-6"),
            Card(
                Div(
                    P("No recent activity", cls="text-gray-500 text-center py-8"),
                    cls="p-4"
                )
            ),
        ),
        
        cls="container mx-auto px-4 py-8"
    )


def InstructorCourseCard(course: dict):
    """Individual course card for instructor dashboard"""
    return Card(
        Div(
            # Course thumbnail
            Div(
                Img(src=course.get("thumbnail_url", "/static/placeholder.jpg"), 
                    alt=course.get("title"),
                    cls="w-full h-48 object-cover"),
                # Status badge
                Span(
                    course.get("status", "draft").capitalize(),
                    cls=f"badge {'badge-success' if course.get('status') == 'published' else 'badge-warning'} absolute top-2 right-2"
                ),
                cls="relative mb-4"
            ),
            # Course info
            H3(course.get("title", "Untitled Course"), cls="text-lg font-semibold mb-2"),
            P(course.get("description", "")[:100] + "...", cls="text-sm text-gray-500 mb-4"),
            # Stats
            Div(
                Div(
                    UkIcon("users", width="16", height="16", cls="inline mr-1"),
                    Span(f"{course.get('enrolled_count', 0)} students", cls="text-sm"),
                    cls="mr-4"
                ),
                Div(
                    UkIcon("star", width="16", height="16", cls="inline mr-1"),
                    Span(f"{course.get('rating', 0)}/5", cls="text-sm"),
                ),
                cls="flex items-center text-gray-600 mb-4"
            ),
            # Action buttons
            Div(
                A("Edit", 
                  href=f"/lms/instructor/courses/{course.get('id')}/edit", 
                  cls="btn btn-sm btn-outline mr-2"),
                A("View", 
                  href=f"/lms/courses/{course.get('id')}", 
                  cls="btn btn-sm btn-primary"),
                cls="flex"
            ),
            cls="p-4"
        ),
        cls="hover:shadow-lg transition-shadow"
    )
