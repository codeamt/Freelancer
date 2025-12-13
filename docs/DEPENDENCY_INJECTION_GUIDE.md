# Dependency Injection Migration Guide

Complete guide for migrating from global singletons to `app.state` dependency injection in FastHTML.

## Overview

This guide covers migrating from global singleton pattern to FastHTML's `app.state` dependency injection pattern.

---

## Why Migrate?

### Problems with Global Singletons

```python
# ❌ Global singleton problems
_db_service = None

def get_db_service():
    global _db_service
    if _db_service is None:
        _db_service = DBService()
    return _db_service

# Problems:
# 1. Shared state across tests
# 2. Cannot mock or override
# 3. Hard to test in isolation
# 4. Race conditions in concurrent code
# 5. Difficult to reset state
```

### Benefits of app.state

```python
# ✅ app.state benefits (FastHTML)
@router.get("/endpoint")
async def endpoint(request: Request):
    db = request.app.state.db_service
    return await db.query(...)

# Benefits:
# 1. Isolated per app instance
# 2. Easy to mock in tests
# 3. Clear dependency injection
# 4. No global state
# 5. Simple, direct access
```

---

## Quick Start

### Step 1: Import Request

```python
from fasthtml.common import *
# No special imports needed - just access request.app.state
```

### Step 2: Update Route Handlers

**Before:**
```python
from core.services.db_service import get_db_service

@router.post("/users")
async def create_user(data: dict):
    db = get_db_service()  # ❌ Global singleton
    return await db.insert("users", data)
```

**After (FastHTML):**
```python
from fasthtml.common import *

@router.post("/users")
async def create_user(request: Request, data: dict):
    db = request.app.state.db_service  # ✅ Dependency injection
    return await db.insert("users", data)
```

### Step 3: Initialize in app.py

```python
from core.di.dependencies import initialize_app_state

# Initialize services
db_service = DBService()
auth_service = AuthService(user_repo)

# Store in app.state
initialize_app_state(
    app,
    db_service=db_service,
    auth_service=auth_service
)
```

---

## Migration Examples

### Example 1: DBService

**Before (Global Singleton):**
```python
# core/services/db_service.py
_db_service_instance = None

def get_db_service() -> DBService:
    global _db_service_instance
    if _db_service_instance is None:
        _db_service_instance = DBService()
    return _db_service_instance

# routes/users.py
@router.get("/users")
async def list_users():
    db = get_db_service()  # ❌ Global
    return await db.find_many("users")
```

**After (app.state):**
```python
# core/di/dependencies.py
def get_db_service(request: Request):
    return request.app.state.db_service

# routes/users.py
from fastapi import Depends
from core.di.dependencies import get_db_service

@router.get("/users")
async def list_users(db = Depends(get_db_service)):  # ✅ Injected
    return await db.find_many("users")
```

---

### Example 2: Settings

**Before:**
```python
# settings.py
settings = Settings()

def get_settings():
    return settings

# routes/config.py
@router.get("/config")
async def get_config():
    settings = get_settings()  # ❌ Global
    return {"env": settings.environment}
```

**After (FastHTML):**
```python
# routes/config.py
from fasthtml.common import *

@router.get("/config")
async def get_config(request: Request):
    settings = request.app.state.settings  # ✅ Injected
    return {"env": settings.environment}
```

---

### Example 3: AuthService

**Before:**
```python
# routes/auth.py
from core.services.auth import AuthService

@router.post("/login")
async def login(credentials: LoginRequest):
    # Create new instance each time (inefficient)
    auth = AuthService(user_repo)  # ❌ No reuse
    return await auth.login(credentials)
```

**After (FastHTML):**
```python
# routes/auth.py
from fasthtml.common import *

@router.post("/login")
async def login(request: Request, credentials: LoginRequest):
    auth = request.app.state.auth_service  # ✅ Reused instance
    return await auth.login(credentials)
```

---

## Testing with app.state

### Test Setup

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

@pytest.fixture
def test_app():
    """Create test app with mock services"""
    from fastapi import FastAPI
    from core.di.dependencies import initialize_app_state
    
    app = FastAPI()
    
    # Create mock services
    mock_db = Mock()
    mock_auth = Mock()
    
    # Initialize app.state with mocks
    initialize_app_state(
        app,
        db_service=mock_db,
        auth_service=mock_auth
    )
    
    return app

@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)
```

### Test Example

```python
def test_create_user(client, test_app):
    """Test user creation with mocked DB"""
    # Configure mock
    test_app.state.db_service.insert.return_value = {"id": "123"}
    
    # Make request
    response = client.post("/users", json={"name": "John"})
    
    # Assert
    assert response.status_code == 200
    test_app.state.db_service.insert.assert_called_once()
```

---

## Advanced Patterns

### Multiple Service Access

```python
from fasthtml.common import *

@router.get("/users/{user_id}")
async def get_user(request: Request, user_id: str):
    # Access multiple services from app.state
    db = request.app.state.db_service
    auth = request.app.state.auth_service
    
    # Use services
    user = await db.get_user(user_id)
    return user
