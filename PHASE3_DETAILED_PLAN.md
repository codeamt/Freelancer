# Phase 3: Service Layer Cleanup - Detailed Plan

**Goal**: Flatten small service directories into single files while preserving large, well-organized services

**Status**: Planning - Ready for Review

---

## Current Service Structure Analysis

### ✅ Keep As-Is (Large, Well-Organized)
- **`auth/`** - 23 files, complex authentication system
  - JWT providers, OAuth adapters, device management
  - Role hierarchy, permissions, audit logging
  - **Decision**: Keep directory structure
  
- **`admin/`** - 5 files, cohesive admin functionality
  - admin_service.py, decorators.py, utils.py
  - **Decision**: Keep directory structure
  
- **`settings/`** - 5 files, settings management
  - **Decision**: Keep directory structure
  
- **`base/`** - 5 files, base service classes
  - email.py, notification.py, storage.py
  - **Decision**: Keep directory structure (foundation classes)

### ⚠️ Flatten to Single Files (2-3 files each)

#### 1. Cart Service (3 files)
**Current**:
```
core/services/cart/
├── __init__.py
├── cart_service.py
└── redis_cart_service.py
```

**Proposed**: `core/services/cart_service.py`
- Merge both cart implementations into single file
- Keep Redis-specific logic as a class

**Imports to Update**:
- `core/bootstrap.py`
- `core/routes/cart.py`
- `examples/eshop/app.py`

**Risk**: LOW - Only 3 files using it

---

#### 2. Editor Service (2 files)
**Current**:
```
core/services/editor/
├── __init__.py
└── omniview.py
```

**Proposed**: `core/services/editor_service.py`
- Rename omniview.py to editor_service.py
- Move to services root

**Imports to Update**:
- `core/routes/editor.py`

**Risk**: LOW - Only 1 file using it

---

#### 3. Order Service (2 files)
**Current**:
```
core/services/order/
├── __init__.py
└── order_service.py
```

**Proposed**: `core/services/order_service.py`
- Move order_service.py to services root

**Imports to Update**:
- `core/bootstrap.py`
- `add_ons/domains/lms/routes/checkout.py`

**Risk**: LOW - Only 2 files using it

---

#### 4. Payment Service (3 files)
**Current**:
```
core/services/payment/
├── __init__.py
├── payment_service.py
└── webhook_base.py
```

**Proposed**: `core/services/payment_service.py`
- Merge payment_service.py and webhook_base.py
- Keep webhook logic as separate class in same file

**Imports to Update**: Need to search

**Risk**: MEDIUM - May have webhook dependencies

---

#### 5. Product Service (2 files)
**Current**:
```
core/services/product/
├── __init__.py
└── product_service.py
```

**Proposed**: `core/services/product_service.py`
- Move product_service.py to services root

**Imports to Update**: Need to search

**Risk**: LOW - Simple move

---

#### 6. Search Service (2 files)
**Current**:
```
core/services/search/
├── __init__.py
└── search_service.py
```

**Proposed**: `core/services/search_service.py`
- Move search_service.py to services root

**Imports to Update**: Need to search

**Risk**: LOW - Simple move

---

## Execution Strategy

### Pre-Flight Checks
1. ✅ Identify all import locations for each service
2. ✅ Verify no circular dependencies
3. ✅ Check for any dynamic imports
4. ✅ Backup current state (git commit)

### Execution Order (Safest First)

#### Step 1: Simple Moves (Lowest Risk)
- **Editor Service** (2 files, 1 import)
- **Product Service** (2 files, minimal imports)
- **Search Service** (2 files, minimal imports)

#### Step 2: Simple Merges (Low Risk)
- **Order Service** (2 files, 2 imports)

#### Step 3: Complex Merges (Medium Risk)
- **Cart Service** (3 files, 3 imports, Redis logic)
- **Payment Service** (3 files, webhook dependencies)

### Per-Service Checklist

For each service to flatten:

1. **Pre-Merge**:
   - [ ] Read all files in directory
   - [ ] Identify all imports of this service
   - [ ] Check for any __init__.py exports
   - [ ] Document any special dependencies

