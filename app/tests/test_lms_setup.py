"""
Test script to verify LMS setup and basic functionality
Run this after migration to ensure everything is working
"""
import asyncio
from sqlalchemy import select
from app.core.db.base_class import async_session_maker
from app.core.db.models import Course, Lesson, Enrollment, User
from app.add_ons.lms.services import CourseService, EnrollmentService
from app.add_ons.lms.schemas import CourseCreate, EnrollmentCreate


async def test_database_tables():
    """Test that all LMS tables exist"""
    print("🔍 Testing database tables...")
    
    async with async_session_maker() as session:
        try:
            # Test Course table
            result = await session.execute(select(Course).limit(1))
            print("✅ Course table exists")
            
            # Test Lesson table
            result = await session.execute(select(Lesson).limit(1))
            print("✅ Lesson table exists")
            
            # Test Enrollment table
            result = await session.execute(select(Enrollment).limit(1))
            print("✅ Enrollment table exists")
            
            print("\n✅ All LMS tables are properly created!\n")
            return True
        except Exception as e:
            print(f"❌ Database table error: {e}")
            return False


async def test_course_creation():
    """Test creating a course"""
    print("🔍 Testing course creation...")
    
    async with async_session_maker() as session:
        try:
            # Check if we have at least one user
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
            if not user:
                print("⚠️  No users found. Create a user first to test course creation.")
                return False
            
            # Create a test course
            course_data = CourseCreate(
                title="Test Course - Python Basics",
                description="A test course to verify LMS functionality",
                price=0.0,
                difficulty="beginner",
                category="programming",
                tags=["python", "test"],
                learning_objectives=["Learn Python basics", "Write simple programs"]
            )
            
            course = await CourseService.create_course(
                db=session,
                course_data=course_data,
                instructor_id=user.id
            )
            
            print(f"✅ Course created successfully! ID: {course.id}")
            print(f"   Title: {course.title}")
            print(f"   Instructor ID: {course.instructor_id}")
            print(f"   Status: {course.status.value}\n")
            
            return True
        except Exception as e:
            print(f"❌ Course creation error: {e}")
            return False


async def test_course_listing():
    """Test listing courses"""
    print("🔍 Testing course listing...")
    
    async with async_session_maker() as session:
        try:
            courses, total = await CourseService.get_courses(
                db=session,
                page=1,
                page_size=10
            )
            
            print(f"✅ Found {total} course(s)")
            for course in courses:
                print(f"   - {course.title} (ID: {course.id})")
            print()
            
            return True
        except Exception as e:
            print(f"❌ Course listing error: {e}")
            return False


async def test_enrollment():
    """Test enrollment functionality"""
    print("🔍 Testing enrollment...")
    
    async with async_session_maker() as session:
        try:
            # Get a user and a course
            user_result = await session.execute(select(User).limit(1))
            user = user_result.scalar_one_or_none()
            
            course_result = await session.execute(select(Course).limit(1))
            course = course_result.scalar_one_or_none()
            
            if not user or not course:
                print("⚠️  Need at least one user and one course to test enrollment")
                return False
            
            # Try to enroll
            enrollment_data = EnrollmentCreate(course_id=course.id)
            enrollment = await EnrollmentService.enroll_user(
                db=session,
                user_id=user.id,
                enrollment_data=enrollment_data
            )
            
            if enrollment:
                print(f"✅ Enrollment created successfully! ID: {enrollment.id}")
                print(f"   User ID: {enrollment.user_id}")
                print(f"   Course ID: {enrollment.course_id}")
                print(f"   Status: {enrollment.status.value}\n")
                return True
            else:
                print("⚠️  User may already be enrolled in this course\n")
                return True
                
        except Exception as e:
            print(f"❌ Enrollment error: {e}")
            return False


async def run_all_tests():
    """Run all LMS tests"""
    print("=" * 60)
    print("🚀 LMS Setup Verification")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Database tables
    results.append(await test_database_tables())
    
    # Test 2: Course creation
    results.append(await test_course_creation())
    
    # Test 3: Course listing
    results.append(await test_course_listing())
    
    # Test 4: Enrollment
    results.append(await test_enrollment())
    
    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! LMS is ready to use.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
    
    print("\n💡 Next steps:")
    print("   1. Start the application: python -m app.core.app")
    print("   2. Visit: http://localhost:8002/lms/courses")
    print("   3. Create courses and enroll students!")
    print()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
