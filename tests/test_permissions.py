"""Permission System Tests - Test decorators and access control."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fasthtml.common import Request
from starlette.responses import JSONResponse

from core.services.auth.decorators import (
    require_permission, require_site_permission,
    require_platform_admin, require_site_admin
)
from core.services.auth.context import UserContext
from core.services.auth.site_scoping import SiteScopingService, SiteAssignment
from core.services.auth.permissions import permission_registry


class TestPlatformPermissionDecorator:
    """Test platform permission decorators."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        request.url.path = "/admin/users"
        request.headers = {"Accept": "application/json"}
        return request
    
    @pytest.fixture
    def platform_admin_context(self):
        """Create a platform admin user context."""
        return UserContext(
            user_id="admin1",
            role="platform_admin",
            roles=["platform_admin"],
            permissions=["platform.users.view", "platform.users.manage"],
            request_cookies={},
            ip_address="127.0.0.1",
            email="admin@example.com"
        )
    
    @pytest.fixture
    def regular_user_context(self):
        """Create a regular user context."""
        return UserContext(
            user_id="user1",
            role="user",
            roles=["user"],
            permissions=["profile.view"],
            request_cookies={},
            ip_address="127.0.0.1",
            email="user@example.com"
        )
    
    @patch('core.services.auth.decorators.current_user_context')
    async def test_platform_permission_granted(self, mock_context, mock_request, platform_admin_context):
        """Test that platform admin can access platform routes."""
        mock_context.get.return_value = platform_admin_context
        
        @require_permission("platform.users.view")
        async def protected_route(request):
            return {"success": True}
        
        result = await protected_route(mock_request)
        assert result["success"] is True
    
    @patch('core.services.auth.decorators.current_user_context')
    async def test_platform_permission_denied(self, mock_context, mock_request, regular_user_context):
        """Test that regular user cannot access platform routes."""
        mock_context.get.return_value = regular_user_context
        
        @require_permission("platform.users.view")
        async def protected_route(request):
            return {"success": True}
        
        result = await protected_route(mock_request)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 403
    
    @patch('core.services.auth.decorators.current_user_context')
    async def test_platform_admin_decorator(self, mock_context, mock_request, platform_admin_context):
        """Test platform admin decorator."""
        mock_context.get.return_value = platform_admin_context
        
        @require_platform_admin()
        async def protected_route(request):
            return {"success": True}
        
        result = await protected_route(mock_request)
        assert result["success"] is True


class TestSitePermissionDecorator:
    """Test site permission decorators."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request with site_id."""
        request = Mock(spec=Request)
        request.url.path = "/admin/site/components"
        request.headers = {"Accept": "application/json"}
        request.path_params = {"site_id": "main"}
        return request
    
    @pytest.fixture
    def site_admin_context(self):
        """Create a site admin user context."""
        return UserContext(
            user_id="site_admin1",
            role="site_admin",
            roles=["site_admin"],
            permissions=["site.theme.edit", "site.content.view"],
            request_cookies={},
            ip_address="127.0.0.1",
            email="siteadmin@example.com"
        )
    
    @pytest.fixture
    def site_owner_context(self):
        """Create a site owner user context."""
        return UserContext(
            user_id="owner1",
            role="site_owner",
            roles=["site_owner"],
            permissions=["site.theme.edit", "site.content.publish", "site.users.manage"],
            request_cookies={},
            ip_address="127.0.0.1",
            email="owner@example.com"
        )
    
    @patch('core.services.auth.decorators.current_user_context')
    @patch('core.services.auth.decorators.site_scoping_service')
    async def test_site_permission_granted(self, mock_scoping, mock_context, mock_request, site_admin_context):
        """Test that site admin can access site routes."""
        mock_context.get.return_value = site_admin_context
        mock_scoping.validate_site_access.return_value = True
        
        @require_site_permission("site.theme.edit")
        async def protected_route(request, site_id: str):
            return {"success": True, "site_id": site_id}
        
        result = await protected_route(mock_request, site_id="main")
        assert result["success"] is True
        assert result["site_id"] == "main"
    
    @patch('core.services.auth.decorators.current_user_context')
    @patch('core.services.auth.decorators.site_scoping_service')
    async def test_site_permission_denied_no_role(self, mock_scoping, mock_context, mock_request):
        """Test that user without site role cannot access site routes."""
        regular_context = UserContext(
            user_id="user1",
            role="user",
            roles=["user"],
            permissions=["profile.view"],
            request_cookies={},
            ip_address="127.0.0.1",
            email="user@example.com"
        )
        mock_context.get.return_value = regular_context
        mock_scoping.validate_site_access.return_value = False
        
        @require_site_permission("site.theme.edit")
        async def protected_route(request, site_id: str):
            return {"success": True}
        
        result = await protected_route(mock_request, site_id="main")
        assert isinstance(result, JSONResponse)
        assert result.status_code == 403
    
    @patch('core.services.auth.decorators.current_user_context')
    @patch('core.services.auth.decorators.site_scoping_service')
    async def test_site_permission_denied_no_assignment(self, mock_scoping, mock_context, mock_request, site_admin_context):
        """Test that site admin cannot access unassigned sites."""
        mock_context.get.return_value = site_admin_context
        mock_scoping.validate_site_access.return_value = False
        
        @require_site_permission("site.theme.edit")
        async def protected_route(request, site_id: str):
            return {"success": True}
        
        result = await protected_route(mock_request, site_id="other")
        assert isinstance(result, JSONResponse)
        assert result.status_code == 403


