"""Authentication and Authorization Exceptions"""


class AuthenticationError(Exception):
    """Base authentication error"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password"""
    pass


class TokenExpiredError(AuthenticationError):
    """JWT token has expired"""
    pass


class InvalidTokenError(AuthenticationError):
    """JWT token is invalid"""
    pass


class AuthorizationError(Exception):
    """Base authorization error"""
    pass


class PermissionDeniedError(AuthorizationError):
    """User lacks required permission"""
    def __init__(self, permission: str, message: str = None):
        self.permission = permission
        self.message = message or f"Permission denied: {permission}"
        super().__init__(self.message)


class RoleRequiredError(AuthorizationError):
    """User lacks required role"""
    def __init__(self, role: str, message: str = None):
        self.role = role
        self.message = message or f"Role required: {role}"
        super().__init__(self.message)


class ResourceAccessDeniedError(AuthorizationError):
    """User cannot access specific resource"""
    def __init__(self, resource_type: str, resource_id: str = None, message: str = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.message = message or f"Access denied to {resource_type}" + (f" {resource_id}" if resource_id else "")
        super().__init__(self.message)
