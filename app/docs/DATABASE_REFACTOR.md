# Database Refactor Documentation

## Overview

Restructured database layer to separate core models from domain-specific models, and introduced universal database services for PostgreSQL, MongoDB, and DuckDB analytics.

---

## Architecture Changes

### Before (Monolithic)
```
core/db/
└── models.py  ← ALL models in one file
    ├── User (core)
    ├── Media (infrastructure)
    ├── Product (commerce)
    ├── Course (LMS)
    └── Post (social)

core/services/
└── db.py  ← MongoDB only
```

### After (Domain-Driven)
```
core/db/models/
├── __init__.py
└── user.py  ← ONLY core User model

add_ons/services/
├── postgres.py   ← PostgreSQL service
├── mongodb.py    ← MongoDB service
└── analytics.py  ← DuckDB service

add_ons/domains/
├── commerce/models/
│   ├── product.py
│   ├── order.py
│   └── inventory.py
│
├── lms/models/
│   ├── course.py
│   ├── lesson.py
│   ├── enrollment.py
│   ├── progress.py
│   ├── assessment.py
│   └── certificate.py
│
└── social/models/
    └── __init__.py  ← MongoDB collections only
```

---

## Database Services

### 1. PostgreSQL Service (`add_ons/services/postgres.py`)

**Purpose:** Relational database for structured, transactional data

**Used By:**
- Commerce (products, orders, inventory)
- LMS (courses, enrollments, assessments)
- Core (users)

**Features:**
- Async SQLAlchemy engine
- Connection pooling
- Session management
- Raw SQL execution

**Usage:**
```python
from add_ons.services.postgres import PostgresService

postgres = PostgresService()
await postgres.connect()

# Get session
async with await postgres.get_session() as session:
    result = await session.execute(query)
    await session.commit()
```

---

### 2. MongoDB Service (`add_ons/services/mongodb.py`)

**Purpose:** Document database for flexible, high-volume data

**Used By:**
- Stream (chat, events, analytics)
- Social (posts, comments, feeds)
- Analytics (logs, metrics)

**Features:**
- Async Motor client
- Generic CRUD operations
- Aggregation pipeline support
- Automatic timestamp injection

**Usage:**
```python
from add_ons/services.mongodb import MongoDBService

mongo = MongoDBService()
await mongo.connect()

# Insert document
post_id = await mongo.insert_one("posts", {
    "user_id": user_id,
    "content": "Hello world!",
    "likes_count": 0
})

# Query documents
posts = await mongo.find_many("posts", {"user_id": user_id})

# Aggregation
trending = await mongo.aggregate("posts", [
    {"$match": {"created_at": {"$gte": yesterday}}},
    {"$sort": {"likes_count": -1}},
    {"$limit": 10}
])
```

---

### 3. Analytics Service (`add_ons/services/analytics.py`)

**Purpose:** DuckDB for querying S3 Parquet files

**Used By:**
- All domains for historical analytics
- Business intelligence
- Data science / ML

**Features:**
- Query Parquet files on S3 directly
- No data warehouse needed
- SQL interface
- Pandas DataFrame output

**Usage:**
```python
from add_ons.services.analytics import AnalyticsService

analytics = AnalyticsService()

# Query S3 Parquet files
trending = analytics.query_s3_parquet(
    "s3://bucket/analytics/2025-12-*/posts.parquet",
    "WHERE views > 1000"
)

# Custom SQL
result = analytics.query("""
    SELECT 
        date_trunc('day', timestamp) as day,
        COUNT(*) as total_views
    FROM read_parquet('s3://bucket/analytics/*/views.parquet')
    GROUP BY day
    ORDER BY day DESC
""")
```

---

## Domain Models

### Core Models (`core/db/models/`)

**Only core models used across ALL domains:**

```python
# core/db/models/user.py
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, server_default=func.now())
```

**Import:**
```python
from core.db.models import User
```

---

### Commerce Models (`add_ons/domains/commerce/models/`)

**PostgreSQL models for e-commerce:**

```python
# Product
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    sku = Column(String, unique=True)

# Order
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(OrderStatus))
    total = Column(Float, nullable=False)

# OrderItem
class OrderItem(Base):
    __tablename__ = "order_items"
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price = Column(Float)

# Inventory
class Inventory(Base):
    __tablename__ = "inventory"
    product_id = Column(Integer, ForeignKey("products.id"))
    stock = Column(Integer, default=0)
    reserved = Column(Integer, default=0)
```

**Import:**
```python
from add_ons.domains.commerce.models import Product, Order, OrderItem, Inventory
```

---

