# Core Admin Service - Usage Guide

## ✅ Created: Shared Admin Framework

### **New Core Services:**

```
app/core/services/admin/
├── __init__.py
├── admin_service.py      # Admin operations (user management, stats)
├── decorators.py         # @require_admin, @require_role
└── utils.py              # is_admin(), has_role()
```

---

## **Features:**

### 1. **AdminService**
Core admin operations available to all add-ons:

- `get_all_users()` - List all users (paginated)
- `get_user_count()` - Total user count
- `get_users_by_role()` - Filter users by role
- `update_user_role()` - Change user roles
- `delete_user()` - Remove user
- `ban_user()` / `unban_user()` - User moderation
- `get_system_stats()` - System metrics
- `search_users()` - Search by username/email

### 2. **Route Protection Decorators**

**@require_admin** - Requires admin role:
```python
@app.get("/admin/dashboard")
@require_admin
async def admin_dashboard(request: Request):
    # Only admins can access
    ...
```

**@require_role** - Requires specific role(s):
```python
@app.get("/instructor/courses")
@require_role("instructor", "admin")
async def instructor_courses(request: Request):
    # Instructors and admins can access
    ...
```

### 3. **Utility Functions**

```python
from core.services import is_admin, has_role

# Check if user is admin
if is_admin(user):
    # Show admin options

# Check if user has specific role
if has_role(user, "instructor"):
    # Show instructor features
```

---

## **Usage in Add-ons:**

### **E-Shop Admin Dashboard**

```python
from core.services import AdminService, require_admin, is_admin

def create_eshop_app():
    db_service = DBService()
    auth_service = AuthService(db_service)
    admin_service = AdminService(db_service, auth_service)
    
    app = FastHTML()
    
    @app.get("/admin")
    @require_admin
    async def eshop_admin(request: Request):
        """E-Shop admin dashboard"""
        user = await get_current_user(request, auth_service)
        
        # Get system stats
        stats = await admin_service.get_system_stats()
        
        # E-Shop specific metrics
        total_products = len(PRODUCTS)
        total_orders = get_order_count()  # Your custom function
        
        content = Div(
            H1("E-Shop Admin Dashboard"),
            
            # System Stats
            Div(
                StatCard("Total Users", stats["total_users"]),
                StatCard("Total Products", total_products),
                StatCard("Total Orders", total_orders),
                cls="grid grid-cols-3 gap-4 mb-8"
            ),
            
            # Admin Actions
            Div(
                H2("Admin Actions"),
                A("Manage Users", href="/admin/users", cls="btn btn-primary"),
                A("Manage Inventory", href="/admin/inventory", cls="btn btn-primary"),
                A("View Orders", href="/admin/orders", cls="btn btn-primary"),
            )
        )
        
        return Layout(content, title="Admin Dashboard", user=user)
    
    @app.get("/admin/users")
    @require_admin
    async def manage_users(request: Request):
        """User management"""
        user = await get_current_user(request, auth_service)
        users = await admin_service.get_all_users(limit=50)
        
        content = Div(
            H1("User Management"),
            Table(
                Thead(Tr(Th("Username"), Th("Email"), Th("Roles"), Th("Actions"))),
                Tbody(*[
                    Tr(
                        Td(u["username"]),
                        Td(u["email"]),
                        Td(", ".join(u.get("roles", []))),
                        Td(
                            Button("Ban", hx_post=f"/admin/users/{u['_id']}/ban"),
                            Button("Delete", hx_delete=f"/admin/users/{u['_id']}")
                        )
                    ) for u in users
                ])
            )
        )
        
        return Layout(content, title="User Management", user=user)
    
    @app.get("/admin/inventory")
    @require_admin
    async def manage_inventory(request: Request):
        """Inventory management (E-Shop specific)"""
        user = await get_current_user(request, auth_service)
        
        content = Div(
            H1("Inventory Management"),
            # Your E-Shop specific inventory UI
            ...
        )
        
        return Layout(content, title="Inventory", user=user)
```

---

### **LMS Admin Dashboard**

