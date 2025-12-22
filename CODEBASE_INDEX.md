# Codebase Index for LLM Navigation

Quick reference guide for navigating the codebase. Updated December 21, 2025.

---

## Current Working Features

- ✅ **Authentication** - Login, registration, JWT, role-based access with multi-role support
- ✅ **E-Shop** - Product catalog, cart, checkout, admin dashboard
- ✅ **LMS** - Course catalog, enrollment, lessons, instructor dashboard
- ✅ **Web Admin** - Dedicated admin portal with site/theme editor
- ✅ **Role-Based Dashboards** - Admin, Instructor, Shop Owner with role hierarchy
- ✅ **Blog (default non-demo add-on)** - `/blog` routes + minimal post creation
- ✅ **Stream (domain add-on)** - Streaming feature set (routes/services/UI)
- ✅ **Social (domain add-on)** - Enhanced social network with posts, comments, likes, follows, DMs
- ✅ **Example Applications** - Social, Streaming, LMS with sleek UI components

---

## Core Concepts

### 1. Authentication
- **Pattern**: JWT tokens in httponly cookies with role-based enforcement
- **Files**: `core/services/auth/*.py`
- **Key Classes**: `AuthService`, `UserRepository`, `UserRole`, `RoleEnforcement`
- **Recent Updates**: Multi-role support, role hierarchy, JWT role versioning, enhanced permissions

### 2. Database Layer
- **Pattern**: PostgreSQL + MongoDB + Redis with repository pattern
- **Files**: `core/db/adapters/`, `core/db/repositories/`
- **Primary**: PostgreSQL (users, products, orders, enrollments)
- **Secondary**: MongoDB (state, analytics), Redis (sessions, cache)

### 3. Dependency Injection
- **Pattern**: Services on `app.state`, accessed via `request.app.state`
- **Services**: `auth_service`, `cart_service`, `db_service`, `user_service`, `social_service`

### 4. UI Layer
- **Pattern**: FastHTML + MonsterUI components with Layout wrapper
- **Files**: `core/ui/layout.py`, `core/ui/pages/`, `core/ui/components/`
- **Key**: Role-based navigation, responsive design, theme customization

### 5. Domain System
- **Pattern**: Modular add-ons with independent models, services, routes, UI
- **Files**: `add_ons/domains/*/`
- **Domains**: Blog, Commerce, LMS, Social, Stream

---

## Directory Quick Reference

```
├── app.py                    # Main entry point
├── core/                     # Shared infrastructure
│   ├── config/               # Configuration & validation
│   ├── db/                   # Database (adapters/, repositories/, models/)
│   ├── middleware/           # Security, auth context
│   ├── routes/               # Core routes (auth, main, admin)
│   ├── services/             # Business logic (auth/, cart/, editor/)
│   ├── ui/                   # UI (layout.py, pages/, components/)
│   ├── addon_loader.py       # Dynamic add-on loading
│   ├── bootstrap.py          # Application bootstrap
│   └── mounting.py           # Route mounting system
│
├── add_ons/                  # Domain modules
│   ├── domains/              # blog/, commerce/, lms/, social/, stream/
│   │   ├── models/           # Domain-specific models
│   │   ├── repositories/     # Domain repositories
│   │   ├── services/         # Domain services
│   │   ├── routes/           # Domain routes
│   │   └── ui/               # Domain UI components
│   └── services/             # Shared addon services
│
└── examples/                 # Working example apps
    ├── social/               # Social network (enhanced)
    ├── streaming/            # Streaming platform
    ├── lms/                  # LMS example
    └── ui/                   # Shared UI components
```

---

## Key File Locations

### Authentication (Most Important)
- `core/services/auth/auth_service.py` - AuthService (login, register, JWT)
- `core/services/auth/enforcement.py` - Role enforcement decorators and permission checking
- `core/services/auth/models.py` - UserRole enum, Pydantic models, multi-role support
- `core/services/auth/helpers.py` - get_current_user_from_request()
- `core/db/repositories/user_repository.py` - UserRepository

### Core Routes
- `core/routes/auth.py` - /auth, /admin/login, /admin/dashboard
- `core/routes/main.py` - Home, landing pages
- `core/routes/admin_sites.py` - Site/theme editor
- `core/routes/settings.py` - Settings management
- `core/routes/profile.py` - User profiles

### Domain Add-ons
- `add_ons/domains/social/` - Social network domain (posts, comments, likes, follows, DMs)
- `add_ons/domains/stream/` - Streaming domain (WebRTC, video, chat)
- `add_ons/domains/blog/` - Blog domain (posts, categories, comments)
- `add_ons/domains/commerce/` - E-commerce domain (products, orders, payments)
- `add_ons/domains/lms/` - Learning Management System (courses, lessons, enrollment)

### Example Applications
- `examples/social/app.py` - Enhanced social network with sleek UI
- `examples/social/ui/components.py` - Social UI components (PostCard, UserCard, etc.)
- `examples/streaming/app.py` - Streaming platform example
- `examples/streaming/ui/components.py` - Streaming UI components
- `examples/lms/app.py` - LMS example application

