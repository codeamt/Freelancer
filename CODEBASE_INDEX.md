# Codebase Index for LLM Navigation

Quick reference guide for navigating the codebase. Optimized for LLM context scanning.

---

## Core Concepts

### 1. State Management
- **Pattern**: Immutable state with actions and transitions
- **Files**: `app/core/state/*.py`
- **Key Classes**: `State`, `Action`, `StateMachineApplication`

### 2. Database Layer
- **Pattern**: Polyglot persistence with repository pattern
- **Files**: `app/core/db/*.py`
- **Databases**: PostgreSQL, MongoDB, Redis, DuckDB, MinIO

### 3. Authentication & Authorization
- **Pattern**: RBAC with UserContext and permissions
- **Files**: `app/core/services/auth/*.py`
- **Key Classes**: `AuthService`, `UserContext`, `Permission`

### 4. Dependency Injection
- **Pattern**: app.state with direct access in route handlers
- **Files**: `app/core/di/*.py`
- **Key Pattern**: Access services via `request.app.state.service_name`

### 5. Error Handling
- **Pattern**: Custom exception hierarchy with middleware
- **Files**: `app/core/exceptions.py`, `app/core/middleware/error_handler.py`
- **Base Class**: `AppException`

---

## Directory Quick Reference

```
app/
├── core/                      # Framework core (reusable)
│   ├── config/               # Configuration & validation
│   ├── db/                   # Database adapters & repositories
│   ├── di/                   # Dependency injection
│   ├── exceptions.py         # Exception hierarchy
│   ├── integrations/         # External services (storage, email, AI)
│   ├── middleware/           # Request/response middleware
│   ├── services/             # Business logic
│   ├── state/                # State management
│   ├── ui/                   # UI components & theme
│   └── workflows/            # Workflow orchestration
│
├── add_ons/                  # Domain modules (LMS, commerce, etc.)
│   └── domains/
│       ├── commerce/
│       ├── lms/
│       ├── social/
│       └── stream/
│
└── routes/                   # HTTP route handlers

docs/                         # Documentation
├── ARCHITECTURE.md           # This file
├── CODEBASE_INDEX.md         # Quick navigation (this file)
├── FILE_MANIFEST.md          # All important files
├── TYPE_SAFETY.md            # Pydantic models guide
├── PYDANTIC_USAGE.md         # Usage examples
├── ERROR_HANDLING.md         # Exception handling guide
├── DEPENDENCY_INJECTION_GUIDE.md  # DI migration guide
└── GLOBAL_SINGLETONS_AUDIT.md     # Singleton audit
```

---

## Key File Locations

### Configuration & Security
- `app/core/config/validation.py` - Startup validation
- `app/core/config/settings_facade.py` - Role-aware settings
- `env.example.txt` - Required environment variables

### Authentication
- `app/core/services/auth/auth_service.py` - Auth business logic
- `app/core/services/auth/models.py` - Pydantic models (User, LoginRequest, etc.)
- `app/core/services/auth/context.py` - UserContext
- `app/core/services/auth/permissions.py` - Permission definitions
- `app/core/services/auth/decorators.py` - @require_auth, @requires_permission

### Database
- `app/core/db/adapters/` - Database adapters (PostgreSQL, MongoDB, Redis)
- `app/core/db/repositories/` - Repository implementations
- `app/core/db/session.py` - Session management
- `app/core/db/transaction_manager.py` - 2PC coordinator
- `app/core/db/connection_pool.py` - Connection pooling

### Services
- `app/core/services/db_service.py` - Database service
- `app/core/services/auth/user_service.py` - User management
- `app/core/services/settings/service.py` - Settings service

### Integrations
- `app/core/integrations/storage/s3_client.py` - S3/MinIO storage
- `app/core/integrations/storage/models.py` - Storage Pydantic models
- `app/core/integrations/huggingface/huggingface_client.py` - AI client
- `app/core/integrations/huggingface/models.py` - AI Pydantic models
- `app/core/integrations/email/` - Email providers
- `app/core/integrations/payment/` - Payment gateways

### State Management
- `app/core/state/state.py` - Immutable State container
- `app/core/state/actions.py` - Action base class
- `app/core/state/builder.py` - StateMachineApplication builder
- `app/core/state/persistence.py` - MongoDB persistence
- `app/core/state/transitions.py` - Transition conditions

### Middleware
- `app/core/middleware/error_handler.py` - Error handling middleware
- `app/core/middleware/security.py` - Security headers, CSRF, rate limiting
- `app/core/middleware/auth_context.py` - User context injection
- `app/core/middleware/redis_session.py` - Redis sessions

### Dependency Injection
- `app/core/di/dependencies.py` - DI helper functions
- `app/core/di/container.py` - ExecutionContext, ServiceContainer

### UI & Components
- `app/core/ui/layout.py` - Layout components
- `app/core/ui/components/` - Reusable UI components
- `app/core/ui/theme/editor.py` - Theme system
- `app/core/ui/state/` - UI state management

