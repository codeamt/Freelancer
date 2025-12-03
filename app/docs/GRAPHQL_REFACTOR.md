# GraphQL Refactor: From Add-on to Service

**Date:** December 2, 2025  
**Status:** ✅ Complete

---

## 🎯 Objective

Refactor GraphQL from a standalone add-on with generic schemas to a universal service that domains use to build their own custom GraphQL APIs.

---

## 💡 Key Insight

**Problem:** GraphQL had generic schemas (User, Media) but each domain needs domain-specific types and resolvers.

**Solution:** GraphQL should be a **service** (schema builder) that domains use to register their own types, queries, and mutations.

---

## 📊 Before vs After

### **Before (GraphQL as Add-on):**
```
add_ons/graphql/                 ← Standalone add-on
├── graphql.py                   ← Generic router (disabled)
└── schemas/                     ← Generic schemas
    ├── schema.py                ← Generic schema
    ├── types.py                 ← User, Media types
    └── resolvers.py             ← Generic resolvers

Problem:
- Generic types don't fit specific domains
- Can't customize per domain
- Disabled due to FastHTML incompatibility
```

### **After (GraphQL as Service):**
```
add_ons/services/
└── graphql.py                   ← Universal GraphQL service
    - GraphQLService (schema builder)
    - Base types (User, Media, Pagination)
    - Helper decorators
    - Singleton pattern

add_ons/domains/commerce/
└── graphql_example.py           ← Commerce-specific GraphQL
    - Product, Order types
    - Commerce queries
    - Commerce mutations

add_ons/domains/lms/
└── graphql_example.py           ← LMS-specific GraphQL
    - Course, Lesson types
    - LMS queries
    - LMS mutations

Benefits:
✅ Each domain defines its own types
✅ GraphQL service builds combined schema
✅ Domains control their own API
✅ Reusable base types
```

---

## 🔧 What Changed

### **1. Created Universal GraphQL Service**
**File:** `add_ons/services/graphql.py`

**Provides:**
- `GraphQLService` class
  - `add_query()` - Register query types
  - `add_mutation()` - Register mutation types
  - `add_type()` - Register custom types
  - `build_schema()` - Build final schema
  - `get_schema()` - Get cached schema

- Base types (common across domains)
  - `UserType` - Base user type
  - `MediaType` - Base media type
  - `PaginationInfo` - Pagination metadata
  - `ErrorType` - Standard error type
  - `BaseQuery` - Base query with health check

- Helper functions
  - `get_graphql_service()` - Singleton instance
  - `@graphql_query` - Decorator for queries
  - `@graphql_mutation` - Decorator for mutations

**Usage:**
```python
from add_ons.services.graphql import GraphQLService, BaseQuery

# Define domain types
@strawberry.type
class Product:
    id: str
    name: str
    price: float

# Define domain queries
@strawberry.type
class ProductQuery(BaseQuery):
    @strawberry.field
    async def products(self) -> List[Product]:
        return await get_products()

# Register with service
graphql = GraphQLService()
graphql.add_query(ProductQuery)
graphql.add_type(Product)

# Build schema
schema = graphql.build_schema()
```

### **2. Removed GraphQL Add-on**
```bash
❌ Deleted: add_ons/graphql/
   - graphql.py
   - schemas/
   - README.md
```

### **3. Created Domain Examples**
```
✅ add_ons/domains/commerce/graphql_example.py
   - Product, Order types
   - Commerce queries (products, orders)
   - Commerce mutations (create_product, update_product)

✅ add_ons/domains/lms/graphql_example.py
   - Course, Lesson, Enrollment types
   - LMS queries (courses, lessons, enrollments, recommendations)
   - LMS mutations (create_course, enroll_course, update_progress)
```

### **4. Updated Services Export**
**File:** `add_ons/services/__init__.py`

**Added:**
```python
from .graphql import GraphQLService, get_graphql_service, BaseQuery

__all__ = [
    "GraphQLService",
    "get_graphql_service",
    "BaseQuery",
]
```

---

## 🏗️ Architecture Pattern

