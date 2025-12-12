# Error Handling Guide

Standardized error handling with custom exceptions across the application.

## Overview

The application uses a custom exception hierarchy for consistent error handling:
- ✅ **Type-safe exceptions** - Clear error types
- ✅ **Structured error data** - Status codes, details, context
- ✅ **Centralized handling** - Middleware catches all exceptions
- ✅ **Clear error messages** - User-friendly responses
- ✅ **Proper logging** - All errors logged with context

---

## Exception Hierarchy

**Location:** `core/exceptions.py`

```
AppException (base)
├── AuthenticationError (401)
│   ├── InvalidCredentialsError
│   ├── TokenExpiredError
│   ├── InvalidTokenError
│   ├── AccountInactiveError
│   └── EmailNotVerifiedError
├── AuthorizationError (403)
│   ├── InsufficientPermissionsError
│   └── InsufficientRoleError
├── ResourceError (404)
│   ├── NotFoundError
│   ├── AlreadyExistsError
│   └── ResourceConflictError (409)
├── ValidationError (422)
│   ├── InvalidInputError
│   └── MissingFieldError
├── StorageError (500)
│   ├── FileNotFoundError (404)
│   ├── FileUploadError
│   ├── FileDownloadError
│   ├── FileSizeLimitError (413)
│   └── InvalidFileTypeError (415)
├── ExternalServiceError (502)
│   ├── AIServiceError
│   ├── PaymentServiceError
│   └── EmailServiceError
├── DatabaseError (500)
│   ├── TransactionError
│   └── ConnectionError
├── BusinessLogicError (400)
│   ├── InsufficientFundsError
│   ├── QuotaExceededError (429)
│   └── InvalidStateError
└── ConfigurationError (500)
```

---

## Usage Examples

### Authentication

**Before (return None):**
```python
async def login(email: str, password: str) -> Optional[Dict]:
    user = await verify_password(email, password)
    if not user:
        return None  # ❌ Caller doesn't know why it failed
    return {"user": user, "token": token}
```

**After (exceptions):**
```python
from core.exceptions import InvalidCredentialsError

async def login(email: str, password: str) -> Dict:
    user = await verify_password(email, password)
    if not user:
        raise InvalidCredentialsError()  # ✅ Clear error type
    return {"user": user, "token": token}
```

### Storage

**Before:**
```python
def download_file(filename: str) -> Optional[bytes]:
    try:
        return s3.get_object(Key=filename)
    except Exception:
        return None  # ❌ Silent failure
```

**After:**
```python
from core.exceptions import FileNotFoundError, FileDownloadError

def download_file(filename: str) -> bytes:
    try:
        return s3.get_object(Key=filename)
    except s3.exceptions.NoSuchKey:
        raise FileNotFoundError(filename)  # ✅ Specific error
    except Exception as e:
        raise FileDownloadError(filename, reason=str(e))  # ✅ Context preserved
```

### AI Service

**Before:**
```python
async def generate_text(prompt: str) -> Optional[str]:
    try:
        response = await api.post(...)
        if response.status_code == 200:
            return response.json()["text"]
        return None  # ❌ Lost status code info
    except Exception:
        return None  # ❌ Lost error details
```

**After:**
```python
from core.exceptions import AIServiceError

async def generate_text(prompt: str) -> str:
    try:
        response = await api.post(...)
        if response.status_code == 200:
            return response.json()["text"]
        raise AIServiceError(
            f"Generation failed with status {response.status_code}",
            model="gpt2"
        )  # ✅ Preserved context
    except httpx.HTTPError as e:
        raise AIServiceError(f"HTTP error: {str(e)}")  # ✅ Clear error type
```

---

## Error Handler Middleware

**Location:** `core/middleware/error_handler.py`

The middleware automatically catches all exceptions and converts them to JSON responses:

```python
from core.middleware.error_handler import ErrorHandlerMiddleware

app.add_middleware(ErrorHandlerMiddleware)
```

### Response Format

All errors return consistent JSON:

```json
{
  "error": "InvalidCredentialsError",
  "message": "Invalid email or password",
  "status_code": 401,
  "details": {}
}
```

### Example Responses

**Authentication Error:**
```json
{
  "error": "InvalidCredentialsError",
  "message": "Invalid email or password",
  "status_code": 401,
  "details": {}
}
```

**Not Found Error:**
```json
{
  "error": "NotFoundError",
  "message": "User with id '123' not found",
  "status_code": 404,
  "details": {
    "resource_type": "User",
    "resource_id": "123"
  }
}
```

**Validation Error:**
```json
{
  "error": "InvalidInputError",
  "message": "Password must be at least 8 characters",
  "status_code": 422,
  "details": {
    "field": "password"
  }
}
```

**Storage Error:**
```json
{
  "error": "FileNotFoundError",
  "message": "File 'document.pdf' not found at path 'lms/user/123/document.pdf'",
  "status_code": 404,
  "details": {
    "filename": "document.pdf",
    "path": "lms/user/123/document.pdf"
  }
}
```

**AI Service Error:**
```json
{
  "error": "AIServiceError",
  "message": "Text generation failed with status 503",
  "status_code": 502,
  "details": {
    "service": "HuggingFace",
    "model": "gpt2"
  }
}
```

---

## Creating Custom Exceptions

### Basic Exception

```python
from core.exceptions import AppException

class CustomError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)
```

### Exception with Context

