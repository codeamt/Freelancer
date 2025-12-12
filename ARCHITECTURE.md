# FastHTML Modular Monolith - Architecture Documentation

## Overview

This is a **modular monolith** web application built with FastHTML/HTMX, following Domain-Driven Design (DDD) principles with a state-first architecture inspired by Burr/Redux patterns.

## Core Architectural Principles

### 1. **Polyglot Persistence**
Multiple specialized databases for different data characteristics:
- **PostgreSQL**: Structured, relational data (users, products, orders)
- **MongoDB**: Documents, flexible schemas (reviews, media, state)
- **Redis**: Caching, sessions, pub/sub
- **DuckDB**: Analytics, OLAP queries
- **MinIO**: Object storage (files, images, videos)

### 2. **State-First Design**
Immutable state management with actions and transitions:
- **State**: Immutable container with versioning (`sequence_id`)
- **Actions**: Pure functions that transform state
- **Transitions**: Conditional flows between actions
- **Persistence**: State saved to MongoDB with partitions (draft/published/preview)

### 3. **Dependency Injection**
Centralized dependency management via ExecutionContext:
- **UserContext**: User identity, permissions, cookies
- **SettingsFacade**: Role-aware configuration access
- **ServiceContainer**: Business logic services
- **IntegrationContainer**: External service clients

### 4. **Role-Based Access Control (RBAC)**
Three-tier permission system:
- **SuperAdmin**: Global configuration, all permissions
- **WebAdmin**: Feature-specific domain settings
- **User**: Public settings + personalized preferences

---

## Directory Structure

```
app/
├── core/                          # Core framework (reusable)
│   ├── addon_loader.py            # Add-on loading and registration
│   ├── config/                    # Configuration management
│   │   └── settings_facade.py    # Role-aware settings access
│   ├── db/                        # Database layer
│   │   ├── adapters/              # Database adapters (Postgres, MongoDB, Redis, etc.)
│   │   ├── repositories/          # Repository pattern implementations
│   │   ├── base_class.py          # Base database classes
│   │   ├── connection_pool.py     # Connection pooling
│   │   ├── session.py             # Session management
│   │   └── transaction_manager.py # Distributed transaction coordinator (2PC)
│   ├── di/                        # Dependency injection
│   │   ├── __init__.py            # DI exports
│   │   └── container.py           # ExecutionContext, ServiceContainer, IntegrationContainer
│   ├── integrations/              # External service clients
│   │   ├── analytics/             # Analytics providers (ConsentManager)
│   │   ├── email/                 # Email providers
│   │   ├── payment/               # Payment gateways (Stripe, PayPal)
│   │   └── storage/               # Storage providers (S3, MinIO)
│   ├── middleware/                # Request/response middleware
│   │   ├── __init__.py            # Middleware exports
│   │   ├── auth_context.py        # User context injection
│   │   ├── redis_session.py       # Redis session management
│   │   └── security.py            # Security headers, rate limiting, CSRF
│   ├── routes/                    # Core HTTP routes
│   │   ├── __init__.py            # Route exports
│   │   ├── admin_sites.py         # Admin site management
│   │   ├── auth.py                # Authentication routes
│   │   ├── editor.py              # Visual editor routes
│   │   ├── main.py                # Main routes
│   │   ├── oauth.py               # OAuth routes
│   │   └── settings.py            # Settings management
│   ├── services/                  # Business logic services
│   │   ├── auth/                  # Authentication & authorization
│   │   │   ├── auth_service.py    # Auth business logic
│   │   │   ├── context.py         # UserContext, PermissionContext
│   │   │   ├── decorators.py      # @require_auth, @requires_permission
│   │   │   ├── permissions.py     # Permission definitions
│   │   │   └── utils.py           # Auth utilities
│   │   ├── admin/                 # Admin services
│   │   ├── editor/                # Editor services
│   │   └── settings/              # Settings services
│   ├── state/                     # State management system
│   │   ├── __init__.py            # State exports
│   │   ├── actions.py             # Action base class
│   │   ├── builder.py             # StateMachineApplication builder
│   │   ├── persistence.py         # State persistence (MongoDB)
│   │   ├── state.py               # Immutable State container
│   │   └── transitions.py         # Transition conditions
│   ├── ui/                        # UI components & theme
│   │   ├── components/            # Reusable UI components
│   │   │   ├── __init__.py        # Component exports
│   │   │   ├── auth.py            # LoginForm, RegisterForm
│   │   │   ├── base.py            # Base components
│   │   │   ├── consent_banner.py  # Cookie consent banner
│   │   │   ├── content.py         # Content components
│   │   │   ├── forms.py           # Form components
│   │   │   └── marketing.py       # Marketing components
│   │   ├── state/                 # UI state management
│   │   │   ├── __init__.py        # ComponentConfig, ComponentType
│   │   │   ├── actions.py         # UI actions (AddComponent, RemoveComponent)
│   │   │   ├── config.py          # Component configuration
│   │   │   └── factory.py         # Component rendering
│   │   ├── theme/                 # Theme system
│   │   │   └── editor.py          # ThemeConfig, ThemeActions
│   │   ├── pages/                 # Page templates
│   │   ├── static/                # Static assets
│   │   ├── __init__.py            # UI exports
│   │   └── layout.py              # Layout components
│   ├── utils/                     # Utilities
│   │   ├── __init__.py            # Empty (can be removed)
│   │   ├── app_factory.py         # App creation helpers (DRY)
│   │   ├── cache.py               # Caching utilities
│   │   ├── cookies.py             # Cookie utilities
│   │   ├── files.py               # File utilities
│   │   ├── helpers.py             # General helpers
│   │   ├── logger.py              # Centralized logging
│   │   ├── responses.py           # Unified response helpers (DRY)
│   │   └── security.py            # Security utilities
│   └── workflows/                 # Workflow orchestration
│       ├── __init__.py            # Workflow exports
│       ├── admin.py               # SiteWorkflowManager, create site workflows
│       └── preview.py             # PreviewPublishManager, preview/publish actions
│
├── add_ons/                       # Domain-specific modules
│   └── domains/                   # Bounded contexts (DDD)
│       ├── commerce/              # E-commerce domain
│       │   ├── models/            # Domain models
│       │   ├── repositories/      # Product, Order repositories
│       │   ├── services/          # Commerce services
│       │   └── routes/            # Commerce routes
│       ├── lms/                   # Learning management system
│       ├── social/                # Social networking
│       └── stream/                # Streaming platform
│
└── examples/                      # Example applications
    ├── eshop/                     # E-commerce example
    ├── lms/                       # LMS example
    ├── social/                    # Social example
    └── streaming/                 # Streaming example
```