### Utilities
- `app/core/utils/logger.py` - Centralized logging
- `app/core/utils/security.py` - Security utilities
- `app/core/utils/helpers.py` - General helpers

### Routes
- `app/routes/auth.py` - Authentication routes
- `app/routes/main.py` - Main routes
- `app/routes/admin_sites.py` - Admin routes
- `app/routes/settings.py` - Settings routes
- `app/routes/editor.py` - Editor routes

### Add-ons
- `app/add_ons/domains/commerce/` - E-commerce domain
- `app/add_ons/domains/lms/` - Learning management system
- `app/add_ons/domains/social/` - Social networking
- `app/add_ons/domains/stream/` - Streaming platform

---

## Common Tasks

### Adding a New Service
1. Create service class in `app/core/services/{domain}/`
2. Create Pydantic models in `{service}_models.py`
3. Add dependency function in `app/core/di/dependencies.py`
4. Initialize in `app/app.py` and store in `app.state`
5. Export from `__init__.py`

### Adding a New Route
1. Create route file in `app/routes/{name}.py`
2. Use `Depends()` for service injection
3. Use Pydantic models for request/response
4. Add permission decorators if needed
5. Register in route loader

### Adding a New Exception
1. Add exception class to `app/core/exceptions.py`
2. Inherit from appropriate base exception
3. Set correct `status_code`
4. Add to `__all__` export

### Adding a New Pydantic Model
1. Create model in appropriate `models.py` file
2. Add validation rules
3. Export from `__init__.py`
4. Update service methods to use model
5. Document in TYPE_SAFETY.md

### Adding a New Database Operation
1. Add method to repository in `app/core/db/repositories/`
2. Use `@transactional` for multi-database operations
3. Choose appropriate database for data type
4. Handle exceptions properly

---

## Search Patterns

### Find Authentication Code
```
app/core/services/auth/
app/core/middleware/auth_context.py
```

### Find Database Code
```
app/core/db/
app/core/db/adapters/
app/core/db/repositories/
```

### Find Error Handling
```
app/core/exceptions.py
app/core/middleware/error_handler.py
```

### Find Pydantic Models
```
app/core/services/auth/models.py
app/core/integrations/storage/models.py
app/core/integrations/huggingface/models.py
```

### Find Dependency Injection
```
app/core/di/dependencies.py
app/app.py (initialization)
```

### Find State Management
```
app/core/state/
app/core/workflows/
```

### Find UI Components
```
app/core/ui/components/
app/core/ui/theme/
```

---

## Important Patterns

### Service Method Pattern (FastHTML)
```python
from fasthtml.common import *

@router.post("/endpoint")
async def endpoint(request: Request, data: RequestModel) -> ResponseModel:
    # Access service from app.state
    service = request.app.state.service_name
    return await service.method(data)
```

### Exception Pattern
```python
from core.exceptions import SpecificError

def method():
    if error_condition:
        raise SpecificError("message", details={...})
```

### Repository Pattern
```python
class Repository:
    def __init__(self, postgres, mongodb, redis):
        self.postgres = postgres
        self.mongodb = mongodb
        self.redis = redis
    
    @transactional
    async def method(self, tm):
        # Multi-database operation
        await tm.execute(self.postgres, ...)
        await tm.execute(self.mongodb, ...)
```

### Action Pattern
```python
class MyAction(Action):
    async def run(self, state: State, **inputs) -> ActionResult:
        # Transform state immutably
        new_data = state.get("key")
        # Modify new_data
        return ActionResult(success=True, data={"key": new_data})
```

---

## Testing Locations

### Unit Tests
- `tests/unit/` - Unit tests for individual components

### Integration Tests
- `tests/integration/` - Integration tests for services

### Test Fixtures
- `tests/conftest.py` - Shared fixtures
- `tests/fixtures/` - Test data

---

## Configuration Files

- `.env` - Environment variables (not in repo)
- `env.example.txt` - Example environment variables
- `docker-compose.yml` - Local development services
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project configuration

---

## Documentation Files

- `ARCHITECTURE.md` - Architecture overview
- `CODEBASE_INDEX.md` - This file (navigation guide)
- `FILE_MANIFEST.md` - Complete file listing
- `README.md` - Project overview
- `docs/TYPE_SAFETY.md` - Type safety guide
- `docs/PYDANTIC_USAGE.md` - Pydantic usage examples
- `docs/ERROR_HANDLING.md` - Error handling guide
- `docs/DEPENDENCY_INJECTION_GUIDE.md` - DI migration guide
- `docs/GLOBAL_SINGLETONS_AUDIT.md` - Singleton audit

---

## Quick Tips for LLMs

1. **Start with ARCHITECTURE.md** for high-level understanding
2. **Use this file (CODEBASE_INDEX.md)** for quick navigation
3. **Check FILE_MANIFEST.md** for complete file listing
4. **Read Pydantic models** to understand data structures
5. **Check exceptions.py** to understand error types
6. **Look at dependencies.py** to understand service injection
7. **Review middleware/** to understand request flow
8. **Check routes/** to understand API endpoints

---

**Last Updated**: December 12, 2025
