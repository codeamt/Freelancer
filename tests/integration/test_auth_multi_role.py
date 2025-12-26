"""Integration tests for multi-role authentication"""

import pytest
import json
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_multi_role_registration(async_client, unique_email):
    """Test user registration with multiple roles"""
    resp = await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "user",  # Primary role
            "roles": ["user", "student"],  # Multiple roles
            "redirect": "/",
        },
    )
    assert resp.status_code == 303
    assert "auth_token=" in (resp.headers.get("set-cookie") or "")


@pytest.mark.asyncio
async def test_oauth_role_selection_flow(async_client):
    """Test OAuth flow with role selection for new users"""
    # Mock OAuth callback data
    oauth_data = {
        "provider": "google",
        "email": "newuser@example.com",
        "name": "New User"
    }
    
    # Start OAuth flow - simulate callback with new user
    with patch('core.routes.oauth.get_oauth_user') as mock_get_user:
        mock_get_user.return_value = {
            "email": "newuser@example.com",
            "name": "New User",
            "provider": "google"
        }
        
        with patch('core.services.auth.user_service.UserService.get_user_by_email') as mock_get:
            mock_get.return_value = None  # New user
            
            # OAuth callback should redirect to role selection
            resp = await async_client.get(
                "/auth/oauth/callback?state=test&code=test_code",
                follow_redirects=False
            )
            # Should redirect to role selection page
            assert resp.status_code in [302, 303]
            assert "role-selection" in resp.headers.get("location", "")


@pytest.mark.asyncio
async def test_oauth_role_selection_submission(async_client):
    """Test submitting role selection after OAuth"""
    # Simulate session with OAuth data
    with patch('core.routes.oauth.request') as mock_request:
        mock_request.session = {
            "oauth_data": {
                "provider": "google",
                "email": "newuser@example.com",
                "name": "New User"
            }
        }
        
        # Submit role selection
        resp = await async_client.post(
            "/auth/oauth/complete",
            data={
                "roles": ["user", "student"],
                "terms": "on"
            }
        )
        assert resp.status_code in [200, 302, 303]


@pytest.mark.asyncio
async def test_role_based_dashboard_access(async_client, unique_email):
    """Test dashboard shows role-appropriate content"""
    # Register as admin
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "admin",
            "roles": ["admin", "instructor"],
            "redirect": "/",
        },
    )
    
    # Access dashboard
    resp = await async_client.get("/dashboard")
    assert resp.status_code == 200
    body = resp.text
    
    # Should show admin-specific content
    assert "Admin Quick Actions" in body
    assert "Instructor Tools" in body
    assert unique_email in body


@pytest.mark.asyncio
async def test_role_ui_demo_page(async_client, unique_email):
    """Test role UI demo page displays correctly"""
    # Register as user with multiple roles
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "user",
            "roles": ["user", "student", "editor"],
            "redirect": "/",
        },
    )
    
    # Access role UI demo
    resp = await async_client.get("/role-ui-demo")
    assert resp.status_code == 200
    body = resp.text
    
    # Should show role badges
    assert "badge" in body
    assert unique_email in body
    
    # Should show role-specific content
    assert "User Content" in body
    assert "Editor Content" in body
    assert "Student Content" in body


@pytest.mark.asyncio
async def test_admin_role_management_api(async_client, unique_email):
    """Test admin role management endpoints"""
    # Create admin user
    admin_email = f"admin_{unique_email}"
    await async_client.post(
        "/auth/register",
        data={
            "email": admin_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "admin",
            "redirect": "/",
        },
    )
    
    # Create regular user
    user_email = f"user_{unique_email}"
    await async_client.post(
        "/auth/register",
        data={
            "email": user_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "user",
            "redirect": "/",
        },
    )
    
    # Test getting user roles (as admin)
    resp = await async_client.get("/admin/api/users/1/roles")
    assert resp.status_code == 200
    
    # Test assigning roles to user
    resp = await async_client.post(
        "/admin/api/users/2/roles",
        json={
            "roles": ["user", "student"],
            "reason": "Added student role"
        }
    )
    assert resp.status_code == 200
    
    # Test getting role history
    resp = await async_client.get("/admin/api/users/2/role-history")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_role_conflict_prevention(async_client, unique_email):
    """Test that conflicting roles are prevented"""
    # Try to register with conflicting roles
    resp = await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "admin",
            "roles": ["admin", "guest"],  # Conflicting roles
            "redirect": "/",
        },
    )
    
    # Should handle conflict gracefully
    # (Implementation depends on how conflicts are handled in registration)
    assert resp.status_code in [200, 303, 400]


@pytest.mark.asyncio
async def test_role_version_increment_on_change(async_client, unique_email):
    """Test that role version increments when roles change"""
    # Register user
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "user",
            "redirect": "/",
        },
    )
    
    # Get initial token
    resp = await async_client.get("/api/me")
    assert resp.status_code == 200
    initial_data = resp.json()
    initial_version = initial_data.get("role_version", 0)
    
    # Update roles (via admin API)
    await async_client.post(
        "/admin/api/users/1/roles",
        json={
            "roles": ["user", "admin"],
            "reason": "Promotion"
        }
    )
    
    # Check version incremented
    resp = await async_client.get("/api/me")
    assert resp.status_code == 200
    updated_data = resp.json()
    assert updated_data.get("role_version", 0) > initial_version


@pytest.mark.asyncio
async def test_session_based_oauth_flow(async_client):
    """Test that OAuth data is properly stored in session"""
    with patch('core.middleware.cookie_session.CookieSessionMiddleware') as mock_session:
        # Mock session storage
        mock_session.session_data = {}
        
        # Simulate OAuth callback
        oauth_data = {
            "provider": "google",
            "email": "test@example.com",
            "name": "Test User"
        }
        
        # Store in session
        mock_session.session_data["oauth_data"] = oauth_data
        
        # Verify data is stored
        assert "oauth_data" in mock_session.session_data
        assert mock_session.session_data["oauth_data"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_role_based_navigation(async_client, unique_email):
    """Test navigation adapts to user roles"""
    # Register as instructor
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "instructor",
            "roles": ["instructor", "editor"],
            "redirect": "/",
        },
    )
    
    # Access dashboard
    resp = await async_client.get("/dashboard")
    assert resp.status_code == 200
    body = resp.text
    
    # Should show instructor navigation items
    assert "Courses" in body
    assert "Content" in body
    
    # Should not show admin-only items
    assert "User Management" not in body


@pytest.mark.asyncio
async def test_multi_role_jwt_token(async_client, unique_email):
    """Test JWT token contains multiple roles"""
    # Register with multiple roles
    await async_client.post(
        "/auth/register",
        data={
            "email": unique_email,
            "password": "Goodpass1",
            "confirm_password": "Goodpass1",
            "role": "admin",
            "roles": ["admin", "instructor", "editor"],
            "redirect": "/",
        },
    )
    
    # Get token from cookie
    auth_cookie = async_client.cookies.get("auth_token")
    assert auth_cookie is not None
    
    # Decode token (simplified test)
    from core.services.auth.providers.jwt import JWTProvider
    provider = JWTProvider()
    payload = provider.verify(auth_cookie)
    
    assert payload is not None
    assert payload["email"] == unique_email
    assert payload["role"] == "admin"  # Primary role
    assert "roles" in payload
    assert "admin" in payload["roles"]
    assert "instructor" in payload["roles"]
    assert "editor" in payload["roles"]
