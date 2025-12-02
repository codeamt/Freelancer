# Core Refactoring Plan

## Objective
Refactor `app/core/` to be a minimal landing page with only shared services. Move add-on specific functionality to `app/add_ons/`.

## Core Should Contain

### UI (`app/core/ui/`)
- ✅ `layout.py` - Base layout with NavBar
- ✅ `components.py` - Shared UI components (HeroSection, FeatureCard, etc.)
- ✅ `pages/home.py` - Landing page
- ✅ `pages/docs.py` - Documentation page
- ✅ `pages/test.py` - Component test page
- ✅ `pages/about.py` - About page
- ✅ `pages/contact.py` - Contact page
- ❌ `pages/login.py` → Move to `add_ons/auth/`
- ❌ `pages/register.py` → Move to `add_ons/auth/`
- ❌ `pages/profile.py` → Move to `add_ons/auth/`
- ❌ `pages/admin.py` → Move to `add_ons/admin/`
- ❌ `pages/example_landing.py` → Move to `add_ons/lms/` (as example)

### Services (`app/core/services/`)
- ✅ `base/` - Abstract base classes (NEW)
- ✅ `db.py` - Generic database service (refactor to extend BaseDBService)
- ✅ `storage.py` - Generic storage service (refactor to extend BaseStorageService)
- ✅ `email.py` - Generic email service (refactor to extend BaseEmailService)
- ✅ `notifications.py` - Generic notification service (refactor to extend BaseNotificationService)
- ✅ `event_bus.py` - Event bus for pub/sub
- ❌ `auth.py` → Keep minimal version, move user management to `add_ons/auth/`
- ❌ `oauth.py` → Move to `add_ons/auth/services/`
- ❌ `stripe.py` → Move to `add_ons/commerce/services/`
- ❌ `analytics.py` → Move to `add_ons/analytics/services/`
- ❌ `recommender.py` → Move to `add_ons/analytics/services/`

### Routes (`app/core/routes/`)
- ✅ `main.py` - Landing page routes only (/, /docs, /test, /about, /contact)
- ❌ `auth.py` → Move to `add_ons/auth/routes/`
- ❌ `admin.py` → Move to `add_ons/admin/routes/`
- ❌ `media.py` → Move to `add_ons/media/routes/`
- ❌ `webhooks.py` → Move to `add_ons/webhooks/routes/`
- ❌ `graphql.py` → Move to `add_ons/graphql/routes/`
- ❌ `ui.py` → Remove (theme switching not needed for minimal core)

### Utils (`app/core/utils/`)
- ✅ `logger.py` - Logging utilities
- ✅ `security.py` - Security utilities (token generation, hashing)

### Middleware (`app/core/middleware/`)
- ✅ `security.py` - Security middleware
- ✅ `session_middleware.py` - Session management

### Database (`app/core/db/`)
- ✅ `models.py` - Shared data models
- ✅ `migrations/` - Database migrations

## Add-ons Structure

### Auth Add-on (`app/add_ons/auth/`)
```
auth/
├── __init__.py
├── README.md
├── services/
│   ├── __init__.py
│   ├── auth_service.py (extends BaseAuthService)
│   └── oauth_service.py
├── routes/
│   ├── __init__.py
│   └── auth_routes.py
├── ui/
│   ├── __init__.py
│   └── pages/
│       ├── __init__.py
│       ├── login.py
│       ├── register.py
│       └── profile.py
└── models/
    ├── __init__.py
    └── user.py
```

### Admin Add-on (`app/add_ons/admin/`)
```
admin/
├── __init__.py
├── README.md
├── services/
│   ├── __init__.py
│   └── admin_service.py
├── routes/
│   ├── __init__.py
│   └── admin_routes.py
└── ui/
    ├── __init__.py
    └── pages/
        ├── __init__.py
        └── dashboard.py
```

### Commerce Add-on (`app/add_ons/commerce/`)
```
commerce/
├── __init__.py
├── README.md
├── services/
│   ├── __init__.py
│   ├── commerce_db.py (extends BaseDBService)
│   ├── payment_service.py
│   └── stripe_service.py
├── routes/
│   ├── __init__.py
│   └── commerce_routes.py
├── ui/
│   └── pages/
│       ├── __init__.py
│       ├── shop.py
│       └── checkout.py
└── models/
    ├── __init__.py
    ├── product.py
    └── order.py
```

### Media Add-on (`app/add_ons/media/`)
```
media/
├── __init__.py
├── README.md
├── services/
│   ├── __init__.py
│   └── media_storage.py (extends BaseStorageService)
├── routes/
│   ├── __init__.py
│   └── media_routes.py
└── workers/
    ├── __init__.py
    └── media_tasks.py
```

### LMS Add-on (Example) (`app/add_ons/lms/`)
```
lms/
├── __init__.py
├── README.md
├── services/
│   ├── __init__.py
│   ├── lms_db.py (extends BaseDBService)
│   ├── lms_email.py (extends BaseEmailService)
│   └── course_service.py
├── routes/
│   ├── __init__.py
│   └── lms_routes.py
├── ui/
│   └── pages/
│       ├── __init__.py
│       ├── courses.py
│       ├── course_detail.py
│       └── student_dashboard.py
└── models/
    ├── __init__.py
    ├── course.py
    ├── lesson.py
    └── enrollment.py
```

## Migration Steps

1. ✅ Create `app/core/services/base/` with abstract base classes
2. ⏳ Create `app/add_ons/` directory structure
3. ⏳ Move auth pages to `add_ons/auth/ui/pages/`
4. ⏳ Move admin pages to `add_ons/admin/ui/pages/`
5. ⏳ Move auth routes and OAuth service to `add_ons/auth/`
6. ⏳ Move media routes and workers to `add_ons/media/`
7. ⏳ Move Stripe service to `add_ons/commerce/services/`
8. ⏳ Clean up `core/ui/pages/` to keep only landing pages
9. ⏳ Update `core/routes/main.py` to only include landing routes
10. ⏳ Create LMS example add-on with full implementation
11. ⏳ Update `app/app.py` to mount add-ons dynamically
12. ⏳ Update documentation

## Benefits

1. **Clear Separation** - Core is truly minimal and focused
2. **Modularity** - Add-ons can be enabled/disabled independently
3. **Scalability** - Easy to add new add-ons without cluttering core
4. **Maintainability** - Each add-on is self-contained
5. **Reusability** - Add-ons can be shared across projects

## Next Actions

Should we proceed with the migration? I recommend:
1. Start with creating the LMS add-on as a complete example
2. Then migrate existing functionality to appropriate add-ons
3. Update app.py to dynamically mount add-ons
