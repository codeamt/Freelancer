"""UI components for LMS add-on"""
from fasthtml.common import *


def CourseCard(course: dict):
    """Display a course card"""
    return Card(
        Div(
            Img(src=course.get('thumbnail_url', '/static/default-course.jpg'), 
                alt=course['title'],
                style="width: 100%; height: 200px; object-fit: cover;"),
            cls="course-thumbnail"
        ),
        Div(
            H3(course['title']),
            P(course.get('description', '')[:150] + '...' if course.get('description') else ''),
            Div(
                Span(f"${course.get('price', 0)}", cls="price"),
                Span(course.get('difficulty', 'beginner').title(), cls="difficulty"),
                cls="course-meta"
            ),
            A("View Course", href=f"/lms/courses/{course['id']}", cls="btn btn-primary"),
            cls="course-content"
        ),
        cls="course-card"
    )


def ProgressBar(percent: float):
    """Display a progress bar"""
    return Div(
        Div(
            style=f"width: {percent}%; height: 20px; background-color: #4CAF50; border-radius: 10px;",
            cls="progress-fill"
        ),
        Span(f"{percent:.1f}%", cls="progress-text"),
        cls="progress-bar",
        style="width: 100%; background-color: #e0e0e0; border-radius: 10px; position: relative;"
    )


def LessonListItem(lesson: dict, is_completed: bool = False):
    """Display a lesson in a list"""
    icon = "✓" if is_completed else "▶"
    status_class = "completed" if is_completed else "pending"
    
    return Li(
        Div(
            Span(icon, cls="lesson-icon"),
            Span(lesson['title'], cls="lesson-title"),
            Span(f"{lesson.get('duration_minutes', 0)} min", cls="lesson-duration"),
            cls=f"lesson-item {status_class}"
        ),
        A("Start Lesson", href=f"/lms/lessons/{lesson['id']}", cls="btn btn-sm")
        if not is_completed else Span("Completed", cls="badge badge-success")
    )


def EnrollmentCard(enrollment: dict):
    """Display an enrollment card with progress"""
    return Card(
        H4(enrollment.get('course_title', 'Course')),
        ProgressBar(enrollment.get('progress_percent', 0)),
        P(f"Status: {enrollment.get('status', 'active').title()}"),
        A("Continue Learning", 
          href=f"/lms/courses/{enrollment['course_id']}", 
          cls="btn btn-primary"),
        cls="enrollment-card"
    )


def AssessmentCard(assessment: dict):
    """Display an assessment card"""
    return Card(
        H4(assessment['title']),
        P(assessment.get('description', '')),
        Div(
            Span(f"Type: {assessment['assessment_type'].title()}", cls="badge"),
            Span(f"Passing Score: {assessment['passing_score']}%", cls="badge"),
            Span(f"Time Limit: {assessment.get('time_limit_minutes', 'No limit')} min", cls="badge"),
            cls="assessment-meta"
        ),
        A("Start Assessment", 
          href=f"/lms/assessments/{assessment['id']}", 
          cls="btn btn-primary"),
        cls="assessment-card"
    )


def CourseHeader(course: dict):
    """Display course header with details"""
    return Div(
        Div(
            H1(course['title']),
            P(course.get('description', ''), cls="course-description"),
            Div(
                Span(f"${course.get('price', 0)}", cls="price-tag"),
                Span(course.get('difficulty', 'beginner').title(), cls="difficulty-badge"),
                Span(f"{course.get('duration_hours', 0)} hours", cls="duration-badge"),
                cls="course-badges"
            ),
            cls="course-header-content"
        ),
        Img(src=course.get('thumbnail_url', '/static/default-course.jpg'),
            alt=course['title'],
            style="width: 100%; max-height: 400px; object-fit: cover;",
            cls="course-header-image"),
        cls="course-header"
    )


def InstructorInfo(instructor: dict):
    """Display instructor information"""
    return Div(
        H3("Instructor"),
        Div(
            Img(src=instructor.get('avatar_url', '/static/default-avatar.jpg'),
                alt=instructor.get('name', 'Instructor'),
                style="width: 60px; height: 60px; border-radius: 50%;"),
            Div(
                P(instructor.get('name', instructor.get('email', 'Instructor')), cls="instructor-name"),
                P(instructor.get('bio', ''), cls="instructor-bio"),
                cls="instructor-details"
            ),
            cls="instructor-card"
        ),
        cls="instructor-section"
    )
