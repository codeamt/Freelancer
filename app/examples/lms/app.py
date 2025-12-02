"""
LMS Example Application

Standalone learning management system demonstrating auth integration.
Can be mounted at any endpoint (e.g., /lms-example).
"""
from fasthtml.common import *
from monsterui.all import *
from core.utils.logger import get_logger
from core.ui.layout import Layout
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from add_ons.auth.services import AuthService
from core.services.db import DBService

logger = get_logger(__name__)

# Sample courses
COURSES = [
    {
        "id": 1,
        "title": "Platform Orientation - Free Course",
        "description": "Get started with our learning platform - completely free!",
        "instructor": "Platform Team",
        "duration": "30 minutes",
        "level": "Beginner",
        "price": 0.00,
        "image": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=1170&auto=format&fit=crop",
        "enrolled": 5420,
        "rating": 4.9,
        "lessons": 5,
        "long_description": "Welcome to our learning platform! This free orientation course will help you navigate the platform, understand how courses work, track your progress, and get the most out of your learning experience.",
        "syllabus": [
            {"title": "Welcome & Platform Overview", "duration": "5 min"},
            {"title": "Navigating Courses", "duration": "5 min"},
            {"title": "Tracking Your Progress", "duration": "5 min"},
            {"title": "Getting Help & Support", "duration": "5 min"},
            {"title": "Next Steps", "duration": "10 min"}
        ]
    },
    {
        "id": 2,
        "title": "Introduction to Python",
        "description": "Learn Python programming from scratch with hands-on projects",
        "instructor": "Dr. Sarah Johnson",
        "duration": "8 weeks",
        "level": "Beginner",
        "price": 49.99,
        "image": "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?q=80&w=1632&auto=format&fit=crop",
        "enrolled": 1250,
        "rating": 4.8,
        "lessons": 42,
        "long_description": "Master Python programming from the ground up. This comprehensive course covers variables, data types, functions, OOP, file handling, web scraping, and data analysis.",
        "syllabus": [
            {"title": "Python Basics", "duration": "2 weeks"},
            {"title": "Functions & Modules", "duration": "2 weeks"},
            {"title": "Object-Oriented Programming", "duration": "2 weeks"},
            {"title": "Advanced Topics & Projects", "duration": "2 weeks"}
        ]
    },
    {
        "id": 3,
        "title": "Web Development Bootcamp",
        "description": "Master HTML, CSS, JavaScript, and modern frameworks",
        "instructor": "Mike Chen",
        "duration": "12 weeks",
        "level": "Intermediate",
        "price": 79.99,
        "image": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?q=80&w=1744&auto=format&fit=crop",
        "enrolled": 2100,
        "rating": 4.9,
        "lessons": 68,
        "long_description": "Become a full-stack web developer with our comprehensive bootcamp. Learn HTML5, CSS3, JavaScript ES6+, React, Node.js, Express, MongoDB, and deploy real-world applications.",
        "syllabus": [
            {"title": "HTML & CSS Fundamentals", "duration": "3 weeks"},
            {"title": "JavaScript & DOM Manipulation", "duration": "3 weeks"},
            {"title": "React & Modern Frontend", "duration": "3 weeks"},
            {"title": "Backend & Full-Stack Projects", "duration": "3 weeks"}
        ]
    },
    {
        "id": 4,
        "title": "Data Science Fundamentals",
        "description": "Learn data analysis, visualization, and machine learning basics",
        "instructor": "Prof. Emily Rodriguez",
        "duration": "10 weeks",
        "level": "Intermediate",
        "price": 99.99,
        "image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1170&auto=format&fit=crop",
        "enrolled": 890,
        "rating": 4.7,
        "lessons": 55,
        "long_description": "Master data science fundamentals including Python for data analysis, pandas, NumPy, matplotlib, seaborn, and introduction to machine learning with scikit-learn.",
        "syllabus": [
            {"title": "Python for Data Analysis", "duration": "2 weeks"},
            {"title": "Data Visualization", "duration": "2 weeks"},
            {"title": "Statistical Analysis", "duration": "3 weeks"},
            {"title": "Machine Learning Basics", "duration": "3 weeks"}
        ]
    },
    {
        "id": 5,
        "title": "Mobile App Development",
        "description": "Build iOS and Android apps with React Native",
        "instructor": "Alex Kumar",
        "duration": "10 weeks",
        "level": "Advanced",
        "price": 89.99,
        "image": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?q=80&w=1740&auto=format&fit=crop",
        "enrolled": 650,
        "rating": 4.6,
        "lessons": 48,
        "long_description": "Build professional cross-platform mobile applications for iOS and Android using React Native. Learn navigation, state management, API integration, and app deployment.",
        "syllabus": [
            {"title": "React Native Basics", "duration": "2 weeks"},
            {"title": "Navigation & State Management", "duration": "3 weeks"},
            {"title": "API Integration & Storage", "duration": "2 weeks"},
            {"title": "Publishing & Deployment", "duration": "3 weeks"}
        ]
    }
]


