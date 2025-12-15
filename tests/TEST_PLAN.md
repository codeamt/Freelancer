# Test Plan - Pre-Production Checklist

This document outlines the unit and integration tests that should pass before shipping **core web admin workflows** and expanding/operationalizing **domain add-ons** (Blog, Stream, Social).

**Last Updated**: December 14, 2025

## Quickstart (Local Test Runs)

### 1) Start test dependencies (Docker)

From the repo root:

```bash
docker compose up -d
```

Notes:
- This starts all services defined in `docker-compose.yml` (Postgres, MongoDB, Redis, etc.).
- Integration tests currently require Postgres reachable at:
  - `postgresql://postgres:postgres@localhost:5432/app_db`
- Integration tests are skipped unless you set `RUN_INTEGRATION_TESTS=1`.

### 2) Run unit tests

```bash
uv run pytest -q tests/unit
```

### 3) Run integration tests

```bash
RUN_INTEGRATION_TESTS=1 uv run pytest -q tests/integration
```

---

## Test Categories

### 1. Authentication Tests (Critical)
### 2. E-Shop Tests
### 3. LMS Tests
### 4. Admin Dashboard Tests
### 5. Database Tests
### 6. Security Tests
### 7. State System + Draft/Publish Workflow Tests
### 8. Web Admin Site Editor + Theme Editor Tests
### 9. Blog Add-on Tests
### 10. Stream Add-on Tests
### 11. Add-on Loader + Add-on Switching Tests (Web Admin)

---

## Implemented Tests (Already in the Repo)

The following test coverage is already implemented.

### Unit (implemented)

- [x] **AUTH**: `tests/unit/test_auth.py`
- [x] **SHOP (cart)**: `tests/unit/test_cart.py`
- [x] **DB**: `tests/unit/test_db.py`
- [x] **STATE**: `tests/unit/test_state_system.py`
- [x] **Config validation**: `tests/unit/test_config_validation.py`
- [x] **Password validation**: `tests/unit/test_password_requirements.py`
- [x] **LMS UI/access smoke**: `tests/unit/test_lms_ui.py`, `tests/unit/test_lms_access.py`
- [x] **Shop UI smoke**: `tests/unit/test_shop_ui.py`

### Integration (implemented)

- [x] **AUTH routes**: `tests/integration/test_auth_routes.py`
- [x] **ADMIN basic**: `tests/integration/test_admin.py` (guarded by `RUN_INTEGRATION_TESTS=1`)
- [x] **E-Shop example**: `tests/integration/test_eshop.py` (guarded by `RUN_INTEGRATION_TESTS=1`)
- [x] **LMS example**: `tests/integration/test_lms.py` (guarded by `RUN_INTEGRATION_TESTS=1`)
- [x] **Security middleware**: `tests/integration/test_security.py`

---

## 7. State System + Draft/Publish Workflow Tests

These validate the state primitives that power site editing and draft/publish.

### Unit Tests

Existing coverage exists in:
- `tests/unit/test_state_system.py`

Add/keep the following tests:

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| STATE-U01 | `test_state_update_is_immutable_and_increments_sequence` | State immutability + sequence increments | New state updated, old state unchanged |
| STATE-U02 | `test_state_manager_history_and_rollback` | Rollback in StateManager | Correct previous state restored |
| STATE-U03 | `test_persister_in_memory_partition_key_and_sequence_match` | InMemoryPersister partitioning + sequence behavior | Load/save works; mismatch returns None |
| STATE-U04 | `test_component_config_visibility_rules_and_roundtrip` | Visibility rules and serialization | should_render matches rules |
| STATE-U05 | `test_component_library_templates_return_component_config` | Component templates return configs | Correct types and visibility |

### New Unit Tests (to add)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| WF-U01 | `test_site_workflow_load_draft_and_published` | Workflow loads draft/published partitions | Correct state per partition |
| WF-U02 | `test_preview_generation_from_draft` | Preview workflow builds preview from draft | Preview reflects draft |
| WF-U03 | `test_publish_promotes_draft_to_published` | Publishing transitions draft -> published | Published updated, draft retained |
| WF-U04 | `test_rollback_to_prior_published_version` | Rollback published version | Previous version becomes active |

---

## 8. Web Admin Site Editor + Theme Editor Tests

These cover `/admin/site/*` routes implemented in `app/core/routes/admin_sites.py`.

### Integration Tests (to add)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| SITE-I01 | `test_admin_site_components_requires_admin` | Non-admin access to `/admin/site/components` | Redirect/denied |
| SITE-I02 | `test_admin_site_components_loads_draft_state` | Admin loads components editor | 200 OK, section selector present |
| SITE-I03 | `test_add_preset_component_persists_to_draft` | Add preset component action | Component appears on reload |
| SITE-I04 | `test_toggle_component_persists_to_draft` | Toggle enabled state | Enabled flips |
| THEME-I01 | `test_theme_editor_loads_draft_theme` | `/admin/site/theme` initial load | 200 OK |
| THEME-I02 | `test_theme_update_colors_persists` | Post theme colors update | Draft theme updated |
| THEME-I03 | `test_theme_update_typography_persists` | Post typography update | Draft theme updated |
| THEME-I04 | `test_theme_update_custom_css_persists` | Post custom css update | Draft theme updated |

Notes:
- Current integration fixtures mount `router_auth` and example apps; you’ll need to mount `router_admin_sites` to run these.

---

## 9. Blog Add-on Tests

Blog is enabled by default for non-demo apps; it should have baseline service + route coverage.

### Unit Tests (to add)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| BLOG-U01 | `test_post_service_list_posts_demo` | Demo storage list | Returns list |
| BLOG-U02 | `test_post_service_create_post_increments_id` | Create post increments id | New post has new id |
| BLOG-U03 | `test_post_service_get_post_missing_returns_none` | Missing post | Returns None |

