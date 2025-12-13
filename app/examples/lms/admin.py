"""
LMS Instructor Dashboard

Instructor/Admin dashboard for managing lessons, KPIs, certificates, and quizzes.
"""
from fasthtml.common import *
from monsterui.all import *
from typing import Optional, List, Dict
from core.ui.layout import Layout


def LMSInstructorDashboard(user: dict, metrics: Optional[dict] = None, demo: bool = False):
    """
    LMS Instructor dashboard with lesson management, KPIs, certificates, and quizzes.
    """
    BASE = "/lms-example"
    
    if not metrics:
        metrics = {
            "total_students": 234,
            "active_enrollments": 156,
            "courses_published": 5,
            "completion_rate": 68,
            "revenue_this_month": 4520.00,
            "pending_reviews": 8
        }
    
    content = Div(
        # Header
        Div(
            Div(
                H1("Instructor Dashboard", cls="text-3xl font-bold"),
                P(f"Welcome back, {user.get('email', 'Instructor')}", cls="text-gray-600"),
                cls="flex-1"
            ),
            Div(
                A("View Courses", href=f"{BASE}/courses", cls="btn btn-outline btn-sm mr-2"),
                A("Logout", href=f"{BASE}/logout", cls="btn btn-ghost btn-sm"),
            ),
            cls="flex justify-between items-center mb-8"
        ),
        
        # Stripe Integration Notice
        Div(
            Div(
                UkIcon("credit-card", width="20", height="20", cls="mr-2"),
                Span("Stripe payments are pre-configured for course sales. ", cls="text-sm font-semibold"),
                A("View Payouts →", href=f"{BASE}/instructor/payouts", cls="link link-primary text-sm"),
                cls="flex items-center"
            ),
            cls="alert alert-info mb-6"
        ),
        
        # KPI Cards
        H2("Performance Overview", cls="text-2xl font-bold mb-4"),
        Div(
            Div(
                Div(
                    UkIcon("users", width="24", height="24", cls="text-blue-500"),
                    cls="mb-2"
                ),
                H3(str(metrics.get("total_students", 0)), cls="text-3xl font-bold"),
                P("Total Students", cls="text-gray-600 text-sm"),
                Span("+18 this week", cls="text-green-500 text-xs"),
                cls="stat bg-base-100 rounded-lg shadow p-4"
            ),
            Div(
                Div(
                    UkIcon("book-open", width="24", height="24", cls="text-green-500"),
                    cls="mb-2"
                ),
                H3(str(metrics.get("active_enrollments", 0)), cls="text-3xl font-bold"),
                P("Active Enrollments", cls="text-gray-600 text-sm"),
                Span("+12% from last month", cls="text-green-500 text-xs"),
                cls="stat bg-base-100 rounded-lg shadow p-4"
            ),
            Div(
                Div(
                    UkIcon("award", width="24", height="24", cls="text-purple-500"),
                    cls="mb-2"
                ),
                H3(f"{metrics.get('completion_rate', 0)}%", cls="text-3xl font-bold"),
                P("Completion Rate", cls="text-gray-600 text-sm"),
                Span("+5% improvement", cls="text-green-500 text-xs"),
                cls="stat bg-base-100 rounded-lg shadow p-4"
            ),
            Div(
                Div(
                    UkIcon("dollar-sign", width="24", height="24", cls="text-orange-500"),
                    cls="mb-2"
                ),
                H3(f"${metrics.get('revenue_this_month', 0):,.2f}", cls="text-3xl font-bold"),
                P("Revenue This Month", cls="text-gray-600 text-sm"),
                A("View Details →", href=f"{BASE}/instructor/earnings", cls="link link-primary text-xs"),
                cls="stat bg-base-100 rounded-lg shadow p-4"
            ),
            cls="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
        ),
        
        # Main Management Sections
        Div(
            # Left Column - Course Management
            Div(
                H2("Course Management", cls="text-xl font-bold mb-4"),
                Div(
                    A(
                        Div(
                            UkIcon("video", width="24", height="24", cls="mr-3"),
                            Div(
                                H4("Lesson Manager", cls="font-bold"),
                                P("Upload and organize course lessons", cls="text-sm text-gray-600"),
                            ),
                            cls="flex items-center"
                        ),
                        href=f"{BASE}/instructor/lessons",
                        cls="card bg-base-100 shadow p-4 hover:shadow-lg transition-shadow block mb-3"
                    ),
                    A(
                        Div(
                            UkIcon("help-circle", width="24", height="24", cls="mr-3"),
                            Div(
                                H4("Quiz Builder", cls="font-bold"),
                                P("Create quizzes and assessments", cls="text-sm text-gray-600"),
                            ),
                            cls="flex items-center"
                        ),
                        href=f"{BASE}/instructor/quizzes",
                        cls="card bg-base-100 shadow p-4 hover:shadow-lg transition-shadow block mb-3"
                    ),
                    A(
                        Div(
                            UkIcon("award", width="24", height="24", cls="mr-3"),
                            Div(
                                H4("Certificate Templates", cls="font-bold"),
                                P("Design completion certificates", cls="text-sm text-gray-600"),
                            ),
                            cls="flex items-center"
                        ),
                        href=f"{BASE}/instructor/certificates",
                        cls="card bg-base-100 shadow p-4 hover:shadow-lg transition-shadow block mb-3"
                    ),
                    A(
                        Div(
                            UkIcon("file-text", width="24", height="24", cls="mr-3"),
                            Div(
                                H4("Course Materials", cls="font-bold"),
                                P("Upload PDFs, resources, and downloads", cls="text-sm text-gray-600"),
                            ),
                            cls="flex items-center"
                        ),
                        href=f"{BASE}/instructor/materials",
                        cls="card bg-base-100 shadow p-4 hover:shadow-lg transition-shadow block mb-3"
                    ),
                    A(
                        Div(
                            UkIcon("message-square", width="24", height="24", cls="mr-3"),
                            Div(
                                H4("Student Reviews", cls="font-bold"),
                                P(f"{metrics.get('pending_reviews', 0)} pending responses", cls="text-sm text-gray-600"),
                            ),
                            cls="flex items-center"
                        ),
                        href=f"{BASE}/instructor/reviews",
                        cls="card bg-base-100 shadow p-4 hover:shadow-lg transition-shadow block mb-3"
                    ),
                ),
                cls="lg:w-1/2"
            ),
            
            # Right Column - Recent Activity
            Div(
                H2("Recent Enrollments", cls="text-xl font-bold mb-4"),
                Div(
                    *[
                        Div(
                            Div(
                                Div(
                                    Span(e["student"][:2].upper(), cls="font-bold text-white"),
                                    cls="w-10 h-10 rounded-full bg-primary flex items-center justify-center mr-3"
                                ),
                                Div(
                                    P(e["student"], cls="font-semibold"),
                                    P(e["course"], cls="text-sm text-gray-600"),
                                ),
                                cls="flex items-center"
                            ),
                            Span(e["time"], cls="text-xs text-gray-500"),
                            cls="flex justify-between items-center p-3 border-b last:border-b-0"
                        )
                        for e in [
                            {"student": "john@example.com", "course": "Python Masterclass", "time": "2 hours ago"},
                            {"student": "jane@example.com", "course": "Web Development", "time": "5 hours ago"},
                            {"student": "bob@example.com", "course": "Data Science 101", "time": "Yesterday"},
                            {"student": "alice@example.com", "course": "Python Masterclass", "time": "Yesterday"},
                            {"student": "charlie@example.com", "course": "Machine Learning", "time": "2 days ago"},
                        ]
                    ],
                    A("View All Students →", href=f"{BASE}/instructor/students", cls="block text-center p-3 link link-primary"),
                    cls="card bg-base-100 shadow"
                ),
                
                # Quick Stats
                H2("Course Performance", cls="text-xl font-bold mt-6 mb-4"),
                Div(
                    *[
                        Div(
                            Div(
                                H4(c["name"], cls="font-semibold"),
                                P(f"{c['students']} students", cls="text-sm text-gray-600"),
                                cls="flex-1"
                            ),
                            Div(
                                Div(
                                    Div(cls="bg-primary h-2 rounded", style=f"width: {c['completion']}%"),
                                    cls="w-24 bg-base-300 rounded h-2"
                                ),
                                Span(f"{c['completion']}%", cls="text-xs text-gray-600 ml-2"),
                                cls="flex items-center"
                            ),
                            cls="flex justify-between items-center p-3 border-b last:border-b-0"
                        )
                        for c in [
                            {"name": "Python Masterclass", "students": 89, "completion": 72},
                            {"name": "Web Development", "students": 56, "completion": 65},
                            {"name": "Data Science 101", "students": 34, "completion": 58},
                        ]
                    ],
                    cls="card bg-base-100 shadow"
                ),
                cls="lg:w-1/2"
            ),
            
            cls="flex flex-col lg:flex-row gap-8 mb-8"
        ),
        
        # Create New Section
        H2("Create New", cls="text-2xl font-bold mb-4"),
        Div(
            A(
                Div(
                    UkIcon("plus-circle", width="32", height="32", cls="text-primary mb-2"),
                    H4("New Course", cls="font-bold"),
                    P("Create a new course from scratch", cls="text-sm text-gray-600"),
                    cls="p-4 text-center"
                ),
                href=f"{BASE}/instructor/courses/new",
                cls="card bg-base-100 shadow hover:shadow-lg transition-shadow"
            ),
            A(
                Div(
                    UkIcon("upload", width="32", height="32", cls="text-secondary mb-2"),
                    H4("Upload Lesson", cls="font-bold"),
                    P("Add a new lesson to existing course", cls="text-sm text-gray-600"),
                    cls="p-4 text-center"
                ),
                href=f"{BASE}/instructor/lessons/upload",
                cls="card bg-base-100 shadow hover:shadow-lg transition-shadow"
            ),
            A(
                Div(
                    UkIcon("clipboard", width="32", height="32", cls="text-accent mb-2"),
                    H4("Create Quiz", cls="font-bold"),
                    P("Build a new assessment", cls="text-sm text-gray-600"),
                    cls="p-4 text-center"
                ),
                href=f"{BASE}/instructor/quizzes/new",
                cls="card bg-base-100 shadow hover:shadow-lg transition-shadow"
            ),
            A(
                Div(
                    UkIcon("file-plus", width="32", height="32", cls="text-neutral mb-2"),
                    H4("Certificate Template", cls="font-bold"),
                    P("Design a new certificate", cls="text-sm text-gray-600"),
                    cls="p-4 text-center"
                ),
                href=f"{BASE}/instructor/certificates/new",
                cls="card bg-base-100 shadow hover:shadow-lg transition-shadow"
            ),
            cls="grid grid-cols-2 lg:grid-cols-4 gap-4"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="Instructor Dashboard | LMS", user=user, show_auth=True, demo=demo)


def LessonManagerPage(user: dict, courses: List[dict], demo: bool = False):
    """Lesson management page for instructors."""
    BASE = "/lms-example"
    
    content = Div(
        # Header
        Div(
            A("← Back to Dashboard", href=f"{BASE}/instructor", cls="btn btn-ghost btn-sm mb-4"),
            Div(
                H1("Lesson Manager", cls="text-3xl font-bold"),
                A("+ Upload Lesson", href=f"{BASE}/instructor/lessons/upload", cls="btn btn-primary"),
                cls="flex justify-between items-center"
            ),
            cls="mb-6"
        ),
        
        # Course selector
        Div(
            Label("Select Course:", cls="label"),
            Select(
                Option("All Courses", value=""),
                *[Option(c["title"], value=str(c["id"])) for c in courses],
                cls="select select-bordered w-64",
                hx_get=f"{BASE}/instructor/lessons/list",
                hx_target="#lessons-list",
                hx_trigger="change",
                name="course_id"
            ),
            cls="mb-6"
        ),
        
        # Lessons list
        Div(
            H2("Lessons", cls="text-xl font-bold mb-4"),
            Div(
                P("Select a course to view lessons", cls="text-gray-600 text-center py-8"),
                id="lessons-list"
            ),
            cls="card bg-base-100 shadow p-4"
        ),
        
        # Upload tips
        Div(
            H3("Supported Formats", cls="text-lg font-bold mb-2"),
            Div(
                Div(
                    UkIcon("video", width="20", height="20", cls="mr-2"),
                    Span("Video: MP4, WebM, MOV", cls="text-sm"),
                    cls="flex items-center"
                ),
                Div(
                    UkIcon("file-text", width="20", height="20", cls="mr-2"),
                    Span("Documents: PDF, DOCX", cls="text-sm"),
                    cls="flex items-center"
                ),
                Div(
                    UkIcon("image", width="20", height="20", cls="mr-2"),
                    Span("Images: PNG, JPG, GIF", cls="text-sm"),
                    cls="flex items-center"
                ),
                cls="flex gap-6"
            ),
            cls="mt-8 p-4 bg-base-200 rounded-lg"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="Lesson Manager | LMS", user=user, show_auth=True, demo=demo)


def QuizBuilderPage(user: dict, demo: bool = False):
    """Quiz builder page for instructors."""
    BASE = "/lms-example"
    
    content = Div(
        # Header
        Div(
            A("← Back to Dashboard", href=f"{BASE}/instructor", cls="btn btn-ghost btn-sm mb-4"),
            Div(
                H1("Quiz Builder", cls="text-3xl font-bold"),
                A("+ Create Quiz", href=f"{BASE}/instructor/quizzes/new", cls="btn btn-primary"),
                cls="flex justify-between items-center"
            ),
            cls="mb-6"
        ),
        
        # Existing quizzes
        H2("Your Quizzes", cls="text-xl font-bold mb-4"),
        Div(
            *[
                Div(
                    Div(
                        H3(q["name"], cls="font-bold"),
                        P(f"{q['questions']} questions • {q['course']}", cls="text-sm text-gray-600"),
                        cls="flex-1"
                    ),
                    Div(
                        Span(q["status"], cls=f"badge {'badge-success' if q['status'] == 'Published' else 'badge-warning'} mr-2"),
                        A("Edit", href=f"{BASE}/instructor/quizzes/{q['id']}", cls="btn btn-ghost btn-sm"),
                        cls="flex items-center"
                    ),
                    cls="flex justify-between items-center p-4 border-b last:border-b-0"
                )
                for q in [
                    {"id": 1, "name": "Python Basics Quiz", "questions": 10, "course": "Python Masterclass", "status": "Published"},
                    {"id": 2, "name": "HTML/CSS Assessment", "questions": 15, "course": "Web Development", "status": "Draft"},
                    {"id": 3, "name": "Data Types Quiz", "questions": 8, "course": "Data Science 101", "status": "Published"},
                ]
            ],
            cls="card bg-base-100 shadow"
        ),
        
        # Question types
        H2("Question Types", cls="text-xl font-bold mt-8 mb-4"),
        Div(
            Div(
                UkIcon("check-circle", width="24", height="24", cls="text-primary mb-2"),
                H4("Multiple Choice", cls="font-bold"),
                P("Single correct answer", cls="text-sm text-gray-600"),
                cls="p-4 text-center"
            ),
            Div(
                UkIcon("check-square", width="24", height="24", cls="text-secondary mb-2"),
                H4("Multi-Select", cls="font-bold"),
                P("Multiple correct answers", cls="text-sm text-gray-600"),
                cls="p-4 text-center"
            ),
            Div(
                UkIcon("type", width="24", height="24", cls="text-accent mb-2"),
                H4("Short Answer", cls="font-bold"),
                P("Text-based response", cls="text-sm text-gray-600"),
                cls="p-4 text-center"
            ),
            Div(
                UkIcon("toggle-left", width="24", height="24", cls="text-neutral mb-2"),
                H4("True/False", cls="font-bold"),
                P("Binary choice", cls="text-sm text-gray-600"),
                cls="p-4 text-center"
            ),
            cls="grid grid-cols-2 lg:grid-cols-4 gap-4"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="Quiz Builder | LMS", user=user, show_auth=True, demo=demo)


def CertificateTemplatesPage(user: dict, demo: bool = False):
    """Certificate templates page for instructors."""
    BASE = "/lms-example"
    
    content = Div(
        # Header
        Div(
            A("← Back to Dashboard", href=f"{BASE}/instructor", cls="btn btn-ghost btn-sm mb-4"),
            Div(
                H1("Certificate Templates", cls="text-3xl font-bold"),
                A("+ Create Template", href=f"{BASE}/instructor/certificates/new", cls="btn btn-primary"),
                cls="flex justify-between items-center"
            ),
            cls="mb-6"
        ),
        
        # Templates
        H2("Your Templates", cls="text-xl font-bold mb-4"),
        Div(
            *[
                Div(
                    # Preview thumbnail
                    Div(
                        Div(
                            UkIcon("award", width="48", height="48", cls="text-primary"),
                            cls="flex items-center justify-center h-32 bg-gradient-to-br from-primary/10 to-secondary/10"
                        ),
                        cls="rounded-t-lg overflow-hidden"
                    ),
                    Div(
                        H3(t["name"], cls="font-bold mb-1"),
                        P(f"Used in {t['courses']} course(s)", cls="text-sm text-gray-600 mb-2"),
                        Div(
                            A("Edit", href=f"{BASE}/instructor/certificates/{t['id']}", cls="btn btn-ghost btn-xs"),
                            A("Preview", href=f"{BASE}/instructor/certificates/{t['id']}/preview", cls="btn btn-ghost btn-xs"),
                            Button("Duplicate", cls="btn btn-ghost btn-xs"),
                        ),
                        cls="p-4"
                    ),
                    cls="card bg-base-100 shadow"
                )
                for t in [
                    {"id": 1, "name": "Classic Certificate", "courses": 3},
                    {"id": 2, "name": "Modern Badge", "courses": 2},
                    {"id": 3, "name": "Professional Diploma", "courses": 1},
                ]
            ],
            cls="grid grid-cols-1 md:grid-cols-3 gap-6"
        ),
        
        # Template elements
        H2("Template Elements", cls="text-xl font-bold mt-8 mb-4"),
        Div(
            Div(
                UkIcon("user", width="20", height="20", cls="mr-2"),
                Span("{{student_name}}", cls="font-mono text-sm"),
                P("Student's full name", cls="text-xs text-gray-500"),
                cls="p-3 bg-base-200 rounded"
            ),
            Div(
                UkIcon("book", width="20", height="20", cls="mr-2"),
                Span("{{course_name}}", cls="font-mono text-sm"),
                P("Course title", cls="text-xs text-gray-500"),
                cls="p-3 bg-base-200 rounded"
            ),
            Div(
                UkIcon("calendar", width="20", height="20", cls="mr-2"),
                Span("{{completion_date}}", cls="font-mono text-sm"),
                P("Date of completion", cls="text-xs text-gray-500"),
                cls="p-3 bg-base-200 rounded"
            ),
            Div(
                UkIcon("hash", width="20", height="20", cls="mr-2"),
                Span("{{certificate_id}}", cls="font-mono text-sm"),
                P("Unique certificate ID", cls="text-xs text-gray-500"),
                cls="p-3 bg-base-200 rounded"
            ),
            cls="grid grid-cols-2 lg:grid-cols-4 gap-4"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="Certificates | LMS", user=user, show_auth=True, demo=demo)
