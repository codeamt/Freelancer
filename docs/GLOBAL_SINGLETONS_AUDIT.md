# Global Singletons Audit

Comprehensive audit of all global singleton instances in the codebase.

## Overview

Found **15 global singleton instances** that should be refactored to use `app.state` dependency injection pattern.

---

## Critical Singletons (High Priority)

### 1. **Settings** (`settings.py`)
```python
# ❌ Current (global singleton)
settings = Settings()

def get_settings() -> Settings:
    return settings
```

**Issues:**
- Global state makes testing difficult
- Cannot have different settings per test
- Hard to mock or override

**Solution:**
```python
# ✅ Use app.state
def get_settings(request: Request) -> Settings:
    return request.app.state.settings
```

---

### 2. **DBService** (`core/services/db_service.py`)
```python
# ❌ Current (global singleton)
_db_service_instance: Optional[DBService] = None

def get_db_service() -> DBService:
    global _db_service_instance
    if _db_service_instance is None:
        _db_service_instance = DBService()
    return _db_service_instance
```

**Issues:**
- Shared database connections across tests
- Cannot isolate test data
- Difficult to test with mock databases

**Solution:**
```python
# ✅ Use app.state
def get_db_service(request: Request) -> DBService:
    return request.app.state.db_service
```

---

### 3. **SessionManager** (`core/db/session.py`)
```python
# ❌ Current (global singleton)
_session_manager: Optional[SessionManager] = None

def initialize_session_manager(postgres, mongodb, redis):
    global _session_manager
    _session_manager = SessionManager(postgres, mongodb, redis)

def get_session_manager() -> SessionManager:
    global _session_manager
    return _session_manager
```

**Issues:**
- Shared session state
- Cannot test session isolation
- Race conditions in concurrent tests

**Solution:**
```python
# ✅ Use app.state
def get_session_manager(request: Request) -> SessionManager:
    return request.app.state.session_manager
```

---

### 4. **SettingsService** (`core/services/settings/service.py`)
```python
# ❌ Current (global singleton)
settings_service = SettingsService()

def initialize_settings_service(db_service):
    global settings_service
    settings_service = SettingsService(db_service)
```

**Issues:**
- Settings changes affect all tests
- Cannot test settings isolation
- Difficult to reset state

---

### 5. **ConnectionPoolManager** (`core/db/connection_pool.py`)
```python
# ❌ Current (global singleton)
_pool_manager: Optional[ConnectionPoolManager] = None

def get_pool_manager() -> ConnectionPoolManager:
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager()
    return _pool_manager
```

**Issues:**
- Shared connection pools
- Cannot test connection failures
- Resource leaks in tests

---

## Medium Priority Singletons

### 6. **AddonLoader** (`core/addon_loader.py`)
```python
_addon_loader: Optional[AddonLoader] = None

def get_addon_loader() -> AddonLoader:
    global _addon_loader
    if _addon_loader is None:
        _addon_loader = AddonLoader()
    return _addon_loader
```

### 7. **GraphQLService** (`add_ons/services/graphql.py`)
```python
_graphql_service: Optional[GraphQLService] = None

def get_graphql_service() -> GraphQLService:
    global _graphql_service
    if _graphql_service is None:
        _graphql_service = GraphQLService()
    return _graphql_service
```

### 8. **EventBus** (`add_ons/services/event_bus_base.py`)
```python
# Singleton
bus = EventBus()
```

### 9. **StatePersister** (`core/state/persistence.py`)
```python
_persister: Optional['StatePersister'] = None

def get_persister() -> 'StatePersister':
    global _persister
    if _persister is None:
        _persister = InMemoryPersister()
    return _persister
```

### 10. **SessionManager (Settings)** (`core/services/settings/session.py`)
```python
session_manager = SessionManager()

def initialize_session_manager(db_service):
    global session_manager
    session_manager = SessionManager(db_service)
```

---

## Low Priority (Registries - Acceptable as Globals)

These are registries that hold configuration data, not runtime state:

### 11. **PermissionRegistry** (`core/services/auth/permissions.py`)
```python
permission_registry = PermissionRegistry()
```

**Note:** Registries are acceptable as globals since they hold static configuration, not runtime state.

### 12. **SettingsRegistry** (`core/services/settings/registry.py`)
```python
settings_registry = SettingsRegistry()
```

### 13. **SchemaRegistry** (`core/db/graphql/schema_registry.py`)
```python
schema_registry = SchemaRegistry()
```

### 14. **EncryptionService** (`core/services/settings/encryption.py`)
```python
encryption_service = EncryptionService()
```

### 15. **SecurityService** (`core/services/auth/security.py`)
```python
security = SecurityService()
```

---

## Context Variables (Not Singletons)

These use `ContextVar` which is thread-safe and request-scoped:

```python
# ✅ OK - Uses ContextVar (request-scoped)
current_user_context: ContextVar[UserContext] = ContextVar('current_user_context')
```

---

## Module-Level Constants (OK)

These are configuration constants, not singletons:

```python
# ✅ OK - Configuration constants
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = int(os.getenv("TOKEN_EXPIRATION_HOURS", "12"))
```

---

## Refactoring Priority

### Phase 1: Critical (Must Fix)
1. ✅ Settings
2. ✅ DBService
3. ✅ SessionManager
4. ✅ SettingsService
5. ✅ ConnectionPoolManager

### Phase 2: Medium (Should Fix)
6. AddonLoader
7. GraphQLService
8. EventBus
9. StatePersister
10. SessionManager (Settings)

### Phase 3: Low (Optional)
11-15. Registries and utility services (acceptable as globals)

---

## Benefits of Refactoring

### Before (Global Singletons)
```python
# ❌ Problems
def my_route():
    db = get_db_service()  # Global instance
    # - Cannot test with mock DB
    # - Shared state across tests
    # - Hard to isolate failures
```

### After (app.state)
```python
# ✅ Benefits
def my_route(request: Request):
    db = request.app.state.db_service
    # - Easy to test with mock DB
    # - Isolated state per app instance
    # - Clear dependency injection
```

### Testing Benefits

**Before:**
```python
# ❌ Tests affect each other
def test_user_creation():
    db = get_db_service()  # Global
    db.insert("users", {...})
    # Data persists across tests!

def test_user_query():
    db = get_db_service()  # Same global instance
    # Sees data from previous test!
```

**After:**
```python
# ✅ Isolated tests
def test_user_creation(test_app):
    db = test_app.state.db_service  # Test instance
    db.insert("users", {...})
    # Isolated to this test

def test_user_query(test_app):
    db = test_app.state.db_service  # Fresh instance
    # Clean state
```

---

## Implementation Plan

### Step 1: Create Dependency Injection Helpers
- Create `core/di/dependencies.py` with FastAPI Depends functions
- Provide type-safe dependency injection

### Step 2: Update app.py
- Initialize all services in `app.state`
- Remove global singleton initialization

### Step 3: Update Service Getters
- Replace global getters with `Depends()` functions
- Update all route handlers

### Step 4: Update Tests
- Create test fixtures that provide isolated app instances
- Remove global state cleanup code

---

## Next Steps

1. Create dependency injection utilities
2. Refactor Phase 1 critical singletons
3. Update app.py initialization
4. Create migration guide for remaining code