---

## Key Systems

### 1. State Management System

**Location**: `app/core/state/`

#### State Structure
```python
State {
    "site_graph": {              # UI structure
        "sections": [
            {
                "id": "hero",
                "type": "hero",
                "components": [ComponentConfig, ...]
            }
        ]
    },
    "theme_state": {             # Visual styling
        "name": "Modern",
        "colors": {...},
        "typography": {...},
        "spacing": {...}
    },
    "site_id": "...",
    "settings": {...}
}
```

#### State Flow
```
Action → Read State → Transform → New State → Persist
```

#### Actions
Pure functions that transform state:
```python
class AddComponentAction(Action):
    async def run(self, state: State, **inputs) -> ActionResult:
        site_graph = state.get("site_graph")
        # Modify site_graph
        return ActionResult(success=True, data={"site_graph": new_graph})
```

#### Persistence
State stored in MongoDB with partitions:
- `partition="draft"` - Working copy
- `partition="published"` - Live version
- `partition="preview"` - Preview snapshots
- `partition="user:{id}"` - User-specific

### 2. User Context & RBAC

**Location**: `app/core/services/auth/context.py`

#### UserContext
Request-scoped object containing:
```python
@dataclass
class UserContext:
    user_id: int
    role: str                    # "SuperAdmin", "WebAdmin", "User"
    permissions: Set[Permission]
    request_cookies: dict        # Incoming cookies
    ip_address: str
    _outgoing_cookies: dict      # Cookies to set on response
    
    def has_permission(self, permission: Permission) -> bool
    def set_cookie(self, key: str, value: str, **kwargs)
    def get_cookie(self, key: str, default=None)
```

#### Permission Decorators
```python
@requires_permission(Permission.MANAGE_USERS)
async def create_user(user_context: UserContext, ...):
    # Only users with MANAGE_USERS permission can call this
```

### 3. Settings Facade

**Location**: `app/core/config/settings_facade.py`

