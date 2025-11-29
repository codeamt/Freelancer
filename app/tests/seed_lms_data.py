"""
Seed script to populate LMS with sample data for testing
Run this to quickly set up demo courses, lessons, and enrollments
"""
import asyncio
from sqlalchemy import select
from app.core.db.base_class import async_session_maker
from app.core.db.models import User, Course, Lesson
from app.add_ons.lms.services import CourseService, LessonService, EnrollmentService
from app.add_ons.lms.schemas import (
    CourseCreate, LessonCreate, EnrollmentCreate,
    CourseDifficulty, CourseStatus, LessonType
)


async def create_sample_courses():
    """Create sample courses"""
    print("📚 Creating sample courses...")
    
    async with async_session_maker() as session:
        # Get first user as instructor
        result = await session.execute(select(User).limit(1))
        instructor = result.scalar_one_or_none()
        
        if not instructor:
            print("❌ No users found. Please create a user first.")
            return []
        
        courses_data = [
            {
                "title": "Python for Beginners",
                "description": "Learn Python programming from scratch. Perfect for absolute beginners with no prior coding experience.",
                "price": 49.99,
                "difficulty": CourseDifficulty.BEGINNER,
                "category": "programming",
                "duration_hours": 10.0,
                "tags": ["python", "programming", "beginner"],
                "requirements": ["Computer with internet", "Willingness to learn"],
                "learning_objectives": [
                    "Understand Python syntax and basic concepts",
                    "Write simple Python programs",
                    "Work with variables, loops, and functions",
                    "Handle errors and exceptions"
                ]
            },
            {
                "title": "Web Development with FastHTML",
                "description": "Build modern web applications using FastHTML, the Python web framework.",
                "price": 79.99,
                "difficulty": CourseDifficulty.INTERMEDIATE,
                "category": "web development",
                "duration_hours": 15.0,
                "tags": ["fasthtml", "web", "python"],
                "requirements": ["Basic Python knowledge", "HTML/CSS basics"],
                "learning_objectives": [
                    "Build web applications with FastHTML",
                    "Create dynamic routes and views",
                    "Work with databases",
                    "Deploy applications to production"
                ]
            },
            {
                "title": "Data Science Fundamentals",
                "description": "Master the fundamentals of data science including statistics, visualization, and machine learning basics.",
                "price": 99.99,
                "difficulty": CourseDifficulty.INTERMEDIATE,
                "category": "data science",
                "duration_hours": 20.0,
                "tags": ["data science", "python", "machine learning"],
                "requirements": ["Python programming", "Basic mathematics"],
                "learning_objectives": [
                    "Analyze data with pandas and numpy",
                    "Create visualizations with matplotlib",
                    "Understand statistical concepts",
                    "Build basic ML models"
                ]
            },
            {
                "title": "Advanced SQL and Database Design",
                "description": "Deep dive into SQL queries, database optimization, and schema design patterns.",
                "price": 89.99,
                "difficulty": CourseDifficulty.ADVANCED,
                "category": "database",
                "duration_hours": 12.0,
                "tags": ["sql", "database", "postgresql"],
                "requirements": ["Basic SQL knowledge", "Database concepts"],
                "learning_objectives": [
                    "Write complex SQL queries",
                    "Optimize database performance",
                    "Design normalized schemas",
                    "Implement indexing strategies"
                ]
            },
            {
                "title": "Introduction to UI/UX Design",
                "description": "Learn the principles of user interface and user experience design.",
                "price": 59.99,
                "difficulty": CourseDifficulty.BEGINNER,
                "category": "design",
                "duration_hours": 8.0,
                "tags": ["ui", "ux", "design"],
                "requirements": ["No prerequisites"],
                "learning_objectives": [
                    "Understand design principles",
                    "Create user-centered designs",
                    "Use design tools effectively",
                    "Conduct user research"
                ]
            }
        ]
        
        created_courses = []
        for course_data in courses_data:
            try:
                course = await CourseService.create_course(
                    db=session,
                    course_data=CourseCreate(**course_data),
                    instructor_id=instructor.id
                )
                # Publish the course
                course.status = CourseStatus.PUBLISHED
                await session.commit()
                await session.refresh(course)
                
                created_courses.append(course)
                print(f"✅ Created: {course.title}")
            except Exception as e:
                print(f"❌ Error creating course: {e}")
        
        print(f"\n✅ Created {len(created_courses)} courses\n")
        return created_courses


async def create_sample_lessons(courses):
    """Create sample lessons for courses"""
    print("📝 Creating sample lessons...")
    
    async with async_session_maker() as session:
        # Get first user as instructor
        result = await session.execute(select(User).limit(1))
        instructor = result.scalar_one_or_none()
        
        if not instructor or not courses:
            print("❌ Need instructor and courses to create lessons")
            return
        
        # Lessons for Python course
        python_course = courses[0]
        python_lessons = [
            {
                "title": "Introduction to Python",
                "description": "What is Python and why learn it?",
                "content": "Python is a high-level, interpreted programming language...",
                "duration_minutes": 15,
                "order": 1,
                "lesson_type": LessonType.VIDEO,
                "is_preview": True
            },
            {
                "title": "Installing Python",
                "description": "Set up your Python development environment",
                "content": "Download Python from python.org...",
                "duration_minutes": 20,
                "order": 2,
                "lesson_type": LessonType.VIDEO,
                "is_preview": True
            },
            {
                "title": "Variables and Data Types",
                "description": "Learn about Python variables and basic data types",
                "content": "Variables store data values. Python has various data types...",
                "duration_minutes": 30,
                "order": 3,
                "lesson_type": LessonType.VIDEO
            },
            {
                "title": "Control Flow - If Statements",
                "description": "Make decisions in your code with if statements",
                "content": "Control flow allows your program to make decisions...",
                "duration_minutes": 25,
                "order": 4,
                "lesson_type": LessonType.VIDEO
            },
            {
                "title": "Loops in Python",
                "description": "Repeat actions with for and while loops",
                "content": "Loops allow you to execute code multiple times...",
                "duration_minutes": 35,
                "order": 5,
                "lesson_type": LessonType.VIDEO
            }
        ]
        
        lesson_count = 0
        for lesson_data in python_lessons:
            try:
                lesson = await LessonService.create_lesson(
                    db=session,
                    lesson_data=LessonCreate(course_id=python_course.id, **lesson_data),
                    instructor_id=instructor.id
                )
                lesson_count += 1
            except Exception as e:
                print(f"❌ Error creating lesson: {e}")
        
        print(f"✅ Created {lesson_count} lessons for '{python_course.title}'\n")


async def seed_all_data():
    """Seed all sample data"""
    print("=" * 60)
    print("🌱 Seeding LMS Sample Data")
    print("=" * 60)
    print()
    
    # Create courses
    courses = await create_sample_courses()
    
    # Create lessons
    if courses:
        await create_sample_lessons(courses)
    
    print("=" * 60)
    print("✅ Sample Data Seeding Complete!")
    print("=" * 60)
    print()
    print("📊 Summary:")
    print(f"   - {len(courses)} courses created")
    print(f"   - Lessons added to first course")
    print(f"   - All courses published and ready")
    print()
    print("🚀 Next steps:")
    print("   1. Start the app: python -m app.core.app")
    print("   2. Visit: http://localhost:8002/lms/courses")
    print("   3. Browse the sample courses!")
    print()


if __name__ == "__main__":
    asyncio.run(seed_all_data())