### Integration Tests (to add)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| BLOG-I01 | `test_blog_list_page` | `GET /blog` | 200 OK |
| BLOG-I02 | `test_blog_new_requires_auth` | `GET /blog/new` unauthenticated | Redirect to login |
| BLOG-I03 | `test_blog_create_post_requires_auth` | `POST /blog/posts` unauthenticated | Error/denied |
| BLOG-I04 | `test_blog_create_and_view_post` | Auth create then view detail | Redirect then 200 OK |

---

## 10. Stream Add-on Tests

Streaming has paywall/access control, attendance, and chat gating that need coverage.

### Unit Tests (to add)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| STREAM-U01 | `test_paywall_free_stream_allows_access` | Free stream access decision | Access granted |
| STREAM-U02 | `test_paywall_paid_stream_requires_member_or_ppv` | Paid stream access decision | Access denied unless member/ppv |
| STREAM-U03 | `test_attendance_upsert_uniqueness` | Attendance uniqueness | One attendance per user/stream |
| STREAM-U04 | `test_chat_gated_by_stream_access` | Chat allowed only with access | Forbidden when no access |
| STREAM-U05 | `test_stream_create_requires_streamer_or_admin` | Stream creation permissions | Denied for normal users |

### Integration Tests (to add)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| STREAM-I01 | `test_stream_list_page` | Stream list route | 200 OK |
| STREAM-I02 | `test_stream_watch_free_unauthenticated` | Free stream watch | 200 OK |
| STREAM-I03 | `test_stream_watch_paid_requires_access` | Paid stream watch without access | Paywall shown |
| STREAM-I04 | `test_stream_attend_and_list_my_upcoming` | Attend then list my upcoming | Attended event present |

---

## 11. Add-on Loader + Add-on Switching Tests (Web Admin)

These support upcoming “switches in dashboard” (enable/disable add-ons) and later submodule sync.

### Unit Tests (to add)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| ADDON-U01 | `test_addon_loader_load_manifest_success` | Load manifest module for known addon | Manifest loaded |
| ADDON-U02 | `test_addon_loader_handles_missing_manifest` | Missing domain manifest | Returns False |
| ADDON-U03 | `test_get_enabled_addons_dependency_resolution` | Dependency closure | Required deps included |

### Integration Tests (to add)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| ADDON-I01 | `test_admin_can_view_addon_switches` | Dashboard shows add-on panel | Toggle UI present |
| ADDON-I02 | `test_admin_toggle_addon_persists_config` | Toggle + reload | State persisted |
| ADDON-I03 | `test_non_admin_cannot_toggle_addons` | Permissions | Denied |
| ADDON-I04 | `test_disabled_addon_routes_unreachable` | Disable then request route | 404/redirect |

---

## Test Implementation Guide

### Directory Structure
```
tests/
├── conftest.py
├── unit/
│   ├── test_auth.py
│   ├── test_cart.py
│   ├── test_config_validation.py
│   ├── test_db.py
│   ├── test_lms_access.py
│   ├── test_lms_ui.py
│   ├── test_password_requirements.py
│   ├── test_shop_ui.py
│   └── test_state_system.py
└── integration/
    ├── conftest.py
    ├── test_admin.py
    ├── test_auth_routes.py
    ├── test_eshop.py
    ├── test_lms.py
    └── test_security.py
```

### Fixtures (conftest.py)

Notes:
- `tests/conftest.py` sets required environment variables for import-time config checks.
- Integration fixtures are defined in `tests/integration/conftest.py` and currently assemble an app that mounts:
  - `router_auth`
  - `/eshop-example` and `/lms-example`
  - security middleware needed for SEC tests

If you add integration tests for Blog/Stream/Admin Sites routes, extend the integration fixture to mount:
- `router_admin_sites`
- `router_blog` (or the app factory that mounts blog by default)
- stream routers (if mounted in that environment)

### Running Tests

```bash
# Run all tests
uv run pytest -q

# Run unit tests only
uv run pytest tests/unit/ -v

# Run integration tests only
uv run pytest tests/integration/ -v

# Run specific test file
uv run pytest tests/unit/test_auth.py -v

# Run with coverage
uv run pytest tests/ --cov=core --cov-report=html
```

---

## Acceptance Criteria

Before shipping Web Admin add-on management and expanding Blog/Stream to production usage, the following must pass:

### Critical (Must Pass)
- [x] Implemented AUTH/DB/SEC/STATE baseline tests exist in `tests/`.
- [ ] CI: run unit suite on every PR.
- [ ] CI: run integration suite when `RUN_INTEGRATION_TESTS=1` in pipeline.

### Important (Should Pass)
- [x] Implemented E-Shop/LMS/Admin integration tests exist (guarded by `RUN_INTEGRATION_TESTS=1`).
- [ ] BLOG-* tests (to add) pass.
- [ ] STREAM-* tests (to add) pass.
- [ ] SITE-*/THEME-* tests (to add) pass.
- [ ] ADDON-* tests (to add) pass.

### Nice to Have
- [ ] 80%+ code coverage on core/services/auth/
- [ ] 70%+ code coverage on core/db/

---

## Notes

1. **Test Database**: Use a separate test database or transactions that rollback
2. **Mocking**: Mock external services (Stripe, email) in tests
3. **Async**: All tests should be async-compatible using pytest-asyncio
4. **CI/CD**: Tests should run in GitHub Actions on every PR

---

## Dependencies

```toml
# Add to pyproject.toml [project.optional-dependencies]
test = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "httpx>=0.24",
]
```
