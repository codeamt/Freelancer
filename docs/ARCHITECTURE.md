# FastHTML Modular Monolith - Architecture Documentation

## Overview

This is a **modular monolith** web application built with FastHTML/HTMX and MonsterUI, following Domain-Driven Design (DDD) principles. The architecture supports multiple domain add-ons (Commerce, LMS, Blog, Stream, Social) with shared core infrastructure.

## Current State (December 2025)

### Working Features
- ✅ **Core Authentication** - Login, registration, JWT tokens, role-based access
- ✅ **E-Shop Example** - Product catalog, cart, checkout flow, admin dashboard
- ✅ **LMS Example** - Course catalog, enrollment, lessons, instructor dashboard  
- ✅ **Web Admin Portal** - Dedicated admin login, site/theme editor access
- ✅ **Role-Based Dashboards** - Admin, Instructor, Shop Owner dashboards
- ✅ **Security Middleware** - Input sanitization, rate limiting, security headers (CSP intentionally not enforced for FastHTML inline styles)
- ✅ **State System + Site Editing Workflow** - Draft/publish workflow for site components and theme
- ✅ **Blog Domain (default non-demo add-on)** - `/blog` routes + minimal post creation
- ✅ **Streaming Domain** - Implemented routes/services/UI (paywall, attendance, chat gating)

### Pending Implementation
- 🔄 **Social Domain** - Posts, comments, likes, follows (scaffolded)
- 🔄 **Stripe Integration** - Payment processing (UI ready, backend pending)

## Core Architectural Principles

### 1. **Polyglot Persistence**
Multiple specialized databases for different data characteristics:
- **PostgreSQL**: Structured, relational data (users, products, orders, enrollments)
- **MongoDB**: Documents, flexible schemas (reviews, media, state)
- **Redis**: Caching, sessions, pub/sub
- **DuckDB**: Analytics, OLAP queries
- **MinIO**: Object storage (files, images, videos)

### 2. **FastHTML + MonsterUI**
Server-side rendering with HTMX for interactivity:
- **FastHTML**: Python-native HTML generation with async support
- **MonsterUI**: DaisyUI-based component library
- **HTMX**: Dynamic updates without JavaScript frameworks
- **Live Reload**: Development hot-reloading

### 3. **Dependency Injection via app.state**
Services initialized at startup and accessed via request:
- **AuthService**: Authentication and authorization
- **CartService**: Shopping cart management
- **DBService**: Database operations
- **UserService**: User management

### 4. **Role-Based Access Control (RBAC)**
Multi-tier permission system:
- **super_admin**: Global configuration, all permissions
- **admin**: Platform administration, site editing
- **instructor/course_creator**: LMS content management
- **shop_owner/merchant**: E-Shop administration
- **student/user**: Standard user access

---

## Directory Structure