### **Service Layer (Infrastructure):**
```
add_ons/services/graphql.py
├── GraphQLService (schema builder)
├── Base types (User, Media, Pagination)
├── BaseQuery (health check)
└── Helper decorators
```

### **Domain Layer (Business Logic):**
```
domains/commerce/graphql_example.py
├── Product, Order types
├── CommerceQuery (products, orders)
└── CommerceMutation (create, update)

domains/lms/graphql_example.py
├── Course, Lesson types
├── LMSQuery (courses, lessons, recommendations)
└── LMSMutation (create, enroll, progress)
```

### **Benefits:**
1. **Separation of Concerns**
   - Service = Schema building infrastructure
   - Domain = Business-specific types/resolvers

2. **Customization**
   - Each domain defines its own API
   - Types match domain models

3. **Composability**
   - Multiple domains can contribute to one schema
   - Or each domain has its own schema

4. **Flexibility**
   - Domains control their resolvers
   - Can add custom logic, auth, caching

---

## 📝 Usage Patterns

### **Pattern 1: Single Schema (All Domains)**
```python
# app.py
from add_ons.services.graphql import get_graphql_service
from add_ons.domains.commerce.graphql_example import register_commerce_graphql
from add_ons.domains.lms.graphql_example import register_lms_graphql

# Register all domains
graphql = get_graphql_service()
register_commerce_graphql()
register_lms_graphql()

# Build combined schema
schema = graphql.build_schema()

# Mount GraphQL endpoint
# (requires FastAPI integration)
```

### **Pattern 2: Per-Domain Schemas**
```python
# commerce/app.py
from add_ons.services.graphql import GraphQLService
from .graphql_example import register_commerce_graphql

# Commerce-only schema
graphql = GraphQLService()
register_commerce_graphql()
schema = graphql.build_schema()

# lms/app.py
from add_ons.services.graphql import GraphQLService
from .graphql_example import register_lms_graphql

# LMS-only schema
graphql = GraphQLService()
register_lms_graphql()
schema = graphql.build_schema()
```

### **Pattern 3: Decorator Pattern**
```python
from add_ons.services.graphql import graphql_query, graphql_mutation

@graphql_query
async def products() -> List[Product]:
    return await get_products()

@graphql_mutation
async def create_product(input: ProductInput) -> Product:
    return await save_product(input)

# Automatically registered with singleton service
```

---

## 🔌 FastHTML Integration

### **Current Status:**
GraphQL is **disabled** in FastHTML due to compatibility issues.

### **Integration Options:**

**Option 1: FastAPI Sub-App**
```python
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from add_ons.services.graphql import get_graphql_service

# Create FastAPI sub-app
graphql_app = FastAPI()
schema = get_graphql_service().build_schema()
graphql_app.include_router(
    GraphQLRouter(schema),
    prefix="/graphql"
)

# Mount in FastHTML app
app.mount("/api", graphql_app)
```

**Option 2: Custom Endpoint**
```python
@app.post("/graphql")
async def graphql_endpoint(request: Request):
    body = await request.json()
    schema = get_graphql_service().build_schema()
    result = await schema.execute(body["query"])
    return result
```

**Option 3: REST Fallback**
```python
# Use REST endpoints instead
@app.get("/api/products")
async def get_products():
    return await fetch_products()
```

---

## 🎯 Domain Example: Commerce

### **Types:**
```python
@strawberry.type
class Product:
    id: str
    name: str
    price: float
    category: str
    in_stock: bool

@strawberry.type
class Order:
    id: str
    user_id: str
    products: List[Product]
    total: float
    status: str
```

### **Queries:**
```python
@strawberry.type
class CommerceQuery(BaseQuery):
    @strawberry.field
    async def products(
        self,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Product]:
        # Filter logic
        return await db.find_products(category, min_price, max_price)
    
    @strawberry.field
    async def product(self, id: str) -> Optional[Product]:
        return await db.find_product(id)
```

### **Mutations:**
```python
@strawberry.type
class CommerceMutation:
    @strawberry.field
    async def create_product(self, input: ProductInput) -> Product:
        return await db.insert_product(input)
    
    @strawberry.field
    async def update_product(self, id: str, input: ProductInput) -> Product:
        return await db.update_product(id, input)
```

