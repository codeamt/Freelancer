# Examples Integration Guide

## Overview

The `app/examples` directory has been updated to use **DBService** and **state system integration** instead of in-memory storage. Examples now leverage existing domain modules (commerce, LMS) to avoid code duplication.

## What Changed

### **E-Shop Example** (`examples/eshop/app.py`)

#### Before
```python
# In-memory cart storage
cart_storage = {}  # {user_id: {product_id: quantity}}

# Manual cart management
if user_id not in cart_storage:
    cart_storage[user_id] = {}
cart_storage[user_id][product_id] = quantity
```

#### After
```python
# Uses CartService from commerce domain
from add_ons.domains.commerce.services.cart_service import CartService
from core.services import get_db_service
from core.services.auth.context import set_user_context, UserContext

db = get_db_service()
cart_service = CartService()

# State-aware cart operations
await cart_service.add_item(user_id, product_id, quantity, price)
cart = await cart_service.get_cart(user_id)
await cart_service.clear_cart(user_id)

# Orders stored in database
await db.insert("orders", order_data)
```

#### Key Updates
1. **CartService Integration** - Uses existing commerce domain service
2. **DBService for Orders** - Orders persisted to database
3. **State System** - User context set for audit trails
4. **No In-Memory Storage** - All data in database/Redis

---

### **LMS Example** (`examples/lms/app.py`)

#### Before
```python
# In-memory enrollment storage
enrollments = {}  # {user_id: [course_ids]}

# Manual enrollment management
if user_id not in enrollments:
    enrollments[user_id] = []
enrollments[user_id].append(course_id)
```

#### After
```python
# Uses DBService for enrollments
from core.services import get_db_service
from core.services.auth.context import set_user_context, UserContext

db = get_db_service()

# Database-backed enrollments
enrollment_data = {
    "user_id": user_id,
    "course_id": course_id,
    "status": "active",
    "progress": 0
}
await db.insert("enrollments", enrollment_data)

# Check enrollment
enrollment = await db.find_one("enrollments", {"user_id": user_id, "course_id": course_id})
is_enrolled = enrollment is not None

# Get user enrollments
enrollments_data = await db.find_many("enrollments", {"user_id": user_id}, limit=100)
```

#### Key Updates
1. **DBService for Enrollments** - All enrollments in database
2. **State System** - User context for audit trails
3. **Shared Data** - Still uses `SAMPLE_COURSES` from LMS domain
4. **No In-Memory Storage** - Database-backed persistence

---

## State System Integration

Both examples now set user context for state-aware operations:

```python
async def get_user(request: Request):
    """Get current user from request and set context"""
    user = await get_current_user_from_request(request, auth_service)
    if user:
        # Set user context for state system
        user_context = UserContext(
            user_id=user.id,
            email=user.email,
            role=getattr(user, 'role', 'user'),
            ip_address=request.client.host if request.client else None
        )
        set_user_context(user_context)
    return user
```

### Benefits
- **Automatic audit trails** - All DB operations include user_id, role, IP
- **Permission-aware** - Operations respect user context
- **Consistent logging** - Centralized user tracking

---

## Database Schema Required

### E-Shop Tables

#### `carts` (via CartService)
```sql
-- Managed by CartService in Redis/Database
-- Structure: {user_id: {items: [{product_id, quantity, price}]}}
```

#### `orders`
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    total DECIMAL(10, 2) NOT NULL,
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### LMS Tables

#### `enrollments`
```sql
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    progress INTEGER DEFAULT 0,
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, course_id)
);
```

---

## Usage Examples

### E-Shop Example

#### Add to Cart
```python
@app.post("/cart/add/{product_id}")
async def add_to_cart(request: Request, product_id: int):
    user = await get_user(request)  # Sets user context
    
    # CartService automatically uses user context for audit
    await cart_service.add_item(
        user_id=user.id,
        product_id=product_id,
        quantity=1,
        price=product["price"]
    )
```

#### Complete Checkout
```python
@app.post("/checkout/complete")
async def complete_checkout(request: Request):
    user = await get_user(request)  # Sets user context
    
    # Store order with automatic audit fields
    order_data = {
        "user_id": user.id,
        "status": "completed",
        "total": calculate_total()
    }
    await db.insert("orders", order_data)  # Includes created_by, updated_by
    
    # Clear cart
    await cart_service.clear_cart(user.id)
```

### LMS Example