Role-aware configuration access:
```python
class SettingsFacade:
    def __init__(self, user_context: UserContext, global_settings: Settings):
        self._user = user_context
        self._global = global_settings
    
    @property
    def analytics_tracking_enabled(self) -> bool:
        # Check user's tracking_opt_out cookie
        # SuperAdmins might be tracked for security
        
    @property
    def can_modify_commerce_settings(self) -> bool:
        # Only admins can modify
```

### 4. Dependency Injection

**Location**: `app/core/di/container.py`

#### ExecutionContext
Bundles all dependencies for Actions:
```python
@dataclass
class ExecutionContext:
    user_context: UserContext
    settings: SettingsFacade
    services: ServiceContainer
    integrations: IntegrationContainer
```

#### Usage in Actions
```python
async def execute(self, state: State, context: ExecutionContext):
    # Access user
    if not context.user_context.has_permission(Permission.PUBLISH):
        return ActionResult(False, "Permission denied")
    
    # Access settings
    if context.settings.analytics_tracking_enabled:
        await context.integrations.analytics.track_event(...)
    
    # Access services
    async with context.services.uow_factory() as uow:
        await uow.site_repo.publish(state.site_id)
```

### 5. Multi-Database Coordination

**Location**: `app/core/db/`

#### Repository Pattern
Repositories coordinate operations across databases:
```python
class ProductRepository:
    def __init__(self, postgres, mongodb, redis):
        self.postgres = postgres  # Structured data
        self.mongodb = mongodb    # Unstructured data
        self.redis = redis        # Cache
    
    @transactional
    async def create_product(self, data, media, transaction_manager):
        # 1. Postgres: structured product data
        product_id = await tm.execute(self.postgres, 'insert', 'products', {...})
        
        # 2. MongoDB: media metadata
        await tm.execute(self.mongodb, 'insert_one', 'product_media', {...})
        
        # 3. Redis: invalidate cache
        await self.redis.delete(f"product:{product_id}")
        
        # All or nothing - automatic rollback on failure
```

#### Transaction Manager
Implements 2PC (Two-Phase Commit):
```python
async with TransactionManager() as tm:
    tm.register(postgres_adapter)
    tm.register(mongodb_adapter)
    
    # Phase 1: Prepare
    await tm.prepare()
    
    # Phase 2: Commit (or rollback on failure)
    await tm.commit()
```

### 6. Cookie & Consent Management

**Location**: `app/core/integrations/analytics/consent_manager.py`

#### Cookie Categories
- **Essential** (no consent needed): session, cart, CSRF, preferences
- **Analytics** (consent required): tracking, performance
- **Marketing** (consent required): ads, conversion tracking
- **Functional** (consent required): chat widgets, embeds

#### ConsentManager
```python
class ConsentManager:
    def __init__(self, user_context: UserContext):
        self.context = user_context
    
    def has_analytics_consent(self) -> bool:
        # Check cookie_consent cookie
        
    def set_consent(self, categories: Dict[str, bool]):
        # Store consent preferences
        
    def requires_consent_banner(self) -> bool:
        # Show banner if no consent set
```

### 7. Theme System

**Location**: `app/core/ui/theme/editor.py`

Theme configuration stored in state:
```python
@dataclass
class ThemeConfig:
    name: str
    colors: ColorScheme
    typography: Typography
    spacing: Spacing
    custom_css: str
    
    def generate_css(self) -> str:
        # Generate CSS from theme config
```

Theme actions modify `theme_state` in State:
```python
class UpdateColorSchemeAction(Action):
    async def run(self, state: State, **inputs) -> ActionResult:
        theme_state = state.get("theme_state")
        theme_state["colors"].update(color_updates)
        return ActionResult(success=True, data={"theme_state": theme_state})
```

### 8. Add-on System

**Location**: `app/core/addon_loader.py` + `app/add_ons/domains/*/manifest.py`

#### Manifest-Based Architecture
Each domain add-on has a `manifest.py` file that declares:
```python
@dataclass
class AddonManifest:
    id: str                              # "lms", "commerce", etc.
    name: str                            # Display name
    version: str                         # Semantic version
    description: str                     # Description
    domain: str                          # Domain identifier
    roles: List[Role]                    # RBAC roles
    settings: List[SettingDefinition]    # Configurable settings
    components: List[Dict]               # UI components
    routes: List[Dict]                   # HTTP routes
    theme_extensions: Dict               # Theme customizations
```

