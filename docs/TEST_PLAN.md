# Test Plan - Pre-Production Checklist

This document outlines the unit and integration tests that should pass before implementing the Social and Streaming domains.

**Last Updated**: December 13, 2025

---

## Test Categories

### 1. Authentication Tests (Critical)
### 2. E-Shop Tests
### 3. LMS Tests
### 4. Admin Dashboard Tests
### 5. Database Tests
### 6. Security Tests

---

## 1. Authentication Tests

### Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| AUTH-U01 | `test_password_hashing` | Verify bcrypt hashing works correctly | Password hashes match on verification |
| AUTH-U02 | `test_jwt_token_creation` | Create JWT with user data | Valid token with correct payload |
| AUTH-U03 | `test_jwt_token_verification` | Verify valid JWT token | Returns user_id, email, role |
| AUTH-U04 | `test_jwt_token_expiration` | Verify expired token rejected | Raises InvalidTokenError |
| AUTH-U05 | `test_user_role_enum` | All roles in UserRole enum | 10 roles defined (including shop_owner, instructor) |

### Integration Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| AUTH-I01 | `test_user_registration` | Register new user via /auth/register | User created in DB, redirect to login |
| AUTH-I02 | `test_user_login` | Login with valid credentials | JWT cookie set, redirect to home |
| AUTH-I03 | `test_login_invalid_credentials` | Login with wrong password | Error message, no cookie set |
| AUTH-I04 | `test_admin_login` | Login via /admin/auth/login | JWT cookie set, redirect to /admin/dashboard |
| AUTH-I05 | `test_admin_login_non_admin` | Non-admin tries admin login | Error: "Admin access required" |
| AUTH-I06 | `test_logout` | User logout | Cookie cleared, redirect to home |
| AUTH-I07 | `test_get_current_user` | Extract user from auth_token cookie | Returns user dict with id, email, role |

---

## 2. E-Shop Tests

### Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| SHOP-U01 | `test_cart_add_item` | Add product to cart | Cart contains item with quantity |
| SHOP-U02 | `test_cart_remove_item` | Remove item from cart | Item removed, cart updated |
| SHOP-U03 | `test_cart_update_quantity` | Update item quantity | Quantity updated correctly |
| SHOP-U04 | `test_cart_total_calculation` | Calculate cart total | Correct sum of (price × quantity) |
| SHOP-U05 | `test_product_card_render` | Render ProductCard component | Valid HTML with product data |

### Integration Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| SHOP-I01 | `test_product_catalog_page` | GET /eshop-example/ | 200 OK, products displayed |
| SHOP-I02 | `test_product_detail_page` | GET /eshop-example/product/{id} | 200 OK, product details shown |
| SHOP-I03 | `test_add_to_cart` | POST /eshop-example/cart/add | Item added, cart count updated |
| SHOP-I04 | `test_view_cart` | GET /eshop-example/cart | 200 OK, cart items displayed |
| SHOP-I05 | `test_checkout_flow` | POST /eshop-example/checkout | Checkout page with Stripe notice |
| SHOP-I06 | `test_shop_admin_access` | GET /eshop-example/admin as shop_owner | 200 OK, dashboard displayed |
| SHOP-I07 | `test_shop_admin_denied` | GET /eshop-example/admin as user | Access denied message |

---

## 3. LMS Tests

### Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| LMS-U01 | `test_course_card_render` | Render CourseCard component | Valid HTML with course data |
| LMS-U02 | `test_lesson_item_render` | Render LessonItem component | Valid HTML with lesson data |
| LMS-U03 | `test_enrollment_check` | Check if user enrolled in course | Boolean result |
| LMS-U04 | `test_progress_calculation` | Calculate course progress | Percentage based on completed lessons |

### Integration Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| LMS-I01 | `test_course_catalog_page` | GET /lms-example/ | 200 OK, courses displayed |
| LMS-I02 | `test_course_detail_page` | GET /lms-example/course/{id} | 200 OK, course details shown |
| LMS-I03 | `test_course_enrollment` | POST /lms-example/enroll/{id} | Enrollment created, redirect to course |
| LMS-I04 | `test_lesson_view` | GET /lms-example/course/{id}/lesson/{id} | 200 OK, lesson content displayed |
| LMS-I05 | `test_instructor_dashboard` | GET /lms-example/instructor as instructor | 200 OK, dashboard displayed |
| LMS-I06 | `test_instructor_denied` | GET /lms-example/instructor as student | Access denied or redirect |
| LMS-I07 | `test_cart_add_paid_course` | POST /lms-example/cart/add | Course added to cart |

