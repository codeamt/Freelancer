# LMS (Learning Management System) Add-on

A comprehensive Learning Management System add-on for the Freelancer platform, enabling course creation, enrollment, progress tracking, and assessments.

## Features

### ✅ Implemented

#### Course Management
- **Create, Read, Update, Delete (CRUD)** operations for courses
- Course status management (Draft, Published, Archived)
- Course difficulty levels (Beginner, Intermediate, Advanced)
- Rich course metadata (tags, requirements, learning objectives)
- Instructor assignment and verification
- Course statistics (enrollments, completion rates)

#### Lesson Management
- Multiple lesson types (Video, Text, Quiz, Assignment)
- Lesson ordering and sequencing
- Preview lessons for non-enrolled users
- Lesson resources and attachments
- Navigation (next/previous lesson)

#### Enrollment System
- User enrollment in courses
- Enrollment status tracking (Active, Completed, Dropped, Expired)
- Payment integration support
- Access control and verification
- Enrollment expiration dates

#### Progress Tracking
- Real-time progress calculation
- Completed lessons tracking
- Time spent tracking
- Last accessed lesson tracking
- Course completion detection
- Detailed progress reports

#### Assessment System
- Multiple assessment types (Quiz, Exam, Assignment)
- Question bank with various question types
- Automatic grading for objective questions
- Attempt limits and time limits
- Passing score configuration
- Submission history and best score tracking

#### Certificate System
- Certificate generation on course completion
- Unique verification codes
- Certificate URL storage

## Database Schema

### Tables Created
- `courses` - Course information
- `lessons` - Lesson content and metadata
- `enrollments` - User course enrollments
- `progress` - Student progress tracking
- `assessments` - Course assessments/quizzes
- `assessment_submissions` - Student assessment submissions
- `certificates` - Course completion certificates

### Enums
- `CourseStatus`: DRAFT, PUBLISHED, ARCHIVED
- `CourseDifficulty`: BEGINNER, INTERMEDIATE, ADVANCED
- `LessonType`: VIDEO, TEXT, QUIZ, ASSIGNMENT
- `EnrollmentStatus`: ACTIVE, COMPLETED, DROPPED, EXPIRED
- `AssessmentType`: QUIZ, EXAM, ASSIGNMENT

## API Endpoints

### Course Endpoints
- `GET /lms/courses` - List all courses (with filters)
- `GET /lms/courses/{id}` - Get course details
- `POST /lms/courses` - Create a new course (instructor)
- `PUT /lms/courses/{id}` - Update course (instructor)
- `DELETE /lms/courses/{id}` - Delete course (instructor)
- `POST /lms/courses/{id}/publish` - Publish course (instructor)

### Enrollment Endpoints
- `POST /lms/enroll` - Enroll in a course
- `GET /lms/my-courses` - Get user's enrolled courses
- `GET /lms/courses/{id}/progress` - Get course progress
- `POST /lms/lessons/{id}/complete` - Mark lesson as complete

## Services

### CourseService
- Course CRUD operations
- Course statistics
- Publishing and archiving
- Instructor verification

### LessonService
- Lesson CRUD operations
- Lesson ordering and reordering
- Next/previous lesson navigation
- Preview lesson filtering

### EnrollmentService
- User enrollment management
- Access verification
- Enrollment status updates
- Course and user enrollment queries

### ProgressService
- Progress tracking and calculation
- Lesson completion marking
- Time tracking
- Detailed progress reports

### AssessmentService
- Assessment creation and management
- Submission handling
- Automatic grading
- Attempt tracking

## UI Components

### Components
- `CourseCard` - Display course in grid/list
- `ProgressBar` - Visual progress indicator
- `LessonListItem` - Lesson in course curriculum
- `EnrollmentCard` - User's enrolled course card
- `AssessmentCard` - Assessment display
- `CourseHeader` - Course detail header
- `InstructorInfo` - Instructor information display

### Pages
- `CourseCatalogPage` - Browse all courses
- `CourseDetailPage` - View course details
- `MyCoursesPage` - User's enrolled courses
- `LessonViewPage` - View and complete lessons
- `InstructorDashboardPage` - Instructor course management

## Setup Instructions

### 1. Run Database Migration

```bash
cd app/core/migrations
alembic upgrade head
```

This will create all necessary LMS tables.