#### Configuration
Enable/disable add-ons in `core/addon_loader.py`:
```python
ENABLED_ADDONS = {
    "lms": True,           # Learning Management System
    "commerce": True,      # E-commerce
    "social": False,       # Social networking
    "stream": False,       # Streaming platform
}
```

#### Loading Process
```
1. AddonLoader.load_enabled_addons()
   ↓
2. For each enabled addon:
   - Import add_ons/domains/{domain}/manifest.py
   - Get {DOMAIN}_MANIFEST
   ↓
3. Register components:
   - Roles → permission_registry
   - Settings → settings system
   - Components → component_library
   - Routes → route loader
   - Theme → theme system
   ↓
4. Store loaded manifest for runtime access
```

#### Available Add-ons
- **LMS** (`add_ons/domains/lms/`) - Courses, lessons, grading, certificates
- **Commerce** (`add_ons/domains/commerce/`) - Products, cart, checkout, payments
- **Social** (`add_ons/domains/social/`) - Posts, comments, likes, follows
- **Stream** (`add_ons/domains/stream/`) - Live streaming, chat, subscriptions

Each manifest defines domain-specific roles, settings, and components.

### 9. Workflow Orchestration

**Location**: `app/core/workflows/`

#### SiteWorkflowManager
High-level API for site operations:
```python
manager = SiteWorkflowManager(persister=persister)

# Create site
result = await manager.create_new_site(
    site_name="My Site",
    initial_sections=[...],
    theme={...},
    user_id="admin"
)

# Load site
result = await manager.load_site(site_id, user_id)
```

#### Workflow Definition
```python
workflow = (
    SiteStateBuilder()
    .with_actions(initialize, add_section, update_theme, validate, publish)
    .with_transitions(
        ("initialize", "add_section", on_success),
        ("add_section", "update_theme", on_success),
        ("update_theme", "validate", on_success)
    )
    .with_conditional_transitions(
        "validate",
        [(no_validation_errors, "publish")],
        default="add_section"  # Loop back on validation failure
    )
    .build()
)
```

---

## Request Flow

### 1. Incoming Request
```
HTTP Request
    ↓
Middleware (Security, Rate Limiting)
    ↓
Auth Middleware (Create UserContext)
    ↓
Route Handler
```

### 2. Dependency Injection
```
Route Handler
    ↓
Create ExecutionContext:
    - UserContext (from middleware)
    - SettingsFacade (user_context + global_settings)
    - ServiceContainer (business services)
    - IntegrationContainer (external clients)
    ↓
Pass to Action/Service
```

### 3. Action Execution
```
Action.execute(state, context)
    ↓
Check Permissions (context.user_context)
    ↓
Check Settings (context.settings)
    ↓
Execute Business Logic (context.services)
    ↓
Call External Services (context.integrations)
    ↓
Transform State (immutable)
    ↓
Return ActionResult + New State
```

### 4. State Persistence
```
New State
    ↓
MongoPersister.save(app_id, state, partition_key)
    ↓
MongoDB Document:
    {
        "app_id": "site_123",
        "partition_key": "draft",
        "state": {...},
        "saved_at": "..."
    }
```

### 5. Response
```
ActionResult
    ↓
Check context.user_context._outgoing_cookies
    ↓
Set Cookies on Response
    ↓
Return HTML/JSON
```

---

## Design Patterns

### 1. **Repository Pattern**
Abstract data access, coordinate multiple databases

### 2. **Unit of Work (UoW)**
Manage transactions across repositories

### 3. **Adapter Pattern**
Unified interface for different databases

### 4. **Command Pattern**
Actions as commands that transform state

### 5. **State Machine**
Workflows as state machines with transitions

### 6. **Facade Pattern**
SettingsFacade provides simplified, role-aware access

### 7. **Dependency Injection**
ExecutionContext bundles all dependencies

### 8. **Decorator Pattern**
@requires_permission for RBAC enforcement

---

## Key Files Reference

### Core Infrastructure
- `app/core/state/state.py` - Immutable State container
- `app/core/state/actions.py` - Action base class
- `app/core/state/persistence.py` - State persistence (MongoDB)
- `app/core/state/builder.py` - StateMachineApplication builder
- `app/core/db/transaction_manager.py` - 2PC coordinator
- `app/core/di/container.py` - ExecutionContext, ServiceContainer, IntegrationContainer
- `app/core/addon_loader.py` - **Consolidated add-on configuration and manifest-based loading**

