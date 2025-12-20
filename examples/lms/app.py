"""
LMS Example Application (Refactored)

Demonstrates how to build an LMS example by importing from domains and services.
No duplication - uses shared data and services.
"""
from fasthtml.common import *
from monsterui.all import *
import os
from datetime import datetime
from core.utils.logger import get_logger
from core.ui.layout import Layout
from core.services.auth import AuthService, UserService
from core.services.auth.helpers import get_current_user
from core.services import SearchService
from core.services.auth.context import set_user_context, UserContext

# Import shared data from LMS domain
from add_ons.domains.lms.data import SAMPLE_COURSES, get_course_by_id, get_free_courses

# Import custom auth UI and certificate generator for this example
from .ui import LMSLoginPage, LMSRegisterPage
# from add_ons.domains.lms.services.certificate_generator import CertificateGenerator  # TODO: Fix circular import

logger = get_logger(__name__)


def create_lms_app(auth_service=None, user_service=None, postgres=None, mongodb=None, redis=None, demo=False):
    """
    Create LMS example app
    
    Args:
        auth_service: Injected authentication service
        user_service: Injected user management service
        postgres: PostgreSQL adapter (optional)
        mongodb: MongoDB adapter (optional)
        redis: Redis adapter (optional)
        demo: Whether to run in demo mode (uses mock data, limited features)
    """
    
    # Use MongoDB adapter directly for document operations (enrollments, etc.)
    # MongoDB is better suited for flexible document storage
    db = mongodb
    
    search_service = SearchService()
    # cert_generator = CertificateGenerator()  # TODO: Fix circular import
    
    # Create app with MonsterUI theme
    app = FastHTML(hdrs=[*Theme.violet.headers(mode="light")])
    
    # Store demo flag in app state
    app.state.demo = demo
    
    # Base path for this mounted app
    BASE = "/lms-example"
    
    logger.info(f"Initializing LMS example app (demo={demo})...")
    
    async def get_user_with_context(request: Request):
        """Get current user from request and set context."""
        user = await get_current_user(request, auth_service)
        if user:
            # Set user context for state system using factory
            from core.services.auth.context import create_user_context
            
            # Create a simple user object for the factory
            class SimpleUser:
                def __init__(self, user_dict):
                    self.id = user_dict.get("id") or int(user_dict.get("_id", 0))
                    self.role = user_dict.get("role", "student")
                    self.email = user_dict.get("email", "")
            
            user_obj = SimpleUser(user)
            user_context = create_user_context(user_obj, request)
            set_user_context(user_context)
        return user
    
    # -----------------------------------------------------------------------------
    # Routes
    # -----------------------------------------------------------------------------
    
    @app.get("/")
    async def home(request: Request):
        """LMS homepage"""
        user = await get_user_with_context(request)
        
        # Get free courses for promotion
        free_courses = get_free_courses()
        
        content = Div(
            # Hero Section
            Div(
                H1("Learn Anything, Anytime", cls="text-5xl font-bold mb-4"),
                P("Access thousands of courses from expert instructors", cls="text-xl text-gray-500 mb-8"),
                Div(
                    A("Browse Courses", href=f"{BASE}/courses", cls="btn btn-primary btn-lg mr-4"),
                    (A("My Courses", href=f"{BASE}/student/dashboard", cls="btn btn-outline btn-lg") if user else
                     A("Sign Up Free", href=f"{BASE}/register", cls="btn btn-outline btn-lg")),
                    cls="flex gap-4 justify-center"
                ),
                cls="text-center py-20 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg mb-12"
            ),
            
            # Free Courses Section
            (Div(
                H2("Start Learning for Free", cls="text-3xl font-bold mb-6"),
                Div(
                    *[CourseCard(course, user) for course in free_courses],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                ),
                cls="mb-12"
            ) if free_courses else None),
            
            # All Courses Section
            Div(
                H2("Popular Courses", cls="text-3xl font-bold mb-6"),
                Div(
                    *[CourseCard(course, user) for course in SAMPLE_COURSES[:6]],
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
        
        return Layout(content, title="LMS | Learn Online", current_path=f"{BASE}/", user=user, show_auth=True, demo=demo)
    
    
    @app.get("/courses")
    async def courses_page(request: Request):
        """All courses page"""
        user = await get_user_with_context(request)
        
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
                *[CourseCard(course, user) for course in SAMPLE_COURSES],
                id="course-results",
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title="All Courses | LMS", current_path=f"{BASE}/courses", user=user, show_auth=True, demo=demo)
    
    
    @app.get("/courses/search")
    async def search_courses(request: Request, q: str = ""):
        """Search courses"""
        user = await get_user_with_context(request)
        
        if not q:
            courses = SAMPLE_COURSES
        else:
            # Use shared SearchService
            results = search_service.search(q, SAMPLE_COURSES, ["title", "description", "instructor"])
            courses = results
        
        return Div(
            *[CourseCard(course, user) for course in courses],
            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        )
    
    
    @app.get("/course/{course_id}")
    async def course_detail(request: Request, course_id: int):
        """Course detail page"""
        user = await get_user_with_context(request)
        
        # Use shared helper function!
        course = get_course_by_id(course_id)
        
        if not course:
            return Layout(
                Div(H1("Course not found"), cls="text-center py-20"),
                title="Not Found",
                user=user,
                show_auth=True,
                demo=demo
            )
        
        user_id = user.get("_id") if user else None
        is_enrolled = False
        if user_id:
            enrollment = await db.find_one("enrollments", {"user_id": user_id, "course_id": course_id})
            is_enrolled = enrollment is not None
        
        content = Div(
            # Back button
            A("← Back to Courses", href=f"{BASE}/courses", cls="btn btn-ghost mb-6"),
            
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
                            A("Go to Course", href=f"{BASE}/student/course/{course_id}", cls="btn btn-primary btn-lg w-full mt-4"),
                            cls="mb-4"
                        ) if is_enrolled else (
                            Div(
                                Button(
                                    "Enroll Now",
                                    cls="btn btn-primary btn-lg w-full mb-2",
                                    hx_post=f"{BASE}/enroll/{course_id}",
                                    hx_target="#enroll-result"
                                ),
                                Button(
                                    UkIcon("shopping-cart", width="18", height="18", cls="mr-2"),
                                    "Add to Cart",
                                    cls="btn btn-outline btn-lg w-full",
                                    hx_post=f"{BASE}/cart/add/{course_id}",
                                    hx_target="#enroll-result"
                                ),
                            ) if user else
                            A("Sign in to Enroll", href=f"{BASE}/login", cls="btn btn-primary btn-lg w-full")
                        )),
                        
                        Div(id="enroll-result", cls="mt-4"),
                        
                        # Stripe info
                        Div(
                            UkIcon("credit-card", width="16", height="16", cls="mr-2"),
                            Span("Pre-configured for Stripe payments", cls="text-xs text-gray-500"),
                            cls="flex items-center justify-center mt-4"
                        ) if course["price"] > 0 else None,
                        
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
        
        return Layout(content, title=f"{course['title']} | LMS", current_path=f"{BASE}/courses/{course_id}", user=user, show_auth=True, demo=demo)
    
    
    @app.post("/enroll/{course_id}")
    async def enroll_course(request: Request, course_id: int):
        """Enroll in course - redirects to checkout for paid courses"""
        user = await get_user_with_context(request)
        
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
        existing = await db.find_one("enrollments", {"user_id": user_id, "course_id": course_id})
        if existing:
            return Div(
                P("You're already enrolled in this course!", cls="text-info"),
                cls="alert alert-info"
            )
        
        # For paid courses, redirect to checkout
        if course["price"] > 0:
            return Div(
                P(f"This course costs ${course['price']}", cls="font-semibold mb-2"),
                A("Proceed to Checkout", href=f"{BASE}/checkout/{course_id}", cls="btn btn-primary"),
                cls="alert alert-warning"
            )
        
        # Free courses - enroll directly
        enrollment_data = {
            "user_id": user_id,
            "course_id": course_id,
            "status": "active",
            "progress": 0
        }
        await db.insert_one("enrollments", enrollment_data)
        
        logger.info(f"User {user_id} enrolled in free course {course_id}")
        
        return Div(
            P(f"✓ Successfully enrolled in {course['title']}!", cls="text-success"),
            A("Go to My Courses", href=f"{BASE}/student/dashboard", cls="btn btn-primary mt-4"),
            cls="alert alert-success"
        )
    
    
    @app.get("/checkout/{course_id}")
    async def checkout_page(request: Request, course_id: int):
        """Checkout page for paid courses"""
        user = await get_user_with_context(request)
        
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/checkout/{course_id}")
        
        course = get_course_by_id(course_id)
        if not course:
            return Layout(
                Div(H1("Course not found"), cls="text-center py-20"),
                title="Not Found",
                user=user,
                show_auth=True,
                demo=demo
            )
        
        content = Div(
            # Back button
            A("← Back to Course", href=f"{BASE}/course/{course_id}", cls="btn btn-ghost mb-6"),
            
            H1("Checkout", cls="text-4xl font-bold mb-8"),
            
            # Stripe notification toast
            Div(
                Div(
                    UkIcon("info", width="20", height="20", cls="mr-2"),
                    Span("This shop is pre-configured for Stripe payments. In production, this would process a real payment.", cls="text-sm"),
                    cls="flex items-center"
                ),
                cls="alert alert-info mb-6"
            ),
            
            Div(
                # Course summary
                Div(
                    Div(
                        Img(src=course["image"], alt=course["title"], cls="w-full h-48 object-cover rounded-lg mb-4"),
                        H2(course["title"], cls="text-2xl font-bold mb-2"),
                        P(f"by {course['instructor']}", cls="text-gray-600 mb-4"),
                        Div(
                            Span("Course Price:", cls="text-gray-600"),
                            Span(f"${course['price']}", cls="text-3xl font-bold text-blue-600 ml-2"),
                            cls="flex items-center"
                        ),
                        cls="bg-base-200 p-6 rounded-lg"
                    ),
                    cls="lg:w-1/2"
                ),
                
                # Payment form (mock)
                Div(
                    Div(
                        H3("Payment Details", cls="text-xl font-bold mb-4"),
                        
                        Form(
                            # Card number
                            Div(
                                Label("Card Number", cls="label"),
                                Input(
                                    type="text",
                                    placeholder="4242 4242 4242 4242",
                                    value="4242 4242 4242 4242",
                                    cls="input input-bordered w-full",
                                    readonly=True
                                ),
                                P("Demo card - no real charge", cls="text-xs text-gray-500 mt-1"),
                                cls="form-control mb-4"
                            ),
                            
                            # Expiry and CVC
                            Div(
                                Div(
                                    Label("Expiry", cls="label"),
                                    Input(
                                        type="text",
                                        placeholder="12/25",
                                        value="12/25",
                                        cls="input input-bordered w-full",
                                        readonly=True
                                    ),
                                    cls="form-control"
                                ),
                                Div(
                                    Label("CVC", cls="label"),
                                    Input(
                                        type="text",
                                        placeholder="123",
                                        value="123",
                                        cls="input input-bordered w-full",
                                        readonly=True
                                    ),
                                    cls="form-control"
                                ),
                                cls="grid grid-cols-2 gap-4 mb-6"
                            ),
                            
                            # Submit button
                            Button(
                                f"Pay ${course['price']} & Enroll",
                                type="submit",
                                cls="btn btn-primary btn-lg w-full"
                            ),
                            
                            hx_post=f"{BASE}/checkout/{course_id}/complete",
                            hx_target="#checkout-result"
                        ),
                        
                        Div(id="checkout-result", cls="mt-4"),
                        
                        # Security note
                        Div(
                            UkIcon("lock", width="16", height="16", cls="mr-2"),
                            Span("Secure checkout powered by Stripe", cls="text-sm text-gray-500"),
                            cls="flex items-center justify-center mt-4"
                        ),
                        
                        cls="bg-base-100 p-6 rounded-lg border"
                    ),
                    cls="lg:w-1/2"
                ),
                
                cls="flex flex-col lg:flex-row gap-8"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title=f"Checkout | {course['title']}", current_path=f"{BASE}/checkout/{course_id}", user=user, show_auth=True, demo=demo)
    
    
    @app.post("/checkout/{course_id}/complete")
    async def complete_checkout(request: Request, course_id: int):
        """Complete checkout and enroll user"""
        user = await get_user_with_context(request)
        
        if not user:
            return Div(P("Please sign in", cls="text-error"), cls="alert alert-error")
        
        course = get_course_by_id(course_id)
        if not course:
            return Div(P("Course not found", cls="text-error"), cls="alert alert-error")
        
        user_id = user.get("_id")
        
        # Check if already enrolled
        existing = await db.find_one("enrollments", {"user_id": user_id, "course_id": course_id})
        if existing:
            return Div(
                P("You're already enrolled in this course!", cls="text-info"),
                A("Go to Course", href=f"{BASE}/student/course/{course_id}", cls="btn btn-primary mt-2"),
                cls="alert alert-info"
            )
        
        # In production, this would verify the Stripe payment
        # For demo, we just simulate success
        
        # Create enrollment
        enrollment_data = {
            "user_id": user_id,
            "course_id": course_id,
            "status": "active",
            "progress": 0,
            "payment_status": "completed",
            "amount_paid": course["price"]
        }
        await db.insert_one("enrollments", enrollment_data)
        
        logger.info(f"User {user_id} purchased and enrolled in course {course_id} for ${course['price']}")
        
        return Div(
            H2("✓ Payment Successful!", cls="text-success text-2xl font-bold mb-2"),
            P(f"You're now enrolled in {course['title']}", cls="mb-4"),
            A("Start Learning", href=f"{BASE}/student/course/{course_id}", cls="btn btn-primary"),
            cls="alert alert-success"
        )
    
    
    # =========================================================================
    # Cart Routes
    # =========================================================================
    
    @app.post("/cart/add/{course_id}")
    async def add_to_cart(request: Request, course_id: int):
        """Add course to cart"""
        user = await get_user_with_context(request)
        
        if not user:
            return Div(P("Please sign in", cls="text-error"), cls="alert alert-error")
        
        course = get_course_by_id(course_id)
        if not course:
            return Div(P("Course not found", cls="text-error"), cls="alert alert-error")
        
        user_id = user.get("_id")
        
        # Check if already enrolled
        existing = await db.find_one("enrollments", {"user_id": user_id, "course_id": course_id})
        if existing:
            return Div(
                P("You're already enrolled in this course!", cls="text-info"),
                cls="alert alert-info"
            )
        
        # Add to cart (stored in MongoDB)
        cart_item = {
            "user_id": user_id,
            "course_id": course_id,
            "price": course["price"],
            "added_at": str(datetime.utcnow())
        }
        
        # Check if already in cart
        existing_cart = await db.find_one("cart_items", {"user_id": user_id, "course_id": course_id})
        if existing_cart:
            return Div(
                P("Course already in cart!", cls="text-info"),
                A("View Cart", href=f"{BASE}/cart", cls="btn btn-sm btn-outline mt-2"),
                cls="alert alert-info"
            )
        
        await db.insert_one("cart_items", cart_item)
        
        return Div(
            P(f"✓ {course['title']} added to cart!", cls="text-success"),
            A("View Cart", href=f"{BASE}/cart", cls="btn btn-sm btn-outline mt-2"),
            cls="alert alert-success"
        )
    
    
    @app.get("/cart")
    async def view_cart(request: Request):
        """View shopping cart"""
        user = await get_user_with_context(request)
        
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/cart")
        
        user_id = user.get("_id")
        cart_items = await db.find_many("cart_items", {"user_id": user_id}, limit=50)
        
        # Get course details for each cart item
        cart_courses = []
        subtotal = 0
        for item in cart_items:
            course = get_course_by_id(item["course_id"])
            if course:
                cart_courses.append(course)
                subtotal += course["price"]
        
        if not cart_courses:
            content = Div(
                H1("Your Cart", cls="text-4xl font-bold mb-8"),
                Div(
                    H2("Your cart is empty", cls="text-2xl mb-4"),
                    P("Browse courses and add them to your cart!", cls="text-gray-600 mb-6"),
                    A("Browse Courses", href=f"{BASE}/courses", cls="btn btn-primary"),
                    cls="text-center py-12"
                ),
                cls="container mx-auto px-4 py-8"
            )
            return Layout(content, title="Cart | LMS", current_path=f"{BASE}/cart", user=user, show_auth=True, demo=demo)
        
        content = Div(
            H1("Your Cart", cls="text-4xl font-bold mb-8"),
            
            # Stripe notification
            Div(
                Div(
                    UkIcon("info", width="20", height="20", cls="mr-2"),
                    Span("This shop is pre-configured for Stripe payments. In production, this would process real payments.", cls="text-sm"),
                    cls="flex items-center"
                ),
                cls="alert alert-info mb-6"
            ),
            
            Div(
                # Cart items
                Div(
                    *[CartCourseItem(course, BASE) for course in cart_courses],
                    cls="space-y-4 lg:w-2/3"
                ),
                
                # Summary
                Div(
                    Div(
                        H2("Order Summary", cls="text-2xl font-bold mb-4"),
                        Div(
                            Span(f"{len(cart_courses)} course(s)", cls="text-gray-600"),
                            Span(f"${subtotal:.2f}", cls="font-bold text-xl"),
                            cls="flex justify-between mb-4"
                        ),
                        Div(cls="divider"),
                        Div(
                            Span("Total:", cls="font-bold text-xl"),
                            Span(f"${subtotal:.2f}", cls="font-bold text-2xl text-blue-600"),
                            cls="flex justify-between mb-6"
                        ),
                        A(
                            "Checkout All",
                            href=f"{BASE}/cart/checkout",
                            cls="btn btn-primary btn-lg w-full"
                        ),
                        Div(
                            UkIcon("lock", width="16", height="16", cls="mr-2"),
                            Span("Secure checkout powered by Stripe", cls="text-xs text-gray-500"),
                            cls="flex items-center justify-center mt-4"
                        ),
                        cls="bg-base-200 p-6 rounded-lg"
                    ),
                    cls="lg:w-1/3"
                ),
                
                cls="flex flex-col lg:flex-row gap-8"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title="Cart | LMS", current_path=f"{BASE}/cart", user=user, show_auth=True, demo=demo)
    
    
    @app.post("/cart/remove/{course_id}")
    async def remove_from_cart(request: Request, course_id: int):
        """Remove course from cart"""
        user = await get_user_with_context(request)
        
        if not user:
            return Div(P("Please sign in", cls="text-error"), cls="alert alert-error")
        
        user_id = user.get("_id")
        await db.delete_one("cart_items", {"user_id": user_id, "course_id": course_id})
        
        # Redirect to cart page
        return RedirectResponse(f"{BASE}/cart", status_code=303)
    
    
    @app.get("/student/course/{course_id}")
    async def student_course_view(request: Request, course_id: int, lesson: int = 1):
        """Student course learning page"""
        user = await get_user_with_context(request)
        
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/student/course/{course_id}")
        
        user_id = user.get("_id")
        
        # Check enrollment
        enrollment = await db.find_one("enrollments", {"user_id": user_id, "course_id": course_id})
        if not enrollment:
            return RedirectResponse(f"{BASE}/course/{course_id}")
        
        course = get_course_by_id(course_id)
        if not course:
            return Layout(
                Div(H1("Course not found"), cls="text-center py-20"),
                title="Not Found",
                user=user,
                show_auth=True,
                demo=demo
            )
        
        # Get lesson progress from enrollment
        completed_lessons = enrollment.get("completed_lessons", [])
        
        # Course lessons (could come from course data in real app)
        lessons = [
            {"id": 1, "title": "Introduction", "duration": "10 min", "content": "Welcome to the course! In this lesson, we'll cover the basics and set up your environment."},
            {"id": 2, "title": "Getting Started", "duration": "15 min", "content": "Now that you're set up, let's dive into the fundamentals and build your first project."},
            {"id": 3, "title": "Core Concepts", "duration": "20 min", "content": "Understanding the core concepts is essential. We'll explore the key principles in depth."},
            {"id": 4, "title": "Advanced Topics", "duration": "25 min", "content": "Ready for more? Let's tackle advanced topics and best practices."},
            {"id": 5, "title": "Final Project", "duration": "30 min", "content": "Put everything together in a comprehensive final project that showcases your skills."},
        ]
        
        # Mark completed lessons
        for l in lessons:
            l["completed"] = l["id"] in completed_lessons
        
        # Get current lesson
        current_lesson = next((l for l in lessons if l["id"] == lesson), lessons[0])
        current_idx = next((i for i, l in enumerate(lessons) if l["id"] == lesson), 0)
        
        completed = len(completed_lessons)
        progress = (completed / len(lessons)) * 100
        
        content = Div(
            # Header
            Div(
                A("← Back to Dashboard", href=f"{BASE}/student/dashboard", cls="btn btn-ghost mb-4"),
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
                        *[LessonItem(l, course_id, l["id"] == lesson, BASE) for l in lessons],
                        cls="space-y-2"
                    ),
                    cls="lg:w-1/3 bg-base-200 p-6 rounded-lg h-fit"
                ),
                
                # Video/content area
                Div(
                    Div(
                        H2(f"Lesson {current_lesson['id']}: {current_lesson['title']}", cls="text-2xl font-bold mb-4"),
                        Div(
                            # Video placeholder
                            Div(
                                UkIcon("play-circle", width="64", height="64"),
                                P("Video Player", cls="mt-2"),
                                cls="bg-gray-800 text-white text-center py-24 rounded-lg mb-6 flex flex-col items-center justify-center"
                            ),
                            # Lesson content
                            P(current_lesson["content"], cls="text-gray-700 mb-6"),
                            P(f"Duration: {current_lesson['duration']}", cls="text-sm text-gray-500 mb-6"),
                            
                            # Navigation buttons
                            Div(
                                (A(
                                    "← Previous",
                                    href=f"{BASE}/student/course/{course_id}?lesson={lessons[current_idx-1]['id']}",
                                    cls="btn btn-outline"
                                ) if current_idx > 0 else Button("← Previous", cls="btn btn-outline", disabled=True)),
                                
                                (Button(
                                    "✓ Completed" if current_lesson["completed"] else "Mark Complete",
                                    cls="btn btn-success" if current_lesson["completed"] else "btn btn-primary",
                                    hx_post=f"{BASE}/student/course/{course_id}/complete/{current_lesson['id']}",
                                    hx_target="#lesson-status",
                                    hx_swap="innerHTML",
                                    disabled=current_lesson["completed"]
                                )),
                                
                                (A(
                                    "Next →",
                                    href=f"{BASE}/student/course/{course_id}?lesson={lessons[current_idx+1]['id']}",
                                    cls="btn btn-outline"
                                ) if current_idx < len(lessons) - 1 else Button("Next →", cls="btn btn-outline", disabled=True)),
                                
                                cls="flex justify-between items-center"
                            ),
                            Div(id="lesson-status", cls="mt-4"),
                            cls="bg-base-100 p-6 rounded-lg"
                        ),
                        cls="w-full"
                    ),
                    cls="lg:w-2/3"
                ),
                
                cls="flex flex-col lg:flex-row gap-6"
            ),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title=f"{course['title']} | Learning", current_path=f"{BASE}/learn/{course_id}", user=user, show_auth=True, demo=demo)
    
    @app.post("/student/course/{course_id}/complete/{lesson_id}")
    async def complete_lesson(request: Request, course_id: int, lesson_id: int):
        """Mark a lesson as complete."""
        user = await get_user_with_context(request)
        
        if not user:
            return Div(P("Please sign in", cls="text-error"), cls="alert alert-error")
        
        user_id = user.get("_id")
        
        # Get enrollment
        enrollment = await db.find_one("enrollments", {"user_id": user_id, "course_id": course_id})
        if not enrollment:
            return Div(P("Not enrolled", cls="text-error"), cls="alert alert-error")
        
        # Update completed lessons
        completed_lessons = enrollment.get("completed_lessons", [])
        if lesson_id not in completed_lessons:
            completed_lessons.append(lesson_id)
            await db.update_one(
                "enrollments",
                {"user_id": user_id, "course_id": course_id},
                {"completed_lessons": completed_lessons, "progress": len(completed_lessons) * 20}
            )
        
        return Div(
            P("✓ Lesson completed!", cls="text-success font-semibold"),
            A("Continue to next lesson →", href=f"{BASE}/student/course/{course_id}?lesson={lesson_id + 1}", cls="btn btn-primary btn-sm mt-2"),
            cls="alert alert-success"
        )
    
    
    @app.get("/student/dashboard")
    async def student_dashboard(request: Request):
        """Student dashboard"""
        user = await get_user_with_context(request)
        
        if not user:
            return RedirectResponse("/login?redirect=/student/dashboard")
        
        user_id = user.get("_id")
        enrollments_data = await db.find_many("enrollments", {"user_id": user_id}, limit=100)
        enrolled_course_ids = [e["course_id"] for e in enrollments_data]
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
                    *[CourseCard(course, user, show_progress=True) for course in enrolled_courses],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                )
            ) if enrolled_courses else Div(
                H2("No Courses Yet", cls="text-2xl font-bold mb-4"),
                P("Start learning by enrolling in a course!", cls="text-gray-600 mb-6"),
                A("Browse Courses", href=f"{BASE}/courses", cls="btn btn-primary"),
                cls="text-center py-12"
            )),
            
            cls="container mx-auto px-4 py-8"
        )
        
        return Layout(content, title="My Dashboard | LMS", current_path=f"{BASE}/student/dashboard", user=user, show_auth=True, demo=demo)
    
    
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
        # Try sanitized form first (from security middleware), fallback to raw form
        form = getattr(request.state, 'sanitized_form', None) or await request.form()
        email = form.get("email")
        password = form.get("password")
        
        if not email or not password:
            return LMSLoginPage(error="Email and password are required")
        
        from core.services.auth.models import LoginRequest
        try:
            result = await auth_service.login(LoginRequest(username=email, password=password))
            
            if result:
                response = RedirectResponse("/", status_code=303)
                response.set_cookie(
                    "auth_token",
                    result.access_token,
                    httponly=True,
                    secure=os.getenv("ENVIRONMENT") == "production",
                    samesite="lax",
                    max_age=result.expires_in
                )
                return response
        except Exception as e:
            logger.error(f"Login failed: {e}")
        
        return LMSLoginPage(error="Invalid credentials")
    
    
    @app.post("/auth/register")
    async def register(request: Request):
        """Handle registration (uses shared AuthService!)"""
        # Try sanitized form first (from security middleware), fallback to raw form
        form = getattr(request.state, 'sanitized_form', None) or await request.form()
        email = form.get("email")
        password = form.get("password")
        
        if not email or not password:
            return LMSRegisterPage(error="Email and password are required")
        
        try:
            # Create user via user_service
            user_id = await user_service.register(email, password)
            
            if not user_id:
                return LMSRegisterPage(error="Registration failed")
            
            # Auto-login after registration
            from core.services.auth.models import LoginRequest
            result = await auth_service.login(LoginRequest(username=email, password=password))
            
            if result:
                response = RedirectResponse("/", status_code=303)
                response.set_cookie(
                    "auth_token",
                    result.access_token,
                    httponly=True,
                    secure=os.getenv("ENVIRONMENT") == "production",
                    samesite="lax",
                    max_age=result.expires_in
                )
                return response
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return LMSRegisterPage(error=str(e))
        
        return LMSRegisterPage(error="Registration failed")
    
    
    # =========================================================================
    # Instructor/Admin Routes
    # =========================================================================
    
    @app.get("/instructor")
    async def instructor_dashboard(request: Request):
        """LMS Instructor Dashboard."""
        from .admin import LMSInstructorDashboard
        
        user = await get_user_with_context(request)
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/instructor")
        
        # Check if user has instructor role
        user_role = user.get("role", "user")
        if user_role not in ["admin", "super_admin", "instructor", "course_creator"]:
            return Layout(
                Div(
                    H1("Access Denied", cls="text-3xl font-bold text-error mb-4"),
                    P("You don't have permission to access the instructor dashboard.", cls="text-gray-600 mb-4"),
                    A("Back to Courses", href=f"{BASE}/courses", cls="btn btn-primary"),
                    cls="text-center py-20"
                ),
                title="Access Denied | LMS",
                user=user,
                show_auth=True,
                demo=demo
            )
        
        return LMSInstructorDashboard(user, demo=demo)
    
    @app.get("/instructor/lessons")
    async def instructor_lessons(request: Request):
        """Lesson manager page."""
        from .admin import LessonManagerPage
        
        user = await get_user_with_context(request)
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/instructor/lessons")
        
        return LessonManagerPage(user, SAMPLE_COURSES, demo=demo)
    
    @app.get("/instructor/quizzes")
    async def instructor_quizzes(request: Request):
        """Quiz builder page."""
        from .admin import QuizBuilderPage
        
        user = await get_user_with_context(request)
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/instructor/quizzes")
        
        return QuizBuilderPage(user, demo=demo)
    
    @app.get("/instructor/certificates")
    async def instructor_certificates(request: Request):
        """Certificate templates page."""
        from .admin import CertificateTemplatesPage
        
        user = await get_user_with_context(request)
        if not user:
            return RedirectResponse(f"{BASE}/login?redirect={BASE}/instructor/certificates")
        
        return CertificateTemplatesPage(user, demo=demo)
    
    logger.info("✓ LMS example app created (refactored - no duplication!)")
    return app


