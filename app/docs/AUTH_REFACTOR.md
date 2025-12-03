# Auth Refactor: From Add-on to Service

**Date:** December 2, 2025  
**Status:** ✅ Complete

---

## 🎯 Objective

Refactor authentication from a standalone add-on with UI/routes to a universal service that domains use to implement their own branded auth experiences.

---

## 💡 Key Insight

**Problem:** Auth had its own generic UI/routes, but each domain needs custom-branded auth pages.

**Solution:** Auth should be a **service** (like JWT, password hashing), not an add-on with UI. Domains implement their own auth UI using the service.

---

## 📊 Before vs After

### **Before (Auth as Add-on):**
```
add_ons/auth/                    ← Standalone add-on
├── routes/                      ← Generic login/register routes
│   ├── auth_routes.py
│   └── oauth_routes.py
├── ui/                          ← Generic login/register pages
│   ├── login.py
│   └── register.py
└── services/                    ← Auth logic
    └── auth_service.py

app.py:
  app.mount("/auth", router_auth)  ← Global /auth routes

Problem:
- Generic UI doesn't match domain branding
- All domains share same /auth routes
- Can't customize UX per domain
```

### **After (Auth as Service):**
```
add_ons/services/
└── auth.py                      ← Universal auth service
    - JWT creation/verification
    - Password hashing
    - Role/permission management
    - Session helpers

examples/eshop/
├── app.py                       ← E-Shop implements own auth
└── auth_ui.py                   ← E-Shop-branded login/register

examples/lms/
├── app.py                       ← LMS implements own auth
└── auth_ui.py                   ← LMS-branded login/register

Benefits:
✅ Each domain has custom-branded auth UI
✅ Auth service is universal and reusable
✅ Domains control their own UX
✅ No generic /auth routes
```

---

## 🔧 What Changed

### **1. Created Universal Auth Service**
**File:** `add_ons/services/auth.py`

**Provides:**
- `AuthService` class
  - `create_access_token()` - JWT creation
  - `verify_access_token()` - JWT verification
  - `authenticate_user()` - Login logic
  - `register_user()` - Registration logic
  - `get_user_by_id()` - User lookup
  - `get_user_roles()` - Role management
  - `get_user_permissions()` - Permission checking
  - `has_role()` - Role checking
  - `has_permission()` - Permission checking

- Helper functions
  - `get_current_user()` - Extract user from request
  - `require_role()` - Decorator for role-based access
  - `require_permission()` - Decorator for permission-based access

**Usage:**
```python
from add_ons.services.auth import AuthService, get_current_user, require_role

# In domain routes
auth = AuthService(db_service)
user = await auth.authenticate_user(email, password)
token = auth.create_access_token(user["_id"])
```

### **2. Removed Auth Add-on**
```bash
❌ Deleted: add_ons/auth/
   - routes/
   - ui/
   - services/
   - docs/

❌ Deleted: add_ons/services/auth_base.py (redundant)
```

### **3. Updated Core Services**
**File:** `core/services/__init__.py`

**Change:**
```python
# Old
from .auth import AuthService, UserService, get_current_user

# New
from add_ons.services.auth import AuthService, get_current_user, require_role
```

**Reason:** Examples import from `core.services`, so we re-export from there for backwards compatibility.

### **4. Updated Main App**
**File:** `app/app.py`

**Removed:**
```python
# Mount auth add-on
from add_ons.auth import router_auth
router_auth.to_app(app)
```

**Added:**
```python
# Note: Auth is now a service (add_ons/services/auth.py)
# Each example implements its own auth UI/routes
```

### **5. Examples Already Compatible**
**No changes needed!**

Examples already import from `core.services`:
```python
from core.services import AuthService, get_current_user
```

They already have their own auth UI:
- `examples/eshop/auth_ui.py` - E-Shop login/register
- `examples/lms/auth_ui.py` - LMS login/register

---

## 🎨 Architecture Pattern

### **Service Layer (Infrastructure):**
```
add_ons/services/auth.py
├── JWT utilities
├── Password hashing
├── Role/permission logic
└── Session helpers
```

### **Domain Layer (Business Logic):**
```
examples/eshop/
├── app.py                    ← E-Shop auth routes
│   @app.post("/login")
│   @app.post("/register")
│
└── auth_ui.py                ← E-Shop auth UI
    - EShopLoginPage()
    - EShopRegisterPage()
```

### **Benefits:**
1. **Separation of Concerns**
   - Service = Technical utilities
   - Domain = Business logic + UX

2. **Customization**
   - Each domain controls its auth UX
   - Branding, redirects, validation

3. **Reusability**
   - Auth service used by all domains
   - No code duplication

4. **Flexibility**
   - Domains can add custom auth flows
   - OAuth, 2FA, magic links, etc.

---

## 📝 Migration Guide

### **For Existing Domains:**

**If you were using:**
```python
from add_ons.auth import router_auth
app.mount("/auth", router_auth)
```