### User & Permissions
- `app/core/services/auth/context.py` - UserContext, PermissionContext
- `app/core/services/auth/decorators.py` - @require_auth, @requires_permission
- `app/core/services/auth/permissions.py` - Permission definitions
- `app/core/config/settings_facade.py` - Role-aware settings access

### Integrations
- `app/core/integrations/analytics/consent_manager.py` - Cookie consent (GDPR/CCPA)
- `app/core/integrations/payment/` - Payment gateways (Stripe, PayPal)
- `app/core/integrations/email/` - Email providers
- `app/core/integrations/storage/` - Storage providers (S3, MinIO)

### Workflows
- `app/core/workflows/admin.py` - SiteWorkflowManager, site creation workflows
- `app/core/workflows/preview.py` - PreviewPublishManager, preview/publish actions

### UI & Components
- `app/core/ui/components/auth.py` - LoginForm, RegisterForm (DRY)
- `app/core/ui/components/consent_banner.py` - Cookie consent banner
- `app/core/ui/state/factory.py` - Component rendering
- `app/core/ui/theme/editor.py` - ThemeConfig, ThemeActions

### Middleware
- `app/core/middleware/security.py` - Security headers, rate limiting, CSRF
- `app/core/middleware/auth_context.py` - User context injection
- `app/core/middleware/redis_session.py` - Redis session management

### Utilities (DRY Improvements)
- `app/core/utils/app_factory.py` - App creation helpers
- `app/core/utils/responses.py` - Unified response helpers
- `app/core/utils/logger.py` - Centralized logging
- `app/core/utils/helpers.py` - General utility functions

---

## Recent Architectural Improvements (December 2025)

### 1. **Security Hardening** ✅
**Location**: `app/core/config/validation.py`

- **Removed insecure defaults** for JWT_SECRET and APP_MEDIA_KEY
- **Startup validation** ensures all required secrets are set
- **Fail-fast approach** prevents app from starting with missing secrets
- **Secret generation helpers** in `env.example.txt`

```python
# Before: ❌ Insecure default
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")

# After: ✅ Required secret
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required")
```

### 2. **Type Safety with Pydantic** ✅
**Locations**: 
- `app/core/services/auth/models.py`
- `app/core/integrations/storage/models.py`
- `app/core/integrations/huggingface/models.py`

All major services now use Pydantic models for type-safe inputs/outputs:

```python
# Before: ❌ Dict-based
async def login(email: str, password: str) -> Optional[Dict]:
    ...

# After: ✅ Pydantic-based
async def login(request: LoginRequest) -> LoginResponse:
    ...
```

**Benefits:**
- Automatic validation
- IDE autocomplete
- Self-documenting APIs
- Type-safe serialization

**Documentation**: `docs/TYPE_SAFETY.md`, `docs/PYDANTIC_USAGE.md`

### 3. **Standardized Error Handling** ✅
**Locations**:
- `app/core/exceptions.py` - Custom exception hierarchy
- `app/core/middleware/error_handler.py` - Centralized error handler

**Exception Hierarchy:**
```
AppException (base)
├── AuthenticationError (401)
├── AuthorizationError (403)
├── ResourceError (404)
├── ValidationError (422)
├── StorageError (500)
├── ExternalServiceError (502)
├── DatabaseError (500)
├── BusinessLogicError (400)
└── ConfigurationError (500)
```

**Benefits:**
- Consistent error responses
- Structured error data
- Automatic logging
- Clear error types

```python
# Before: ❌ return None
if not user:
    return None

# After: ✅ raise exception
if not user:
    raise InvalidCredentialsError()
```

**Documentation**: `docs/ERROR_HANDLING.md`

### 4. **Dependency Injection Framework** ✅
**Location**: `app/core/di/dependencies.py`

Replaced global singletons with `app.state` dependency injection:

```python
# Before: ❌ Global singleton
_db_service = None
def get_db_service():
    global _db_service
    if _db_service is None:
        _db_service = DBService()
    return _db_service

# After: ✅ Dependency injection (FastHTML)
@router.post("/users")
async def create_user(request: Request, data: dict):
    # Access service directly from app.state
    db = request.app.state.db_service
    return await db.insert("users", data)
```

**Benefits:**
- Isolated per app instance
- Easy to mock in tests
- No global state
- Simple, direct access

**Documentation**: `docs/DEPENDENCY_INJECTION_GUIDE.md`, `docs/GLOBAL_SINGLETONS_AUDIT.md`