```python
from core.exceptions import AppException

class OrderCancelledError(AppException):
    def __init__(self, order_id: str, reason: str):
        super().__init__(
            f"Order {order_id} was cancelled: {reason}",
            status_code=409,
            details={"order_id": order_id, "reason": reason}
        )
```

---

## Best Practices

### 1. Use Specific Exceptions

```python
# ✅ Good - Specific exception
if not user:
    raise NotFoundError("User", user_id)

# ❌ Bad - Generic exception
if not user:
    raise Exception("User not found")
```

### 2. Preserve Context

```python
# ✅ Good - Includes details
raise FileUploadError(filename, reason="File too large")

# ❌ Bad - Lost context
raise FileUploadError(filename)
```

### 3. Don't Catch and Return None

```python
# ✅ Good - Let exception propagate
async def get_user(user_id: str) -> User:
    user = await repo.find(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return user

# ❌ Bad - Swallows error
async def get_user(user_id: str) -> Optional[User]:
    try:
        return await repo.find(user_id)
    except Exception:
        return None  # Caller doesn't know what went wrong
```

### 4. Re-raise Custom Exceptions

```python
# ✅ Good - Preserve custom exceptions
try:
    await service.process()
except AIServiceError:
    raise  # Let it propagate
except Exception as e:
    raise AIServiceError(str(e))

# ❌ Bad - Wraps custom exception
try:
    await service.process()
except Exception as e:
    raise AIServiceError(str(e))  # Wraps AIServiceError in AIServiceError
```

### 5. Add Helpful Details

```python
# ✅ Good - Actionable error message
raise InvalidInputError(
    "password",
    "Password must contain at least one uppercase letter, one lowercase letter, and one digit"
)

# ❌ Bad - Vague error
raise ValidationError("Invalid password")
```

---

## Migration Guide

### Step 1: Replace `return None`

**Before:**
```python
def find_user(user_id: str) -> Optional[User]:
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return None
    return user
```

**After:**
```python
from core.exceptions import NotFoundError

def find_user(user_id: str) -> User:
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise NotFoundError("User", user_id)
    return user
```

### Step 2: Update Type Hints

**Before:**
```python
async def login(email: str, password: str) -> Optional[Dict]:
    ...
```

**After:**
```python
async def login(email: str, password: str) -> Dict:
    """
    Raises:
        InvalidCredentialsError: If credentials are invalid
    """
    ...
```

### Step 3: Update Callers

**Before:**
```python
result = await auth_service.login(email, password)
if result is None:
    return {"error": "Login failed"}
return result
```

**After:**
```python
try:
    result = await auth_service.login(email, password)
    return result
except InvalidCredentialsError as e:
    # Middleware handles this automatically
    raise
```

---

## Testing with Exceptions

### Test Exception is Raised

```python
import pytest
from core.exceptions import NotFoundError

async def test_get_user_not_found():
    with pytest.raises(NotFoundError) as exc_info:
        await user_service.get_user("invalid-id")
    
    assert exc_info.value.status_code == 404
    assert "invalid-id" in str(exc_info.value)
```

### Test Exception Details

```python
async def test_file_upload_error_details():
    with pytest.raises(FileUploadError) as exc_info:
        await storage.upload_file("test.pdf", data)
    
    error = exc_info.value
    assert error.details["filename"] == "test.pdf"
    assert "reason" in error.details
```

---

## Logging

All exceptions are automatically logged by the middleware:

```python
# Logged automatically:
# WARNING: InvalidCredentialsError: Invalid email or password
#   path: /api/auth/login
#   method: POST
#   status_code: 401
```

For custom logging:

```python
from core.utils.logger import get_logger

logger = get_logger(__name__)

try:
    await risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", extra={"user_id": user_id})
    raise
```

---

## Summary

### Before (Inconsistent)
- ❌ Mix of `return None`, exceptions, and error dicts
- ❌ Lost error context
- ❌ No type safety
- ❌ Inconsistent error responses

### After (Standardized)
- ✅ Custom exception hierarchy
- ✅ Preserved error context
- ✅ Type-safe error handling
- ✅ Consistent JSON responses
- ✅ Automatic logging
- ✅ Clear error messages

---

## Changes Made

### Services Updated

1. **AuthService** (`core/services/auth/auth_service.py`)
   - `login()` - Raises `InvalidCredentialsError`
   - `refresh_token()` - Raises `InvalidTokenError`, `NotFoundError`
   - `verify_token()` - Raises `InvalidTokenError`

2. **StorageService** (`core/integrations/storage/s3_client.py`)
   - `download_domain_file()` - Raises `FileNotFoundError`, `FileDownloadError`
   - `get_object_metadata()` - Raises `FileNotFoundError`, `StorageError`
   - `delete_object()` - Raises `StorageError`

3. **HuggingFaceClient** (`core/integrations/huggingface/huggingface_client.py`)
   - `generate_text()` - Raises `AIServiceError`
   - `classify_text()` - Raises `AIServiceError`
   - `analyze_sentiment()` - Raises `AIServiceError`
   - `answer_question()` - Raises `AIServiceError`
   - `summarize_text()` - Raises `AIServiceError`
   - `generate_image()` - Raises `AIServiceError`

---

## Next Steps

1. **Update remaining services** - Apply exception pattern to other services
2. **Add exception tests** - Test exception handling in all services
3. **Update API documentation** - Document possible exceptions for each endpoint
4. **Client error handling** - Update frontend to handle structured errors