# -----------------------------------------------------------------------------
# Helper Components
# -----------------------------------------------------------------------------

def CourseCard(course: dict, user: dict = None, show_progress: bool = False):
    """Course card component"""
    user_id = user.get("_id") if user else None
    # Note: is_enrolled check removed - enrollment status checked in routes via database
    is_enrolled = False
    
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
            href=f"/lms-example/course/{course['id']}"
        )
    )


def LessonItem(lesson: dict, course_id: int, is_current: bool = False, base_path: str = "/lms-example"):
    """Lesson item component for course content sidebar"""
    return A(
        Div(
            Div(
                Span("✓", cls="text-success font-bold mr-2") if lesson["completed"] else Span("○", cls="text-gray-400 mr-2"),
                Span(lesson["title"], cls="font-semibold"),
                cls="flex items-center"
            ),
            Span(lesson["duration"], cls="text-sm text-gray-500"),
            cls="flex justify-between items-center"
        ),
        href=f"{base_path}/student/course/{course_id}?lesson={lesson['id']}",
        cls=f"block p-3 rounded transition-colors {'bg-primary text-white' if is_current else 'bg-base-100 hover:bg-base-300'}"
    )


def CartCourseItem(course: dict, base_path: str):
    """Cart item component for courses"""
    return Div(
        Div(
            # Course image
            A(
                Img(
                    src=course["image"],
                    alt=course["title"],
                    cls="w-24 h-24 object-cover rounded"
                ),
                href=f"{base_path}/course/{course['id']}"
            ),
            
            # Course info
            Div(
                A(
                    H3(course["title"], cls="font-semibold text-lg hover:text-blue-600"),
                    href=f"{base_path}/course/{course['id']}"
                ),
                P(f"by {course['instructor']}", cls="text-gray-600 text-sm"),
                Span(course["level"], cls="badge badge-outline badge-sm mt-1"),
                cls="flex-1 ml-4"
            ),
            
            # Price and remove
            Div(
                P(f"${course['price']:.2f}", cls="font-bold text-xl text-blue-600"),
                Form(
                    Button(
                        UkIcon("trash-2", width="16", height="16"),
                        " Remove",
                        cls="btn btn-sm btn-ghost text-error mt-2",
                        type="submit"
                    ),
                    action=f"{base_path}/cart/remove/{course['id']}",
                    method="post"
                ),
                cls="text-right"
            ),
            cls="flex items-center gap-4"
        ),
        cls="card bg-base-100 shadow p-4"
    )
