# Codebase Consolidation Plan

## Current State
- **214 Python files** in core directory
- **40+ subdirectories** with varying levels of nesting
- Multiple duplicate utilities and redundant structures

## Identified Redundancies

### 1. Duplicate Security Utilities
- `/core/utils/security.py` - Encryption, password hashing, tokens
- `/core/ui/utils/security.py` - HTML sanitization, XSS prevention
- **Action**: Merge into single security module with clear separation

### 2. Multiple Static Directories
- `/core/static/` - General static files
- `/core/ui/static/` - UI-specific static files
- **Action**: Consolidate under single `/core/assets/`

### 3. Scattered UI Components
- `/core/ui/components/` - UI components
- `/core/ui/pages/` - Page components
- `/core/ui/helpers/` - UI helpers
- **Action**: Flatten to `/core/ui/` with clear naming

### 4. Redundant Utils
- `/core/utils/` - General utilities
- `/core/ui/utils/` - UI-specific utilities
- **Action**: Merge with namespacing

### 5. Overlapping Services
- `/core/services/auth/` - Authentication
- `/core/services/admin/` - Admin features
- `/core/services/encryption/` - Encryption (duplicates security utils)
- **Action**: Reorganize by domain

## Proposed Structure

```
core/
├── app.py                 # Main app entry
├── config/               # Configuration only
├── database/             # All DB-related
│   ├── adapters/
│   ├── migrations/
│   ├── models/
│   └── repositories/
├── services/             # Business logic
│   ├── auth.py
│   ├── user.py
│   ├── product.py
│   └── ...
├── api/                  # API routes
│   ├── auth/
│   ├── admin/
│   └── ...
├── ui/                   # UI layer
│   ├── components/
│   ├── pages/
│   └── utils.py
├── integrations/         # External services
│   ├── stripe.py
│   ├── email.py
│   └── ...
├── utils/                # General utilities
│   ├── security.py
│   ├── cache.py
│   ├── logger.py
│   └── ...
├── gdpr/                 # Compliance (keep as is)
├── middleware/           # Middleware
└── assets/               # Static files
    ├── css/
    ├── js/
    └── images/
```

## Migration Steps

### Phase 1: Consolidate Utils
1. Merge security utilities
2. Remove duplicate functions
3. Update all imports

### Phase 2: Restructure UI
1. Flatten UI directory
2. Merge static directories
3. Update component imports

### Phase 3: Reorganize Services
1. Merge related services
2. Remove encryption service (use utils)
3. Update service imports

### Phase 4: Clean Up
1. Remove empty directories
2. Update documentation
3. Fix any remaining imports

## Benefits
- Reduced file count by ~30%
- Simpler directory structure
- Easier navigation
- Reduced cognitive load
- Better maintainability

## Implementation Notes
- Use automated refactoring where possible
- Update imports systematically
- Test after each phase
- Keep git history clean