### LMS Models (`add_ons/domains/lms/models/`)

**PostgreSQL models for learning management:**

```python
# Course
class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    instructor_id = Column(Integer, ForeignKey("users.id"))
    price = Column(Float, default=0.0)
    status = Column(Enum(CourseStatus))

# Lesson
class Lesson(Base):
    __tablename__ = "lessons"
    course_id = Column(Integer, ForeignKey("courses.id"))
    title = Column(String, nullable=False)
    lesson_type = Column(Enum(LessonType))
    order = Column(Integer)

# Enrollment
class Enrollment(Base):
    __tablename__ = "enrollments"
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    status = Column(Enum(EnrollmentStatus))

# Progress
class Progress(Base):
    __tablename__ = "progress"
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"))
    completed_lessons = Column(JSONB)
    progress_percent = Column(Float)

# Assessment
class Assessment(Base):
    __tablename__ = "assessments"
    course_id = Column(Integer, ForeignKey("courses.id"))
    title = Column(String)
    assessment_type = Column(Enum(AssessmentType))
    questions = Column(JSONB)

# AssessmentSubmission
class AssessmentSubmission(Base):
    __tablename__ = "assessment_submissions"
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Float)
    passed = Column(Boolean)

# Certificate
class Certificate(Base):
    __tablename__ = "certificates"
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    verification_code = Column(String, unique=True)
```

**Import:**
```python
from add_ons.domains.lms.models import (
    Course, Lesson, Enrollment, Progress,
    Assessment, AssessmentSubmission, Certificate
)
```

---

### Social Models (`add_ons/domains/social/models/`)

**MongoDB collections (no PostgreSQL models):**

Social domain uses MongoDB for flexibility:
- `posts` - User posts
- `comments` - Nested comments
- `likes` - User interactions
- `follows` - User relationships
- `activity_feed` - Denormalized feed
- `notifications` - User notifications

**Usage:**
```python
from add_ons.services.mongodb import MongoDBService

mongo = MongoDBService()

# Create post
await mongo.insert_one("posts", {
    "user_id": user_id,
    "content": "Hello!",
    "media": {"s3_key": "videos/user123/post456.mp4"},
    "likes_count": 0,
    "comments_count": 0
})

# Get user feed
feed = await mongo.aggregate("posts", [
    {"$match": {"user_id": {"$in": following_ids}}},
    {"$sort": {"created_at": -1}},
    {"$limit": 20}
])
```

---

## Domain Extensions

Domains can extend base services for custom operations:

### Example: Commerce PostgreSQL Extension

```python
# add_ons/domains/commerce/db/orders.py
from add_ons.services.postgres import PostgresService
from add_ons.domains.commerce.models import Order, OrderItem, Product

class CommercePostgresService(PostgresService):
    """Commerce-specific PostgreSQL operations"""
    
    async def create_order(self, user_id: int, items: List[Dict]):
        """Create order with ACID transaction"""
        async with await self.get_session() as session:
            async with session.begin():
                # Create order
                order = Order(user_id=user_id, total=total)
                session.add(order)
                await session.flush()
                
                # Create order items
                for item in items:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=item["product_id"],
                        quantity=item["quantity"]
                    )
                    session.add(order_item)
                    
                    # Update inventory (ACID!)
                    await session.execute(
                        update(Product)
                        .where(Product.id == item["product_id"])
                        .values(stock=Product.stock - item["quantity"])
                    )
                
                await session.commit()
                return order.id
```

### Example: Social MongoDB Extension

```python
# add_ons/domains/social/db/posts.py
from add_ons.services.mongodb import MongoDBService

class SocialMongoService(MongoDBService):
    """Social-specific MongoDB operations"""
    
    async def create_post(self, user_id: str, content: str, media: Dict = None):
        """Create post with social-specific logic"""
        post = {
            "user_id": user_id,
            "content": content,
            "media": media,
            "likes_count": 0,
            "hashtags": self._extract_hashtags(content),
            "mentions": self._extract_mentions(content)
        }
        return await self.insert_one("posts", post)
    
    async def get_user_feed(self, user_id: str, limit: int = 20):
        """Get personalized feed"""
        pipeline = [
            {"$match": {"user_id": {"$in": await self._get_following(user_id)}}},
            {"$sort": {"created_at": -1}},
            {"$limit": limit}
        ]
        return await self.aggregate("posts", pipeline)
```

---

## Database Selection Guide

### Use PostgreSQL When:
- ✅ ACID transactions required (payments, orders)
- ✅ Complex relationships (courses → lessons → assessments)
- ✅ Data integrity critical (financial data)
- ✅ Structured schema (products, users)
- ✅ SQL queries needed (reporting)