### 2. Environment Variables

No additional environment variables required. The LMS uses the existing database connection.

### 3. Access the LMS

The LMS is mounted at `/lms` in your application:
- Course catalog: `http://localhost:8002/lms/courses`
- My courses: `http://localhost:8002/lms/my-courses`

## Usage Examples

### Creating a Course (Instructor)

```python
from app.add_ons.lms.services import CourseService
from app.add_ons.lms.schemas import CourseCreate

course_data = CourseCreate(
    title="Introduction to Python",
    description="Learn Python from scratch",
    price=49.99,
    difficulty="beginner",
    category="programming",
    tags=["python", "programming", "beginner"],
    learning_objectives=[
        "Understand Python syntax",
        "Write basic programs",
        "Work with data structures"
    ]
)

course = await CourseService.create_course(db, course_data, instructor_id)
```

### Enrolling in a Course

```python
from app.add_ons.lms.services import EnrollmentService
from app.add_ons.lms.schemas import EnrollmentCreate

enrollment_data = EnrollmentCreate(
    course_id=1,
    payment_id="stripe_payment_123"
)

enrollment = await EnrollmentService.enroll_user(db, user_id, enrollment_data)
```

### Tracking Progress

```python
from app.add_ons.lms.services import ProgressService

# Mark lesson as complete
progress = await ProgressService.mark_lesson_complete(
    db, 
    enrollment_id=1, 
    lesson_id=5,
    time_spent_minutes=30
)

# Get detailed progress
progress_detail = await ProgressService.get_course_progress_detail(
    db, 
    user_id=1, 
    course_id=1
)
```

## Architecture

### Service Layer
All business logic is contained in service classes, making it easy to:
- Test functionality independently
- Reuse logic across different endpoints
- Maintain separation of concerns

### Schema Layer
Pydantic models provide:
- Request/response validation
- Type safety
- Automatic API documentation
- Data serialization

### Database Layer
SQLAlchemy models with:
- Async support for better performance
- Relationship management
- Migration support via Alembic

## Integration with Other Add-ons

### Commerce Integration
- Course pricing and payment processing
- Payment ID tracking in enrollments
- Revenue tracking for instructors

### Media Integration
- Course thumbnails
- Lesson videos
- Resource attachments

### Social Integration
- Course reviews and ratings (future)
- Discussion forums (future)
- Student interactions (future)

## Future Enhancements

### Planned Features
- [ ] Course reviews and ratings
- [ ] Discussion forums per course
- [ ] Live sessions/webinars
- [ ] Course bundles and subscriptions
- [ ] Advanced analytics dashboard
- [ ] Gamification (badges, points)
- [ ] Mobile app support
- [ ] Offline course downloads
- [ ] Multi-language support
- [ ] Course recommendations

### Technical Improvements
- [ ] Caching for course listings
- [ ] Full-text search for courses
- [ ] Video streaming optimization
- [ ] Real-time progress updates (WebSocket)
- [ ] Bulk operations for instructors
- [ ] Export course data
- [ ] Import courses from other platforms

## Testing

### Running Tests
```bash
# Run all LMS tests
pytest app/add_ons/lms/tests/

# Run specific test file
pytest app/add_ons/lms/tests/test_course_service.py

# Run with coverage
pytest --cov=app/add_ons/lms app/add_ons/lms/tests/
```

### Test Coverage
- Unit tests for all services
- Integration tests for API endpoints
- End-to-end tests for user flows

## Performance Considerations

### Database Indexes
The migration creates indexes on:
- `courses.instructor_id`
- `courses.status`
- `courses.category`
- `lessons.course_id`
- `enrollments.user_id`
- `enrollments.course_id`
- `progress.enrollment_id`

### Query Optimization
- Use `selectinload` for relationships to avoid N+1 queries
- Pagination for large result sets
- Filtered queries to reduce data transfer

## Security

### Access Control
- Instructors can only modify their own courses
- Students can only access enrolled courses
- Preview lessons available to all users
- Assessment answers hidden from students

### Data Validation
- All inputs validated via Pydantic schemas
- SQL injection prevention via SQLAlchemy
- XSS prevention in UI components

## Support

For issues, questions, or feature requests, please refer to the main project documentation or contact the development team.

## License

This add-on is part of the Freelancer platform and follows the same license.
