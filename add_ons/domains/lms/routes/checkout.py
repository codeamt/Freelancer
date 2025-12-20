"""LMS Routes - Course Checkout & Enrollment"""
from fasthtml.common import *
from core.ui.layout import Layout
from core.utils.logger import get_logger
from core.services.auth import get_current_user_from_context
logger = get_logger(__name__)

# Initialize router
router_lms_checkout = APIRouter()


@router_lms_checkout.get("/lms/course/{course_id}/enroll")
async def course_enrollment_page(request: Request, course_id: str):
    """Course enrollment/checkout page"""
    user = get_current_user_from_context()
    
    if not user:
        return RedirectResponse(f"/auth/login?redirect=/lms/course/{course_id}/enroll")
    
    # Get course as product
    course = product_service.get_product(course_id)
    
    if not course:
        content = Div(
            H1("Course Not Found", cls="text-3xl font-bold text-error mb-4"),
            P("The course you're looking for doesn't exist.", cls="mb-4"),
            A("Browse Courses", href="/lms/courses", cls="btn btn-primary"),
            cls="container mx-auto px-4 py-8 text-center"
        )
        return Layout(content, title="Course Not Found | LMS")
    
    content = Div(
        H1("Enroll in Course", cls="text-3xl font-bold mb-8"),
        
        Div(
            # Course Info
            Div(
                H2(course.name, cls="text-2xl font-bold mb-4"),
                P(course.description, cls="text-gray-600 mb-6"),
                
                Div(
                    Span(f"${course.price}", cls="text-3xl font-bold text-primary"),
                    Span("One-time payment", cls="text-sm text-gray-500 ml-2"),
                    cls="mb-6"
                ),
                
                # Enrollment Form
                Form(
                    Button(
                        "Enroll Now",
                        type="submit",
                        cls="btn btn-primary btn-lg w-full"
                    ),
                    hx_post=f"/lms/course/{course_id}/checkout",
                    hx_target="#checkout-result"
                ),
                
                Div(id="checkout-result", cls="mt-4"),
                
                cls="bg-base-200 p-8 rounded-lg"
            ),
            
            cls="max-w-2xl mx-auto"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title=f"Enroll in {course.name} | LMS")


@router_lms_checkout.post("/lms/course/{course_id}/checkout")
async def process_course_checkout(request: Request, course_id: str):
    """Process course enrollment checkout"""
    user = get_current_user_from_context()
    
    if not user:
        return Div(
            P("Please sign in to enroll", cls="text-error"),
            cls="alert alert-error"
        )
    
    # Get course
    course = product_service.get_product(course_id)
    
    if not course:
        return Div(
            P("Course not found", cls="text-error"),
            cls="alert alert-error"
        )
    
    try:
        # Create checkout session for course
        base_url = str(request.base_url).rstrip('/')
        success_url = f"{base_url}/lms/enrollment/success?course_id={course_id}&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}/lms/course/{course_id}/enroll"
        
        # Create payment intent
        payment_result = payment_service.create_payment_intent(
            amount=course.price,
            currency='usd',
            metadata={
                'course_id': course_id,
                'user_id': str(user['id']),
                'type': 'course_enrollment'
            }
        )
        
        if not payment_result:
            return Div(
                P("Failed to create payment session", cls="text-error"),
                cls="alert alert-error"
            )
        
        # Create order for course enrollment
        from core.services.order import OrderItem
        order_item = OrderItem(
            product_id=course_id,
            product_name=course.name,
            price=course.price,
            quantity=1
        )
        
        order = order_service.create_order(
            user_id=str(user['id']),
            items=[order_item],
            payment_intent_id=payment_result.get('id'),
            metadata={'course_id': course_id, 'type': 'course_enrollment'}
        )
        
        logger.info(f"Created course enrollment order {order.order_id} for user {user['id']}, course {course_id}")
        
        # For demo, redirect to success (in production, would redirect to Stripe)
        return Div(
            Script(f"""
                window.location.href = '{success_url.replace('{{CHECKOUT_SESSION_ID}}', payment_result.get('id', 'demo'))}';
            """)
        )
        
    except Exception as e:
        logger.error(f"Course checkout failed: {e}")
        return Div(
            P("Enrollment failed. Please try again.", cls="text-error"),
            cls="alert alert-error"
        )


@router_lms_checkout.get("/lms/enrollment/success")
async def enrollment_success(request: Request, course_id: str, session_id: str = None):
    """Enrollment success page - mark order as paid and enroll student"""
    user = get_current_user_from_context()
    
    if not user:
        return RedirectResponse("/auth/login")
    
    user_id = str(user['id'])
    
    # Mark order as paid
    user_orders = order_service.get_user_orders(user_id)
    if user_orders:
        # Find the order for this course
        course_order = None
        for order in reversed(user_orders):
            if order.metadata.get('course_id') == course_id:
                course_order = order
                break
        
        if course_order:
            order_service.mark_order_as_paid(course_order.order_id, session_id)
            logger.info(f"Course enrollment order {course_order.order_id} marked as paid")
    
    # Get course info
    course = product_service.get_product(course_id)
    
    content = Div(
        Div(
            H1("🎉 Enrollment Successful!", cls="text-4xl font-bold text-success mb-4"),
            P(f"Welcome to {course.name if course else 'the course'}!", cls="text-xl mb-8"),
            
            Div(
                P("You now have full access to all course materials.", cls="mb-4"),
                P("Start learning right away!", cls="mb-6"),
                
                Div(
                    A("Go to Course", href=f"/lms/course/{course_id}", cls="btn btn-primary mr-2"),
                    A("My Courses", href="/lms/student/dashboard", cls="btn btn-outline"),
                    cls="flex justify-center gap-2"
                )
            ),
            
            cls="text-center max-w-2xl mx-auto bg-base-200 p-12 rounded-lg"
        ),
        cls="container mx-auto px-4 py-16"
    )
    
    return Layout(content, title="Enrollment Successful | LMS")


@router_lms_checkout.get("/lms/enrollment/cancel")
async def enrollment_cancel(request: Request, course_id: str):
    """Handle cancelled enrollment"""
    content = Div(
        Div(
            H1("Enrollment Cancelled", cls="text-3xl font-bold mb-4"),
            P("Your enrollment was not completed.", cls="text-xl mb-8"),
            
            Div(
                A("Try Again", href=f"/lms/course/{course_id}/enroll", cls="btn btn-primary mr-2"),
                A("Browse Courses", href="/lms/courses", cls="btn btn-outline"),
                cls="flex justify-center gap-2"
            ),
            
            cls="text-center max-w-2xl mx-auto bg-base-200 p-12 rounded-lg"
        ),
        cls="container mx-auto px-4 py-16"
    )
    
    return Layout(content, title="Enrollment Cancelled | LMS")