**Domains:** Commerce, LMS, Core

### Use MongoDB When:
- ✅ Flexible schema needed (different post types)
- ✅ High write volume (chat messages, events)
- ✅ Nested documents (comments, threads)
- ✅ Real-time data (feeds, notifications)
- ✅ Denormalized for speed (activity feeds)

**Domains:** Stream, Social, Analytics

### Use DuckDB When:
- ✅ Historical analytics (trends over time)
- ✅ Complex aggregations (cohort analysis)
- ✅ Ad-hoc queries (business intelligence)
- ✅ Data science (ML features)
- ✅ Query S3 directly (no data warehouse)

**Domains:** All (for analytics)

---

## Data Flow Example: Social Domain

### 1. User Posts Video
```python
# Upload to S3
from add_ons.services.storage import StorageService
storage = StorageService()
video_key = storage.upload_secure_object(
    module="social",
    user_id=user_id,
    filename=f"videos/{user_id}/{post_id}.mp4",
    data=video_data
)

# Store metadata in MongoDB
from add_ons.services.mongodb import MongoDBService
mongo = MongoDBService()
await mongo.insert_one("posts", {
    "user_id": user_id,
    "content": "Check out my video!",
    "media": {
        "type": "video",
        "s3_key": video_key,
        "thumbnail_url": f"https://cdn.../thumb.jpg"
    },
    "views_count": 0
})
```

### 2. User Views Video
```python
# Record interaction in MongoDB
await mongo.insert_one("interactions", {
    "post_id": post_id,
    "user_id": viewer_id,
    "type": "view",
    "watch_duration": 45
})

# Update counters
await mongo.update_one("posts",
    {"_id": post_id},
    {"$inc": {"views_count": 1}}
)
```

### 3. Nightly Analytics Export
```python
# Export MongoDB to S3 as Parquet
import pandas as pd

interactions = await mongo.find_many("interactions", {
    "timestamp": {"$gte": yesterday}
})

df = pd.DataFrame(interactions)
df.to_parquet(f"s3://bucket/analytics/{date}/interactions.parquet")
```

### 4. Analytics Query
```python
# Query S3 Parquet with DuckDB
from add_ons.services.analytics import AnalyticsService

analytics = AnalyticsService()
trending = analytics.query("""
    SELECT 
        post_id,
        COUNT(*) as total_views,
        COUNT(DISTINCT user_id) as unique_viewers
    FROM read_parquet('s3://bucket/analytics/2025-12-*/interactions.parquet')
    WHERE type = 'view'
    GROUP BY post_id
    ORDER BY total_views DESC
    LIMIT 10
""")
```

---

## Migration Guide

### Old Code (Before Refactor)
```python
# Old import
from core.db.models import User, Course, Product

# Old DB service
from core.services.db import DBService
db = DBService()
await db.insert_one("posts", {...})
```

### New Code (After Refactor)
```python
# Core model
from core.db.models import User

# Domain models
from add_ons.domains.lms.models import Course
from add_ons.domains.commerce.models import Product

# Database services
from add_ons.services.postgres import PostgresService
from add_ons.services.mongodb import MongoDBService

# PostgreSQL (for structured data)
postgres = PostgresService()
async with await postgres.get_session() as session:
    session.add(course)
    await session.commit()

# MongoDB (for flexible data)
mongo = MongoDBService()
await mongo.insert_one("posts", {...})
```

---

## Benefits

### 1. Separation of Concerns
- ✅ Core models separate from domain models
- ✅ Each domain owns its data
- ✅ Clear boundaries

### 2. Modularity
- ✅ Enable/disable domains independently
- ✅ Domain models only loaded when needed
- ✅ Easier testing

### 3. Scalability
- ✅ Right database for the job
- ✅ PostgreSQL for transactions
- ✅ MongoDB for flexibility
- ✅ DuckDB for analytics

### 4. Maintainability
- ✅ Smaller, focused files
- ✅ Domain-specific logic isolated
- ✅ Easier to understand

### 5. Flexibility
- ✅ Domains can extend base services
- ✅ Custom queries per domain
- ✅ Mix databases as needed

---

## Summary

**Before:**
- ❌ All models in one file
- ❌ Only MongoDB service
- ❌ No analytics support
- ❌ Mixed concerns

**After:**
- ✅ Models organized by domain
- ✅ PostgreSQL, MongoDB, DuckDB services
- ✅ S3 + Parquet analytics
- ✅ Clear separation of concerns
- ✅ Domain extensions supported

**Result:** Clean, scalable, domain-driven database architecture! 🎯
