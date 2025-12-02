# Role-Based Access Control System

## Overview

The FastApp uses a flexible role-based system to control access and determine user experience.

## Available Roles

### 1. **user** (Default)
- **Purpose**: General customers/shoppers
- **Access**: 
  - Browse products in e-shop
  - Add to cart and checkout
  - Basic profile management
- **Redirect After Login**: `/` (home page)

### 2. **student**
- **Purpose**: Course learners
- **Access**:
  - All "user" permissions
  - Enroll in courses
  - Track learning progress
  - Access course materials
  - Take assessments
- **Redirect After Login**: `/lms/student/dashboard`

### 3. **instructor**
- **Purpose**: Course creators/teachers
- **Access**:
  - All "student" permissions
  - Create and manage courses
  - View student enrollments
  - Grade assessments
  - Course analytics
- **Redirect After Login**: `/lms/instructor/dashboard`

### 4. **admin**
- **Purpose**: Platform administrators
- **Access**:
  - Full system access
  - User management
  - Content moderation
  - Platform settings
  - Analytics dashboard
- **Redirect After Login**: `/admin/dashboard`

## Role Assignment Flow

### During Registration

**File**: `app/add_ons/auth/ui/pages/register.py`

Users can select their role during registration:

```python
Select(
    Option("Browse and shop (Customer)", value="user", selected=True),
    Option("Learn courses (Student)", value="student"),
    Option("Teach courses (Instructor)", value="instructor"),
    ...
)
```

**File**: `app/add_ons/auth/routes/auth_routes.py` (Line 181-212)

```python
role = form_data.get("role", "user")  # Get selected role
valid_roles = ["user", "student", "instructor"]

user = await auth_service.register_user(
    email=email,
    password=password,
    username=username,
    roles=[role]  # Assign selected role
)
```

**File**: `app/add_ons/auth/services/auth_service.py` (Line 275-283)

```python
roles = extra_fields.pop("roles", ["user"])  # Extract roles

user_data = {
    "_id": user_id,
    "email": email,
    "username": username or email,
    "password_hash": hash_password(password),
    "roles": roles,  # Store in user document
    ...
}
```

### After Login - Role-Based Redirect

**File**: `app/add_ons/auth/routes/auth_routes.py` (Line 132-142)

```python
if "admin" in roles:
    redirect_url = "/admin/dashboard"
elif "instructor" in roles:
    redirect_url = "/lms/instructor/dashboard"
elif "student" in roles:
    redirect_url = "/lms/student/dashboard"
else:
    redirect_url = "/"  # Default for "user"
```

## Multi-Role Support

Users can have **multiple roles** simultaneously:

```python
user_data = {
    "roles": ["user", "student", "instructor"]  # Multiple roles
}
```

The redirect logic uses **priority order**:
1. Admin (highest priority)
2. Instructor
3. Student
4. User (lowest priority)

## Checking Roles in Code

### In Routes:

```python
@app.get("/instructor/dashboard")
async def instructor_dashboard(request: Request):
    user = await get_current_user(request)
    
    if not user or "instructor" not in user.get("roles", []):
        return RedirectResponse("/")
    
    # Instructor-only content
    return InstructorDashboard()
```

### In Services:

```python
def has_permission(self, user_id: str, permission: str) -> bool:
    """Check if user has specific permission"""
    roles = self.get_user_roles(user_id)
    
    role_permissions = {
        "instructor": ["courses.create", "courses.update"],
        "student": ["courses.view", "courses.enroll"],
    }
    
    permissions = set()
    for role in roles:
        permissions.update(role_permissions.get(role, []))
    
    return permission in permissions
```

## Role Permissions Matrix

| Feature | user | student | instructor | admin |
|---------|------|---------|------------|-------|
| Browse Products | ✅ | ✅ | ✅ | ✅ |
| Purchase Items | ✅ | ✅ | ✅ | ✅ |
| Browse Courses | ✅ | ✅ | ✅ | ✅ |
| Enroll in Courses | ❌ | ✅ | ✅ | ✅ |
| Create Courses | ❌ | ❌ | ✅ | ✅ |
| Manage Users | ❌ | ❌ | ❌ | ✅ |
| Platform Settings | ❌ | ❌ | ❌ | ✅ |

## Changing User Roles

### Option 1: Admin Panel (Future)

```python
@app.post("/admin/users/{user_id}/roles")
async def update_user_roles(user_id: str, roles: List[str]):
    await auth_service.update_user_roles(user_id, roles)
    return {"success": True}
```

### Option 2: Self-Service (Settings Page)

```python
@app.post("/auth/settings/role")
async def change_role(request: Request):
    user = await get_current_user(request)
    new_role = form_data.get("role")
    
    # Only allow certain transitions
    allowed_transitions = {
        "user": ["student"],  # Users can become students
        "student": ["instructor"],  # Students can become instructors
    }
    
    current_role = user["roles"][0]
    if new_role in allowed_transitions.get(current_role, []):
        await auth_service.update_user_roles(user["_id"], [new_role])
```

### Option 3: Database Direct (Development)

```python
# In MongoDB
db.users.updateOne(
    { "email": "user@example.com" },
    { $set: { "roles": ["instructor"] } }
)

# In Python (demo mode)
auth_service._user_cache[user_id]["roles"] = ["instructor"]
```

## Example Use Cases

### E-Commerce Shop
- **Customers**: `user` role
- **Vendors**: `instructor` role (repurposed)
- **Shop Admin**: `admin` role

### Learning Platform
- **Learners**: `student` role
- **Teachers**: `instructor` role
- **Platform Admin**: `admin` role

### Hybrid Platform
- **Basic User**: `["user"]`
- **Student Shopper**: `["user", "student"]`
- **Teaching Vendor**: `["user", "instructor"]`
- **Super Admin**: `["user", "student", "instructor", "admin"]`

## Security Considerations

1. **Never trust client-side role checks** - Always verify on server
2. **Admin role should be invite-only** - Don't allow self-registration as admin
3. **Audit role changes** - Log all role modifications
4. **Validate role transitions** - Not all role changes should be allowed
5. **Use permissions, not just roles** - More granular control

## Testing Roles

### Test User Creation:

```python
# Create test users with different roles
test_users = [
    {"email": "customer@test.com", "roles": ["user"]},
    {"email": "student@test.com", "roles": ["student"]},
    {"email": "teacher@test.com", "roles": ["instructor"]},
    {"email": "admin@test.com", "roles": ["admin"]},
]

for user in test_users:
    await auth_service.register_user(
        email=user["email"],
        password="testpass123",
        username=user["email"].split("@")[0],
        roles=user["roles"]
    )
```

### Test Login Redirects:

1. Login as `customer@test.com` → Should redirect to `/`
2. Login as `student@test.com` → Should redirect to `/lms/student/dashboard`
3. Login as `teacher@test.com` → Should redirect to `/lms/instructor/dashboard`
4. Login as `admin@test.com` → Should redirect to `/admin/dashboard`

## Current Implementation Status

✅ **Implemented:**
- Role selection during registration
- Role-based login redirects
- Role storage in user documents
- Multi-role support

⏳ **Coming Soon:**
- Admin dashboard for role management
- User settings page for role changes
- Permission-based access control
- Role change audit logs
- Instructor dashboard
- Student dashboard

---

**Quick Reference**: 
- Registration form: `app/add_ons/auth/ui/pages/register.py`
- Role assignment: `app/add_ons/auth/routes/auth_routes.py:181-212`
- Role storage: `app/add_ons/auth/services/auth_service.py:275-283`
- Login redirects: `app/add_ons/auth/routes/auth_routes.py:132-142`