class TestSiteScopingService:
    """Test site scoping validation."""
    
    @pytest.fixture
    def scoping_service(self):
        """Create site scoping service."""
        return SiteScopingService()
    
    @pytest.fixture
    def platform_admin_context(self):
        """Create platform admin context."""
        return UserContext(
            user_id="admin1",
            role="platform_admin",
            roles=["platform_admin"],
            permissions=["platform.admin.access"],
            request_cookies={},
            ip_address="127.0.0.1",
            email="admin@example.com"
        )
    
    @pytest.fixture
    def site_admin_context(self):
        """Create site admin context."""
        return UserContext(
            user_id="site_admin1",
            role="site_admin",
            roles=["site_admin"],
            permissions=["site.theme.edit"],
            request_cookies={},
            ip_address="127.0.0.1",
            email="siteadmin@example.com"
        )
    
    @pytest.fixture
    def site_owner_context(self):
        """Create site owner context."""
        return UserContext(
            user_id="owner1",
            role="site_owner",
            roles=["site_owner"],
            permissions=["site.users.manage"],
            request_cookies={},
            ip_address="127.0.0.1",
            email="owner@example.com"
        )
    
    async def test_platform_admin_bypass(self, scoping_service, platform_admin_context):
        """Test that platform admins can access any site."""
        request = Mock()
        result = scoping_service.validate_site_access(
            request, platform_admin_context, "any_site", "site.theme.edit"
        )
        assert result is True
    
    async def test_site_admin_has_access(self, scoping_service, site_admin_context):
        """Test that site admin can access their site."""
        request = Mock()
        result = scoping_service.validate_site_access(
            request, site_admin_context, "main", "site.theme.edit"
        )
        assert result is True
    
    async def test_site_owner_has_access(self, scoping_service, site_owner_context):
        """Test that site owner can access their site."""
        request = Mock()
        result = scoping_service.validate_site_access(
            request, site_owner_context, "main", "site.users.manage"
        )
        assert result is True
    
    async def test_site_admin_cannot_manage_users(self, scoping_service, site_admin_context):
        """Test that site admin cannot manage users."""
        request = Mock()
        result = scoping_service.validate_site_access(
            request, site_admin_context, "main", "site.users.manage"
        )
        assert result is False
    
    async def test_regular_user_no_access(self, scoping_service):
        """Test that regular user has no site access."""
        regular_context = UserContext(
            user_id="user1",
            role="user",
            roles=["user"],
            permissions=["profile.view"],
            request_cookies={},
            ip_address="127.0.0.1",
            email="user@example.com"
        )
        request = Mock()
        result = scoping_service.validate_site_access(
            request, regular_context, "main", "site.theme.edit"
        )
        assert result is False