def create_lms_app():
    """Create and configure the LMS example app"""
    
    # Initialize services
    db_service = DBService()
    auth_service = AuthService(db_service)
    
    # Create FastHTML app
    app = FastHTML(hdrs=[*Theme.slate.headers()])
    
    # In-memory enrollment storage (in production, use database)
    enrollments = {}
    
    async def get_current_user(request: Request):
        """Get current user from request"""
        try:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                user_data = auth_service.verify_token(token)
                if user_data:
                    return await auth_service.get_user_by_id(user_data.get("sub"))
            
            # Try cookie
            token = request.cookies.get("auth_token")
            if token:
                user_data = auth_service.verify_token(token)
                if user_data:
                    return await auth_service.get_user_by_id(user_data.get("sub"))
            
            return None
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    @app.get("/")
    async def lms_home(request: Request):
        """Main LMS page with course catalog"""
        user = await get_current_user(request)
        
        # Get user enrollments
        user_enrollments = []
        if user:
            user_enrollments = enrollments.get(user.get("_id"), [])
        
        content = Div(
            # Header
            Div(
                H1("📚 LMS Example", cls="text-4xl font-bold mb-2"),
                P("Learn new skills with our comprehensive courses", cls="text-xl text-gray-500 mb-4"),
                Div(
                    Span("✓ Public course catalog", cls="badge badge-success mr-2"),
                    Span("✓ Auth-protected enrollment", cls="badge badge-info mr-2"),
                    Span("✓ Progress tracking", cls="badge badge-primary"),
                    cls="mb-8"
                ),
                cls="text-center mb-12"
            ),
            
            # User Status
            Div(
                (Div(
                    Span(f"👤 Logged in as: {user.get('username')}", cls="font-semibold mr-4"),
                    Span(f"Enrolled in {len(user_enrollments)} courses", cls="text-sm text-gray-500 mr-4"),
                    A("My Courses", href="/lms-example/my-courses", cls="btn btn-sm btn-primary mr-2"),
                    A("Logout", href="/auth/logout", cls="link link-primary"),
                    cls="flex items-center justify-center mb-8"
                ) if user else Div(
                    Span("👋 Not logged in", cls="text-gray-500 mr-4"),
                    A("Sign In", href="/auth/login?redirect=/lms-example", cls="btn btn-sm btn-primary mr-2"),
                    A("Register", href="/auth/register?redirect=/lms-example", cls="btn btn-sm btn-outline"),
                    cls="flex items-center justify-center mb-8"
                ))
            ),
            
            # Course Catalog
            Div(
                H2("Course Catalog", cls="text-2xl font-bold mb-6"),
                Div(
                    *[CourseCard(course, user, user_enrollments) for course in COURSES],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6 mb-12"
                ),
            ),
            
            # Features Section
            Div(
                H2("Platform Features", cls="text-2xl font-bold mb-6 text-center"),
                Div(
                    FeatureCard("📖", "Rich Content", "Video lessons, quizzes, and downloadable resources"),
                    FeatureCard("🎯", "Progress Tracking", "Track your learning progress and achievements"),
                    FeatureCard("👥", "Expert Instructors", "Learn from industry professionals"),
                    FeatureCard("📱", "Mobile Friendly", "Learn anywhere, anytime on any device"),
                    FeatureCard("💬", "Discussion Forums", "Connect with peers and instructors"),
                    FeatureCard("🏆", "Certificates", "Earn certificates upon course completion"),
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8"
                ),
                cls="mt-16 mb-8"
            )
        )
        
        return Layout(content, title="LMS Example | FastApp")
    
    @app.get("/course/{course_id}")
    async def course_detail(request: Request, course_id: int):
        """Course detail page"""
        user = await get_current_user(request)
        
        # Find course
        course = next((c for c in COURSES if c["id"] == course_id), None)
        if not course:
            return Layout(
                Div(
                    H1("Course Not Found", cls="text-3xl font-bold mb-4"),
                    A("← Back to Courses", href="/lms-example", cls="btn btn-primary"),
                    cls="text-center py-16"
                ),
                title="Course Not Found"
            )
        
        # Check if enrolled
        is_enrolled = False
        if user:
            user_enrollments = enrollments.get(user.get("_id"), [])
            is_enrolled = course_id in user_enrollments
        
        is_free = course["price"] == 0
        
        content = Div(
            # Back button
            A(
                UkIcon("arrow-left", width="20", height="20", cls="mr-2"),
                "Back to Courses",
                href="/lms-example",
                cls="btn btn-ghost mb-6"
            ),
            
            # Course detail
            Div(
                # Course image
                Div(
                    Img(
                        src=course["image"],
                        alt=course["title"],
                        cls="w-full h-96 object-cover rounded-lg shadow-lg"
                    ),
                    cls="lg:col-span-1"
                ),
                
                # Course info
                Div(
                    # Level badge
                    Span(course["level"], cls=f"badge {'badge-success' if is_free else 'badge-primary'} mb-4"),
                    
                    # Title
                    H1(course["title"], cls="text-4xl font-bold mb-4"),
                    
                    # Instructor
                    Div(
                        UkIcon("user", width="20", height="20", cls="inline mr-2"),
                        Span(f"Instructor: {course['instructor']}", cls="text-lg text-gray-600"),
                        cls="mb-4"
                    ),
                    
                    # Stats
                    Div(
                        Div(
                            UkIcon("clock", width="20", height="20", cls="inline mr-2 text-blue-500"),
                            Span(course["duration"], cls="font-semibold"),
                            cls="mr-6"
                        ),
                        Div(
                            UkIcon("book", width="20", height="20", cls="inline mr-2 text-green-500"),
                            Span(f"{course['lessons']} lessons", cls="font-semibold"),
                            cls="mr-6"
                        ),
                        Div(
                            UkIcon("star", width="20", height="20", cls="inline mr-2 text-yellow-500"),
                            Span(f"{course['rating']}/5.0", cls="font-semibold"),
                            cls="mr-6"
                        ),
                        Div(
                            UkIcon("users", width="20", height="20", cls="inline mr-2 text-purple-500"),
                            Span(f"{course['enrolled']:,} students", cls="font-semibold"),
                        ),
                        cls="flex flex-wrap items-center mb-6"
                    ),
                    
                    # Price
                    Div(
                        (Span("FREE", cls="text-4xl font-bold text-green-600") if is_free
                         else Span(f"${course['price']}", cls="text-4xl font-bold text-blue-600")),
                        cls="mb-6"
                    ),
                    
                    # Description
                    P(course.get("long_description", course["description"]), cls="text-lg text-gray-600 mb-6"),
                    
                    # Syllabus
                    (Div(
                        H3("Course Syllabus:", cls="text-xl font-semibold mb-3"),
                        Div(
                            *[Div(
                                Div(
                                    UkIcon("check-circle", width="20", height="20", cls="text-green-500"),
                                    cls="mr-3"
                                ),
                                Div(
                                    P(item["title"], cls="font-semibold"),
                                    P(item["duration"], cls="text-sm text-gray-500"),
                                    cls="flex-1"
                                ),
                                cls="flex items-start p-3 bg-base-200 rounded-lg"
                            ) for item in course.get("syllabus", [])],
                            cls="space-y-2 mb-6"
                        )
                    ) if course.get("syllabus") else None),
                    
                    # Enrollment button
                    Div(id="enroll-action", cls="mb-4"),
                    (Div(
                        Span("✓ Enrolled", cls="badge badge-success badge-lg py-4 px-6"),
                        A("Start Learning", href="/lms-example/my-courses", cls="btn btn-primary btn-lg ml-4"),
                        cls="flex items-center"
                    ) if is_enrolled else (
                        Button(
                            UkIcon("play-circle", width="20", height="20", cls="mr-2"),
                            "Enroll Now" if course["price"] > 0 else "Start Free Course",
                            cls="btn btn-primary btn-lg",
                            hx_post=f"/lms-example/enroll/{course_id}",
                            hx_target="#enroll-action",
                            hx_swap="innerHTML"
                        ) if user else A(
                            UkIcon("lock", width="20", height="20", cls="mr-2"),
                            "Sign in to enroll",
                            href=f"/auth/login?redirect=/lms-example/course/{course_id}",
                            cls="btn btn-primary btn-lg"
                        )
                    )),
                    
                    cls="lg:col-span-1"
                ),
                
                cls="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12"
            )
        )
        
        return Layout(content, title=f"{course['title']} | LMS")
    
    @app.get("/my-courses")
    async def my_courses(request: Request):
        """User's enrolled courses"""
        user = await get_current_user(request)
        
        if not user:
            return RedirectResponse("/auth/login?redirect=/lms-example/my-courses")
        
        user_enrollments = enrollments.get(user.get("_id"), [])
        enrolled_courses = [c for c in COURSES if c["id"] in user_enrollments]
        
        content = Div(
            H1("My Courses", cls="text-3xl font-bold mb-8"),
            
            (Div(
                *[EnrolledCourseCard(course) for course in enrolled_courses],
                cls="grid grid-cols-1 md:grid-cols-2 gap-6"
            ) if enrolled_courses else Div(
                Card(
                    Div(
                        UkIcon("book", width="48", height="48", cls="text-gray-400 mb-4"),
                        H3("No courses yet", cls="text-xl font-semibold mb-2"),
                        P("Browse the catalog and enroll in a course to get started!", cls="text-gray-500 mb-4"),
                        A("Browse Courses", href="/lms-example", cls="btn btn-primary"),
                        cls="text-center p-12"
                    )
                )
            ))
        )
        
        return Layout(content, title="My Courses | FastApp")
    
    @app.post("/enroll/{course_id}")
    async def enroll_course(request: Request, course_id: int):
        """Enroll in a course (requires auth)"""
        user = await get_current_user(request)
        
        if not user:
            return Div(
                P("⚠️ Please sign in to enroll in courses", cls="text-warning"),
                A("Sign In", href="/auth/login?redirect=/lms-example", cls="btn btn-sm btn-primary mt-2"),
                cls="alert alert-warning"
            )
        
        # Find course
        course = next((c for c in COURSES if c["id"] == course_id), None)
        if not course:
            return Div(
                P("❌ Course not found", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Check if already enrolled
        user_id = user.get("_id")
        if user_id not in enrollments:
            enrollments[user_id] = []
        
        if course_id in enrollments[user_id]:
            return Div(
                P("ℹ️ You're already enrolled in this course", cls="text-info"),
                cls="alert alert-info"
            )
        
        # Enroll user
        enrollments[user_id].append(course_id)
        logger.info(f"User {user_id} enrolled in course {course_id}")
        
        return Div(
            Div(
                P(f"✓ Successfully enrolled in {course['title']}!", cls="text-success"),
                A("Go to My Courses", href="/lms-example/my-courses", cls="btn btn-sm btn-primary mt-2"),
                cls="alert alert-success"
            ),
            Script("""
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            """)
        )
    
    def CourseCard(course: dict, user: dict = None, enrollments: list = None):
        """Course card component"""
        is_enrolled = enrollments and course["id"] in enrollments
        is_free = course["price"] == 0
        
        return Card(
            Div(
                # Course image - clickable
                A(
                    Img(
                        src=course["image"],
                        alt=course["title"],
                        cls="w-full h-48 object-cover rounded-t-lg hover:opacity-90 transition-opacity"
                    ),
                    href=f"/lms-example/course/{course['id']}"
                ),
                # Course info
                Div(
                    Div(
                        Span(course["level"], cls=f"badge badge-sm {'badge-success' if is_free else 'badge-outline'} mr-2"),
                        Span(f"{course['duration']}", cls="badge badge-sm badge-ghost"),
                        cls="mb-2"
                    ),
                    A(
                        H3(course["title"], cls="text-lg font-semibold mb-2 hover:text-blue-600 transition-colors"),
                        href=f"/lms-example/course/{course['id']}"
                    ),
                    P(course["description"], cls="text-sm text-gray-500 mb-4 line-clamp-2"),
                    
                    # Course meta
                    Div(
                        Div(
                            UkIcon("user", width="16", height="16", cls="inline mr-1"),
                            Span(course["instructor"], cls="text-xs"),
                            cls="mr-3"
                        ),
                        Div(
                            UkIcon("star", width="16", height="16", cls="inline mr-1"),
                            Span(f"{course['rating']}", cls="text-xs"),
                            cls="mr-3"
                        ),
                        Div(
                            UkIcon("users", width="16", height="16", cls="inline mr-1"),
                            Span(f"{course['enrolled']}", cls="text-xs"),
                        ),
                        cls="flex items-center text-gray-600 mb-4 text-sm"
                    ),
                    
                    Div(
                        (Span("FREE", cls="text-xl font-bold text-green-600") if is_free
                         else Span(f"${course['price']}", cls="text-xl font-bold text-blue-600")),
                        Span(f"{course['lessons']} lessons", cls="text-sm text-gray-500"),
                        cls="flex justify-between items-center mb-4"
                    ),
                    
                    # View details button
                    A(
                        UkIcon("eye", width="16", height="16", cls="mr-2"),
                        "View Details",
                        href=f"/lms-example/course/{course['id']}",
                        cls="btn btn-primary btn-sm w-full"
                    ),
                    
                    cls="p-4"
                ),
                cls="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow"
            )
        )
    
    def EnrolledCourseCard(course: dict):
        """Enrolled course card with progress"""
        return Card(
            Div(
                Img(src=course["image"], alt=course["title"], cls="w-full h-32 object-cover rounded-t-lg"),
                Div(
                    H3(course["title"], cls="font-semibold mb-2"),
                    P(f"Instructor: {course['instructor']}", cls="text-sm text-gray-500 mb-2"),
                    
                    # Progress bar
                    Div(
                        Div(
                            Span("Progress: 0%", cls="text-xs"),
                            cls="mb-1"
                        ),
                        Div(
                            Div(cls="bg-blue-600 h-2 rounded", style="width: 0%"),
                            cls="bg-gray-200 h-2 rounded mb-4"
                        ),
                    ),
                    
                    A("Continue Learning →", href=f"/lms-example/course/{course['id']}", cls="btn btn-primary btn-sm w-full"),
                    cls="p-4"
                ),
                cls="hover:shadow-lg transition-shadow"
            )
        )
    
    def FeatureCard(icon: str, title: str, description: str):
        """Feature card component"""
        return Card(
            Div(
                Div(icon, cls="text-4xl mb-3 text-center"),
                H3(title, cls="text-lg font-semibold mb-2 text-center"),
                P(description, cls="text-sm text-gray-500 text-center"),
                cls="p-6 text-center"
            ),
            cls="hover:shadow-lg transition-shadow"
        )
    
    return app