```python
from core.services import AdminService, require_admin, require_role

def create_lms_app():
    db_service = DBService()
    auth_service = AuthService(db_service)
    admin_service = AdminService(db_service, auth_service)
    
    app = FastHTML()
    
    @app.get("/admin")
    @require_admin
    async def lms_admin(request: Request):
        """LMS admin dashboard"""
        user = await get_current_user(request, auth_service)
        
        # Get system stats
        stats = await admin_service.get_system_stats()
        
        # LMS specific metrics
        instructors = await admin_service.get_users_by_role("instructor")
        students = await admin_service.get_users_by_role("student")
        total_courses = len(COURSES)
        
        content = Div(
            H1("LMS Admin Dashboard"),
            
            # Stats
            Div(
                StatCard("Total Users", stats["total_users"]),
                StatCard("Instructors", len(instructors)),
                StatCard("Students", len(students)),
                StatCard("Courses", total_courses),
                cls="grid grid-cols-4 gap-4 mb-8"
            ),
            
            # Admin Actions
            Div(
                H2("Admin Actions"),
                A("Manage Users", href="/admin/users", cls="btn btn-primary"),
                A("Moderate Courses", href="/admin/courses", cls="btn btn-primary"),
                A("View Analytics", href="/admin/analytics", cls="btn btn-primary"),
            )
        )
        
        return Layout(content, title="Admin Dashboard", user=user)
    
    @app.get("/instructor/dashboard")
    @require_role("instructor", "admin")
    async def instructor_dashboard(request: Request):
        """Instructor dashboard (instructors and admins)"""
        user = await get_current_user(request, auth_service)
        
        content = Div(
            H1("Instructor Dashboard"),
            # Instructor-specific features
            ...
        )
        
        return Layout(content, title="Instructor Dashboard", user=user)
    
    @app.get("/admin/courses")
    @require_admin
    async def moderate_courses(request: Request):
        """Course moderation (LMS specific)"""
        user = await get_current_user(request, auth_service)
        
        content = Div(
            H1("Course Moderation"),
            # Your LMS specific course moderation UI
            ...
        )
        
        return Layout(content, title="Course Moderation", user=user)
```

---

## **Architecture:**

```
┌─────────────────────────────────────────┐
│         Core Services (Shared)          │
├─────────────────────────────────────────┤
│  AdminService                           │
│  ├── User management                    │
│  ├── Role management                    │
│  ├── System stats                       │
│  └── User moderation                    │
│                                         │
│  Decorators                             │
│  ├── @require_admin                     │
│  └── @require_role                      │
└─────────────────────────────────────────┘
                    ▲
                    │ imports
                    │
┌───────────────────┴─────────────────────┐
│         Add-on Admin Dashboards         │
├──────────────────────────────────────────┤
│  E-Shop Admin                            │
│  ├── User management (shared)            │
│  ├── Inventory management (custom)       │
│  └── Order management (custom)           │
│                                          │
│  LMS Admin                               │
│  ├── User management (shared)            │
│  ├── Course moderation (custom)          │
│  └── Analytics (custom)                  │
└──────────────────────────────────────────┘
```

---

## **Benefits:**

### ✅ **Shared Foundation**
- All add-ons get user management for free
- Consistent admin experience across add-ons
- Role-based access control built-in

### ✅ **Add-on Specific Extensions**
- E-Shop: Inventory, orders, products
- LMS: Course moderation, instructor management
- Social: Content moderation, post management

### ✅ **Security Built-in**
- `@require_admin` decorator protects routes
- `@require_role` for granular permissions
- Automatic redirect for unauthorized access

---

## **Next Steps:**

1. **Create E-Shop Admin Dashboard**
   - User management (shared)
   - Inventory management
   - Order history
   - Sales analytics

2. **Create LMS Admin Dashboard**
   - User management (shared)
   - Course moderation
   - Instructor approval
   - Student analytics

3. **Add Admin Nav Item**
   - Show "Admin" link in nav for admins
   - Link to add-on specific admin dashboard

---

## **Example: Adding Admin Link to Nav**

In `core/ui/layout.py`:

```python
if show_auth and user:
    nav_items.extend([
        # ... existing items ...
        
        # Admin link (only for admins)
        (A(
            UkIcon("shield", width="20", height="20"),
            "Admin",
            href="/admin",  # Each add-on defines its own /admin route
            cls="btn btn-ghost btn-sm text-warning",
            title="Admin Dashboard"
        ) if is_admin(user) else None),
    ])
```

---

## **Result:**

✅ **Shared admin framework** - All add-ons get core admin features
✅ **Extensible** - Each add-on adds its own admin features
✅ **Secure** - Role-based access control with decorators
✅ **Consistent** - Same admin experience across platform

Every add-on now has a solid foundation for admin dashboards! 🎉