### **Registration:**
```python
def register_commerce_graphql():
    graphql = GraphQLService()
    graphql.add_query(CommerceQuery)
    graphql.add_mutation(CommerceMutation)
    graphql.add_type(Product)
    graphql.add_type(Order)
    return graphql
```

---

## 🎯 Domain Example: LMS

### **Types:**
```python
@strawberry.type
class Course:
    id: str
    title: str
    instructor_name: str
    duration_hours: int
    price: float
    rating: Optional[float]

@strawberry.type
class Enrollment:
    id: str
    user_id: str
    course_id: str
    progress: float  # 0-100
    completed: bool
```

### **Queries:**
```python
@strawberry.type
class LMSQuery(BaseQuery):
    @strawberry.field
    async def courses(
        self,
        category: Optional[str] = None,
        min_rating: Optional[float] = None
    ) -> List[Course]:
        return await db.find_courses(category, min_rating)
    
    @strawberry.field
    async def recommend_courses(
        self,
        user_id: str,
        interests: List[str]
    ) -> List[Course]:
        # ML-based recommendations
        return await ai.recommend_courses(user_id, interests)
```

### **Mutations:**
```python
@strawberry.type
class LMSMutation:
    @strawberry.field
    async def enroll_course(self, user_id: str, course_id: str) -> Enrollment:
        return await db.create_enrollment(user_id, course_id)
    
    @strawberry.field
    async def update_progress(self, enrollment_id: str, progress: float) -> Enrollment:
        return await db.update_enrollment_progress(enrollment_id, progress)
```

---

## 🔒 Security & Auth

### **Protecting Resolvers:**
```python
from add_ons.services.auth import require_role, get_current_user

@strawberry.type
class SecureQuery(BaseQuery):
    @strawberry.field
    @require_role("admin")
    async def admin_data(self, info) -> str:
        # Only admins can access
        return "Secret data"
    
    @strawberry.field
    async def user_data(self, info) -> str:
        user = await get_current_user(info.context["request"])
        if not user:
            raise Exception("Not authenticated")
        return f"Data for {user['email']}"
```

### **Context Injection:**
```python
# In GraphQL setup
schema = graphql.build_schema()

# In endpoint
@app.post("/graphql")
async def graphql_endpoint(request: Request):
    context = {
        "request": request,
        "user": await get_current_user(request)
    }
    result = await schema.execute(
        query=body["query"],
        context_value=context
    )
    return result
```

---

## 📊 Comparison: GraphQL vs REST

### **When to Use GraphQL:**
- ✅ Complex, nested data requirements
- ✅ Multiple resources in one request
- ✅ Client-specific data needs
- ✅ Mobile apps (bandwidth optimization)
- ✅ Flexible querying

### **When to Use REST:**
- ✅ Simple CRUD operations
- ✅ File uploads
- ✅ Caching requirements
- ✅ FastHTML/HTMX integration
- ✅ Simpler implementation

### **Recommendation:**
- Use **REST** for FastHTML examples (better compatibility)
- Use **GraphQL** when you need flexibility and have FastAPI integration

---

## ✅ Summary

### **What We Did:**
1. ✅ Created universal GraphQL service (`add_ons/services/graphql.py`)
2. ✅ Removed GraphQL add-on with generic schemas
3. ✅ Created domain-specific GraphQL examples
4. ✅ Established pattern for domain GraphQL integration

### **Benefits:**
- 🎨 **Custom APIs** - Each domain defines its own types
- 🔧 **Universal Service** - Schema building is reusable
- 📦 **Better Organization** - Clear service/domain separation
- 🚀 **Flexibility** - Domains control their resolvers

### **Architecture:**
```
Services (Infrastructure)  →  Domains (Business Logic)
   graphql.py              →  commerce/graphql_example.py
   (Schema builder)        →  (Product types & queries)
```

### **Pattern:**
Same as Auth refactor - infrastructure provides tools, domains implement business logic.

---

**Status:** ✅ Complete  
**Integration:** ⚙️ Requires FastAPI (currently disabled)  
**Recommendation:** ⭐ Use this pattern for all infrastructure services
