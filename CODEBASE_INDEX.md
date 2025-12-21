# Codebase Index for LLM Navigation

Quick reference guide for navigating the codebase. Updated December 20, 2025.

---

## Current Working Features

- ✅ **Authentication** - Login, registration, JWT, role-based access
- ✅ **E-Shop** - Product catalog, cart, checkout, admin dashboard
- ✅ **LMS** - Course catalog, enrollment, lessons, instructor dashboard
- ✅ **Web Admin** - Dedicated admin portal with site/theme editor
- ✅ **Role-Based Dashboards** - Admin, Instructor, Shop Owner
- ✅ **Blog (default non-demo add-on)** - `/blog` routes + minimal post creation
- ✅ **Stream (domain add-on)** - Streaming feature set (routes/services/UI)

---

## Core Concepts

### 1. Authentication
- **Pattern**: JWT tokens in httponly cookies with role-based enforcement
- **Files**: `app/core/services/auth/*.py`
- **Key Classes**: `AuthService`, `UserRepository`, `UserRole`, `RoleEnforcement`
- **Recent Updates**: Added role enforcement decorators, multi-role support, JWT role versioning

### 2. Database Layer
- **Pattern**: PostgreSQL with repository pattern
- **Files**: `app/core/db/adapters/`, `app/core/db/repositories/`
- **Primary**: PostgreSQL (users, products, orders, enrollments)

### 3. Dependency Injection
- **Pattern**: Services on `app.state`, accessed via `request.app.state`
- **Services**: `auth_service`, `cart_service`, `db_service`, `user_service`

### 4. UI Layer
- **Pattern**: FastHTML + MonsterUI components
- **Files**: `app/core/ui/layout.py`, `app/core/ui/pages/`, `app/core/ui/components/`
- **Key**: Role-based navigation in Layout component

---

## Directory Quick Reference

```
app/
├── app.py                    # Main entry point
├── core/                     # Shared infrastructure
│   ├── config/               # Configuration & validation
│   ├── db/                   # Database (adapters/, repositories/, models/)
│   ├── middleware/           # Security, auth context
│   ├── routes/               # Core routes (auth, main, admin)
│   ├── services/             # Business logic (auth/, cart/, editor/)
│   └── ui/                   # UI (layout.py, pages/, components/)
│
├── add_ons/                  # Domain modules
│   ├── domains/              # blog/, commerce/, lms/, social/, stream/
│   ├── services/             # Shared addon services
│   └── webhooks/             # Stripe webhooks
│
└── examples/                 # Working example apps
    ├── eshop/                # E-Shop (app.py, admin.py)
    ├── lms/                  # LMS (app.py, admin.py)
    ├── social/               # Social (scaffolded)
    └── streaming/            # Streaming (scaffolded)
```

---

## Key File Locations

### Authentication (Most Important)
- `app/core/services/auth/auth_service.py` - AuthService (login, register, JWT)
- `app/core/services/auth/enforcement.py` - Role enforcement decorators and permission checking
- `app/core/services/auth/models.py` - UserRole enum, Pydantic models, multi-role support
- `app/core/services/auth/helpers.py` - get_current_user_from_request()
- `app/core/db/repositories/user_repository.py` - UserRepository

### Routes
- `app/core/routes/auth.py` - /auth, /admin/login, /admin/dashboard
- `app/core/routes/main.py` - Home, landing pages
- `app/core/routes/admin_sites.py` - Site/theme editor

### Web Admin workflow + state system
- `app/core/ui/pages/admin_auth.py` - Web admin dashboard UI
- `app/core/workflows/preview.py` - Draft/publish/preview workflow
- `app/core/workflows/admin.py` - Site workflow manager
- `app/core/ui/theme/editor.py` - Theme editor manager
- `app/core/WEB_ADMIN_TODOS.md` - Add-on switches + future git/submodule sync plan

### UI Components
- `app/core/ui/layout.py` - Global Layout with role-based nav
- `app/core/ui/pages/auth.py` - AuthPage, AuthTabContent
- `app/core/ui/pages/admin_auth.py` - WebAdminAuthPage, WebAdminDashboard

### Example Apps
- `app/examples/eshop/app.py` - E-Shop routes
- `app/examples/eshop/admin.py` - EShopAdminDashboard
- `app/examples/lms/app.py` - LMS routes
- `app/examples/lms/admin.py` - InstructorDashboard

### Middleware
- `app/core/middleware/security.py` - SecurityMiddleware (sanitization, rate limiting)

### Database
- `app/core/db/adapters/postgres_adapter.py` - PostgreSQL adapter
- `app/core/db/adapters/mongodb_adapter.py` - MongoDB adapter
- `app/core/db/adapters/redis_adapter.py` - Redis adapter
- `app/core/db/init_schema.py` - Schema initialization

### Add-on system
- `app/core/addon_loader.py` - Manifest-based add-on loader + enabled/disabled registry
- `app/core/app_factory.py` - `create_app(demo=...)` (non-demo mounts Blog)
- `app/core/ui/layout.py` - Demo nav uses example-app dropdown; non-demo nav links to `/blog`

### Blog (default add-on)
- `app/add_ons/domains/blog/routes/posts.py` - blog routes
- `app/add_ons/domains/blog/services/post_service.py` - PostService

### Stream (domain add-on)
- `app/add_ons/domains/stream/routes/` - stream routes
- `app/add_ons/domains/stream/services/` - stream services
- `app/add_ons/domains/stream/ui/` - stream UI

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
    return Layout(content, user=user)
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
user_role = user.get("role", "user")
if user_role in ["admin", "super_admin"]:
    # Admin access
elif user_role in ["instructor", "course_creator"]:
    # Instructor access
elif user_role in ["shop_owner", "merchant"]:
    # Shop owner access
```

---

## Test Credentials

| Role | Email | Password | Dashboard |
|------|-------|----------|-----------|
| Admin | `admin@test.com` | `Admin123!` | `/admin/dashboard` |
| Instructor | `instructor@test.com` | `Instructor123!` | `/lms-example/instructor` |
| Shop Owner | `shopowner@test.com` | `Shopowner123!` | `/eshop-example/admin` |

---

## Quick Start

```bash
# Start dependencies
docker compose up -d

# Run app
uv run python app/app.py

# Access at http://localhost:5001
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
- **Core Platform**: Admin fixes and core feature restoration in progress
- **Role System**: Enhanced with enforcement decorators and multi-role support
- **Documentation**: DEVELOPMENT_TODOS.md provides prioritized task list

### Key Files for Development
- `DEVELOPMENT_TODOS.md` - Prioritized development roadmap
- `docs/FILE_MANIFEST.md` - Complete file listing
- `app/core/WEB_ADMIN_TODOS.md` - Admin-specific tasks

---

**Last Updated**: December 20, 2025
**Recent Changes**: Updated role system documentation, added development roadmap section