```

### Optional Service Access

```python
from fasthtml.common import *

@router.get("/feature")
async def feature_endpoint(request: Request):
    # Check if service exists
    settings = getattr(request.app.state, 'settings', None)
    if settings and settings.feature_enabled:
        return {"enabled": True}
    return {"enabled": False}
```

### Helper Functions

```python
from fasthtml.common import *

async def get_current_user(request: Request, token: str):
    """Helper to get current user from token"""
    auth = request.app.state.auth_service
    return await auth.verify_token(token)

@router.get("/profile")
async def get_profile(request: Request):
    token = request.cookies.get("auth_token")
    user = await get_current_user(request, token)
    return {"user_id": user.sub}
```

---

## Migration Checklist

### For Each Service

- [ ] Create dependency function in `core/di/dependencies.py`
- [ ] Initialize service in `app.py` and store in `app.state`
- [ ] Update all route handlers to use `Depends()`
- [ ] Remove global singleton code
- [ ] Update tests to use test app fixtures
- [ ] Verify no global state remains

### For Each Route File

- [ ] Import `Request` from `fasthtml.common`
- [ ] Add `request: Request` parameter to route handlers
- [ ] Access services via `request.app.state.service_name`
- [ ] Remove direct service instantiation
- [ ] Remove global singleton calls
- [ ] Test routes with new dependency injection

---

## Common Patterns

### Pattern 1: Direct Access (FastHTML)

```python
@router.get("/endpoint")
async def endpoint(request: Request):
    svc = request.app.state.service_name
    return await svc.do_something()
```

### Pattern 2: Multiple Services (FastHTML)

```python
@router.post("/complex")
async def complex_endpoint(request: Request, data: dict):
    # Access multiple services
    db = request.app.state.db_service
    auth = request.app.state.auth_service
    storage = request.app.state.storage_service
    # Use all three services
    pass
```

### Pattern 3: Helper Functions (FastHTML)

```python
async def get_user_by_id(request: Request, user_id: str):
    """Helper function to get user"""
    user_svc = request.app.state.user_service
    return await user_svc.get_user(user_id)

@router.get("/users/{user_id}/profile")
async def user_profile(request: Request, user_id: str):
    user = await get_user_by_id(request, user_id)
    return user
```

---

## Troubleshooting

### Error: "Service not initialized in app.state"

**Problem:**
```python
RuntimeError: DBService not initialized in app.state
```

**Solution:**
```python
# In app.py, ensure service is initialized
from core.di.dependencies import initialize_app_state

db_service = DBService()
initialize_app_state(app, db_service=db_service)
```

### Error: "Cannot access request outside of request context"

**Problem:**
```python
# ❌ Trying to access app.state outside route
db = request.app.state.db_service  # No request available!
```

**Solution:**
```python
# ✅ Access in route handler (FastHTML)
@router.get("/data")
async def get_data(request: Request):
    db = request.app.state.db_service
    return await db.query()
```

### Tests Failing After Migration

**Problem:**
Tests fail because services aren't in app.state

**Solution:**
```python
@pytest.fixture
def test_app():
    app = FastAPI()
    # Initialize test services
    initialize_app_state(
        app,
        db_service=MockDBService(),
        auth_service=MockAuthService()
    )
    return app
```

---

## Best Practices

### 1. Always Use Type Hints (FastHTML)

```python
# ✅ Good - Type hints help IDE
from starlette.requests import Request
from core.services.db_service import DBService

@router.get("/data")
async def get_data(request: Request):
    db: DBService = request.app.state.db_service
    return await db.query()
```

### 2. Initialize All Services in app.py

```python
# ✅ Good - Central initialization
def create_app():
    app = FastAPI()
    
    # Initialize all services
    db = DBService()
    auth = AuthService(user_repo)
    storage = StorageService()
    
    # Store in app.state
    initialize_app_state(
        app,
        db_service=db,
        auth_service=auth,
        storage_service=storage
    )
    
    return app
```

### 3. Direct Access is Recommended (FastHTML)

```python
# ✅ Good - Direct access in FastHTML
@router.get("/data")
async def get_data(request: Request):
    db = request.app.state.db_service
    return await db.query()

# This is the FastHTML pattern - simple and direct
```

### 4. Test with Isolated App Instances

```python
# ✅ Good - Each test gets fresh app
def test_feature_a(test_app):
    # test_app is isolated
    pass

def test_feature_b(test_app):
    # Different test_app instance
    pass
```

---

## Summary

### Before (Global Singletons)
- ❌ Shared state across tests
- ❌ Hard to mock
- ❌ Global variables
- ❌ Race conditions
- ❌ Difficult to reset

### After (app.state in FastHTML)
- ✅ Isolated per app instance
- ✅ Easy to mock in tests
- ✅ Clear dependency injection
- ✅ Simple, direct access
- ✅ No global state

---

## Next Steps

1. Review `GLOBAL_SINGLETONS_AUDIT.md` for list of singletons
2. Start with Phase 1 critical services
3. Update one service at a time
4. Test thoroughly after each migration
5. Update documentation as you go
