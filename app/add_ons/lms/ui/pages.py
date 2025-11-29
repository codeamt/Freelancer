"""UI pages for LMS add-on"""
from fasthtml.common import *
from .components import CourseCard, EnrollmentCard, ProgressBar, CourseHeader, InstructorInfo


def CourseCatalogPage(courses: list, page: int = 1, total_pages: int = 1):
    """Course catalog page"""
    return Div(
        H1("Course Catalog"),
        Div(
            Form(
                Input(type="text", name="search", placeholder="Search courses..."),
                Select(
                    Option("All Categories", value=""),
                    Option("Programming", value="programming"),
                    Option("Design", value="design"),
                    Option("Business", value="business"),
                    Option("Marketing", value="marketing"),
                    name="category"
                ),
                Button("Search", type="submit"),
                method="get",
                action="/lms/courses",
                cls="search-form"
            ),
            cls="course-filters"
        ),
        Div(
            *[CourseCard(course) for course in courses],
            cls="course-grid"
        ),
        Div(
            *[
                A(str(i), href=f"/lms/courses?page={i}", 
                  cls="page-link active" if i == page else "page-link")
                for i in range(1, total_pages + 1)
            ],
            cls="pagination"
        ) if total_pages > 1 else None,
        cls="course-catalog"
    )


def CourseDetailPage(course: dict, lessons: list = None, is_enrolled: bool = False):
    """Course detail page"""
    lessons = lessons or []
    
    return Div(
        CourseHeader(course),
        Div(
            Div(
                H2("Course Content"),
                Ul(
                    *[
                        Li(
                            Span(f"{i+1}. {lesson['title']}"),
                            Span(f"{lesson.get('duration_minutes', 0)} min", cls="duration")
                        )
                        for i, lesson in enumerate(lessons)
                    ],
                    cls="lesson-list"
                ),
                H2("What You'll Learn"),
                Ul(
                    *[Li(obj) for obj in course.get('learning_objectives', [])],
                    cls="objectives-list"
                ) if course.get('learning_objectives') else P("No learning objectives specified."),
                H2("Requirements"),
                Ul(
                    *[Li(req) for req in course.get('requirements', [])],
                    cls="requirements-list"
                ) if course.get('requirements') else P("No requirements."),
                cls="course-main-content"
            ),
            Div(
                Card(
                    H3(f"${course.get('price', 0)}"),
                    Form(
                        Input(type="hidden", name="course_id", value=course['id']),
                        Button(
                            "Enroll Now" if not is_enrolled else "Go to Course",
                            type="submit",
                            cls="btn btn-primary btn-large"
                        ),
                        method="post",
                        action="/lms/enroll" if not is_enrolled else f"/lms/courses/{course['id']}/learn"
                    ),
                    P(f"⏱ {course.get('duration_hours', 0)} hours"),
                    P(f"📚 {len(lessons)} lessons"),
                    P(f"📊 {course.get('difficulty', 'beginner').title()} level"),
                    cls="enrollment-card"
                ),
                InstructorInfo(course.get('instructor', {})) if course.get('instructor') else None,
                cls="course-sidebar"
            ),
            cls="course-detail-layout"
        ),
        cls="course-detail-page"
    )


def MyCoursesPage(enrollments: list):
    """My courses page showing user's enrollments"""
    return Div(
        H1("My Courses"),
        Div(
            *[EnrollmentCard(enrollment) for enrollment in enrollments]
            if enrollments else P("You haven't enrolled in any courses yet."),
            cls="enrollments-grid"
        ),
        A("Browse Courses", href="/lms/courses", cls="btn btn-primary"),
        cls="my-courses-page"
    )


def LessonViewPage(lesson: dict, course: dict, progress: dict = None):
    """Lesson view page"""
    return Div(
        Div(
            A("← Back to Course", href=f"/lms/courses/{course['id']}", cls="back-link"),
            H1(lesson['title']),
            P(lesson.get('description', ''), cls="lesson-description"),
            cls="lesson-header"
        ),
        Div(
            Div(
                # Video player or content
                Div(
                    Iframe(
                        src=lesson.get('video_url', ''),
                        width="100%",
                        height="500px",
                        frameborder="0",
                        allowfullscreen=True
                    ) if lesson.get('video_url') else Div(
                        P("No video available"),
                        cls="no-video"
                    ),
                    cls="lesson-video"
                ),
                Div(
                    H3("Lesson Content"),
                    Div(lesson.get('content', 'No content available.'), cls="lesson-text"),
                    cls="lesson-content-section"
                ),
                cls="lesson-main"
            ),
            Div(
                Card(
                    H3("Progress"),
                    ProgressBar(progress.get('progress_percent', 0)) if progress else P("Not started"),
                    Form(
                        Input(type="hidden", name="lesson_id", value=lesson['id']),
                        Input(type="hidden", name="enrollment_id", value=progress.get('enrollment_id', '')),
                        Button("Mark as Complete", type="submit", cls="btn btn-success"),
                        method="post",
                        action=f"/lms/lessons/{lesson['id']}/complete"
                    ),
                    cls="progress-card"
                ),
                cls="lesson-sidebar"
            ),
            cls="lesson-layout"
        ),
        cls="lesson-view-page"
    )


def InstructorDashboardPage(courses: list, stats: dict = None):
    """Instructor dashboard page"""
    stats = stats or {}
    
    return Div(
        H1("Instructor Dashboard"),
        Div(
            Card(
                H3("Total Courses"),
                P(str(stats.get('total_courses', len(courses))), cls="stat-number"),
                cls="stat-card"
            ),
            Card(
                H3("Total Students"),
                P(str(stats.get('total_students', 0)), cls="stat-number"),
                cls="stat-card"
            ),
            Card(
                H3("Total Revenue"),
                P(f"${stats.get('total_revenue', 0)}", cls="stat-number"),
                cls="stat-card"
            ),
            cls="stats-grid"
        ),
        Div(
            H2("Your Courses"),
            A("Create New Course", href="/lms/courses/create", cls="btn btn-primary"),
            Div(
                *[CourseCard(course) for course in courses]
                if courses else P("You haven't created any courses yet."),
                cls="course-grid"
            ),
            cls="instructor-courses"
        ),
        cls="instructor-dashboard"
    )