---

## 4. Admin Dashboard Tests

### Integration Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| ADMIN-I01 | `test_admin_login_page` | GET /admin/login | 200 OK, login form displayed |
| ADMIN-I02 | `test_admin_dashboard_authenticated` | GET /admin/dashboard with admin token | 200 OK, dashboard displayed |
| ADMIN-I03 | `test_admin_dashboard_unauthenticated` | GET /admin/dashboard without token | Redirect to /admin/login |
| ADMIN-I04 | `test_role_based_nav_admin` | Layout nav for admin user | Shows "Admin Dashboard" link |
| ADMIN-I05 | `test_role_based_nav_instructor` | Layout nav for instructor | Shows "Instructor Dashboard" link |
| ADMIN-I06 | `test_role_based_nav_shop_owner` | Layout nav for shop_owner | Shows "Shop Dashboard" link |

---

## 5. Database Tests

### Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| DB-U01 | `test_postgres_connection` | Connect to PostgreSQL | Connection established |
| DB-U02 | `test_user_repository_create` | Create user via repository | User inserted, ID returned |
| DB-U03 | `test_user_repository_get_by_email` | Find user by email | User object returned |
| DB-U04 | `test_user_repository_verify_password` | Verify password hash | Returns user on match, None on fail |

### Integration Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| DB-I01 | `test_schema_initialization` | Run init_schema.py | Tables created without errors |
| DB-I02 | `test_connection_pool` | Multiple concurrent queries | All queries complete successfully |

---

## 6. Security Tests

### Integration Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| SEC-I01 | `test_xss_prevention` | Submit script tag in form | Input sanitized, no script execution |
| SEC-I02 | `test_sql_injection_prevention` | Submit SQL in form field | Input sanitized, query safe |
| SEC-I03 | `test_rate_limiting` | Exceed rate limit | 429 Too Many Requests |
| SEC-I04 | `test_httponly_cookie` | Check auth_token cookie flags | httponly=True, secure in production |
| SEC-I05 | `test_password_requirements` | Register with weak password | Validation error returned |

---

## Test Implementation Guide

### Directory Structure
```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_auth.py         # AUTH-U* tests
│   ├── test_cart.py         # SHOP-U* tests
│   ├── test_lms.py          # LMS-U* tests
│   └── test_db.py           # DB-U* tests
├── integration/
│   ├── test_auth_routes.py  # AUTH-I* tests
│   ├── test_eshop.py        # SHOP-I* tests
│   ├── test_lms.py          # LMS-I* tests
│   ├── test_admin.py        # ADMIN-I* tests
│   └── test_security.py     # SEC-I* tests
└── fixtures/
    ├── users.json           # Test user data
    ├── products.json        # Test product data
    └── courses.json         # Test course data
```

### Fixtures (conftest.py)

```python
import pytest
from httpx import AsyncClient
from app.app import create_app

@pytest.fixture
async def app():
    """Create test application instance."""
    app = create_app(testing=True)
    yield app

@pytest.fixture
async def client(app):
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def admin_user(app):
    """Create admin user for testing."""
    return {
        "email": "admin@test.com",
        "password": "Admin123!",
        "role": "admin"
    }

@pytest.fixture
async def auth_token(client, admin_user):
    """Get auth token for admin user."""
    response = await client.post("/auth/login", data=admin_user)
    return response.cookies.get("auth_token")
```

### Running Tests

```bash
# Run all tests
cd app && uv run pytest tests/ -v

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

Before implementing Social and Streaming domains, the following must pass:

### Critical (Must Pass)
- [ ] All AUTH-* tests pass
- [ ] All DB-* tests pass
- [ ] All SEC-* tests pass

### Important (Should Pass)
- [ ] All SHOP-I01 through SHOP-I05 pass
- [ ] All LMS-I01 through LMS-I05 pass
- [ ] All ADMIN-* tests pass

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