### 5. **Async HTTP Client** ✅
**Location**: `app/core/integrations/huggingface/huggingface_client.py`

Replaced synchronous `requests` with async `httpx`:

```python
# Before: ❌ Blocking in async
async def generate_text(prompt: str):
    response = requests.post(url, ...)  # Blocks event loop!

# After: ✅ True async
async def generate_text(request: TextGenerationRequest):
    async with httpx.AsyncClient() as client:
        response = await client.post(url, ...)
```

---

## Future Improvements

### High Priority
1. **Migrate critical singletons to app.state** (Settings, DBService, SessionManager)
2. **Implement ExecutionContext injection** in all Actions
3. **Add @requires_permission decorators** to all service methods
4. **Add comprehensive tests** for Pydantic models and exceptions
5. **Create middleware** to inject ExecutionContext into requests

### Medium Priority
1. **Consolidate Stripe webhook handlers** across domains
2. **Add integration tests** for state transitions
3. **Implement versioning UI** for state rollback
4. **Add audit logging** for all state changes
5. **Performance profiling** and optimization

### Low Priority
1. **GraphQL API** for external integrations
2. **WebSocket support** for real-time updates
3. **Background job system** for async tasks
4. **Multi-tenancy support** with tenant isolation
5. **OpenAPI documentation** generation

---

## Development Guidelines

### 1. **State Modifications**
- Always use Actions to modify state
- Never mutate state directly
- Return new State instances

### 2. **Database Operations**
- Use repositories, not direct adapter calls
- Wrap multi-database operations in @transactional
- Choose the right database for data characteristics

### 3. **Permissions**
- Always check permissions before sensitive operations
- Use @requires_permission decorator
- Pass UserContext to all service methods

### 4. **Settings Access**
- Use SettingsFacade, not direct settings access
- Respect role-based configuration visibility
- Check feature flags before new features

### 5. **Cookie Management**
- Essential cookies don't need consent
- Check consent before setting tracking cookies
- Use UserContext.set_cookie() for response cookies

### 6. **Testing**
- Test Actions in isolation with mock state
- Test repositories with test database
- Test workflows end-to-end
- Test permission enforcement

---

## Glossary

- **Action**: Pure function that transforms State
- **Adapter**: Database-specific implementation
- **ExecutionContext**: Bundle of all dependencies for Actions
- **Partition**: Logical separation of state (draft/published/preview)
- **Repository**: Coordinates data access across databases
- **SettingsFacade**: Role-aware configuration access
- **State**: Immutable container for application state
- **Transition**: Conditional flow between Actions
- **UoW (Unit of Work)**: Manages transactions across repositories
- **UserContext**: Request-scoped user identity and permissions
- **Workflow**: State machine orchestrating multiple Actions

---

## Contact & Support

For questions about this architecture:
1. Review this document
2. Check code comments in key files
3. Review TODOS.md for known issues
4. Review UNIFYING_STATE_SERVICES_SETTINGS_INTEGRATIONS.md for detailed patterns

---

## Development Environment

### Docker Compose Setup

**Single file for local development**: `docker-compose.yml`

Production uses Infrastructure as Code (IaC) - no Docker Compose needed.

**Services provided:**
- **PostgreSQL** (port 5432) - Structured data
- **MongoDB** (port 27017) - Documents and state
- **Redis** (port 6379) - Caching and sessions
- **DuckDB** - Analytics (embedded, optional container)
- **MinIO** (ports 9000/9001) - S3-compatible object storage

**Quick start:**
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Reset volumes (clean slate)
docker compose down -v
```

All services include:
- ✅ Healthchecks
- ✅ Environment variable support
- ✅ Persistent volumes
- ✅ Auto-restart policies
- ✅ Version pinning (no `:latest` tags)

---

**Last Updated**: December 12, 2025
**Version**: 1.1

## Quick Reference Documentation

For detailed information on recent improvements:
- **Security**: `docs/env.example.txt` - Required environment variables
- **Type Safety**: `docs/TYPE_SAFETY.md`, `docs/PYDANTIC_USAGE.md`
- **Error Handling**: `docs/ERROR_HANDLING.md`
- **Dependency Injection**: `docs/DEPENDENCY_INJECTION_GUIDE.md`, `docs/GLOBAL_SINGLETONS_AUDIT.md`
- **Codebase Navigation**: `CODEBASE_INDEX.md`, `FILE_MANIFEST.md`
