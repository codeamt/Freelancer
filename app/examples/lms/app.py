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

from core.services import DBService, AuthService, get_current_user, SearchService
from core.services.db import DBService
from .auth_ui import LMSLoginPage, LMSRegisterPage
from .certificate_generator import CertificateGenerator

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
    search_service = SearchService(db_service)
    
    # Create FastHTML app
    app = FastHTML(hdrs=[*Theme.violet.headers(mode="light")])
    
    # In-memory storage (in production, use database)
    enrollments = {}  # {user_id: [course_ids]}
    instructor_courses = {}  # {instructor_id: [course_ids]}
    course_analytics = {}  # {course_id: {"enrollments": count, "completions": count, "avg_score": float}}
    
    async def get_user(request: Request):
        """Get current user from request - wrapper for core utility"""
        return await get_current_user(request, auth_service)
    
    # ============================================================================
    # LMS Auth Routes
    # ============================================================================
    
    @app.get("/auth")
    def lms_auth_page(request: Request):
        """LMS unified auth page with tabs for login/register"""
        redirect_url = request.query_params.get("redirect", "/lms-example")
        error = request.query_params.get("error")
        
        # Error messages
        error_messages = {
            "missing_fields": "Please fill in all required fields",
            "invalid_credentials": "Invalid email or password",
            "password_mismatch": "Passwords do not match",
            "password_short": "Password must be at least 8 characters",
            "user_exists": "An account with this email already exists",
            "server_error": "An error occurred. Please try again."
        }
        error_msg = error_messages.get(error) if error else None
        
        content = Div(
            # Header
            Div(
                H1("🎓 Welcome to Learning", cls="text-4xl font-bold mb-2 text-center"),
                P("Start your learning journey today", cls="text-xl text-gray-500 text-center mb-8"),
                cls="mb-8"
            ),
            
            # Error alert
            (Div(
                P(f"⚠️ {error_msg}", cls="text-error"),
                cls="alert alert-error mb-6 max-w-2xl mx-auto"
            ) if error_msg else None),
            
            # Tabbed auth form
            Div(
                # Tabs
                Div(
                    Input(type="radio", name="auth_tabs", id="tab_login", cls="tab-toggle", checked=True),
                    Input(type="radio", name="auth_tabs", id="tab_register", cls="tab-toggle"),
                    
                    Div(
                        Label("Returning Learner", htmlFor="tab_login", cls="tab tab-lg tab-lifted"),
                        Label("New Learner", htmlFor="tab_register", cls="tab tab-lg tab-lifted"),
                        cls="tabs tabs-lifted mb-0"
                    ),
                    
                    # Login Tab Content
                    Div(
                        Card(
                            Form(
                                H3("Welcome Back!", cls="text-2xl font-bold mb-6 text-center"),
                                
                                Div(
                                    Label("Email", cls="label font-semibold"),
                                    Input(
                                        type="email",
                                        name="email",
                                        placeholder="your@email.com",
                                        required=True,
                                        cls="input input-bordered w-full"
                                    ),
                                    cls="form-control mb-4"
                                ),
                                
                                Div(
                                    Label("Password", cls="label font-semibold"),
                                    Input(
                                        type="password",
                                        name="password",
                                        placeholder="••••••••",
                                        required=True,
                                        cls="input input-bordered w-full"
                                    ),
                                    cls="form-control mb-6"
                                ),
                                
                                Button(
                                    "Sign In & Continue Learning",
                                    type="submit",
                                    cls="btn btn-primary w-full btn-lg"
                                ),
                                
                                method="post",
                                action=f"/lms-example/auth/login?redirect={redirect_url}"
                            ),
                            cls="p-8"
                        ),
                        cls="tab-content login-tab"
                    ),
                    
                    # Register Tab Content
                    Div(
                        Card(
                            Form(
                                H3("Start Your Journey!", cls="text-2xl font-bold mb-6 text-center"),
                                
                                Div(
                                    Label("Email", cls="label font-semibold"),
                                    Input(
                                        type="email",
                                        name="email",
                                        placeholder="your@email.com",
                                        required=True,
                                        cls="input input-bordered w-full"
                                    ),
                                    cls="form-control mb-4"
                                ),
                                
                                Div(
                                    Label("Password", cls="label font-semibold"),
                                    Input(
                                        type="password",
                                        name="password",
                                        placeholder="At least 8 characters",
                                        required=True,
                                        minlength="8",
                                        cls="input input-bordered w-full"
                                    ),
                                    cls="form-control mb-4"
                                ),
                                
                                Div(
                                    Label("Confirm Password", cls="label font-semibold"),
                                    Input(
                                        type="password",
                                        name="confirm_password",
                                        placeholder="Re-enter password",
                                        required=True,
                                        cls="input input-bordered w-full"
                                    ),
                                    cls="form-control mb-4"
                                ),
                                
                                Div(
                                    Label("I am a:", cls="label font-semibold"),
                                    Select(
                                        Option("Student", value="student", selected=True),
                                        Option("Instructor", value="instructor"),
                                        Option("Admin", value="admin"),
                                        name="role",
                                        required=True,
                                        cls="select select-bordered w-full"
                                    ),
                                    cls="form-control mb-6"
                                ),
                                
                                Button(
                                    "Create Account & Start Learning",
                                    type="submit",
                                    cls="btn btn-primary w-full btn-lg"
                                ),
                                
                                method="post",
                                action=f"/lms-example/auth/register?redirect={redirect_url}"
                            ),
                            cls="p-8"
                        ),
                        cls="tab-content register-tab"
                    ),
                    
                    cls="max-w-2xl mx-auto"
                ),
                
                # CSS for tab functionality
                Style("""
                    .tab-toggle { display: none; }
                    .tab-content { display: none; }
                    #tab_login:checked ~ div .login-tab { display: block; }
                    #tab_register:checked ~ div .register-tab { display: block; }
                    #tab_login:checked ~ div label[for="tab_login"] { 
                        background-color: hsl(var(--b1));
                        border-bottom-color: hsl(var(--b1));
                    }
                    #tab_register:checked ~ div label[for="tab_register"] { 
                        background-color: hsl(var(--b1));
                        border-bottom-color: hsl(var(--b1));
                    }
                """)
            )
        )
        
        return Layout(content, title="Start Learning | LMS", show_auth=False)
    
    @app.get("/login")
    def lms_login_page(request: Request):
        """LMS login page - redirect to unified auth"""
        redirect_url = request.query_params.get("redirect", "/lms-example")
        return RedirectResponse(f"/lms-example/auth?redirect={redirect_url}")
    
    @app.get("/register")
    def lms_register_page(request: Request):
        """LMS registration page - redirect to unified auth"""
        redirect_url = request.query_params.get("redirect", "/lms-example")
        return RedirectResponse(f"/lms-example/auth?redirect={redirect_url}")
    
    @app.post("/auth/login")
    async def lms_login(request: Request):
        """Handle LMS login"""
        form_data = await request.form()
        email = form_data.get("email")
        password = form_data.get("password")
        
        # Get redirect URL
        redirect_url = request.query_params.get("redirect", "/lms-example")
        
        # Validation
        if not all([email, password]):
            logger.warning("Login failed: Missing credentials")
            return RedirectResponse(f"/lms-example/auth?redirect={redirect_url}&error=missing_fields", status_code=303)
        
        try:
            # Authenticate user
            user = await auth_service.authenticate_user(email, password)
            
            if not user:
                logger.warning(f"Login failed: Invalid credentials for {email}")
                return RedirectResponse(f"/lms-example/auth?redirect={redirect_url}&error=invalid_credentials", status_code=303)
            
            # Create token
            token_data = {
                "sub": str(user.get("_id")),
                "email": email,
                "username": user.get("username"),
                "roles": user.get("roles", ["student"])
            }
            token = auth_service.create_token(token_data)
            
            logger.info(f"LMS user {email} logged in, redirecting to {redirect_url}")
            
            # Create response with redirect and set cookie
            response = RedirectResponse(url=redirect_url, status_code=303)
            response.set_cookie(
                key="auth_token",
                value=token,
                max_age=86400,  # 24 hours
                httponly=False,  # Allow JavaScript access
                samesite="lax"
            )
            return response
            
        except Exception as e:
            logger.error(f"LMS login error: {e}")
            return RedirectResponse(f"/lms-example/auth?redirect={redirect_url}&error=server_error", status_code=303)
    
    @app.post("/auth/register")
    async def lms_register(request: Request):
        """Handle LMS registration"""
        form_data = await request.form()
        email = form_data.get("email")
        password = form_data.get("password")
        confirm_password = form_data.get("confirm_password")
        role = form_data.get("role", "student")  # Default to student
        
        # Get redirect URL
        redirect_url = request.query_params.get("redirect", "/lms-example")
        
        # Validation - redirect back with error
        if not all([email, password, confirm_password]):
            logger.warning("Registration failed: Missing fields")
            return RedirectResponse(f"/lms-example/auth?redirect={redirect_url}&error=missing_fields", status_code=303)
        
        if password != confirm_password:
            logger.warning("Registration failed: Passwords don't match")
            return RedirectResponse(f"/lms-example/auth?redirect={redirect_url}&error=password_mismatch", status_code=303)
        
        if len(password) < 8:
            logger.warning("Registration failed: Password too short")
            return RedirectResponse(f"/lms-example/auth?redirect={redirect_url}&error=password_short", status_code=303)
        
        try:
            # Register user with selected role
            # Username defaults to email
            user = await auth_service.register_user(
                email=email,
                password=password,
                username=email,  # Use email as username
                roles=[role]  # Use selected role
            )
            
            if not user:
                logger.warning(f"Registration failed: User {email} already exists")
                return RedirectResponse(f"/lms-example/auth?redirect={redirect_url}&error=user_exists", status_code=303)
            
            logger.info(f"LMS user {email} registered successfully")
            
            # Auto-login: Generate token
            token_data = {
                "sub": str(user.get("_id")),
                "email": email,
                "username": user.get("username"),
                "roles": user.get("roles", ["student"])
            }
            token = auth_service.create_token(token_data)
            
            logger.info(f"LMS user {email} auto-logged in, redirecting to {redirect_url}")
            
            # Create response with redirect and set cookie
            response = RedirectResponse(url=redirect_url, status_code=303)
            response.set_cookie(
                key="auth_token",
                value=token,
                max_age=86400,  # 24 hours
                httponly=False,  # Allow JavaScript access
                samesite="lax"
            )
            return response
            
        except Exception as e:
            logger.error(f"LMS registration error: {e}")
            return RedirectResponse(f"/lms-example/auth?redirect={redirect_url}&error=server_error", status_code=303)
    
    # ============================================================================
    # LMS Routes
    # ============================================================================
    
    @app.get("/search")
    async def search_courses(request: Request, q: str = "", category: str = "", level: str = ""):
        """Search courses with filters"""
        user = await get_user(request)
        
        # Build filters
        filters = {}
        if category:
            filters["category"] = category
        if level:
            filters["level"] = level
        
        # Search courses
        search_fields = ["title", "description", "instructor"]
        results = search_service.search_with_filters(
            data=COURSES,
            query=q if q else None,
            filters=filters if filters else None,
            search_fields=search_fields,
            limit=50
        )
        
        # Get user enrollments
        user_enrollments = []
        if user:
            user_enrollments = enrollments.get(user.get("_id"), [])
        
        content = Div(
            # Search header
            Div(
                H1("🔍 Search Courses", cls="text-3xl font-bold mb-4"),
                P(f"Found {len(results)} courses", cls="text-gray-500 mb-6"),
                
                # Search form
                Form(
                    Div(
                        Input(
                            type="text",
                            name="q",
                            placeholder="Search courses...",
                            value=q,
                            cls="input input-bordered w-full max-w-md"
                        ),
                        Select(
                            Option("All Categories", value="", selected=not category),
                            Option("Programming", value="programming", selected=category == "programming"),
                            Option("Design", value="design", selected=category == "design"),
                            Option("Business", value="business", selected=category == "business"),
                            name="category",
                            cls="select select-bordered ml-2"
                        ),
                        Select(
                            Option("All Levels", value="", selected=not level),
                            Option("Beginner", value="Beginner", selected=level == "Beginner"),
                            Option("Intermediate", value="Intermediate", selected=level == "Intermediate"),
                            Option("Advanced", value="Advanced", selected=level == "Advanced"),
                            name="level",
                            cls="select select-bordered ml-2"
                        ),
                        Button(
                            UkIcon("search", width="20", height="20", cls="mr-2"),
                            "Search",
                            type="submit",
                            cls="btn btn-primary ml-2"
                        ),
                        A(
                            "Clear",
                            href="/lms-example/search",
                            cls="btn btn-ghost ml-2"
                        ),
                        cls="flex items-center gap-2"
                    ),
                    method="get",
                    action="/lms-example/search",
                    cls="mb-8"
                ),
                cls="mb-8"
            ),
            
            # Results
            (Div(
                *[CourseCard(course, user, user_enrollments) for course in results],
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6"
            ) if results else Div(
                Card(
                    Div(
                        UkIcon("search", width="48", height="48", cls="text-gray-400 mb-4"),
                        H3("No courses found", cls="text-xl font-semibold mb-2"),
                        P("Try adjusting your search or filters", cls="text-gray-500 mb-4"),
                        A("Browse All Courses", href="/lms-example", cls="btn btn-primary"),
                        cls="text-center p-8"
                    )
                )
            ))
        )
        
        return Layout(content, title="Search Courses | LMS", show_auth=False)
    
    @app.get("/")
    async def lms_home(request: Request):
        """Main LMS page with course catalog"""
        user = await get_user(request)
        
        # Get user enrollments
        user_enrollments = []
        if user:
            user_enrollments = enrollments.get(user.get("_id"), [])
        
        content = Div(
            # Hero Section - 5-Course Bootcamp with Background Image
            Div(
                # Background image with overlay
                Div(
                    # Dark overlay for better text readability
                    Div(cls="absolute inset-0 bg-black bg-opacity-60"),
                    
                    # Content
                    Div(
                        # Bootcamp badge
                        Span("🔥 LIMITED TIME OFFER", cls="badge badge-error badge-lg mb-4"),
                        
                        # Main heading
                        H1("Full-Stack Developer Bootcamp", cls="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 text-white"),
                        P("Master 5 essential courses in 12 weeks", cls="text-lg md:text-xl lg:text-2xl text-gray-200 mb-6"),
                    
                        # Course list
                        Div(
                            Div(
                                UkIcon("check-circle", width="20", height="20", cls="text-success mr-2"),
                                Span("Platform Orientation", cls="text-sm md:text-base lg:text-lg text-white"),
                                cls="flex items-center mb-2"
                            ),
                            Div(
                                UkIcon("check-circle", width="20", height="20", cls="text-success mr-2"),
                                Span("Python Programming Basics", cls="text-sm md:text-base lg:text-lg text-white"),
                                cls="flex items-center mb-2"
                            ),
                            Div(
                                UkIcon("check-circle", width="20", height="20", cls="text-success mr-2"),
                                Span("Web Development Fundamentals", cls="text-sm md:text-base lg:text-lg text-white"),
                                cls="flex items-center mb-2"
                            ),
                            Div(
                                UkIcon("check-circle", width="20", height="20", cls="text-success mr-2"),
                                Span("Database Design & SQL", cls="text-sm md:text-base lg:text-lg text-white"),
                                cls="flex items-center mb-2"
                            ),
                            Div(
                                UkIcon("check-circle", width="20", height="20", cls="text-success mr-2"),
                                Span("Full-Stack Project", cls="text-sm md:text-base lg:text-lg text-white"),
                                cls="flex items-center mb-6"
                            ),
                            cls="mb-6"
                        ),
                    
                        # Countdown timer
                        Div(
                            Div(
                                P("Next Cohort Starts In:", cls="text-sm text-gray-300 mb-2"),
                                Div(
                                    Div(
                                        Span("7", id="days", cls="countdown-value text-2xl md:text-3xl lg:text-4xl font-bold text-white"),
                                        Span("Days", cls="text-xs text-gray-300"),
                                        cls="flex flex-col items-center"
                                    ),
                                    Span(":", cls="text-2xl md:text-3xl mx-1 md:mx-2 text-white"),
                                    Div(
                                        Span("12", id="hours", cls="countdown-value text-2xl md:text-3xl lg:text-4xl font-bold text-white"),
                                        Span("Hours", cls="text-xs text-gray-300"),
                                        cls="flex flex-col items-center"
                                    ),
                                    Span(":", cls="text-2xl md:text-3xl mx-1 md:mx-2 text-white"),
                                    Div(
                                        Span("34", id="minutes", cls="countdown-value text-2xl md:text-3xl lg:text-4xl font-bold text-white"),
                                        Span("Minutes", cls="text-xs text-gray-300"),
                                        cls="flex flex-col items-center"
                                    ),
                                    Span(":", cls="text-2xl md:text-3xl mx-1 md:mx-2 text-white"),
                                    Div(
                                        Span("56", id="seconds", cls="countdown-value text-2xl md:text-3xl lg:text-4xl font-bold text-white"),
                                        Span("Seconds", cls="text-xs text-gray-300"),
                                        cls="flex flex-col items-center"
                                    ),
                                    cls="flex items-center justify-center"
                                ),
                                cls="bg-black bg-opacity-40 rounded-lg p-6 mb-6"
                            )
                        ),
                    
                        # CTA buttons
                        Div(
                            (Div(
                                A(
                                    UkIcon("play-circle", width="24", height="24", cls="mr-2"),
                                    "Enroll Now - $299",
                                    href="/lms-example/bootcamp/enroll",
                                    cls="btn btn-primary btn-lg mr-3"
                                ),
                                A("My Courses", href="/lms-example/my-courses", cls="btn btn-outline btn-md md:btn-lg sm:mr-3"),
                                A(
                                    UkIcon("search", width="20", height="20", cls="mr-2"),
                                    "Search Courses",
                                    href="/lms-example/search",
                                    cls="btn btn-ghost btn-md md:btn-lg"
                                ),
                                cls="flex flex-col sm:flex-row gap-3 justify-center"
                            ) if user else Div(
                                A(
                                    UkIcon("rocket", width="24", height="24", cls="mr-2"),
                                    "Start Learning - Enroll Now",
                                    href="/lms-example/auth",
                                    cls="btn btn-primary btn-md md:btn-lg sm:mr-3"
                                ),
                                A(
                                    UkIcon("search", width="20", height="20", cls="mr-2"),
                                    "Browse Courses",
                                    href="/lms-example/search",
                                    cls="btn btn-outline btn-md md:btn-lg"
                                ),
                                cls="flex flex-col sm:flex-row justify-center gap-3"
                            )),
                            cls="mb-4"
                        ),
                        
                        # User status (small)
                        (Div(
                            Span(f"👤 {user.get('username')}", cls="text-sm text-gray-300 mr-3"),
                            (A("Instructor Dashboard", href="/lms-example/instructor/dashboard", cls="link link-primary text-sm mr-3") 
                             if "instructor" in user.get("roles", []) or "admin" in user.get("roles", []) else None),
                            A("Logout", href="/auth/logout", cls="link link-primary text-sm"),
                            cls="flex items-center justify-center"
                        ) if user else None),
                        
                        cls="text-center max-w-4xl mx-auto relative z-10"
                    ),
                    
                    cls="relative min-h-[700px] flex items-center justify-center px-4",
                    style="background-image: url('https://images.unsplash.com/photo-1472289065668-ce650ac443d2?q=80&w=1169&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'); background-size: cover; background-position: center;"
                ),
                cls="mb-16 -mx-4"
            ),
            
            # Popular Courses Carousel
            Div(
                H2("Popular Courses", cls="text-3xl font-bold mb-8 text-center"),
                Div(
                    Div(
                        *[CompactCourseCard(course, user, user_enrollments) for course in COURSES],
                        cls="carousel carousel-center space-x-4 p-4 bg-base-200 rounded-box"
                    ),
                    cls="mb-16"
                ),
                
                # Autoplay script
                Script("""
                    const carousel = document.querySelector('.carousel');
                    if (carousel) {
                        let scrollAmount = 0;
                        const cardWidth = 320; // Approximate card width + gap
                        
                        setInterval(() => {
                            scrollAmount += cardWidth;
                            if (scrollAmount >= carousel.scrollWidth - carousel.clientWidth) {
                                scrollAmount = 0;
                            }
                            carousel.scrollTo({
                                left: scrollAmount,
                                behavior: 'smooth'
                            });
                        }, 3000); // Auto-scroll every 3 seconds
                    }
                """)
            ),
            
            # Newsletter CTA (for all users)
            Div(
                Card(
                    Div(
                        UkIcon("mail", width="48", height="48", cls="text-primary mb-4"),
                        H2("Stay Updated!", cls="text-3xl font-bold mb-3"),
                        P("Subscribe to our newsletter and be the first to know about new courses and bootcamps", cls="text-lg text-gray-400 mb-6"),
                        Form(
                            Div(
                                Input(
                                    type="email",
                                    name="email",
                                    placeholder="Enter your email",
                                    required=True,
                                    cls="input input-bordered input-lg w-full max-w-md mr-3"
                                ),
                                Button(
                                    UkIcon("send", width="20", height="20", cls="mr-2"),
                                    "Subscribe",
                                    type="submit",
                                    cls="btn btn-primary btn-lg"
                                ),
                                cls="flex gap-3 justify-center items-center"
                            ),
                            method="post",
                            action="/lms-example/newsletter/subscribe",
                            cls="mb-3"
                        ),
                        P("🔒 We respect your privacy. Unsubscribe anytime.", cls="text-sm text-gray-400"),
                        cls="text-center p-12"
                    )
                ),
                cls="max-w-4xl mx-auto mb-16"
            ),
            
            # Countdown timer script
            Script("""
                // Countdown to a date 7 days from now
                const countdownDate = new Date().getTime() + (7 * 24 * 60 * 60 * 1000);
                
                function updateCountdown() {
                    const now = new Date().getTime();
                    const distance = countdownDate - now;
                    
                    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                    const seconds = Math.floor((distance % (1000 * 60)) / 1000);
                    
                    document.getElementById('days').textContent = days;
                    document.getElementById('hours').textContent = hours;
                    document.getElementById('minutes').textContent = minutes;
                    document.getElementById('seconds').textContent = seconds;
                }
                
                updateCountdown();
                setInterval(updateCountdown, 1000);
            """),
            
            # Membership Pricing Section
            Div(
                Div(
                    H2("Choose Your Learning Path", cls="text-3xl font-bold mb-3 text-center"),
                    P("Unlock your potential with flexible membership options", cls="text-gray-500 text-center mb-12"),
                    
                    # Pricing cards
                    Div(
                        # Free Tier
                        Div(
                            Div(
                                # Header
                                Div(
                                    Span("FREE", cls="text-xs tracking-widest text-gray-500 mb-2 block font-medium"),
                                    H3("Explorer", cls="text-2xl font-bold mb-2"),
                                    Div(
                                        Span("$0", cls="text-4xl font-bold"),
                                        Span("/forever", cls="text-gray-500 ml-2"),
                                        cls="mb-6"
                                    ),
                                    cls="text-center mb-6 pb-6 border-b border-gray-200"
                                ),
                                
                                # Features
                                Div(
                                    Div(
                                        UkIcon("check", width="20", height="20", cls="text-success mr-3"),
                                        Span("Access to free courses", cls="text-sm"),
                                        cls="flex items-start mb-3"
                                    ),
                                    Div(
                                        UkIcon("check", width="20", height="20", cls="text-success mr-3"),
                                        Span("Community forum access", cls="text-sm"),
                                        cls="flex items-start mb-3"
                                    ),
                                    Div(
                                        UkIcon("check", width="20", height="20", cls="text-success mr-3"),
                                        Span("Basic progress tracking", cls="text-sm"),
                                        cls="flex items-start mb-3"
                                    ),
                                    Div(
                                        UkIcon("x", width="20", height="20", cls="text-gray-300 mr-3"),
                                        Span("Premium courses", cls="text-sm text-gray-400"),
                                        cls="flex items-start mb-3"
                                    ),
                                    Div(
                                        UkIcon("x", width="20", height="20", cls="text-gray-300 mr-3"),
                                        Span("Certificates", cls="text-sm text-gray-400"),
                                        cls="flex items-start mb-3"
                                    ),
                                    cls="mb-8"
                                ),
                                
                                # CTA
                                A(
                                    "Get Started",
                                    href="/lms-example/auth",
                                    cls="btn btn-outline btn-block"
                                ),
                                
                                cls="p-8"
                            ),
                            cls="bg-white border border-gray-200 rounded-lg hover:shadow-lg transition-all"
                        ),
                        
                        # Monthly Tier
                        Div(
                            Div(
                                # Header
                                Div(
                                    Span("MONTHLY", cls="text-xs tracking-widest text-primary mb-2 block font-medium"),
                                    H3("Learner", cls="text-2xl font-bold mb-2"),
                                    Div(
                                        Span("$29", cls="text-4xl font-bold"),
                                        Span("/month", cls="text-gray-500 ml-2"),
                                        cls="mb-6"
                                    ),
                                    cls="text-center mb-6 pb-6 border-b border-gray-200"
                                ),
                                
                                # Features
                                Div(
                                    Div(
                                        UkIcon("check", width="20", height="20", cls="text-success mr-3"),
                                        Span("All free tier features", cls="text-sm font-medium"),
                                        cls="flex items-start mb-3"
                                    ),
                                    Div(
                                        UkIcon("check", width="20", height="20", cls="text-success mr-3"),
                                        Span("Access to all premium courses", cls="text-sm"),
                                        cls="flex items-start mb-3"
                                    ),
                                    Div(
                                        UkIcon("check", width="20", height="20", cls="text-success mr-3"),
                                        Span("Course certificates", cls="text-sm"),
                                        cls="flex items-start mb-3"
                                    ),
                                    Div(
                                        UkIcon("check", width="20", height="20", cls="text-success mr-3"),
                                        Span("Priority support", cls="text-sm"),
                                        cls="flex items-start mb-3"
                                    ),
                                    Div(
                                        UkIcon("check", width="20", height="20", cls="text-success mr-3"),
                                        Span("Downloadable resources", cls="text-sm"),
                                        cls="flex items-start mb-3"
                                    ),
                                    cls="mb-8"
                                ),
                                
                                # CTA
                                A(
                                    "Start Learning",
                                    href="/lms-example/auth",
                                    cls="btn btn-primary btn-block"
                                ),
                                
                                cls="p-8"
                            ),
                            cls="bg-white border-2 border-primary rounded-lg shadow-xl transform scale-105 relative"
                        ),
                        
                        # Annual Tier
                        Div(
                            # Popular badge
                            Div(
                                Span("BEST VALUE", cls="badge badge-accent badge-sm absolute -top-3 left-1/2 transform -translate-x-1/2"),
                            ),
                            
                            Div(
                                # Header
                                Div(
                                    Span("ANNUAL", cls="text-xs tracking-widest text-accent mb-2 block font-medium"),
                                    H3("Pro Learner", cls="text-2xl font-bold mb-2"),
                                    Div(
                                        Span("$290", cls="text-4xl font-bold"),
                                        Span("/year", cls="text-gray-500 ml-2"),
                                        cls="mb-2"
                                    ),
                                    Div(
                                        Span("Save $58 annually", cls="text-sm text-success font-medium"),
                                        cls="mb-6"
                                    ),
                                    cls="text-center mb-6 pb-6 border-b border-gray-200"
                                ),
                                
                                # Features
                                Div(
                                    Div(
                                        UkIcon("check", width="20", height="20", cls="text-success mr-3"),
                                        Span("All monthly tier features", cls="text-sm font-medium"),
                                        cls="flex items-start mb-3"
                                    ),
                                    Div(
                                        UkIcon("star", width="20", height="20", cls="text-warning mr-3"),
                                        Span("10% off bootcamp enrollment", cls="text-sm font-bold text-warning"),
                                        cls="flex items-start mb-3"
                                    ),
                                    Div(
                                        UkIcon("check", width="20", height="20", cls="text-success mr-3"),
                                        Span("Exclusive annual member events", cls="text-sm"),
                                        cls="flex items-start mb-3"
                                    ),
                                    Div(
                                        UkIcon("check", width="20", height="20", cls="text-success mr-3"),
                                        Span("Early access to new courses", cls="text-sm"),
                                        cls="flex items-start mb-3"
                                    ),
                                    Div(
                                        UkIcon("check", width="20", height="20", cls="text-success mr-3"),
                                        Span("1-on-1 mentorship session", cls="text-sm"),
                                        cls="flex items-start mb-3"
                                    ),
                                    cls="mb-8"
                                ),
                                
                                # CTA
                                A(
                                    "Become a Pro",
                                    href="/lms-example/auth",
                                    cls="btn btn-accent btn-block"
                                ),
                                
                                cls="p-8"
                            ),
                            cls="bg-white border border-gray-200 rounded-lg hover:shadow-lg transition-all relative"
                        ),
                        
                        cls="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto items-start"
                    ),
                    
                    # Additional info
                    Div(
                        P("💳 All plans include a 14-day money-back guarantee", cls="text-center text-sm text-gray-500 mb-2"),
                        P("🔒 Cancel anytime, no questions asked", cls="text-center text-sm text-gray-500"),
                        cls="mt-12"
                    ),
                ),
                cls="mt-16 mb-8 bg-gradient-to-b from-blue-50 to-white py-16 -mx-4 px-4"
            )
        )
        
        return Layout(content, title="LMS Example | FastApp", user=user, cart_count=0, show_auth=True)
    
    @app.get("/course/{course_id}")
    async def course_detail(request: Request, course_id: int):
        """Course detail page"""
        user = await get_user(request)
        
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
                    # Level badge and enrollment status
                    Div(
                        Span(course["level"], cls=f"badge {'badge-success' if is_free else 'badge-primary'} mr-2"),
                        (Span("✓ Enrolled", cls="badge badge-success") if is_enrolled else None),
                        cls="mb-4"
                    ),
                    
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
                    
                    # Progress tracker (for enrolled students)
                    (Div(
                        H3("Your Progress:", cls="text-xl font-semibold mb-3"),
                        Div(
                            Div(
                                Span("0%", id=f"progress-text-{course_id}", cls="font-semibold text-sm"),
                                cls="mb-2"
                            ),
                            Div(
                                Div(
                                    id=f"progress-bar-{course_id}",
                                    cls="bg-success h-2 rounded-full transition-all duration-300",
                                    style="width: 0%"
                                ),
                                cls="w-full bg-base-300 rounded-full h-2"
                            ),
                            Span("0 of 0 lessons completed", id=f"progress-count-{course_id}", cls="text-sm text-gray-500 mt-2 block"),
                            cls="mb-6"
                        ),
                        Script(f"""
                            // Calculate and display progress
                            const key = 'lms_progress_course_{course_id}';
                            let progress = JSON.parse(localStorage.getItem(key) || '{{}}');
                            const totalLessons = {course['lessons']};
                            const completedLessons = Object.keys(progress).filter(k => progress[k]).length;
                            const percentage = Math.round((completedLessons / totalLessons) * 100);
                            
                            document.getElementById('progress-text-{course_id}').textContent = percentage + '%';
                            document.getElementById('progress-bar-{course_id}').style.width = percentage + '%';
                            document.getElementById('progress-count-{course_id}').textContent = 
                                completedLessons + ' of ' + totalLessons + ' lessons completed';
                        """)
                    ) if is_enrolled else None),
                    
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
                        A("Continue Learning", href=f"/lms-example/course/{course_id}/lesson/1", cls="btn btn-primary btn-lg ml-4"),
                        cls="flex items-center"
                    ) if is_enrolled else (
                        A(
                            UkIcon("play-circle", width="20", height="20", cls="mr-2"),
                            "Start Free Course",
                            href=f"/lms-example/course/{course_id}/lesson/1",
                            cls="btn btn-primary btn-lg"
                        ) if is_free else (
                            Button(
                                UkIcon("play-circle", width="20", height="20", cls="mr-2"),
                                "Enroll Now",
                                cls="btn btn-primary btn-lg",
                                hx_post=f"/lms-example/enroll/{course_id}",
                                hx_target="#enroll-action",
                                hx_swap="innerHTML"
                            ) if user else A(
                            UkIcon("lock", width="20", height="20", cls="mr-2"),
                            "Sign in to enroll",
                            href=f"/lms-example/login?redirect=/lms-example/course/{course_id}",
                            cls="btn btn-primary btn-lg"
                        )
                        )
                    )),
                    
                    cls="lg:col-span-1"
                ),
                
                cls="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12"
            )
        )
        
        return Layout(content, title=f"{course['title']} | LMS", user=user, cart_count=0, show_auth=True)
    
    @app.get("/course/{course_id}/lesson/{lesson_num}")
    async def view_lesson(request: Request, course_id: int, lesson_num: int):
        """View a specific lesson"""
        # Find course
        course = next((c for c in COURSES if c["id"] == course_id), None)
        if not course:
            return RedirectResponse("/lms-example")
        
        # Get lesson from syllabus
        syllabus = course.get("syllabus", [])
        if lesson_num < 1 or lesson_num > len(syllabus):
            return RedirectResponse(f"/lms-example/course/{course_id}")
        
        lesson = syllabus[lesson_num - 1]
        
        # Demo lesson content (for free course)
        lesson_content = {
            1: {
                "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",  # Demo video
                "description": "Welcome to the platform! In this lesson, you'll learn how to navigate courses, track your progress, and make the most of your learning experience.",
                "resources": [
                    {"name": "Platform Guide PDF", "url": "#"},
                    {"name": "Quick Start Checklist", "url": "#"},
                ]
            },
            2: {
                "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
                "description": "Learn how to browse courses, filter by category, and find the perfect course for your goals.",
                "resources": [
                    {"name": "Course Navigation Guide", "url": "#"},
                ]
            },
            3: {
                "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
                "description": "Understand how progress tracking works and how to monitor your learning journey.",
                "resources": [
                    {"name": "Progress Tracking Guide", "url": "#"},
                ]
            },
            4: {
                "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
                "description": "Learn how to get help when you need it and connect with our support team.",
                "resources": [
                    {"name": "Support Resources", "url": "#"},
                ]
            },
            5: {
                "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
                "description": "Discover what's next and how to continue your learning journey with our platform.",
                "resources": [
                    {"name": "Course Catalog", "url": "/lms-example"},
                    {"name": "Learning Paths", "url": "#"},
                ]
            }
        }
        
        current_lesson = lesson_content.get(lesson_num, lesson_content[1])
        
        content = Div(
            # Back to course button
            A(
                UkIcon("arrow-left", width="20", height="20", cls="mr-2"),
                "Back to Course",
                href=f"/lms-example/course/{course_id}",
                cls="btn btn-ghost mb-6"
            ),
            
            # Lesson header
            Div(
                Span(f"Lesson {lesson_num} of {len(syllabus)}", cls="badge badge-primary mb-2"),
                H1(lesson["title"], cls="text-3xl font-bold mb-2"),
                P(lesson["duration"], cls="text-gray-500 mb-6"),
                cls="mb-6"
            ),
            
            # Main content grid: Video + Lesson List
            Div(
                # Video player and content (left side)
                Div(
                    # Video player
                    Div(
                        Iframe(
                            src=current_lesson["video_url"],
                            width="100%",
                            height="500",
                            frameborder="0",
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
                            allowfullscreen=True,
                            cls="rounded-lg shadow-lg"
                        ),
                        cls="mb-8"
                    ),
                
                # Lesson description
                Div(
                    H2("About this lesson", cls="text-2xl font-bold mb-4"),
                    P(current_lesson["description"], cls="text-lg text-gray-600 mb-6"),
                    cls="mb-8"
                ),
                
                # Resources
                (Div(
                    H3("Lesson Resources", cls="text-xl font-bold mb-4"),
                    Div(
                        *[A(
                            UkIcon("download", width="16", height="16", cls="mr-2"),
                            resource["name"],
                            href=resource["url"],
                            cls="flex items-center p-3 bg-base-200 rounded-lg hover:bg-base-300 transition-colors",
                            target="_blank" if resource["url"].startswith("http") else None
                        ) for resource in current_lesson.get("resources", [])],
                        cls="space-y-2 mb-8"
                    )
                ) if current_lesson.get("resources") else None),
                
                # Mark as complete button
                Div(
                    Button(
                        UkIcon("check-circle", width="20", height="20", cls="mr-2"),
                        Span("Mark as Complete", id=f"complete-text-{lesson_num}"),
                        id=f"complete-btn-{lesson_num}",
                        cls="btn btn-success btn-lg w-full mb-6",
                        onclick=f"""
                            const key = 'lms_progress_course_{course_id}';
                            let progress = JSON.parse(localStorage.getItem(key) || '{{}}');
                            progress[{lesson_num}] = true;
                            localStorage.setItem(key, JSON.stringify(progress));
                            this.classList.add('btn-disabled');
                            document.getElementById('complete-text-{lesson_num}').textContent = '✓ Completed';
                        """
                    ),
                    Script(f"""
                        // Check if lesson is already completed
                        const key = 'lms_progress_course_{course_id}';
                        let progress = JSON.parse(localStorage.getItem(key) || '{{}}');
                        if (progress[{lesson_num}]) {{
                            const btn = document.getElementById('complete-btn-{lesson_num}');
                            btn.classList.add('btn-disabled');
                            document.getElementById('complete-text-{lesson_num}').textContent = '✓ Completed';
                        }}
                    """),
                    cls="mb-6"
                ),
                
                    # Navigation buttons
                    Div(
                        A(
                            UkIcon("arrow-left", width="20", height="20", cls="mr-2"),
                            "Previous Lesson",
                            href=f"/lms-example/course/{course_id}/lesson/{lesson_num - 1}",
                            cls="btn btn-outline" if lesson_num > 1 else "btn btn-outline btn-disabled"
                        ) if lesson_num > 1 else Div(),
                        
                        A(
                            "Next Lesson",
                            UkIcon("arrow-right", width="20", height="20", cls="ml-2"),
                            href=f"/lms-example/course/{course_id}/lesson/{lesson_num + 1}",
                            cls="btn btn-primary"
                        ) if lesson_num < len(syllabus) else A(
                            "Take Final Exam",
                            UkIcon("file-text", width="20", height="20", cls="ml-2"),
                            href=f"/lms-example/course/{course_id}/exam",
                            cls="btn btn-success"
                        ),
                        cls="flex justify-between items-center"
                    ),
                    
                    cls="lg:col-span-2"
                ),
                
                # Lesson list sidebar (right side)
                Div(
                    H3("Course Lessons", cls="text-xl font-bold mb-4"),
                    Div(
                        *[A(
                            Div(
                                Div(
                                    Span(str(i + 1), cls="font-semibold mr-3"),
                                    Div(
                                        P(s["title"], cls="font-medium text-sm"),
                                        P(s["duration"], cls="text-xs text-gray-500"),
                                        cls="flex-1"
                                    ),
                                    cls="flex items-start"
                                ),
                                # Completion checkmark
                                Span(
                                    "✓",
                                    id=f"lesson-check-{i + 1}",
                                    cls="text-success font-bold hidden"
                                ),
                                cls="flex items-center justify-between"
                            ),
                            href=f"/lms-example/course/{course_id}/lesson/{i + 1}",
                            cls=f"block p-3 rounded-lg transition-colors {'bg-primary text-primary-content' if i + 1 == lesson_num else 'bg-base-200 hover:bg-base-300'}"
                        ) for i, s in enumerate(syllabus)],
                        cls="space-y-2"
                    ),
                    # Script to show completion checkmarks
                    Script(f"""
                        const key = 'lms_progress_course_{course_id}';
                        let progress = JSON.parse(localStorage.getItem(key) || '{{}}');
                        Object.keys(progress).forEach(lessonNum => {{
                            if (progress[lessonNum]) {{
                                const check = document.getElementById('lesson-check-' + lessonNum);
                                if (check) check.classList.remove('hidden');
                            }}
                        }});
                    """),
                    cls="lg:col-span-1"
                ),
                
                cls="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto"
            )
        )
        
        return Layout(content, title=f"{lesson['title']} | {course['title']}", user=None, cart_count=0, show_auth=True)
    
    @app.get("/course/{course_id}/exam")
    async def course_exam(request: Request, course_id: int):
        """Course final exam"""
        user = await get_user(request)
        
        # Find course
        course = next((c for c in COURSES if c["id"] == course_id), None)
        if not course:
            return RedirectResponse("/lms-example")
        
        # Sample exam questions (in production, these would come from database)
        exam_questions = [
            {
                "id": 1,
                "question": "What is the primary purpose of this course?",
                "options": [
                    "To learn advanced programming",
                    "To understand the platform and course structure",
                    "To get certified",
                    "To network with other students"
                ],
                "correct": 1  # Index of correct answer (0-based)
            },
            {
                "id": 2,
                "question": "How do you track your progress in a course?",
                "options": [
                    "By emailing the instructor",
                    "Progress is tracked automatically as you complete lessons",
                    "You must manually update your progress",
                    "Progress tracking is not available"
                ],
                "correct": 1
            },
            {
                "id": 3,
                "question": "What should you do if you need help during a course?",
                "options": [
                    "Give up and try another course",
                    "Skip the difficult parts",
                    "Use the support resources and contact the instructor",
                    "Wait until the course ends"
                ],
                "correct": 2
            },
            {
                "id": 4,
                "question": "What happens when you complete all lessons in a course?",
                "options": [
                    "Nothing, the course just ends",
                    "You can take the final exam",
                    "You are automatically enrolled in the next course",
                    "You must pay for certification"
                ],
                "correct": 1
            },
            {
                "id": 5,
                "question": "How can you access course resources?",
                "options": [
                    "Resources are not provided",
                    "You must purchase them separately",
                    "They are available in each lesson for download",
                    "Only after completing the course"
                ],
                "correct": 2
            }
        ]
        
        content = Div(
            # Back to course button
            A(
                UkIcon("arrow-left", width="20", height="20", cls="mr-2"),
                "Back to Course",
                href=f"/lms-example/course/{course_id}",
                cls="btn btn-ghost mb-6"
            ),
            
            # Exam header
            Div(
                Div(
                    UkIcon("file-text", width="48", height="48", cls="text-primary mb-4"),
                    H1(f"{course['title']} - Final Exam", cls="text-3xl font-bold mb-2"),
                    P(f"{len(exam_questions)} multiple choice questions", cls="text-lg text-gray-500 mb-6"),
                    cls="text-center mb-8"
                ),
                
                # Exam form
                Form(
                    Div(
                        *[Div(
                            H3(f"Question {q['id']}", cls="text-xl font-semibold mb-3"),
                            P(q["question"], cls="text-lg mb-4"),
                            Div(
                                *[Div(
                                    Label(
                                        Input(
                                            type="radio",
                                            name=f"question_{q['id']}",
                                            value=str(i),
                                            required=True,
                                            cls="radio radio-primary mr-3"
                                        ),
                                        option,
                                        cls="flex items-center cursor-pointer"
                                    ),
                                    cls="p-3 bg-base-200 rounded-lg hover:bg-base-300 transition-colors mb-2"
                                ) for i, option in enumerate(q["options"])],
                                cls="space-y-2"
                            ),
                            cls="mb-8 p-6 bg-base-100 rounded-lg border border-base-300"
                        ) for q in exam_questions],
                        cls="mb-8"
                    ),
                    
                    # Submit button
                    Button(
                        UkIcon("check-circle", width="20", height="20", cls="mr-2"),
                        "Submit Exam",
                        type="submit",
                        cls="btn btn-primary btn-lg w-full"
                    ),
                    
                    method="post",
                    action=f"/lms-example/course/{course_id}/exam/submit"
                ),
                
                cls="max-w-4xl mx-auto"
            )
        )
        
        return Layout(content, title=f"Final Exam | {course['title']}", user=user, cart_count=0, show_auth=True)
    
    @app.post("/course/{course_id}/exam/submit")
    async def submit_exam(request: Request, course_id: int):
        """Grade the exam and return results"""
        form_data = await request.form()
        
        # Find course
        course = next((c for c in COURSES if c["id"] == course_id), None)
        if not course:
            return RedirectResponse("/lms-example")
        
        # Correct answers (in production, fetch from database)
        correct_answers = {
            "question_1": "1",
            "question_2": "1",
            "question_3": "2",
            "question_4": "1",
            "question_5": "2"
        }
        
        # Grade the exam
        total_questions = len(correct_answers)
        correct_count = 0
        results = []
        
        for question_key, correct_answer in correct_answers.items():
            user_answer = form_data.get(question_key)
            is_correct = user_answer == correct_answer
            if is_correct:
                correct_count += 1
            results.append({
                "question": question_key,
                "correct": is_correct,
                "user_answer": user_answer,
                "correct_answer": correct_answer
            })
        
        # Calculate percentage
        percentage = round((correct_count / total_questions) * 100)
        passed = percentage >= 70  # 70% to pass
        
        # Results page
        content = Div(
            # Back to course button
            A(
                UkIcon("arrow-left", width="20", height="20", cls="mr-2"),
                "Back to Course",
                href=f"/lms-example/course/{course_id}",
                cls="btn btn-ghost mb-6"
            ),
            
            # Results header
            Div(
                Div(
                    UkIcon("award" if passed else "x-circle", width="64", height="64", 
                           cls=f"{'text-success' if passed else 'text-error'} mb-4"),
                    H1("Exam Results", cls="text-4xl font-bold mb-4"),
                    Div(
                        Span(f"{percentage}%", cls=f"text-6xl font-bold {'text-success' if passed else 'text-error'}"),
                        cls="mb-4"
                    ),
                    P(f"{correct_count} out of {total_questions} correct", cls="text-xl text-gray-500 mb-4"),
                    Span("✓ Passed!" if passed else "✗ Not Passed", 
                         cls=f"badge {'badge-success' if passed else 'badge-error'} badge-lg py-4 px-6"),
                    cls="text-center mb-12"
                ),
                
                # Detailed results
                Div(
                    H2("Question Breakdown", cls="text-2xl font-bold mb-6"),
                    Div(
                        *[Div(
                            Div(
                                Span("✓" if r["correct"] else "✗", 
                                     cls=f"text-2xl {'text-success' if r['correct'] else 'text-error'} mr-4"),
                                Span(f"Question {r['question'].split('_')[1]}", cls="font-semibold"),
                                cls="flex items-center"
                            ),
                            cls=f"p-4 rounded-lg {'bg-success bg-opacity-10' if r['correct'] else 'bg-error bg-opacity-10'}"
                        ) for r in results],
                        cls="space-y-3 mb-8"
                    )
                ),
                
                # Action buttons
                Div(
                    (A(
                        UkIcon("download", width="20", height="20", cls="mr-2"),
                        "Download Certificate",
                        href=f"/lms-example/course/{course_id}/certificate?score={percentage}",
                        cls="btn btn-success btn-lg mr-4",
                        download=f"{course['title']}_Certificate.png"
                    ) if passed else None),
                    A("Retake Exam", href=f"/lms-example/course/{course_id}/exam", cls="btn btn-outline btn-lg mr-4"),
                    A("Back to Course", href=f"/lms-example/course/{course_id}", cls="btn btn-primary btn-lg"),
                    cls="flex justify-center gap-4"
                ),
                
                cls="max-w-4xl mx-auto"
            )
        )
        
        return Layout(content, title=f"Exam Results | {course['title']}", user=None, cart_count=0, show_auth=True)
    
    @app.get("/course/{course_id}/certificate")
    async def download_certificate(request: Request, course_id: int, score: int = None):
        """Generate and download course completion certificate"""
        from starlette.responses import StreamingResponse
        
        user = await get_user(request)
        
        # Find course
        course = next((c for c in COURSES if c["id"] == course_id), None)
        if not course:
            return RedirectResponse("/lms-example")
        
        # Get student name (use username or email)
        student_name = "Student"
        if user:
            student_name = user.get("username", user.get("email", "Student"))
        
        # Generate certificate
        cert_generator = CertificateGenerator()
        certificate_image = cert_generator.generate_certificate(
            student_name=student_name,
            course_title=course["title"],
            score=score,
            instructor_name=course.get("instructor"),
            certificate_id=f"CERT-{course_id}-{user.get('_id') if user else 'GUEST'}"
        )
        
        # Return as downloadable image
        return StreamingResponse(
            certificate_image,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename={course['title'].replace(' ', '_')}_Certificate.png"
            }
        )
    
    # ============================================================================
    # Instructor Dashboard Routes
    # ============================================================================
    
    @app.get("/instructor/dashboard")
    async def instructor_dashboard(request: Request):
        """Instructor dashboard - course management and analytics"""
        user = await get_user(request)
        
        if not user:
            return RedirectResponse("/lms-example/login?redirect=/lms-example/instructor/dashboard")
        
        # Check if user is instructor
        user_roles = user.get("roles", [])
        if "instructor" not in user_roles and "admin" not in user_roles:
            return Layout(
                Div(
                    H1("Access Denied", cls="text-3xl font-bold mb-4"),
                    P("You must be an instructor to access this page.", cls="text-lg text-gray-500 mb-4"),
                    A("Back to Home", href="/lms-example", cls="btn btn-primary"),
                    cls="text-center py-16"
                ),
                title="Access Denied",
                user=user
            )
        
        # Get instructor's courses
        user_id = user.get("_id")
        instructor_course_ids = instructor_courses.get(user_id, [])
        instructor_course_list = [c for c in COURSES if c["id"] in instructor_course_ids]
        
        # Calculate total stats
        total_enrollments = sum(course_analytics.get(c["id"], {}).get("enrollments", 0) for c in instructor_course_list)
        total_completions = sum(course_analytics.get(c["id"], {}).get("completions", 0) for c in instructor_course_list)
        
        content = Div(
            # Header
            Div(
                H1("👨‍🏫 Instructor Dashboard", cls="text-4xl font-bold mb-2"),
                P(f"Welcome back, {user.get('username')}", cls="text-xl text-gray-500 mb-8"),
                cls="mb-8"
            ),
            
            # Stats cards
            Div(
                Card(
                    Div(
                        UkIcon("book", width="32", height="32", cls="text-primary mb-2"),
                        H3("Total Courses", cls="text-lg text-gray-500"),
                        P(str(len(instructor_course_list)), cls="text-4xl font-bold text-primary"),
                        cls="text-center p-6"
                    )
                ),
                Card(
                    Div(
                        UkIcon("users", width="32", height="32", cls="text-success mb-2"),
                        H3("Total Enrollments", cls="text-lg text-gray-500"),
                        P(str(total_enrollments), cls="text-4xl font-bold text-success"),
                        cls="text-center p-6"
                    )
                ),
                Card(
                    Div(
                        UkIcon("check-circle", width="32", height="32", cls="text-info mb-2"),
                        H3("Completions", cls="text-lg text-gray-500"),
                        P(str(total_completions), cls="text-4xl font-bold text-info"),
                        cls="text-center p-6"
                    )
                ),
                cls="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
            ),
            
            # Action buttons
            Div(
                A(
                    UkIcon("plus", width="20", height="20", cls="mr-2"),
                    "Create New Course",
                    href="/lms-example/instructor/course/new",
                    cls="btn btn-primary btn-lg"
                ),
                cls="mb-8"
            ),
            
            # Courses list
            Div(
                H2("Your Courses", cls="text-2xl font-bold mb-6"),
                
                (Div(
                    *[InstructorCourseCard(course, course_analytics.get(course["id"], {})) 
                      for course in instructor_course_list],
                    cls="space-y-4"
                ) if instructor_course_list else Card(
                    Div(
                        UkIcon("book", width="48", height="48", cls="text-gray-400 mb-4"),
                        H3("No courses yet", cls="text-xl font-semibold mb-2"),
                        P("Create your first course to get started!", cls="text-gray-500 mb-4"),
                        A("Create Course", href="/lms-example/instructor/course/new", cls="btn btn-primary"),
                        cls="text-center p-12"
                    )
                ))
            )
        )
        
        return Layout(content, title="Instructor Dashboard | LMS", user=user, cart_count=0, show_auth=True)
    
    @app.get("/instructor/course/new")
    async def new_course_form(request: Request):
        """Form to create a new course"""
        user = await get_user(request)
        
        if not user or "instructor" not in user.get("roles", []):
            return RedirectResponse("/lms-example/login")
        
        content = Div(
            # Back button
            A(
                UkIcon("arrow-left", width="20", height="20", cls="mr-2"),
                "Back to Dashboard",
                href="/lms-example/instructor/dashboard",
                cls="btn btn-ghost mb-6"
            ),
            
            # Form header
            Div(
                H1("Create New Course", cls="text-3xl font-bold mb-2"),
                P("Fill in the details to create your course", cls="text-lg text-gray-500 mb-8"),
                cls="mb-8"
            ),
            
            # Course form
            Card(
                Form(
                    # Course title
                    Div(
                        Label("Course Title", cls="label font-semibold"),
                        Input(
                            type="text",
                            name="title",
                            placeholder="e.g., Advanced Python Programming",
                            required=True,
                            cls="input input-bordered w-full"
                        ),
                        cls="form-control mb-4"
                    ),
                    
                    # Description
                    Div(
                        Label("Short Description", cls="label font-semibold"),
                        Textarea(
                            name="description",
                            placeholder="Brief description of the course...",
                            required=True,
                            rows="3",
                            cls="textarea textarea-bordered w-full"
                        ),
                        cls="form-control mb-4"
                    ),
                    
                    # Long description
                    Div(
                        Label("Detailed Description", cls="label font-semibold"),
                        Textarea(
                            name="long_description",
                            placeholder="Comprehensive course description...",
                            required=True,
                            rows="5",
                            cls="textarea textarea-bordered w-full"
                        ),
                        cls="form-control mb-4"
                    ),
                    
                    # Duration and Level
                    Div(
                        Div(
                            Label("Duration", cls="label font-semibold"),
                            Input(
                                type="text",
                                name="duration",
                                placeholder="e.g., 8 weeks",
                                required=True,
                                cls="input input-bordered w-full"
                            ),
                            cls="form-control"
                        ),
                        Div(
                            Label("Level", cls="label font-semibold"),
                            Select(
                                Option("Beginner", value="Beginner"),
                                Option("Intermediate", value="Intermediate"),
                                Option("Advanced", value="Advanced"),
                                name="level",
                                required=True,
                                cls="select select-bordered w-full"
                            ),
                            cls="form-control"
                        ),
                        cls="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4"
                    ),
                    
                    # Price and Lessons
                    Div(
                        Div(
                            Label("Price ($)", cls="label font-semibold"),
                            Input(
                                type="number",
                                name="price",
                                placeholder="0.00",
                                step="0.01",
                                min="0",
                                required=True,
                                cls="input input-bordered w-full"
                            ),
                            cls="form-control"
                        ),
                        Div(
                            Label("Number of Lessons", cls="label font-semibold"),
                            Input(
                                type="number",
                                name="lessons",
                                placeholder="10",
                                min="1",
                                required=True,
                                cls="input input-bordered w-full"
                            ),
                            cls="form-control"
                        ),
                        cls="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4"
                    ),
                    
                    # Image URL
                    Div(
                        Label("Course Image URL", cls="label font-semibold"),
                        Input(
                            type="url",
                            name="image",
                            placeholder="https://images.unsplash.com/...",
                            required=True,
                            cls="input input-bordered w-full"
                        ),
                        P("Use a high-quality image from Unsplash or similar", cls="text-sm text-gray-500 mt-1"),
                        cls="form-control mb-6"
                    ),
                    
                    # Submit button
                    Button(
                        UkIcon("check", width="20", height="20", cls="mr-2"),
                        "Create Course",
                        type="submit",
                        cls="btn btn-primary btn-lg w-full"
                    ),
                    
                    method="post",
                    action="/lms-example/instructor/course/create"
                ),
                cls="max-w-3xl mx-auto p-8"
            )
        )
        
        return Layout(content, title="Create Course | LMS", user=user, cart_count=0, show_auth=True)
    
    @app.post("/instructor/course/create")
    async def create_course(request: Request):
        """Handle course creation"""
        user = await get_user(request)
        
        if not user or "instructor" not in user.get("roles", []):
            return RedirectResponse("/lms-example/login")
        
        form_data = await request.form()
        
        # Create new course
        new_course_id = max([c["id"] for c in COURSES]) + 1 if COURSES else 1
        new_course = {
            "id": new_course_id,
            "title": form_data.get("title"),
            "description": form_data.get("description"),
            "long_description": form_data.get("long_description"),
            "instructor": user.get("username"),
            "duration": form_data.get("duration"),
            "level": form_data.get("level"),
            "price": float(form_data.get("price", 0)),
            "image": form_data.get("image"),
            "enrolled": 0,
            "rating": 5.0,
            "lessons": int(form_data.get("lessons", 1)),
            "syllabus": []  # Can be added later
        }
        
        # Add to courses list
        COURSES.append(new_course)
        
        # Add to instructor's courses
        user_id = user.get("_id")
        if user_id not in instructor_courses:
            instructor_courses[user_id] = []
        instructor_courses[user_id].append(new_course_id)
        
        # Initialize analytics
        course_analytics[new_course_id] = {
            "enrollments": 0,
            "completions": 0,
            "avg_score": 0,
            "exam_scores": []
        }
        
        logger.info(f"Course created: {new_course['title']} by {user.get('username')}")
        
        return RedirectResponse(f"/lms-example/instructor/course/{new_course_id}/edit", status_code=303)
    
    @app.get("/instructor/course/{course_id}/edit")
    async def edit_course_form(request: Request, course_id: int):
        """Form to edit an existing course"""
        user = await get_user(request)
        
        if not user or "instructor" not in user.get("roles", []):
            return RedirectResponse("/lms-example/login")
        
        # Find course
        course = next((c for c in COURSES if c["id"] == course_id), None)
        if not course:
            return RedirectResponse("/lms-example/instructor/dashboard")
        
        # Get analytics
        analytics = course_analytics.get(course_id, {})
        
        content = Div(
            # Back button
            A(
                UkIcon("arrow-left", width="20", height="20", cls="mr-2"),
                "Back to Dashboard",
                href="/lms-example/instructor/dashboard",
                cls="btn btn-ghost mb-6"
            ),
            
            # Header with analytics
            Div(
                H1(f"Edit: {course['title']}", cls="text-3xl font-bold mb-6"),
                
                # Analytics cards
                Div(
                    Card(
                        Div(
                            UkIcon("users", width="24", height="24", cls="text-primary mb-2"),
                            P("Enrollments", cls="text-sm text-gray-500"),
                            P(str(analytics.get("enrollments", 0)), cls="text-2xl font-bold"),
                            cls="text-center p-4"
                        )
                    ),
                    Card(
                        Div(
                            UkIcon("check-circle", width="24", height="24", cls="text-success mb-2"),
                            P("Completions", cls="text-sm text-gray-500"),
                            P(str(analytics.get("completions", 0)), cls="text-2xl font-bold"),
                            cls="text-center p-4"
                        )
                    ),
                    Card(
                        Div(
                            UkIcon("award", width="24", height="24", cls="text-info mb-2"),
                            P("Avg Exam Score", cls="text-sm text-gray-500"),
                            P(f"{analytics.get('avg_score', 0):.0f}%", cls="text-2xl font-bold"),
                            cls="text-center p-4"
                        )
                    ),
                    Card(
                        Div(
                            UkIcon("star", width="24", height="24", cls="text-warning mb-2"),
                            P("Rating", cls="text-sm text-gray-500"),
                            P(f"{course.get('rating', 0):.1f}/5.0", cls="text-2xl font-bold"),
                            cls="text-center p-4"
                        )
                    ),
                    cls="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
                ),
                
                cls="mb-8"
            ),
            
            # Edit form (similar to create form but pre-filled)
            Card(
                Form(
                    Div(
                        Label("Course Title", cls="label font-semibold"),
                        Input(
                            type="text",
                            name="title",
                            value=course["title"],
                            required=True,
                            cls="input input-bordered w-full"
                        ),
                        cls="form-control mb-4"
                    ),
                    
                    Div(
                        Label("Short Description", cls="label font-semibold"),
                        Textarea(
                            course["description"],
                            name="description",
                            required=True,
                            rows="3",
                            cls="textarea textarea-bordered w-full"
                        ),
                        cls="form-control mb-4"
                    ),
                    
                    Div(
                        Label("Price ($)", cls="label font-semibold"),
                        Input(
                            type="number",
                            name="price",
                            value=str(course["price"]),
                            step="0.01",
                            min="0",
                            required=True,
                            cls="input input-bordered w-full"
                        ),
                        cls="form-control mb-6"
                    ),
                    
                    Button(
                        UkIcon("save", width="20", height="20", cls="mr-2"),
                        "Save Changes",
                        type="submit",
                        cls="btn btn-primary btn-lg w-full"
                    ),
                    
                    method="post",
                    action=f"/lms-example/instructor/course/{course_id}/update"
                ),
                cls="max-w-3xl mx-auto p-8"
            )
        )
        
        return Layout(content, title=f"Edit {course['title']} | LMS", user=user, cart_count=0, show_auth=True)
    
    @app.post("/instructor/course/{course_id}/update")
    async def update_course(request: Request, course_id: int):
        """Handle course update"""
        user = await get_user(request)
        
        if not user or "instructor" not in user.get("roles", []):
            return RedirectResponse("/lms-example/login")
        
        form_data = await request.form()
        
        # Find and update course
        for course in COURSES:
            if course["id"] == course_id:
                course["title"] = form_data.get("title")
                course["description"] = form_data.get("description")
                course["price"] = float(form_data.get("price", 0))
                break
        
        logger.info(f"Course updated: {course_id} by {user.get('username')}")
        
        return RedirectResponse(f"/lms-example/instructor/course/{course_id}/edit", status_code=303)
    
    @app.post("/newsletter/subscribe")
    async def subscribe_newsletter(request: Request):
        """Handle newsletter subscription"""
        form_data = await request.form()
        email = form_data.get("email")
        
        if email:
            logger.info(f"Newsletter subscription: {email}")
            # In production: save to database, send to Mailgun, etc.
            
            return Div(
                Div(
                    P(f"✓ Thanks for subscribing! We'll send new course updates to {email}", cls="text-success"),
                    cls="alert alert-success max-w-2xl mx-auto"
                ),
                Script("""
                    setTimeout(() => {
                        window.location.href = '/lms-example';
                    }, 3000);
                """)
            )
        
        return RedirectResponse("/lms-example")
    
    @app.get("/my-courses")
    async def my_courses(request: Request):
        """User's enrolled courses"""
        user = await get_user(request)
        
        if not user:
            return RedirectResponse("/lms-example/login?redirect=/lms-example/my-courses")
        
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
        
        return Layout(content, title="My Courses | FastApp", user=user, cart_count=0, show_auth=True)
    
    @app.post("/enroll/{course_id}")
    async def enroll_course(request: Request, course_id: int):
        """Enroll in a course (requires auth)"""
        user = await get_user(request)
        
        if not user:
            return Div(
                P("⚠️ Please sign in to enroll in courses", cls="text-warning"),
                A("Sign In", href="/lms-example/login?redirect=/lms-example", cls="btn btn-sm btn-primary mt-2"),
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
    
    def CompactCourseCard(course: dict, user: dict = None, enrollments: list = None):
        """Compact course card for carousel"""
        is_enrolled = enrollments and course["id"] in enrollments
        is_free = course["price"] == 0
        
        return Div(
            Card(
                # Course image
                A(
                    Img(
                        src=course["image"],
                        alt=course["title"],
                        cls="w-full h-40 object-cover rounded-t-lg"
                    ),
                    href=f"/lms-example/course/{course['id']}"
                ),
                
                # Course info
                Div(
                    Div(
                        Span(course["level"], cls="badge badge-sm badge-outline mr-1"),
                        Span(f"${course['price']}" if not is_free else "FREE", 
                             cls=f"badge badge-sm {'badge-success' if is_free else 'badge-primary'}"),
                        cls="mb-2"
                    ),
                    A(
                        H3(course["title"], cls="text-base font-semibold mb-1 hover:text-primary line-clamp-2"),
                        href=f"/lms-example/course/{course['id']}"
                    ),
                    P(course["description"], cls="text-xs text-gray-500 mb-2 line-clamp-2"),
                    Div(
                        Span(f"⭐ {course['rating']}", cls="text-xs mr-2"),
                        Span(f"👥 {course['enrolled']}", cls="text-xs text-gray-500"),
                        cls="flex items-center"
                    ),
                    cls="p-3"
                ),
                cls="w-72"
            ),
            cls="carousel-item"
        )
    
    def InstructorCourseCard(course: dict, analytics: dict):
        """Course card for instructor dashboard with analytics"""
        return Card(
            Div(
                # Course image and info
                Div(
                    Img(
                        src=course["image"],
                        alt=course["title"],
                        cls="w-32 h-32 object-cover rounded-lg"
                    ),
                    cls="mr-6"
                ),
                
                # Course details
                Div(
                    H3(course["title"], cls="text-xl font-bold mb-2"),
                    P(course["description"], cls="text-gray-500 mb-3 line-clamp-2"),
                    
                    # Quick stats
                    Div(
                        Span(f"👥 {analytics.get('enrollments', 0)} students", cls="badge badge-ghost mr-2"),
                        Span(f"✓ {analytics.get('completions', 0)} completed", cls="badge badge-ghost mr-2"),
                        Span(f"⭐ {course.get('rating', 0):.1f}", cls="badge badge-ghost"),
                        cls="mb-3"
                    ),
                    
                    # Actions
                    Div(
                        A("Edit Course", href=f"/lms-example/instructor/course/{course['id']}/edit", cls="btn btn-sm btn-primary mr-2"),
                        A("View", href=f"/lms-example/course/{course['id']}", cls="btn btn-sm btn-outline"),
                        cls="flex gap-2"
                    ),
                    
                    cls="flex-1"
                ),
                
                cls="flex items-start p-6"
            )
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
