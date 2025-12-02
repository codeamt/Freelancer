# Auth Add-on - Login Flow Documentation

## Overview

The auth add-on provides complete authentication and authorization with role-based access control and intelligent redirects.

## User Roles

### 1. Admin
- **Permissions**: Full system access (`*` wildcard)
- **Login Redirect**: `/admin/dashboard`
- **Can**: Manage all users, courses, content, and system settings

### 2. Instructor
- **Permissions**: 
  - `courses.create`, `courses.update`, `courses.delete`
  - `lessons.create`, `lessons.update`, `lessons.delete`
- **Login Redirect**: `/lms/instructor/dashboard`
- **Can**: Create and manage their own courses and lessons

### 3. Student
- **Permissions**:
  - `courses.view`, `courses.enroll`
  - `lessons.view`
  - `assessments.take`
- **Login Redirect**: `/lms/student/dashboard`
- **Can**: Enroll in courses, view lessons, take assessments

### 4. User (Default)
- **Permissions**:
  - `profile.view`, `profile.update`
- **Login Redirect**: `/profile`
- **Can**: View and update their own profile

## Login Flow

### 1. User Visits Login Page
```
GET /auth/login
→ Displays LoginPage with email/password form
```

### 2. User Submits Credentials
```
POST /auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
```

### 3. Authentication Process
```python
# 1. Validate credentials
user = await auth_service.authenticate_user(email, password)

# 2. Create JWT token with user data
token_data = {
    "sub": user["_id"],
    "email": user["email"],
    "username": user.get("username"),
    "roles": user.get("roles", ["user"])
}
token = auth_service.create_token(token_data)

# 3. Determine redirect based on role
if "admin" in roles:
    redirect_url = "/admin/dashboard"
elif "instructor" in roles:
    redirect_url = "/lms/instructor/dashboard"
elif "student" in roles:
    redirect_url = "/lms/student/dashboard"
else:
    redirect_url = "/profile"

# 4. Store token in localStorage and redirect
localStorage.setItem('auth_token', token)
window.location.href = redirect_url
```

### 4. Subsequent Requests
All authenticated requests include the JWT token:
```
Authorization: Bearer <token>
```

## Registration Flow

### 1. User Visits Registration Page
```
GET /auth/register
→ Displays RegisterPage with username/email/password form
```

### 2. User Submits Registration
```
POST /auth/register
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "password123",
  "confirm_password": "password123"
}
```

### 3. Registration Process
```python
# 1. Validate input
- All fields required
- Passwords must match
- Password minimum 8 characters
- Email/username must be unique

# 2. Create user with default role
user = await auth_service.register_user(
    email=email,
    password=password,  # Hashed automatically
    username=username
)

# 3. Redirect to login
window.location.href = '/auth/login'
```

## Profile Management

### View Profile
```
GET /auth/profile
→ Requires authentication
→ Displays ProfilePage with user data
```

### Update Profile
```
PUT /auth/profile/{user_id}
{
  "username": "newusername",
  "full_name": "John Doe",
  "bio": "Software developer"
}
→ Requires authentication
→ User can only update their own profile
```

### Change Password
```
POST /auth/password/change
{
  "old_password": "oldpass123",
  "new_password": "newpass123",
  "confirm_password": "newpass123"
}
→ Requires authentication
→ Validates old password before changing
```

## Permission Checking

### In Routes
```python
from add_ons.auth.routes.auth_routes import get_current_user

@router.get("/courses/create")
async def create_course_page(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login")
    
    # Check permission
    if not auth_service.has_permission(user["_id"], "courses.create"):
        return RedirectResponse("/")  # Or 403 page
    
    return CourseCreatePage()
```

### In Services
```python
# Check specific permission
has_perm = auth_service.has_permission(user_id, "courses.create")

# Check role
is_admin = auth_service.has_role(user_id, "admin")

# Get all permissions
permissions = auth_service.get_user_permissions(user_id)
```

## Role Assignment

### Default (Registration)
- New users get `["user"]` role by default

### Admin Assignment
```python
# Update user roles (admin only)
await auth_service.update_user_roles(user_id, ["instructor", "student"])
```

### Role Hierarchy
```
admin > instructor > student > user
```

## Security Features

### 1. Password Hashing
- Uses bcrypt for password hashing
- Passwords never stored in plain text

### 2. JWT Tokens
- Signed with JWT_SECRET
- Expires after 12 hours (configurable)
- Contains user ID, email, username, and roles

### 3. Token Verification
- All protected routes verify token
- Invalid/expired tokens redirect to login

### 4. Authorization
- Role-based access control (RBAC)
- Permission-based access control
- Wildcard permissions for admins

## Example User Scenarios

### Scenario 1: Student Enrolls in Course
```
1. Student logs in → Redirected to /lms/student/dashboard
2. Views available courses
3. Clicks "Enroll" → Checks permission "courses.enroll" ✓
4. Successfully enrolled
```

### Scenario 2: Instructor Creates Course
```
1. Instructor logs in → Redirected to /lms/instructor/dashboard
2. Clicks "Create Course"
3. System checks permission "courses.create" ✓
4. Displays course creation form
5. Submits course → Saved with instructor_id
```

### Scenario 3: Admin Manages Users
```
1. Admin logs in → Redirected to /admin/dashboard
2. Views all users
3. System checks permission "*" (wildcard) ✓
4. Can edit any user, assign roles, delete accounts
```

### Scenario 4: Regular User Tries to Create Course
```
1. User logs in → Redirected to /profile
2. Tries to access /courses/create
3. System checks permission "courses.create" ✗
4. Redirected to home page or shown 403 error
```

## Integration with Other Add-ons

### LMS Add-on
- Uses auth service for instructor/student identification
- Checks permissions before course operations
- Filters content based on user role

### Admin Add-on
- Uses auth service to verify admin role
- Provides user management interface
- Can assign/revoke roles

### Commerce Add-on
- Uses auth for customer identification
- Links orders to user accounts
- Checks permissions for seller features

## Configuration

### Environment Variables
```bash
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
TOKEN_EXPIRATION_HOURS=12
```

### Database Collections
- `users` - User accounts and profiles
- `sessions` - Active sessions (optional)
- `password_resets` - Password reset tokens (optional)

## Testing

### Test Users
Create test users with different roles:

```python
# Admin
await auth_service.register_user(
    email="admin@test.com",
    password="admin123",
    username="admin"
)
await auth_service.update_user_roles(admin_id, ["admin"])

# Instructor
await auth_service.register_user(
    email="instructor@test.com",
    password="instructor123",
    username="instructor"
)
await auth_service.update_user_roles(instructor_id, ["instructor"])

# Student
await auth_service.register_user(
    email="student@test.com",
    password="student123",
    username="student"
)
await auth_service.update_user_roles(student_id, ["student"])
```

### Test Login Flows
1. Login as each role type
2. Verify correct redirect
3. Test permission checks
4. Test unauthorized access attempts