2. **Merge**:
   - [ ] Create new single file in services root
   - [ ] Copy all classes/functions from subdirectory
   - [ ] Preserve all docstrings and comments
   - [ ] Maintain class structure (don't flatten classes)

3. **Update Imports**:
   - [ ] Update all identified import locations
   - [ ] Change from `from core.services.X import Y` to `from core.services.X_service import Y`
   - [ ] Verify no dynamic imports missed

4. **Cleanup**:
   - [ ] Remove old directory
   - [ ] Update `core/services/__init__.py` exports

5. **Verification**:
   - [ ] Run import checks
   - [ ] Test affected routes/functionality
   - [ ] Verify no import errors

---

## Import Pattern Changes

### Before (Directory Structure)
```python
from core.services.cart import CartService
from core.services.editor import OmniviewService
from core.services.order import OrderService
from core.services.payment import PaymentService
from core.services.product import ProductService
from core.services.search import SearchService
```

### After (Flat Structure)
```python
from core.services.cart_service import CartService, RedisCartService
from core.services.editor_service import OmniviewService
from core.services.order_service import OrderService
from core.services.payment_service import PaymentService, WebhookBase
from core.services.product_service import ProductService
from core.services.search_service import SearchService
```

---

## Rollback Plan

### If Issues Arise:
1. **Git Revert**: Each service flattening is a separate commit
2. **Import Mapping**: Document all import changes in commit message
3. **Test Coverage**: Run test suite after each service
4. **Incremental**: Can stop at any point and keep completed services

### Commit Strategy:
```bash
git commit -m "Phase 3.1: Flatten editor service (2 files → 1)"
git commit -m "Phase 3.2: Flatten product service (2 files → 1)"
git commit -m "Phase 3.3: Flatten search service (2 files → 1)"
git commit -m "Phase 3.4: Flatten order service (2 files → 1)"
git commit -m "Phase 3.5: Flatten cart service (3 files → 1)"
git commit -m "Phase 3.6: Flatten payment service (3 files → 1)"
```

---

## Testing Requirements

### After Each Service Flattening:
1. **Import Test**: Verify all imports resolve
2. **Route Test**: Test affected routes manually
3. **Integration Test**: Run relevant integration tests
4. **Bootstrap Test**: Ensure app starts without errors

### Full Test Suite:
- Run after completing all service flattenings
- Verify no regressions in existing functionality

---

## Benefits

### Code Organization:
- **Simpler structure**: Fewer directories to navigate
- **Easier discovery**: All services at same level
- **Consistent pattern**: Small services = single file, large services = directory

### Developer Experience:
- **Faster navigation**: Less clicking through directories
- **Clear imports**: Obvious where services live
- **Reduced cognitive load**: Flat is better than nested (for small modules)

### Maintenance:
- **Easier refactoring**: Single files easier to move/rename
- **Clear boundaries**: Each service file is self-contained
- **Better IDE support**: Single files index faster

---

## Risks & Mitigations

### Risk 1: Breaking Imports
**Mitigation**: 
- Comprehensive grep search before changes
- Update all imports in single commit per service
- Test immediately after each change

### Risk 2: Circular Dependencies
**Mitigation**:
- Check for circular imports before merging
- Keep service dependencies minimal
- Use dependency injection where needed

### Risk 3: Lost Context
**Mitigation**:
- Preserve all docstrings and comments
- Maintain git history (move, don't delete/recreate)
- Document any special considerations

### Risk 4: Dynamic Imports
**Mitigation**:
- Search for string-based imports
- Check for importlib usage
- Verify plugin/addon loading patterns

---

## Success Criteria

### Phase 3 Complete When:
- [ ] All 6 small services flattened to single files
- [ ] All imports updated and verified
- [ ] Old directories removed
- [ ] `core/services/__init__.py` updated
- [ ] All tests passing
- [ ] No import errors on startup
- [ ] Documentation updated

### Final Structure:
```
core/services/
├── __init__.py
├── admin/ (keep - 5 files)
├── auth/ (keep - 23 files)
├── base/ (keep - 5 files)
├── settings/ (keep - 5 files)
├── cart_service.py (new - merged from 3 files)
├── db_service.py (existing)
├── editor_service.py (new - merged from 2 files)
├── order_service.py (new - merged from 2 files)
├── payment_service.py (new - merged from 3 files)
├── product_service.py (new - merged from 2 files)
└── search_service.py (new - merged from 2 files)
```

---

## Timeline Estimate

- **Step 1** (Simple Moves): 30-45 minutes
- **Step 2** (Simple Merges): 15-20 minutes
- **Step 3** (Complex Merges): 45-60 minutes
- **Testing & Verification**: 30 minutes
- **Total**: 2-3 hours

---

## Decision Points

### Before Starting:
1. **Confirm flattening approach**: Single files vs keeping directories
2. **Review import locations**: Ensure we found all usages
3. **Test environment ready**: Can run tests after each change

### During Execution:
1. **Stop if circular dependencies found**: Redesign approach
2. **Stop if dynamic imports discovered**: Document and handle specially
3. **Pause for testing**: Don't proceed if tests fail

---

**Status**: Ready for execution pending user approval
**Next Step**: Execute Step 1 (Simple Moves) - Editor, Product, Search services
