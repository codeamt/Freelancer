# Auth Add-on

Authentication and user management add-on for FastApp.

## Features

- **User Registration** - Email/password registration with validation
- **User Login** - Secure authentication with JWT tokens
- **OAuth Integration** - Google, GitHub, and other OAuth providers
- **Profile Management** - User profile viewing and editing
- **Role-Based Access Control** - Roles and permissions system
- **Password Reset** - Secure password reset flow
- **Email Verification** - Email verification for new accounts

## Structure

```
auth/
├── services/
│   ├── auth_service.py      # Extends BaseAuthService
│   ├── oauth_service.py     # OAuth provider integration
│   └── user_service.py      # User CRUD operations
├── routes/
│   └── auth_routes.py       # Auth endpoints
├── ui/
│   └── pages/
│       ├── login.py         # Login page
│       ├── register.py      # Registration page
│       └── profile.py       # User profile page
└── models/
    └── user.py              # User data model
```

## Usage

### Mounting in App

```python
from add_ons.auth import router_auth

# Mount auth routes
router_auth.to_app(app)
```

### Using Auth Service

```python
from add_ons.auth import AuthService

auth_service = AuthService()

# Authenticate user
user = await auth_service.authenticate_user("user@example.com", "password")

# Check permissions
has_perm = auth_service.has_permission(user_id, "courses.create")
```

## Configuration

Set these environment variables:

- `JWT_SECRET` - Secret key for JWT tokens
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `GITHUB_CLIENT_ID` - GitHub OAuth client ID
- `GITHUB_CLIENT_SECRET` - GitHub OAuth client secret

## API Endpoints

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/logout` - Logout user
- `GET /auth/profile` - Get user profile
- `PUT /auth/profile` - Update user profile
- `POST /auth/password/reset` - Request password reset
- `POST /auth/password/reset/confirm` - Confirm password reset
- `GET /auth/oauth/google` - Google OAuth login
- `GET /auth/oauth/google/callback` - Google OAuth callback
