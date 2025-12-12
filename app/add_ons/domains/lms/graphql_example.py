"""
Example: LMS Domain GraphQL Integration

Shows how LMS domain adds its own GraphQL queries and types.
"""

import strawberry
from typing import List, Optional
from datetime import datetime
from add_ons.services.graphql import GraphQLService, BaseQuery

# -----------------------------------------------------------------------------
# LMS Types
# -----------------------------------------------------------------------------

@strawberry.type
class Course:
    """Course type for LMS"""
    id: str
    title: str
    description: Optional[str] = None
    instructor_id: str
    instructor_name: str
    duration_hours: int
    price: float
    rating: Optional[float] = None
    enrolled_count: int = 0
    created_at: datetime


@strawberry.type
class Lesson:
    """Lesson type for LMS"""
    id: str
    course_id: str
    title: str
    content: str
    order: int
    duration_minutes: int


@strawberry.type
class Enrollment:
    """Enrollment type for LMS"""
    id: str
    user_id: str
    course_id: str
    progress: float  # 0-100
    completed: bool
    enrolled_at: datetime


@strawberry.input
class CourseInput:
    """Input for creating/updating courses"""
    title: str
    description: Optional[str] = None
    duration_hours: int
    price: float


# -----------------------------------------------------------------------------
# LMS Queries
# -----------------------------------------------------------------------------

@strawberry.type
class LMSQuery(BaseQuery):
    """LMS-specific GraphQL queries"""
    
    @strawberry.field
    async def courses(
        self,
        category: Optional[str] = None,
        instructor_id: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: int = 10
    ) -> List[Course]:
        """Get courses with optional filters"""
        from core.services import get_db_service
        db = get_db_service()
        
        filters = {}
        if category:
            filters["category"] = category
        if instructor_id:
            filters["instructor_id"] = instructor_id
        if min_rating:
            filters["rating"] = {"$gte": min_rating}
        
        courses_data = await db.find_many("courses", filters, limit=limit)
        
        return [Course(
            id=str(c.get("id", c.get("_id"))),
            title=c["title"],
            description=c.get("description", ""),
            instructor_id=str(c["instructor_id"]),
            instructor_name=c.get("instructor_name", ""),
            duration_hours=c.get("duration_hours", 0),
            price=c.get("price", 0.0),
            rating=c.get("rating", 0.0),
            enrolled_count=c.get("enrolled_count", 0),
            created_at=c.get("created_at", datetime.utcnow())
        ) for c in courses_data]
    
    @strawberry.field
    async def course(self, id: str) -> Optional[Course]:
        """Get a single course by ID"""
        from core.services import get_db_service
        db = get_db_service()
        
        course_data = await db.find_one("courses", {"id": id})
        if not course_data:
            return None
        
        return Course(
            id=str(course_data.get("id", course_data.get("_id"))),
            title=course_data["title"],
            description=course_data.get("description", ""),
            instructor_id=str(course_data["instructor_id"])
        )
    
    @strawberry.field
    async def lessons(self, course_id: str) -> List[Lesson]:
        """Get lessons for a course"""
        from core.services import get_db_service
        db = get_db_service()
        
        lessons_data = await db.find_many("lessons", {"course_id": course_id})
        
        return [Lesson(
            id=str(l.get("id", l.get("_id"))),
            course_id=l["course_id"],
            title=l["title"],
            content=l.get("content", "")
        ) for l in lessons_data]
    
    @strawberry.field
    async def enrollments(self, user_id: str) -> List[Enrollment]:
        """Get enrollments for a user"""
        from core.services import get_db_service
        db = get_db_service()
        
        enrollments_data = await db.find_many("enrollments", {"user_id": user_id})
        
        return [Enrollment(
            id=str(e.get("id", e.get("_id"))),
            user_id=e["user_id"],
            course_id=e["course_id"],
            status=e.get("status", "active")
        ) for e in enrollments_data]
    
    @strawberry.field
    async def recommend_courses(
        self,
        user_id: str,
        interests: List[str],
        limit: int = 5
    ) -> List[Course]:
        """Recommend courses based on user interests"""
        # TODO: Implement ML-based recommendations
        return []


# -----------------------------------------------------------------------------
# LMS Mutations
# -----------------------------------------------------------------------------

@strawberry.type
class LMSMutation:
    """LMS-specific GraphQL mutations"""
    
    @strawberry.field
    async def create_course(self, input: CourseInput) -> Course:
        """Create a new course"""
        from core.services import get_db_service
        db = get_db_service()
        
        course_data = {
            "title": input.title,
            "description": input.description,
            "instructor_id": input.instructor_id
        }
        
        result = await db.insert("courses", course_data)
        
        return Course(
            id=str(result.get("id", result.get("_id"))),
            title=result["title"],
            description=input.description,
            instructor_id="instructor-id",
            instructor_name="Instructor Name",
            duration_hours=input.duration_hours,
            price=input.price,
            created_at=datetime.utcnow()
        )
    
    @strawberry.field
    async def enroll_course(self, user_id: str, course_id: str) -> Enrollment:
        """Enroll a user in a course"""
        # TODO: Implement actual enrollment logic
        return Enrollment(
            id="enrollment-id",
            user_id=user_id,
            course_id=course_id,
            progress=0.0,
            completed=False,
            enrolled_at=datetime.utcnow()
        )
    
    @strawberry.field
    async def update_progress(
        self,
        enrollment_id: str,
        progress: float
    ) -> Enrollment:
        """Update course progress"""
        # TODO: Implement actual progress update
        return Enrollment(
            id=enrollment_id,
            user_id="user-id",
            course_id="course-id",
            progress=progress,
            completed=progress >= 100.0,
            enrolled_at=datetime.utcnow()
        )


# -----------------------------------------------------------------------------
# Register with GraphQL Service
# -----------------------------------------------------------------------------

def register_lms_graphql():
    """Register LMS GraphQL types with the service"""
    graphql = GraphQLService()
    
    # Add queries
    graphql.add_query(LMSQuery)
    
    # Add mutations
    graphql.add_mutation(LMSMutation)
    
    # Add types
    graphql.add_type(Course)
    graphql.add_type(Lesson)
    graphql.add_type(Enrollment)
    
    return graphql


# Usage in domain app:
# from .graphql_example import register_lms_graphql
# graphql = register_lms_graphql()
# schema = graphql.build_schema()
