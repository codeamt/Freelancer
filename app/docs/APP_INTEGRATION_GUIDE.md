# Add-on Integration Guide

## Overview

FastApp uses a flexible add-on system that allows freelancers to easily enable/disable features per project.

## Configuration-Based Approach (Recommended)

### 1. Enable/Disable Add-ons

Edit `app/config/addons.py`:

```python
ENABLED_ADDONS = {
    "auth": True,      # ✓ Enable authentication
    "lms": True,       # ✓ Enable learning management
    "commerce": True,  # ✓ Enable e-commerce
    "admin": False,    # ✗ Disable admin (not needed)
    "social": False,   # ✗ Disable social (not needed)
}
```

### 2. Update app.py

```python
from fasthtml.common import *
from monsterui.all import Theme
from core.addon_loader import load_addons
from core.routes.main import router_main

# Initialize app
app, rt = fast_app(
    hdrs=[
        *Theme.slate.headers(),
    ],
)

# Mount core routes (landing pages)
router_main.to_app(app)

# Auto-load enabled add-ons
addon_loader = load_addons(app)

# Log loaded add-ons
print(f"Loaded add-ons: {', '.join(addon_loader.get_loaded_addons())}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
```

## Manual Approach (Alternative)

If you prefer explicit control, you can manually mount add-ons:

```python
from fasthtml.common import *
from monsterui.all import Theme

# Core routes
from core.routes.main import router_main

# Add-on routes (import only what you need)
from add_ons.auth import router_auth
from add_ons.lms import router_lms
from add_ons.commerce import router_commerce

# Initialize app
app, rt = fast_app(
    hdrs=[*Theme.slate.headers()],
)

# Mount core
router_main.to_app(app)

# Mount add-ons (comment out to disable)
router_auth.to_app(app)      # Authentication
router_lms.to_app(app)        # Learning Management
router_commerce.to_app(app)   # E-commerce

# Disabled add-ons (commented out)
# from add_ons.admin import router_admin
# router_admin.to_app(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
```

## Per-Client Customization

### Scenario 1: Simple Blog (No Auth)
```python
ENABLED_ADDONS = {
    "auth": False,     # No user accounts needed
    "lms": False,
    "commerce": False,
}
```

### Scenario 2: Course Platform
```python
ENABLED_ADDONS = {
    "auth": True,      # User accounts
    "lms": True,       # Course management
    "commerce": True,  # Sell courses
    "admin": True,     # Admin dashboard
}
```

### Scenario 3: E-commerce Only
```python
ENABLED_ADDONS = {
    "auth": True,      # User accounts
    "commerce": True,  # Shop
    "lms": False,      # No courses
}
```

### Scenario 4: Social Platform
```python
ENABLED_ADDONS = {
    "auth": True,      # User accounts
    "social": True,    # Posts, comments, likes
    "media": True,     # Image uploads
    "lms": False,
    "commerce": False,
}
```

## Dependency Resolution

The system automatically enables required dependencies:

```python
# If you enable LMS...
ENABLED_ADDONS = {
    "lms": True,
    "auth": False,  # ← Will be auto-enabled (LMS requires auth)
}

# Result: Both 'auth' and 'lms' will be loaded
```

## Environment-Based Configuration

For different environments (dev/staging/prod):

```python
import os

ENV = os.getenv("ENVIRONMENT", "development")

if ENV == "development":
    ENABLED_ADDONS = {
        "auth": True,
        "lms": True,
        "commerce": True,
        "admin": True,  # Enable admin in dev
    }
elif ENV == "production":
    ENABLED_ADDONS = {
        "auth": True,
        "lms": True,
        "commerce": True,
        "admin": False,  # Disable admin in prod
    }
```

## Checking Loaded Add-ons at Runtime

```python
from core.addon_loader import load_addons

addon_loader = load_addons(app)

# Check if specific add-on is loaded
if addon_loader.is_loaded("commerce"):
    print("Commerce features available")

# Get all loaded add-ons
loaded = addon_loader.get_loaded_addons()
print(f"Active features: {', '.join(loaded)}")
```

## Add-on Routes

Each add-on is mounted at its designated path:

| Add-on | Mount Point | Example Routes |
|--------|-------------|----------------|
| auth | `/auth` | `/auth/login`, `/auth/register`, `/auth/profile` |
| lms | `/lms` | `/lms/courses`, `/lms/student/dashboard` |
| commerce | `/shop` | `/shop`, `/shop/cart`, `/shop/checkout` |
| admin | `/admin` | `/admin/dashboard`, `/admin/users` |
| social | `/social` | `/social/feed`, `/social/profile` |

## Benefits

### For Freelancers:
1. **Quick Setup** - Enable only needed features
2. **Clean Code** - No commented-out code
3. **Easy Customization** - One config file per project
4. **Clear Billing** - Charge per enabled feature

### For Clients:
1. **Pay for What You Need** - Only enabled features
2. **Easy Upgrades** - Enable new features anytime
3. **Fast Performance** - No unused code loaded

### For Maintenance:
1. **Version Control** - Config changes tracked
2. **Testing** - Test with different configurations
3. **Deployment** - Different configs per environment

## Example: Client Project Setup

```bash
# 1. Clone base project
git clone <repo> client-project
cd client-project

# 2. Configure for client needs
vim app/config/addons.py
# Enable: auth, commerce
# Disable: lms, social, admin

# 3. Run project
python -m app.app

# 4. Only auth and commerce features are available!
```

## Troubleshooting

### Add-on Not Loading
Check logs:
```
INFO: Loading 3 enabled add-ons: auth, commerce, lms
ERROR: Failed to load add-on 'lms': No module named 'add_ons.lms'
```

Solution: Ensure add-on directory exists and has `__init__.py`

### Dependency Issues
```python
# If LMS requires auth but auth is disabled:
ADDON_DEPENDENCIES = {
    "lms": ["auth"],  # LMS needs auth
}

# Auth will be auto-enabled
```

### Route Conflicts
```python
# Change mount points if needed
ADDON_ROUTES = {
    "commerce": "/store",  # Instead of /shop
}
```

## Recommendation for Freelancers

**Use Configuration-Based Approach** because:
- ✅ Cleaner than commenting code
- ✅ Easy to track in version control
- ✅ Can be environment-specific
- ✅ Automatic dependency resolution
- ✅ Professional and maintainable

**Manual Approach** is fine for:
- Small projects (1-2 add-ons)
- Learning/prototyping
- When you want explicit control

---

**Next Steps**: Update your `app/app.py` to use the configuration-based loader!
