import os
import sys
import asyncio
import pytest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-please-change-000000000000000000000000")
os.environ.setdefault("APP_MEDIA_KEY", "test-media-key-please-change-000000000000000000000000")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def unique_email():
    """Generate unique email for each test"""
    import uuid
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def sample_user():
    """Sample user object for testing"""
    from core.services.auth.models import UserRole
    
    class MockUser:
        def __init__(self):
            self.id = 1
            self.email = "test@example.com"
            self.role = UserRole.USER
            self.roles = [UserRole.USER]
            self.role_version = 1
            self.password_hash = "hashed_password"
            self.created_at = "2024-01-01T00:00:00Z"
            self.updated_at = "2024-01-01T00:00:00Z"
    
    return MockUser()


@pytest.fixture
def sample_admin_user():
    """Sample admin user object for testing"""
    from core.services.auth.models import UserRole
    
    class MockAdminUser:
        def __init__(self):
            self.id = 2
            self.email = "admin@example.com"
            self.role = UserRole.ADMIN
            self.roles = [UserRole.ADMIN, UserRole.INSTRUCTOR]
            self.role_version = 1
            self.password_hash = "hashed_password"
            self.created_at = "2024-01-01T00:00:00Z"
            self.updated_at = "2024-01-01T00:00:00Z"
    
    return MockAdminUser()


def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "role: mark test as role-based access test"
    )
    config.addinivalue_line(
        "markers", "oauth: mark test as OAuth related"
    )
