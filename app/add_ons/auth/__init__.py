"""
Auth Add-on

Provides authentication and user management functionality including:
- User registration and login
- OAuth integration (Google, GitHub, etc.)
- Profile management
- Role-based access control

## Quick Start

```python
from add_ons.auth import router_auth, AuthService, UserService

# Mount routes
router_auth.to_app(app)

# Use services
auth_service = AuthService(db_service)
user = await auth_service.authenticate_user("user@example.com", "password")
```

## Role-Based Redirects

After login, users are redirected based on their role:
- **admin** → `/admin/dashboard`
- **instructor** → `/lms/instructor/dashboard`
- **student** → `/lms/student/dashboard`
- **user** → `/profile`
"""
from .routes import router_auth
from .services import AuthService, UserService
from .ui.pages import LoginPage, RegisterPage, ProfilePage, SettingsPage

__all__ = [
    "router_auth",
    "AuthService",
    "UserService",
    "LoginPage",
    "RegisterPage",
    "ProfilePage",
    "SettingsPage",
]
