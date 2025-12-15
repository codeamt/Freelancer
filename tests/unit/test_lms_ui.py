def test_course_card_render():
    from app.add_ons.domains.lms.ui.components import CourseCard

    course = {
        "id": 123,
        "title": "Intro to Testing",
        "description": "A" * 200,
        "price": 49,
        "difficulty": "beginner",
        "thumbnail_url": "https://example.com/course.png",
    }

    html = str(CourseCard(course))

    assert "Intro to Testing" in html
    assert "View Course" in html
    assert "href=\"/lms/courses/123\"" in html
    assert "$49" in html


def test_lesson_item_render():
    from app.add_ons.domains.lms.ui.components import LessonListItem

    lesson = {"id": 7, "title": "Lesson 7", "duration_minutes": 12}

    html_pending = str(LessonListItem(lesson, is_completed=False))
    assert "Lesson 7" in html_pending
    assert "12 min" in html_pending
    assert "Start Lesson" in html_pending

    html_completed = str(LessonListItem(lesson, is_completed=True))
    assert "Lesson 7" in html_completed
    assert "Completed" in html_completed


def test_progress_bar_render():
    from app.add_ons.domains.lms.ui.components import ProgressBar

    html = str(ProgressBar(33.3333))
    assert "33.3%" in html
    assert "width: 33.3333%" in html