#### Enroll in Course
```python
@app.post("/enroll/{course_id}")
async def enroll_course(request: Request, course_id: int):
    user = await get_user(request)  # Sets user context
    
    # Check existing enrollment
    existing = await db.find_one("enrollments", {
        "user_id": user.get("_id"),
        "course_id": course_id
    })
    
    if not existing:
        # Create enrollment with automatic audit fields
        enrollment_data = {
            "user_id": user.get("_id"),
            "course_id": course_id,
            "status": "active",
            "progress": 0
        }
        await db.insert("enrollments", enrollment_data)
```

#### Student Dashboard
```python
@app.get("/student/dashboard")
async def student_dashboard(request: Request):
    user = await get_user(request)  # Sets user context
    
    # Get all enrollments from database
    enrollments_data = await db.find_many(
        "enrollments",
        {"user_id": user.get("_id")},
        limit=100
    )
    
    # Map to courses
    enrolled_course_ids = [e["course_id"] for e in enrollments_data]
    enrolled_courses = [get_course_by_id(cid) for cid in enrolled_course_ids]
```

---

## Comparison: Before vs After

### E-Shop Example

| Feature | Before | After |
|---------|--------|-------|
| Cart Storage | In-memory dict | CartService (Redis/DB) |
| Order Storage | Not persisted | Database with audit |
| User Context | Not tracked | Automatic via state system |
| Code Duplication | Custom cart logic | Uses commerce domain service |
| Persistence | Lost on restart | Persistent storage |

### LMS Example

| Feature | Before | After |
|---------|--------|-------|
| Enrollment Storage | In-memory dict | Database with audit |
| User Context | Not tracked | Automatic via state system |
| Enrollment Check | Dict lookup | Database query |
| Code Duplication | Custom logic | Uses shared LMS data |
| Persistence | Lost on restart | Persistent storage |

---

## Benefits of Integration

### 1. **No Code Duplication**
- E-Shop uses `CartService` from commerce domain
- LMS uses shared `SAMPLE_COURSES` data
- Both use centralized `DBService`

### 2. **Persistent Storage**
- Carts survive server restarts
- Enrollments and orders persisted
- Audit trails for compliance

### 3. **State System Integration**
- Automatic user context tracking
- Audit fields (created_by, updated_by, IP, role)
- Permission-aware operations

### 4. **Production-Ready Patterns**
- Repository pattern (E-Shop)
- Service layer (both)
- Transaction management (DBService)
- Dependency injection

### 5. **Consistent Architecture**
- Examples follow same patterns as main app
- Easy to understand and extend
- Demonstrates best practices

---

## Migration Notes

### For Existing Examples

If you have custom examples, migrate them by:

1. **Add DBService**
   ```python
   from core.services import get_db_service
   db = get_db_service()
   ```

2. **Add State System**
   ```python
   from core.services.auth.context import set_user_context, UserContext
   
   async def get_user(request: Request):
       user = await get_current_user(request, auth_service)
       if user:
           user_context = UserContext(
               user_id=user.id,
               email=user.email,
               role=user.get('role', 'user'),
               ip_address=request.client.host if request.client else None
           )
           set_user_context(user_context)
       return user
   ```

3. **Replace In-Memory Storage**
   ```python
   # Before
   storage = {}
   storage[key] = value
   
   # After
   await db.insert("table_name", data)
   result = await db.find_one("table_name", {"key": value})
   ```

4. **Use Domain Services**
   ```python
   # Instead of custom logic, import from domains
   from add_ons.domains.commerce.services.cart_service import CartService
   from add_ons.domains.lms.data import SAMPLE_COURSES
   ```

---

## Testing

### E-Shop Example
```bash
# Start app
python app/main.py

# Visit example
http://localhost:8000/eshop-example

# Test cart operations
1. Browse products
2. Add to cart (requires login)
3. View cart
4. Checkout
5. Verify order in database
```

### LMS Example
```bash
# Start app
python app/main.py

# Visit example
http://localhost:8000/lms-example

# Test enrollments
1. Browse courses
2. Enroll in course (requires login)
3. View dashboard
4. Verify enrollment in database
```

---

## Future Enhancements

### Social Example (Planned)
- User profiles in database
- Posts and feed using DBService
- Real-time features with WebSockets
- State-aware social interactions

### Streaming Example (Planned)
- Stream metadata in database
- Use stream domain services
- Live streaming state management
- Viewer analytics with DBService

---

## Summary

✅ **E-Shop Example**
- Uses CartService from commerce domain
- Orders stored in database
- State system integration
- No in-memory storage

✅ **LMS Example**
- Enrollments in database
- Uses shared LMS data
- State system integration
- No in-memory storage

✅ **Both Examples**
- DBService for persistence
- User context for audit trails
- Production-ready patterns
- No code duplication

The examples now demonstrate **real-world architecture** with persistent storage, state management, and domain service integration! 🎉
