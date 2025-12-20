"""
Custom Exception Hierarchy

Standardized exceptions for consistent error handling across the application.
"""
from typing import Optional, Dict, Any


class AppException(Exception):
    """
    Base exception for all application errors.
    
    All custom exceptions should inherit from this.
    """
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details
        }


# =============================================================================
# Authentication & Authorization Exceptions
# =============================================================================

class AuthenticationError(AppException):
    """Base class for authentication errors"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired"""
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid or malformed"""
    def __init__(self, message: str = "Invalid or malformed token"):
        super().__init__(message)


class AuthorizationError(AppException):
    """Base class for authorization errors"""
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user lacks required permissions"""
    def __init__(self, required_permission: str, message: Optional[str] = None):
        msg = message or f"Insufficient permissions. Required: {required_permission}"
        super().__init__(msg, details={"required_permission": required_permission})


class InsufficientRoleError(AuthorizationError):
    """Raised when user lacks required role"""
    def __init__(self, required_role: str, message: Optional[str] = None):
        msg = message or f"Insufficient role. Required: {required_role}"
        super().__init__(msg, details={"required_role": required_role})


class AccountInactiveError(AuthenticationError):
    """Raised when user account is inactive or suspended"""
    def __init__(self, message: str = "Account is inactive or suspended"):
        super().__init__(message)


class EmailNotVerifiedError(AuthenticationError):
    """Raised when email verification is required"""
    def __init__(self, message: str = "Email verification required"):
        super().__init__(message)


# =============================================================================
# Resource Exceptions
# =============================================================================

class ResourceError(AppException):
    """Base class for resource-related errors"""
    def __init__(self, message: str, status_code: int = 404, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status_code, details=details)


class NotFoundError(ResourceError):
    """Raised when a requested resource is not found"""
    def __init__(self, resource_type: str, resource_id: Any, message: Optional[str] = None):
        msg = message or f"{resource_type} with id '{resource_id}' not found"
        super().__init__(
            msg,
            status_code=404,
            details={"resource_type": resource_type, "resource_id": str(resource_id)}
        )


class AlreadyExistsError(ResourceError):
    """Raised when attempting to create a resource that already exists"""
    def __init__(self, resource_type: str, identifier: str, message: Optional[str] = None):
        msg = message or f"{resource_type} with identifier '{identifier}' already exists"
        super().__init__(
            msg,
            status_code=409,
            details={"resource_type": resource_type, "identifier": identifier}
        )


class ResourceConflictError(ResourceError):
    """Raised when a resource operation conflicts with current state"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, details=details)


# =============================================================================
# Validation Exceptions
# =============================================================================

class ValidationError(AppException):
    """Base class for validation errors"""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(message, status_code=422, details=details)


class InvalidInputError(ValidationError):
    """Raised when input data is invalid"""
    def __init__(self, field: str, message: str, value: Any = None):
        details = {"field": field}
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, field=field, details=details)


class MissingFieldError(ValidationError):
    """Raised when a required field is missing"""
    def __init__(self, field: str, message: Optional[str] = None):
        msg = message or f"Required field '{field}' is missing"
        super().__init__(msg, field=field)


# =============================================================================
# Storage Exceptions
# =============================================================================

class StorageError(AppException):
    """Base class for storage-related errors"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status_code, details=details)


class FileNotFoundError(StorageError):
    """Raised when a file is not found in storage"""
    def __init__(self, filename: str, path: Optional[str] = None):
        message = f"File '{filename}' not found"
        if path:
            message += f" at path '{path}'"
        super().__init__(
            message,
            status_code=404,
            details={"filename": filename, "path": path}
        )


class FileUploadError(StorageError):
    """Raised when file upload fails"""
    def __init__(self, filename: str, reason: Optional[str] = None):
        message = f"Failed to upload file '{filename}'"
        if reason:
            message += f": {reason}"
        super().__init__(message, details={"filename": filename, "reason": reason})


class FileDownloadError(StorageError):
    """Raised when file download fails"""
    def __init__(self, filename: str, reason: Optional[str] = None):
        message = f"Failed to download file '{filename}'"
        if reason:
            message += f": {reason}"
        super().__init__(message, details={"filename": filename, "reason": reason})


class FileSizeLimitError(StorageError):
    """Raised when file exceeds size limit"""
    def __init__(self, filename: str, size: int, max_size: int):
        message = f"File '{filename}' exceeds size limit ({size} > {max_size} bytes)"
        super().__init__(
            message,
            status_code=413,
            details={"filename": filename, "size": size, "max_size": max_size}
        )


class InvalidFileTypeError(StorageError):
    """Raised when file type is not allowed"""
    def __init__(self, filename: str, file_type: str, allowed_types: list):
        message = f"File type '{file_type}' not allowed for '{filename}'. Allowed: {', '.join(allowed_types)}"
        super().__init__(
            message,
            status_code=415,
            details={"filename": filename, "file_type": file_type, "allowed_types": allowed_types}
        )


# =============================================================================
# External Service Exceptions
# =============================================================================

class ExternalServiceError(AppException):
    """Base class for external service errors"""
    def __init__(self, service_name: str, message: str, status_code: int = 502, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["service"] = service_name
        super().__init__(message, status_code=status_code, details=details)


class AIServiceError(ExternalServiceError):
    """Raised when AI service (HuggingFace) encounters an error"""
    def __init__(self, message: str, model: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if model:
            details["model"] = model
        super().__init__("HuggingFace", message, details=details)


class PaymentServiceError(ExternalServiceError):
    """Raised when payment service (Stripe) encounters an error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("Stripe", message, details=details)


class EmailServiceError(ExternalServiceError):
    """Raised when email service encounters an error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("Email", message, details=details)


# =============================================================================
# Database Exceptions
# =============================================================================

class DatabaseError(AppException):
    """Base class for database errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class TransactionError(DatabaseError):
    """Raised when database transaction fails"""
    def __init__(self, message: str = "Transaction failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details=details)


class ConnectionError(DatabaseError):
    """Raised when database connection fails"""
    def __init__(self, database: str, message: Optional[str] = None):
        msg = message or f"Failed to connect to {database} database"
        super().__init__(msg, details={"database": database})


# =============================================================================
# Business Logic Exceptions
# =============================================================================

class BusinessLogicError(AppException):
    """Base class for business logic errors"""
    def __init__(self, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status_code, details=details)


class InsufficientFundsError(BusinessLogicError):
    """Raised when user has insufficient funds"""
    def __init__(self, required: float, available: float):
        message = f"Insufficient funds. Required: ${required:.2f}, Available: ${available:.2f}"
        super().__init__(
            message,
            details={"required": required, "available": available}
        )


class QuotaExceededError(BusinessLogicError):
    """Raised when user exceeds quota or rate limit"""
    def __init__(self, resource: str, limit: int, current: int):
        message = f"Quota exceeded for {resource}. Limit: {limit}, Current: {current}"
        super().__init__(
            message,
            status_code=429,
            details={"resource": resource, "limit": limit, "current": current}
        )


class InvalidStateError(BusinessLogicError):
    """Raised when operation is invalid for current state"""
    def __init__(self, message: str, current_state: str, required_state: Optional[str] = None):
        details = {"current_state": current_state}
        if required_state:
            details["required_state"] = required_state
        super().__init__(message, details=details)


# =============================================================================
# Configuration Exceptions
# =============================================================================

class ConfigurationError(AppException):
    """Raised when application configuration is invalid"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)