```
app/
├── app.py                         # Main application entry point
├── core/                          # Core framework (shared infrastructure)
│   ├── config/                    # Configuration
│   │   ├── settings_facade.py     # Role-aware settings
│   │   └── validation.py          # Startup validation
│   ├── db/                        # Database layer
│   │   ├── adapters/              # PostgreSQL, MongoDB, Redis adapters
│   │   ├── repositories/          # Repository pattern (UserRepository, etc.)
│   │   ├── models/                # SQLAlchemy/Pydantic models
│   │   └── migrations/            # Database migrations
│   ├── middleware/                # Request middleware
│   │   ├── security.py            # Input sanitization, rate limiting
│   │   ├── auth_context.py        # User context injection
│   │   └── error_handler.py       # Centralized error handling
│   ├── routes/                    # Core HTTP routes
│   │   ├── auth.py                # Auth routes (/auth, /admin/login, /admin/dashboard)
│   │   ├── main.py                # Home, landing pages
│   │   ├── admin_sites.py         # Site/theme editor
│   │   ├── cart.py                # Shared cart routes
│   │   └── profile.py             # User profile
│   ├── services/                  # Business logic
│   │   ├── auth/                  # AuthService, UserRepository, JWT
│   │   ├── cart/                  # CartService
│   │   ├── editor/                # Site/theme editing
│   │   └── settings/              # Settings management
│   ├── ui/                        # UI layer (FastHTML + MonsterUI)
│   │   ├── components/            # Reusable components
│   │   ├── pages/                 # Page templates (AuthPage, AdminDashboard, etc.)
│   │   ├── layout.py              # Global Layout with role-based nav
│   │   └── theme/                 # Theme system
│   └── utils/                     # Utilities (logger, helpers, security)
│
├── add_ons/                       # Domain modules
│   ├── domains/
│   │   ├── blog/                  # Blog domain (default non-demo add-on)
│   │   ├── commerce/              # E-commerce domain logic
│   │   ├── lms/                   # LMS domain logic
│   │   ├── social/                # Social domain (scaffolded)
│   │   └── stream/                # Streaming domain
│   ├── services/                  # Shared addon services
│   └── webhooks/                  # Stripe webhooks
│
└── examples/                      # Working example apps
    ├── eshop/                     # E-Shop (app.py, admin.py, ui/)
    ├── lms/                       # LMS (app.py, admin.py, ui/)
    ├── social/                    # Social (scaffolded)
    └── streaming/                 # Streaming (scaffolded)
```

---

## Key Systems

### 1. Authentication System

**Location**: `app/core/services/auth/`

#### Components
- **AuthService** (`auth_service.py`) - Login, registration, JWT token management
- **UserRepository** (`app/core/db/repositories/`) - User CRUD operations
- **JWT Provider** (`app/core/services/auth/providers/jwt.py`) - Token creation and verification
- **Models** (`models.py`) - Pydantic models for type safety

#### User Roles (UserRole enum)
```python
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    EDITOR = "editor"
    MEMBER = "member"
    USER = "user"
    INSTRUCTOR = "instructor"
    STUDENT = "student"
    SHOP_OWNER = "shop_owner"
    MERCHANT = "merchant"
    COURSE_CREATOR = "course_creator"
```

#### Authentication Flow
```
1. User submits credentials → /auth/login or /admin/auth/login
2. AuthService.login() validates credentials
3. JWT token created with user_id, email, role
4. Token stored in httponly cookie (auth_token)
5. Subsequent requests: get_current_user_from_request() extracts user
```

### 2. Role-Based Navigation

**Location**: `app/core/ui/layout.py`

The global Layout component dynamically shows dashboard links based on user role:

```python
if user_role in ["admin", "super_admin"]:
    dashboard_link = "/admin/dashboard"
elif user_role in ["instructor", "course_creator"]:
    dashboard_link = "/lms-example/instructor"
elif user_role in ["shop_owner", "merchant"]:
    dashboard_link = "/eshop-example/admin"
```

### 3. Example Apps Architecture

Each example app follows the same pattern:

**E-Shop** (`app/examples/eshop/`)
- `app.py` - Routes, product catalog, cart, checkout
- `admin.py` - Admin dashboard components
- `ui/` - E-Shop specific UI components

**LMS** (`app/examples/lms/`)
- `app.py` - Routes, course catalog, enrollment, lessons
- `admin.py` - Instructor dashboard components
- `ui/` - LMS specific UI components

#### Shared Services
Both examples use shared core services:
- `request.app.state.auth_service` - Authentication
- `request.app.state.cart_service` - Cart management
- `request.app.state.db_service` - Database operations

### 4. Security Middleware

**Location**: `app/core/middleware/security.py`

Features:
- **Input Sanitization** - XSS prevention, SQL injection protection
- **Rate Limiting** - Request throttling per IP
- **CSRF** - Middleware exists, but may be disabled in some flows due to HTMX integration needs
- **Security Headers** - CSP, X-Frame-Options, etc.

Notes:
- CSP is intentionally not enforced in `SecurityHeaders` because FastHTML/MonsterUI uses inline styles and CDN resources.

Form data access pattern:
```python
# Try sanitized form first, fallback to raw
form = getattr(request.state, 'sanitized_form', None) or await request.form()
```

