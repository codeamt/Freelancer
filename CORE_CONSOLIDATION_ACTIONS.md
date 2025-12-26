# Core Consolidation - Immediate Actions

## Quick Wins (Can be done safely)

### 1. Merge Security Utilities ✅
- Already created `core/utils/security_new.py` with consolidated functions
- **Next step**: Replace old files and update imports

### 2. Remove Redundant Encryption Service
- `core/services/encryption/` duplicates security utilities
- **Action**: Delete directory and update imports

### 3. Consolidate Static Files
- Merge `core/static/` and `core/ui/static/` into `core/assets/`
- **Action**: Move files and update references

## Medium Impact (Requires testing)

### 4. Flatten UI Structure
- Move components from `core/ui/components/` to `core/ui/`
- Add prefix to avoid conflicts
- **Risk**: May break component imports

### 5. Merge Utils Directories
- Consolidate `core/utils/` and `core/ui/utils/`
- **Risk**: Import conflicts

## High Impact (Major refactoring)

### 6. Reorganize Services
- Merge related services
- Remove domain-specific subdirectories
- **Risk**: High - affects entire application

## Recommended Approach

1. **Start with Quick Wins** (Phase 1)
   - Merge security utilities
   - Remove encryption service
   - Consolidate static files
   
2. **Test thoroughly** after each change
   
3. **Proceed with Medium Impact** (Phase 2)
   - Only if Phase 1 is successful
   
4. **Skip High Impact** for now
   - Current structure works
   - Risk outweighs benefit

## Files to Update After Consolidation

### Import Updates Needed:
```python
# Old imports to replace:
from core.ui.utils.security import sanitize_html
from core.services.encryption import encrypt_text

# New imports:
from core.utils.security import sanitize_html, encrypt_text
```

### Static File Paths:
```python
# Old paths:
/core/static/css/
/core/ui/static/js/

# New paths:
/core/assets/css/
/core/assets/js/
```

## Automated Script Usage

```bash
# Dry run to see changes
uv run python scripts/consolidate_core.py

# Execute Phase 1 (safe changes)
uv run python scripts/consolidate_core.py --phase 1 --execute

# Execute all phases (risky)
uv run python scripts/consolidate_core.py --execute
```

## Rollback Plan

Before making changes:
1. Commit current state
2. Create backup branch
3. Document all file changes

If issues arise:
1. Use git to revert
2. Check test suite
3. Fix any broken imports manually