**Change to:**
```python
from add_ons.services.auth import AuthService, get_current_user

# Implement your own routes
@app.post("/login")
async def login(request: Request):
    auth = AuthService(db_service)
    # Your custom login logic
    
@app.post("/register")
async def register(request: Request):
    auth = AuthService(db_service)
    # Your custom registration logic
```

### **For New Domains:**

1. **Import auth service:**
   ```python
   from add_ons.services.auth import AuthService, get_current_user, require_role
   ```

2. **Create domain-specific auth UI:**
   ```python
   # my_domain/auth_ui.py
   def MyDomainLoginPage():
       return Div(
           # Your custom login form
           # With your branding
       )
   ```

3. **Implement auth routes:**
   ```python
   # my_domain/app.py
   @app.post("/login")
   async def login(request: Request):
       auth = AuthService(db_service)
       user = await auth.authenticate_user(email, password)
       if user:
           token = auth.create_access_token(user["_id"])
           # Set cookie, redirect, etc.
   ```

---

## 🔒 Security Features

### **Maintained:**
- ✅ JWT token creation/verification
- ✅ Password hashing (bcrypt)
- ✅ Role-based access control (RBAC)
- ✅ Permission-based access control
- ✅ Token expiration
- ✅ Secure cookie handling

### **Enhanced:**
- ✅ Domains control auth flow
- ✅ Custom validation per domain
- ✅ Domain-specific redirects
- ✅ Flexible session management

---

## 🧪 Testing

### **Service Tests:**
```python
# Test auth service
from add_ons.services.auth import AuthService

auth = AuthService()

# Test JWT
token = auth.create_access_token("user123")
payload = auth.verify_access_token(token)
assert payload["sub"] == "user123"

# Test password
user = await auth.register_user("test@example.com", "password123")
assert user is not None

authenticated = await auth.authenticate_user("test@example.com", "password123")
assert authenticated is not None
```

### **Domain Tests:**
```python
# Test domain auth routes
response = client.post("/login", data={
    "email": "test@example.com",
    "password": "password123"
})
assert response.status_code == 200
assert "access_token" in response.cookies
```

---

## 📊 Impact Analysis

### **Breaking Changes:**
```
❌ Global /auth routes removed
❌ add_ons.auth module removed
```

### **Non-Breaking:**
```
✅ Examples already compatible (import from core.services)
✅ Auth service API unchanged
✅ JWT tokens still work
✅ Roles/permissions still work
```

### **Migration Effort:**
```
Examples:     ✅ No changes needed
New domains:  ⚙️ Implement own auth UI (recommended pattern)
Old code:     ⚠️ Update imports if using add_ons.auth directly
```

---

## 🎯 Best Practices

### **1. Domain Auth Implementation:**
```python
# ✅ Good: Domain-specific auth
@app.post("/my-domain/login")
async def domain_login(request: Request):
    auth = AuthService(db_service)
    # Custom validation
    # Custom redirects
    # Domain-specific logic
```

```python
# ❌ Bad: Generic auth
@app.post("/auth/login")  # Generic route
async def generic_login(request: Request):
    # One-size-fits-all logic
```

### **2. Custom Branding:**
```python
# ✅ Good: Branded UI
def EShopLoginPage():
    return Div(
        H1("Welcome to E-Shop"),
        # E-Shop colors, logo, style
    )
```

```python
# ❌ Bad: Generic UI
def LoginPage():
    return Div(
        H1("Login"),  # Generic
    )
```

### **3. Service Usage:**
```python
# ✅ Good: Use service for logic
auth = AuthService(db_service)
user = await auth.authenticate_user(email, password)

# ❌ Bad: Duplicate auth logic
# Don't reimplement JWT, password hashing, etc.
```

---

## 📚 Related Documentation

- `ARCHITECTURE.md` - Overall architecture
- `SCHEMA_CLEANUP.md` - Schema organization
- `MIDDLEWARE_FASTHTML_COMPATIBILITY.md` - Middleware setup
- `add_ons/services/auth.py` - Auth service source code

---

## ✅ Summary

### **What We Did:**
1. ✅ Created universal auth service (`add_ons/services/auth.py`)
2. ✅ Removed auth add-on with generic UI/routes
3. ✅ Updated core services to re-export auth
4. ✅ Removed redundant `auth_base.py`
5. ✅ Updated main app (removed /auth mount)
6. ✅ Verified examples still work

### **Benefits:**
- 🎨 **Custom UX** - Each domain controls its auth UI
- 🔧 **Universal Service** - Auth logic is reusable
- 📦 **Better Organization** - Clear service/domain separation
- 🚀 **Flexibility** - Domains can customize auth flows

### **Architecture:**
```
Services (Infrastructure)  →  Domains (Business Logic)
     auth.py              →  eshop/auth_ui.py
     (JWT, passwords)     →  (E-Shop branding)
```

---

**Status:** ✅ Complete  
**Breaking Changes:** Minimal (examples unaffected)  
**Recommendation:** ⭐ Use this pattern for all infrastructure services