### 5. Database Layer

**Location**: `app/core/db/`

#### PostgreSQL Adapter
Primary database for structured data:
- Users, products, orders, enrollments
- Connection pooling with asyncpg

#### Repository Pattern
```python
class UserRepository:
    async def get_by_email(self, email: str) -> Optional[User]
    async def verify_password(self, email: str, password: str) -> Optional[User]
    async def create(self, user_data: dict) -> User
```

---

## Request Flow

```
HTTP Request
    ↓
Security Middleware (sanitize inputs, rate limit)
    ↓
Route Handler
    ↓
Access services via request.app.state
    ↓
Business logic (AuthService, CartService, etc.)
    ↓
Database operations (PostgresAdapter)
    ↓
Render UI (FastHTML + MonsterUI components)
    ↓
HTTP Response (HTML with HTMX attributes)
```

---

## Key Files Reference

### Authentication
- `app/core/services/auth/auth_service.py` - AuthService (login, register, JWT)
- `app/core/services/auth/models.py` - Pydantic models (UserRole, LoginRequest, etc.)
- `app/core/services/auth/helpers.py` - get_current_user_from_request()
- `app/core/db/repositories/base_repository.py` - UserRepository

### Routes
- `app/core/routes/auth.py` - /auth, /admin/login, /admin/dashboard
- `app/core/routes/main.py` - Home, landing pages
- `app/core/routes/admin_sites.py` - Site/theme editor routes

### UI Components
- `app/core/ui/layout.py` - Global Layout with role-based navigation
- `app/core/ui/pages/auth.py` - AuthPage, AuthTabContent
- `app/core/ui/pages/admin_auth.py` - WebAdminAuthPage, WebAdminDashboard

### Example Apps
- `app/examples/eshop/app.py` - E-Shop routes and logic
- `app/examples/eshop/admin.py` - EShopAdminDashboard
- `app/examples/lms/app.py` - LMS routes and logic
- `app/examples/lms/admin.py` - InstructorDashboard

### Middleware
- `app/core/middleware/security.py` - SecurityMiddleware

### Database
- `app/core/db/adapters/postgres_adapter.py` - PostgreSQL adapter
- `app/core/db/init_schema.py` - Database schema initialization

---

## Test Credentials

For testing admin dashboards:

| Role | Email | Password | Dashboard |
|------|-------|----------|-----------|
| Admin | `admin@test.com` | `Admin123!` | `/admin/dashboard` |
| Instructor | `instructor@test.com` | `Instructor123!` | `/lms-example/instructor` |
| Shop Owner | `shopowner@test.com` | `Shopowner123!` | `/eshop-example/admin` |

---

## Development Environment

### Docker Compose Setup

**Single file for local development**: `docker-compose.yml`

**Services:**
- **PostgreSQL** (port 5432) - Primary database
- **Redis** (port 6379) - Caching and sessions
- **MongoDB** (port 27017) - Document/state storage
- **DuckDB** (optional) - Analytics container
- **MinIO** (9000/9001) - S3-compatible object storage

**Quick start:**
```bash
# Start services
docker compose up -d

# Run the app
cd app && uv run python app.py

# Access at http://localhost:5001
```

### Required Environment Variables
```bash
JWT_SECRET=your-secret-key-here
POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/app_db
MONGO_URL=mongodb://root:example@localhost:27017
REDIS_URL=redis://localhost:6379
```

---

## Next Steps (Roadmap)

### Immediate (Web Admin Add-ons + Blog/Stream hardening)
1. Add add-on enable/disable switches to Web Admin dashboard
2. Persist add-on config and apply safely (restart-required first)
3. Expand Blog and Stream test coverage (see `app/core/TEST_PLAN.md`)
4. Connect Stripe webhooks for payments

### Short-term
1. Add comprehensive test suite
2. Implement real-time notifications
3. Add file upload to MinIO/S3

### Medium-term
1. GraphQL API layer
2. WebSocket support for live features
3. Background job processing

---

**Last Updated**: December 14, 2025
**Version**: 2.0
