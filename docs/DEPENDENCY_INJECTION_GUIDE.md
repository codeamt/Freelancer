# Dependency Injection Migration Guide

Complete guide for migrating from global singletons to `app.state` dependency injection.

## Overview

This guide covers migrating from global singleton pattern to FastAPI's `app.state` dependency injection pattern.

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
# ✅ app.state benefits
def get_db_service(request: Request):
    return request.app.state.db_service

# Benefits:
# 1. Isolated per app instance
# 2. Easy to mock in tests
# 3. Clear dependency injection
# 4. No global state
# 5. Type-safe with FastAPI Depends
```

---

## Quick Start

### Step 1: Import Dependencies

```python
from fastapi import Depends, Request
from core.di.dependencies import get_db_service, get_auth_service
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

**After:**
```python
from fastapi import Depends
from core.di.dependencies import get_db_service

@router.post("/users")
async def create_user(
    data: dict,
    db = Depends(get_db_service)  # ✅ Dependency injection
):
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

**After:**
```python
# core/di/dependencies.py
def get_settings(request: Request):
    return request.app.state.settings

# routes/config.py
from fastapi import Depends
from core.di.dependencies import get_settings

@router.get("/config")
async def get_config(settings = Depends(get_settings)):  # ✅ Injected
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

**After:**
```python
# routes/auth.py
from fastapi import Depends
from core.di.dependencies import get_auth_service

@router.post("/login")
async def login(
    credentials: LoginRequest,
    auth = Depends(get_auth_service)  # ✅ Reused instance
):
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

### Nested Dependencies

```python
from fastapi import Depends

def get_user_service(
    db = Depends(get_db_service),
    auth = Depends(get_auth_service)
):
    """UserService depends on DB and Auth"""
    return UserService(db, auth)

@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    user_svc = Depends(get_user_service)  # Auto-resolves dependencies
):
    return await user_svc.get_user(user_id)
```

### Optional Dependencies

```python
from core.di.dependencies import get_settings_optional

@router.get("/feature")
async def feature_endpoint(
    settings = Depends(get_settings_optional)
):
    if settings and settings.feature_enabled:
        return {"enabled": True}
    return {"enabled": False}
```

### Class-Based Dependencies

```python
from fastapi import Depends

class UserDependency:
    def __init__(self, request: Request):
        self.auth = request.app.state.auth_service
    
    async def __call__(self, token: str):
        return await self.auth.verify_token(token)

@router.get("/profile")
async def get_profile(
    user = Depends(UserDependency())
):
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

- [ ] Import `Depends` from `fastapi`
- [ ] Import dependency functions from `core.di.dependencies`
- [ ] Add dependency parameters to route handlers
- [ ] Remove direct service instantiation
- [ ] Update function signatures with type hints
- [ ] Test routes with new dependency injection

---

## Common Patterns

### Pattern 1: Simple Dependency

```python
# Dependency function
def get_service(request: Request):
    return request.app.state.service

# Usage
@router.get("/endpoint")
async def endpoint(svc = Depends(get_service)):
    return await svc.do_something()
```

### Pattern 2: Multiple Dependencies

```python
@router.post("/complex")
async def complex_endpoint(
    db = Depends(get_db_service),
    auth = Depends(get_auth_service),
    storage = Depends(get_storage_service)
):
    # Use all three services
    pass
```

### Pattern 3: Dependency with Parameters

```python
def get_user_by_id(user_id: str):
    def dependency(
        user_svc = Depends(get_user_service)
    ):
        return user_svc.get_user(user_id)
    return Depends(dependency)

@router.get("/users/{user_id}/profile")
async def user_profile(
    user = Depends(get_user_by_id)
):
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
# ❌ Trying to use dependency outside route
db = get_db_service()  # No request available!
```

**Solution:**
```python
# ✅ Use dependency in route handler
@router.get("/data")
async def get_data(db = Depends(get_db_service)):
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

### 1. Always Use Type Hints

```python
# ✅ Good - Type hints help IDE
from core.services.db_service import DBService

@router.get("/data")
async def get_data(db: DBService = Depends(get_db_service)):
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

### 3. Use Dependency Functions, Not Direct Access

```python
# ❌ Bad - Direct access
@router.get("/data")
async def get_data(request: Request):
    db = request.app.state.db_service
    return await db.query()

# ✅ Good - Use dependency function
@router.get("/data")
async def get_data(db = Depends(get_db_service)):
    return await db.query()
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

### After (app.state)
- ✅ Isolated per app instance
- ✅ Easy to mock in tests
- ✅ Clear dependency injection
- ✅ Type-safe with Depends
- ✅ No global state

---

## Next Steps

1. Review `GLOBAL_SINGLETONS_AUDIT.md` for list of singletons
2. Start with Phase 1 critical services
3. Update one service at a time
4. Test thoroughly after each migration
5. Update documentation as you go