class TestPermissionRegistry:
    """Test permission registry and role resolution."""
    
    def test_permission_registry_initialization(self):
        """Test that permission registry is properly initialized."""
        assert permission_registry is not None
        assert len(permission_registry.roles) > 0
        assert len(permission_registry.permissions) > 0
    
    def test_role_permission_resolution(self):
        """Test that roles resolve to correct permissions."""
        # Test platform admin permissions
        platform_admin_permissions = permission_registry.resolve_permissions(["platform_admin"])
        assert len(platform_admin_permissions) >= 2
        # Check for platform wildcard permission
        platform_perms = [p for p in platform_admin_permissions if p.resource == "platform" and p.action == "*"]
        assert len(platform_perms) > 0
        
        # Test site admin permissions
        site_admin_permissions = permission_registry.resolve_permissions(["site_admin"])
        assert len(site_admin_permissions) >= 4
        # Check for specific site permissions
        theme_edit_perms = [p for p in site_admin_permissions if p.resource == "site.theme.edit"]
        assert len(theme_edit_perms) > 0
        
        # Test site owner permissions (should include site admin + more)
        site_owner_permissions = permission_registry.resolve_permissions(["site_owner"])
        assert len(site_owner_permissions) >= len(site_admin_permissions)
        # Check for site owner specific permissions
        site_manage_perms = [p for p in site_owner_permissions if p.resource == "site.users.manage"]
        assert len(site_manage_perms) > 0
    
    def test_multi_role_permission_resolution(self):
        """Test that multiple roles combine permissions."""
        multi_role_permissions = permission_registry.resolve_permissions(["site_admin", "platform_support"])
        # Check for site admin permissions
        site_perms = [p for p in multi_role_permissions if p.resource == "site.theme.edit"]
        assert len(site_perms) > 0
        # Check for platform support permissions  
        platform_perms = [p for p in multi_role_permissions if p.resource == "platform.users.view"]
        assert len(platform_perms) > 0


class TestAuditLogging:
    """Test audit logging functionality."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        request.url.path = "/admin/users"
        request.method = "GET"
        request.headers = {"Accept": "application/json", "user-agent": "test-agent"}
        request.client.host = "127.0.0.1"
        request.query_params = {}
        return request
    
    @patch('core.services.auth.audit_middleware.logger')
    async def test_audit_logging_success(self, mock_logger, mock_request):
        """Test that successful admin actions are logged."""
        from core.services.auth.audit_middleware import AdminAuditMiddleware
        
        middleware = AdminAuditMiddleware(None)
        
        # Verify the route is detected as admin route
        assert middleware._is_admin_route(mock_request) is True
        
        # Mock the call_next function
        response = Mock()
        response.status_code = 200
        response.headers = {"content-length": "100"}
        call_next = AsyncMock(return_value=response)
        
        # Set up user context
        with patch('core.services.auth.audit_middleware.current_user_context') as mock_context:
            user_context = UserContext(
                user_id="admin1",
                role="platform_admin",
                roles=["platform_admin"],
                permissions=["platform.users.view"],
                request_cookies={},
                ip_address="127.0.0.1",
                email="admin@example.com"
            )
            mock_context.get.return_value = user_context
            
            await middleware.dispatch(mock_request, call_next)
        
        # Verify call_next was called (middleware processed the request)
        call_next.assert_called_once_with(mock_request)
        
        # Verify some logging method was called (either info, warning, or error)
        assert mock_logger.info.called or mock_logger.warning.called or mock_logger.error.called
    
    @patch('core.services.auth.audit_middleware.logger')
    async def test_audit_logging_error(self, mock_logger, mock_request):
        """Test that failed admin actions are logged at warning level."""
        from core.services.auth.audit_middleware import AdminAuditMiddleware
        
        middleware = AdminAuditMiddleware(None)
        
        # Mock the call_next function with error response
        response = Mock()
        response.status_code = 403
        call_next = AsyncMock(return_value=response)
        
        # Set up user context
        with patch('core.services.auth.audit_middleware.current_user_context') as mock_context:
            user_context = UserContext(
                user_id="user1",
                role="user",
                roles=["user"],
                permissions=["profile.view"],
                request_cookies={},
                ip_address="127.0.0.1",
                email="user@example.com"
            )
            mock_context.get.return_value = user_context
            
            await middleware.dispatch(mock_request, call_next)
        
        # Verify warning logging was called
        mock_logger.warning.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])
