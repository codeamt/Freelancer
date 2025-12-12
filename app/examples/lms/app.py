"""
LMS Example Application (Refactored)

Demonstrates how to build an LMS example by importing from domains and services.
No duplication - uses shared data and services.
"""
from fasthtml.common import *
from monsterui.all import *
from core.utils.logger import get_logger
from core.ui.layout import Layout

# Import shared services (no recreation!)
from core.services import AuthService, get_current_user, SearchService

# Import shared data from LMS domain
from add_ons.domains.lms.data import SAMPLE_COURSES, get_course_by_id, get_free_courses

# Import custom auth UI and certificate generator for this example
from .ui import LMSLoginPage, LMSRegisterPage
# from add_ons.domains.lms.services.certificate_generator import CertificateGenerator  # TODO: Fix circular import

logger = get_logger(__name__)


def create_lms_app(auth_service=None, user_service=None, postgres=None, mongodb=None, redis=None):
    """Create LMS example app"""
    
    # Initialize services (shared, not recreated)
    search_service = SearchService()
    # cert_generator = CertificateGenerator()  # TODO: Fix circular import
    
    # Create app with MonsterUI theme
    app = FastHTML(hdrs=[*Theme.violet.headers(mode="light")])
    
    # In-memory enrollment storage (in production, use database)
    enrollments = {}  # {user_id: [course_ids]}
    
    # Base path for this mounted app
    BASE = "/lms-example"
    
    async def get_user(request: Request):
        """Get current user from request"""
        return await get_current_user(request, auth_service)
    
    # -----------------------------------------------------------------------------
    # Routes
    # -----------------------------------------------------------------------------
    
    @app.get("/")
    async def home(request: Request):
        """LMS homepage"""
        user = await get_user(request)
        
        # Get free courses for promotion
        free_courses = get_free_courses()
        
        content = Div(
            # Hero Section
            Div(
                H1("Learn Anything, Anytime", cls="text-5xl font-bold mb-4"),
                P("Access thousands of courses from expert instructors", cls="text-xl text-gray-500 mb-8"),
                Div(
                    A("Browse Courses", href="courses", cls="btn btn-primary btn-lg mr-4"),
                    (A("My Courses", href="student/dashboard", cls="btn btn-outline btn-lg") if user else
                     A("Sign Up Free", href="register", cls="btn btn-outline btn-lg")),
                    cls="flex gap-4 justify-center"
                ),
                cls="text-center py-20 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg mb-12"
            ),
            
            # Free Courses Section
            (Div(
                H2("Start Learning for Free", cls="text-3xl font-bold mb-6"),
                Div(
                    *[CourseCard(course, user, enrollments) for course in free_courses],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                ),
                cls="mb-12"
            ) if free_courses else None),
            
            # All Courses Section
            Div(
                H2("Popular Courses", cls="text-3xl font-bold mb-6"),
                Div(
                    *[CourseCard(course, user, enrollments) for course in SAMPLE_COURSES[:6]],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                ),
                cls="mb-12"
            ),
            
            # Stats Section
            Div(
                Div(
                    Div(
                        H3("10,000+", cls="text-4xl font-bold text-blue-600"),
                        P("Students Enrolled", cls="text-gray-600"),
                        cls="text-center"
                    ),
                    Div(
                        H3("500+", cls="text-4xl font-bold text-blue-600"),
                        P("Courses Available", cls="text-gray-600"),
                        cls="text-center"
                    ),
                    Div(
                        H3("50+", cls="text-4xl font-bold text-blue-600"),
                        P("Expert Instructors", cls="text-gray-600"),
                        cls="text-center"
                    ),
                    cls="grid grid-cols-1 md:grid-cols-3 gap-8"
                ),
                cls="bg-base-200 p-12 rounded-lg"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title="LMS | Learn Online")
    
    
    @app.get("/courses")
    async def courses_page(request: Request):
        """All courses page"""
        user = await get_user(request)
        
        content = Div(
            H1("All Courses", cls="text-4xl font-bold mb-8"),
            
            # Search bar
            Form(
                Input(
                    type="text",
                    name="q",
                    placeholder="Search courses...",
                    cls="input input-bordered w-full",
                    hx_get="/courses/search",
                    hx_trigger="keyup changed delay:500ms",
                    hx_target="#course-results"
                ),
                cls="mb-8"
            ),
            
            # Course grid (using shared data!)
            Div(
                *[CourseCard(course, user, enrollments) for course in SAMPLE_COURSES],
                id="course-results",
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title="All Courses | LMS")
    
    
    @app.get("/courses/search")
    async def search_courses(request: Request, q: str = ""):
        """Search courses"""
        user = await get_user(request)
        
        if not q:
            courses = SAMPLE_COURSES
        else:
            # Use shared SearchService
            results = search_service.search(q, SAMPLE_COURSES, ["title", "description", "instructor"])
            courses = results
        
        return Div(
            *[CourseCard(course, user, enrollments) for course in courses],
            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        )
    
    
    @app.get("/course/{course_id}")
    async def course_detail(request: Request, course_id: int):
        """Course detail page"""
        user = await get_user(request)
        
        # Use shared helper function!
        course = get_course_by_id(course_id)
        
        if not course:
            return Layout(
                Div(H1("Course not found"), cls="text-center py-20"),
                title="Not Found"
            )
        
        user_id = user.get("_id") if user else None
        is_enrolled = user_id and user_id in enrollments and course_id in enrollments[user_id]
        
        content = Div(
            # Back button
            A("← Back to Courses", href="courses", cls="btn btn-ghost mb-6"),
            
            # Course header
            Div(
                # Image
                Div(
                    Img(src=course["image"], alt=course["title"], cls="w-full h-64 object-cover rounded-lg"),
                    cls="lg:w-1/2"
                ),
                
                # Info
                Div(
                    Div(
                        Span(course["level"], cls="badge badge-primary mr-2"),
                        Span(f"{course.get('students', 0)} students", cls="text-sm text-gray-500"),
                        cls="mb-4"
                    ),
                    H1(course["title"], cls="text-3xl font-bold mb-4"),
                    P(course["description"], cls="text-lg text-gray-600 mb-4"),
                    
                    # Instructor & Rating
                    Div(
                        Div(
                            UkIcon("user", width="20", height="20", cls="mr-2"),
                            Span(course["instructor"], cls="font-semibold"),
                            cls="flex items-center mb-2"
                        ),
                        Div(
                            UkIcon("star", width="20", height="20", cls="mr-2 text-yellow-500"),
                            Span(f"{course.get('rating', 0)} ({course.get('students', 0)} reviews)", cls="text-gray-600"),
                            cls="flex items-center mb-2"
                        ),
                        Div(
                            UkIcon("clock", width="20", height="20", cls="mr-2"),
                            Span(course["duration"], cls="text-gray-600"),
                            cls="flex items-center"
                        ),
                    ),
                    
                    # Price & Enroll
                    Div(
                        (H2("Free", cls="text-4xl font-bold text-green-600 mb-4") if course["price"] == 0 else
                         H2(f"${course['price']}", cls="text-4xl font-bold text-blue-600 mb-4")),
                        
                        # Enroll button
                        (Div(
                            Span("✓ Enrolled", cls="text-success text-lg font-semibold"),
                            A("Go to Course", href=f"student/course/{course_id}", cls="btn btn-primary btn-lg w-full mt-4"),
                            cls="mb-4"
                        ) if is_enrolled else (
                            Button(
                                "Enroll Now",
                                cls="btn btn-primary btn-lg w-full",
                                hx_post=f"{BASE}/enroll/{course_id}",
                                hx_target="#enroll-result"
                            ) if user else
                            A("Sign in to Enroll", href="login", cls="btn btn-primary btn-lg w-full")
                        )),
                        
                        Div(id="enroll-result", cls="mt-4"),
                        
                        cls="bg-base-200 p-6 rounded-lg mt-6"
                    ),
                    
                    cls="lg:w-1/2"
                ),
                
                cls="flex flex-col lg:flex-row gap-8 mb-12"
            ),
            
            # Course details tabs
            Div(
                # About
                Div(
                    H2("About This Course", cls="text-2xl font-bold mb-4"),
                    P(course.get("long_description", course["description"]), cls="text-gray-700 mb-6"),
                    
                    H3("What You'll Learn", cls="text-xl font-semibold mb-3"),
                    Ul(
                        *[Li(f"✓ {feature}", cls="mb-2") for feature in course.get("features", [])],
                        cls="space-y-2 mb-6"
                    ) if course.get("features") else None,
                    
                    cls="mb-8"
                ),
                
                cls="max-w-4xl"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title=f"{course['title']} | LMS")
    
    
    @app.post("/enroll/{course_id}")
    async def enroll_course(request: Request, course_id: int):
        """Enroll in course"""
        user = await get_user(request)
        
        if not user:
            return Div(
                P("Please sign in to enroll", cls="text-error"),
                cls="alert alert-error"
            )
        
        course = get_course_by_id(course_id)
        if not course:
            return Div(P("Course not found", cls="text-error"), cls="alert alert-error")
        
        user_id = user.get("_id")
        
        # Check if already enrolled
        if user_id in enrollments and course_id in enrollments[user_id]:
            return Div(
                P("You're already enrolled in this course!", cls="text-info"),
                cls="alert alert-info"
            )
        
        # Enroll user (in production: save to database)
        if user_id not in enrollments:
            enrollments[user_id] = []
        enrollments[user_id].append(course_id)
        
        logger.info(f"User {user_id} enrolled in course {course_id}")
        
        return Div(
            P(f"✓ Successfully enrolled in {course['title']}!", cls="text-success"),
            A("Go to My Courses", href="student/dashboard", cls="btn btn-primary mt-4"),
            cls="alert alert-success"
        )
    
    
    @app.get("/student/course/{course_id}")
    async def student_course_view(request: Request, course_id: int):
        """Student course learning page"""
        user = await get_user(request)
        
        if not user:
            return RedirectResponse("/login?redirect=/student/course/{course_id}")
        
        user_id = user.get("_id")
        
        # Check enrollment
        if user_id not in enrollments or course_id not in enrollments[user_id]:
            return RedirectResponse(f"/course/{course_id}")
        
        course = get_course_by_id(course_id)
        if not course:
            return Layout(Div(H1("Course not found"), cls="text-center py-20"), title="Not Found")
        
        # Mock lessons data
        lessons = [
            {"id": 1, "title": "Introduction", "duration": "10 min", "completed": True},
            {"id": 2, "title": "Getting Started", "duration": "15 min", "completed": True},
            {"id": 3, "title": "Core Concepts", "duration": "20 min", "completed": False},
            {"id": 4, "title": "Advanced Topics", "duration": "25 min", "completed": False},
            {"id": 5, "title": "Final Project", "duration": "30 min", "completed": False},
        ]
        
        completed = sum(1 for l in lessons if l["completed"])
        progress = (completed / len(lessons)) * 100
        
        content = Div(
            # Header
            Div(
                A("← Back to Dashboard", href="student/dashboard", cls="btn btn-ghost mb-4"),
                H1(course["title"], cls="text-4xl font-bold mb-2"),
                P(f"by {course['instructor']}", cls="text-gray-600 mb-6"),
                
                # Progress bar
                Div(
                    Div(
                        Span(f"{progress:.0f}% Complete", cls="font-semibold"),
                        Span(f"{completed}/{len(lessons)} lessons", cls="text-sm text-gray-600"),
                        cls="flex justify-between mb-2"
                    ),
                    Progress(value=progress, max=100, cls="progress progress-primary w-full"),
                    cls="mb-8"
                ),
                cls="mb-8"
            ),
            
            # Course content
            Div(
                # Lessons sidebar
                Div(
                    H2("Course Content", cls="text-2xl font-bold mb-4"),
                    Div(
                        *[LessonItem(lesson, course_id) for lesson in lessons],
                        cls="space-y-2"
                    ),
                    cls="lg:w-1/3 bg-base-200 p-6 rounded-lg"
                ),
                
                # Video/content area
                Div(
                    Div(
                        H2("Lesson 1: Introduction", cls="text-2xl font-bold mb-4"),
                        Div(
                            Div("📹 Video Player Placeholder", cls="bg-gray-800 text-white text-center py-32 rounded-lg mb-6"),
                            P("Welcome to the course! In this lesson, we'll cover the basics and get you started.", cls="text-gray-700 mb-4"),
                            Div(
                                Button("← Previous", cls="btn btn-outline", disabled=True),
                                Button("Mark Complete & Next →", cls="btn btn-primary"),
                                cls="flex justify-between"
                            ),
                            cls="bg-base-100 p-6 rounded-lg"
                        ),
                        cls="lg:w-2/3"
                    ),
                    cls="lg:w-2/3"
                ),
                
                cls="flex flex-col lg:flex-row gap-6"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title=f"{course['title']} | Learning")
    
    
    @app.get("/student/dashboard")
    async def student_dashboard(request: Request):
        """Student dashboard"""
        user = await get_user(request)
        
        if not user:
            return RedirectResponse("/login?redirect=/student/dashboard")
        
        user_id = user.get("_id")
        enrolled_course_ids = enrollments.get(user_id, [])
        enrolled_courses = [get_course_by_id(cid) for cid in enrolled_course_ids]
        enrolled_courses = [c for c in enrolled_courses if c]  # Filter None
        
        content = Div(
            H1("My Learning Dashboard", cls="text-4xl font-bold mb-8"),
            
            # Stats
            Div(
                Div(
                    H3(str(len(enrolled_courses)), cls="text-3xl font-bold text-blue-600"),
                    P("Enrolled Courses", cls="text-gray-600"),
                    cls="stat"
                ),
                Div(
                    H3("0", cls="text-3xl font-bold text-green-600"),
                    P("Completed", cls="text-gray-600"),
                    cls="stat"
                ),
                Div(
                    H3("0", cls="text-3xl font-bold text-purple-600"),
                    P("Certificates", cls="text-gray-600"),
                    cls="stat"
                ),
                cls="stats shadow mb-8"
            ),
            
            # Enrolled courses
            (Div(
                H2("My Courses", cls="text-2xl font-bold mb-6"),
                Div(
                    *[CourseCard(course, user, enrollments, show_progress=True) for course in enrolled_courses],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                )
            ) if enrolled_courses else Div(
                H2("No Courses Yet", cls="text-2xl font-bold mb-4"),
                P("Start learning by enrolling in a course!", cls="text-gray-600 mb-6"),
                A("Browse Courses", href="courses", cls="btn btn-primary"),
                cls="text-center py-12"
            )),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title="My Dashboard | LMS")
    
    
    # -----------------------------------------------------------------------------
    # Auth Routes (using custom UI)
    # -----------------------------------------------------------------------------
    
    @app.get("/login")
    async def login_page(request: Request):
        """Login page with custom UI"""
        return LMSLoginPage()
    
    
    @app.get("/register")
    async def register_page(request: Request):
        """Register page with custom UI"""
        return LMSRegisterPage()
    
    
    @app.post("/auth/login")
    async def login(request: Request):
        """Handle login (uses shared AuthService!)"""
        form = await request.form()
        email = form.get("email")
        password = form.get("password")
        
        user = await auth_service.authenticate(email, password)
        
        if user:
            token = auth_service.create_token(user["_id"])
            response = RedirectResponse("/", status_code=303)
            response.set_cookie("auth_token", token, httponly=True)
            return response
        
        return LMSLoginPage(error="Invalid credentials")
    
    
    @app.post("/auth/register")
    async def register(request: Request):
        """Handle registration (uses shared AuthService!)"""
        form = await request.form()
        email = form.get("email")
        password = form.get("password")
        
        try:
            user_id = await auth_service.register(email, password)
            token = auth_service.create_token(user_id)
            response = RedirectResponse("/", status_code=303)
            response.set_cookie("auth_token", token, httponly=True)
            return response
        except Exception as e:
            return LMSRegisterPage(error=str(e))
    
    
    logger.info("✓ LMS example app created (refactored - no duplication!)")
    return app


# -----------------------------------------------------------------------------
# Helper Components
# -----------------------------------------------------------------------------

def CourseCard(course: dict, user: dict = None, enrollments: dict = None, show_progress: bool = False):
    """Course card component"""
    user_id = user.get("_id") if user else None
    is_enrolled = user_id and enrollments and user_id in enrollments and course["id"] in enrollments[user_id]
    
    return Div(
        A(
            Div(
                # Image with badge
                Div(
                    Img(src=course["image"], alt=course["title"], cls="w-full h-48 object-cover"),
                    (Span("FREE", cls="badge badge-success absolute top-2 right-2") if course["price"] == 0 else
                     Span(f"${course['price']}", cls="badge badge-primary absolute top-2 right-2")),
                    (Span("✓ Enrolled", cls="badge badge-info absolute top-2 left-2") if is_enrolled else None),
                    cls="relative"
                ),
                
                # Content
                Div(
                    # Level badge
                    Span(course["level"], cls="badge badge-outline badge-sm mb-2"),
                    
                    H3(course["title"], cls="text-lg font-semibold mb-2"),
                    P(course["description"], cls="text-sm text-gray-500 mb-3 line-clamp-2"),
                    
                    # Instructor
                    Div(
                        UkIcon("user", width="16", height="16", cls="mr-1"),
                        Span(course["instructor"], cls="text-sm text-gray-600"),
                        cls="flex items-center mb-2"
                    ),
                    
                    # Stats
                    Div(
                        Div(
                            UkIcon("star", width="16", height="16", cls="mr-1 text-yellow-500"),
                            Span(str(course.get("rating", 0)), cls="text-sm"),
                            cls="flex items-center"
                        ),
                        Div(
                            UkIcon("users", width="16", height="16", cls="mr-1"),
                            Span(f"{course.get('students', 0)} students", cls="text-sm"),
                            cls="flex items-center"
                        ),
                        cls="flex gap-4 text-gray-600"
                    ),
                    
                    # Progress bar (if enrolled and show_progress)
                    (Div(
                        Div(cls="progress progress-primary w-full", value="30", max="100"),
                        P("30% Complete", cls="text-xs text-gray-500 mt-1"),
                        cls="mt-3"
                    ) if show_progress and is_enrolled else None),
                    
                    cls="p-4"
                ),
                
                cls="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow"
            ),
            href=f"course/{course['id']}"
        )
    )


def LessonItem(lesson: dict, course_id: int):
    """Lesson item component for course content sidebar"""
    return Div(
        Div(
            Div(
                Span("✓", cls="text-success font-bold mr-2") if lesson["completed"] else Span("○", cls="text-gray-400 mr-2"),
                Span(lesson["title"], cls="font-semibold" if not lesson["completed"] else ""),
                cls="flex items-center"
            ),
            Span(lesson["duration"], cls="text-sm text-gray-500"),
            cls="flex justify-between items-center"
        ),
        cls="p-3 bg-base-100 rounded hover:bg-base-300 cursor-pointer transition-colors"
    )