### UI Components
- `core/ui/layout.py` - Global Layout with role-based nav
- `core/ui/components/auth.py` - Auth forms and components
- `core/ui/components/base.py` - Base UI components
- `examples/social/ui/components.py` - Shared social/streaming components

### Middleware
- `core/middleware/security.py` - SecurityMiddleware (sanitization, rate limiting)
- `core/middleware/error_handler.py` - Centralized error handling
- `core/middleware/auth_context.py` - User context injection

### Database
- `core/db/adapters/postgres_adapter.py` - PostgreSQL adapter
- `core/db/adapters/mongodb_adapter.py` - MongoDB adapter
- `core/db/adapters/redis_adapter.py` - Redis adapter
- `core/db/session.py` - Session management
- `core/db/transaction_manager.py` - Transaction coordination

### Add-on System
- `core/addon_loader.py` - Manifest-based add-on loader + registry
- `core/bootstrap.py` - Application bootstrap and service initialization
- `core/mounting.py` - Route mounting and example app registration

---

## Common Patterns

### Route Handler Pattern
```python
@app.get("/path")
async def handler(request: Request):
    auth_service = request.app.state.auth_service
    user = await get_current_user_from_request(request, auth_service)
    if not user:
        return RedirectResponse("/auth?tab=login")
    return Layout(content, title="Page Title", user=user, show_auth=True)
```

### Domain Service Pattern
```python
# Domain service usage
social_service = request.app.state.social_service
posts = await social_service.get_posts(user_id)
return SocialFeed(posts, current_user_id, base_path)
```

### Form Data Pattern
```python
# Always use this pattern for form handling
form = getattr(request.state, 'sanitized_form', None) or await request.form()
email = form.get("email")
password = form.get("password")
```

### Role Check Pattern
```python
user_roles = user.get("roles", ["user"])
if "super_admin" in user_roles:
    # Super admin access
elif "admin" in user_roles:
    # Admin access
elif "instructor" in user_roles:
    # Instructor access
```

### UI Component Pattern
```python
# Using shared UI components
content = Div(
    ExampleHeader("Title", "Subtitle"),
    SocialFeed(posts, current_user_id, base_path),
    ExampleBackLink(),
    cls="min-h-screen bg-gray-50"
)
return Layout(content, title="Page Title", user=user)
```

---

## Test Credentials

| Role | Email | Password | Dashboard |
|------|-------|----------|-----------|
| Admin | `admin@freelancer.dev` | `AdminPass123!` | `/admin/dashboard` |
| Instructor | `instructor@test.com` | `Instructor123!` | `/lms-example/instructor` |
| Shop Owner | `shopowner@test.com` | `Shopowner123!` | `/eshop-example/admin` |

---

## Quick Start

```bash
# Start dependencies
docker compose up -d

# Run app
DEMO_MODE=true uv run python app.py

# Access at http://localhost:5001
```

### Example Applications
```bash
# Social Network
http://localhost:5001/social-example

# Streaming Platform  
http://localhost:5001/streaming-example

# LMS Example
http://localhost:5001/lms-example
```

### Run tests
```bash
docker compose up -d
uv run pytest -q

# integration (requires Postgres; skipped unless enabled)
RUN_INTEGRATION_TESTS=1 uv run pytest -q tests/integration
```

---

## Development Roadmap

### Current Status
- **Core Platform**: Production-ready with enhanced authentication and role system
- **Domain System**: 5 fully scaffolded domains (Blog, Commerce, LMS, Social, Stream)
- **Example Applications**: Enhanced social and streaming examples with sleek UI
- **Documentation**: Comprehensive TODOS.md with production-ready roadmap

### Key Files for Development
- `TODOS.md` - Comprehensive production-ready TODOs organized by component
- `FILE_MANIFEST.md` - Complete file listing with current structure
- `ARCHITECTURE.md` - Architecture overview and design patterns

### Recent Major Updates
- ✅ Enhanced social example app with complete UI components
- ✅ Added streaming example app with video features
- ✅ Updated social domain with complete models and services
- ✅ Improved authentication with multi-role support
- ✅ Added comprehensive production-ready TODOs documentation

---

## Architecture Highlights

### Modular Design
- **Core Framework**: Independent of domain logic
- **Domain Add-ons**: Self-contained with models, services, routes, UI
- **Example Applications**: Demonstrate domain capabilities
- **Shared Components**: Reusable UI components across examples

### Technology Stack
- **Backend**: FastHTML + Python 3.13
- **Frontend**: MonsterUI + TailwindCSS
- **Database**: PostgreSQL + MongoDB + Redis
- **Authentication**: JWT with role-based access
- **Architecture**: Repository pattern + Dependency Injection

### Key Features
- **Multi-Role System**: Hierarchical roles with permissions
- **Real-time Updates**: WebSocket support for live features
- **Responsive Design**: Mobile-first UI components
- **Production Ready**: Comprehensive error handling, logging, monitoring

---

**Last Updated**: December 21, 2025
**Recent Changes**: Enhanced social/streaming examples, updated domain structure, comprehensive TODOs
**Total Files**: 300+ documented components
