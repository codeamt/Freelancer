# Pydantic Models Usage Guide

Complete guide for using Pydantic models with services.

## Overview

All major services now use Pydantic models for type-safe inputs and outputs:
- ✅ **AuthService** - Login, token refresh, verification
- ✅ **StorageService** - File upload, download, URL generation
- ✅ **HuggingFaceClient** - Text generation, classification, summarization

---

## Auth Service

### Login

**Before:**
```python
# ❌ Dict-based (old way)
result = await auth_service.login(
    email="user@example.com",
    password="SecurePass123!",
    create_session=True
)
# Returns: Dict or None
```

**After:**
```python
# ✅ Pydantic-based (new way)
from core.services.auth import LoginRequest, LoginResponse

request = LoginRequest(
    username="user@example.com",  # Can be email or username
    password="SecurePass123!",
    remember_me=True
)

response: LoginResponse = await auth_service.login(request)

# Type-safe access
print(response.access_token)
print(response.user.email)
print(response.expires_in)  # seconds
```

**Benefits:**
- ✅ IDE autocomplete for all fields
- ✅ Automatic validation (email format, password strength)
- ✅ Clear error messages if validation fails
- ✅ Type hints work correctly

### Token Refresh

**Before:**
```python
# ❌ Dict-based
result = await auth_service.refresh_token(old_token)
if result is None:
    # Why did it fail? 🤷
    handle_error()
```

**After:**
```python
# ✅ Pydantic-based
from core.services.auth import TokenRefreshRequest, TokenRefreshResponse

request = TokenRefreshRequest(refresh_token=old_token)

try:
    response: TokenRefreshResponse = await auth_service.refresh_token(request)
    print(response.access_token)
    print(response.expires_in)
except InvalidTokenError as e:
    # Clear error type
    print(f"Token refresh failed: {e.message}")
```

### Token Verification

**Before:**
```python
# ❌ Dict-based
payload = await auth_service.verify_token(token)
if payload:
    user_id = payload.get("user_id")  # Could be None
```

**After:**
```python
# ✅ Pydantic-based
from core.services.auth import TokenPayload

try:
    payload: TokenPayload = await auth_service.verify_token(token)
    print(payload.sub)  # user_id
    print(payload.email)
    print(payload.roles)  # List[UserRole]
except InvalidTokenError:
    # Token is invalid or expired
    handle_invalid_token()
```

---

## Storage Service

### File Upload

**Before:**
```python
# ❌ Many parameters
success = storage.upload_domain_file(
    domain="lms",
    level=StorageLevel.USER,
    filename="document.pdf",
    data=file_bytes,
    user_id="user123",
    content_type="application/pdf",
    metadata={"course_id": "101"}
)
if not success:
    # Upload failed, but why? 🤷
    handle_error()
```

**After:**
```python
# ✅ Pydantic-based
from core.integrations.storage import (
    FileUploadRequest,
    FileUploadResponse,
    StorageLevel
)

request = FileUploadRequest(
    domain="lms",
    level=StorageLevel.USER,
    filename="document.pdf",
    content_type="application/pdf",
    user_id="user123",
    metadata={"course_id": "101"},
    compress=True,
    encrypt=True
)

try:
    response: FileUploadResponse = await storage.upload_domain_file(
        request=request,
        data=file_bytes
    )
    
    print(f"Uploaded to: {response.key}")
    print(f"Size: {response.size} bytes")
    print(response.message)
except FileUploadError as e:
    print(f"Upload failed: {e.message}")
    print(f"Reason: {e.details.get('reason')}")
```

### Generate Upload URL

**Before:**
```python
# ❌ Dict return
result = storage.generate_upload_url(
    domain="lms",
    level=StorageLevel.USER,
    filename="video.mp4",
    content_type="video/mp4",
    user_id="user123",
    expires_in=3600
)
url = result["url"]
fields = result["fields"]
```

**After:**
```python
# ✅ Pydantic-based
from core.integrations.storage import UploadUrlRequest, UploadUrlResponse

request = UploadUrlRequest(
    domain="lms",
    level=StorageLevel.USER,
    filename="video.mp4",
    content_type="video/mp4",
    user_id="user123",
    expires_in=3600
)

response: UploadUrlResponse = storage.generate_upload_url(request)

# Type-safe access
print(response.url)
print(response.fields)  # Dict[str, str]
print(response.key)
print(f"Expires in {response.expires_in} seconds")
```

### Generate Download URL

**Before:**
```python
# ❌ String return
url = storage.generate_download_url(
    domain="lms",
    level=StorageLevel.USER,
    filename="document.pdf",
    user_id="user123",
    expires_in=3600
)
```

**After:**
```python
# ✅ Pydantic-based
from core.integrations.storage import DownloadUrlRequest, DownloadUrlResponse

request = DownloadUrlRequest(
    domain="lms",
    level=StorageLevel.USER,
    filename="document.pdf",
    user_id="user123",
    expires_in=3600
)

response: DownloadUrlResponse = storage.generate_download_url(request)

print(response.url)
print(f"Expires in {response.expires_in} seconds")
```

---

## HuggingFace AI Service

### Text Generation

**Before:**
```python
# ❌ Many parameters
text = await ai_client.generate_text(
    prompt="Write a story about a robot",
    model="gpt2",
    max_length=200,
    temperature=0.8,
    top_p=0.9,
    num_return_sequences=1
)
if text is None:
    # Generation failed 🤷
    handle_error()
```

**After:**
```python
# ✅ Pydantic-based
from core.integrations.huggingface import (
    TextGenerationRequest,
    TextGenerationResponse
)

request = TextGenerationRequest(
    prompt="Write a story about a robot",
    model="gpt2",
    max_length=200,
    temperature=0.8,
    top_p=0.9,
    num_return_sequences=1
)

try:
    response: TextGenerationResponse = await ai_client.generate_text(request)
    
    print(response.generated_text)  # str or List[str]
    print(f"Model: {response.model}")
    print(f"Prompt length: {response.prompt_length}")
    print(f"Generated length: {response.generated_length}")
except AIServiceError as e:
    print(f"Generation failed: {e.message}")
    print(f"Model: {e.details.get('model')}")
```

### Text Classification

**Before:**
```python
# ❌ Complex return type
results = await ai_client.classify_text(
    text="This product is amazing!",
    model="distilbert-base-uncased-finetuned-sst-2-english",
    labels=None
)
if results is None:
    handle_error()
else:
    for result in results[0]:
        print(f"{result['label']}: {result['score']}")
```

**After:**
```python
# ✅ Pydantic-based
from core.integrations.huggingface import (
    TextClassificationRequest,
    TextClassificationResponse
)

request = TextClassificationRequest(
    text="This product is amazing!",
    labels=["positive", "negative", "neutral"]  # Optional
)

try:
    response: TextClassificationResponse = await ai_client.classify_text(request)
    
    for result in response.results:
        print(f"{result.label}: {result.score:.2%}")
    
    print(f"Model: {response.model}")
except AIServiceError as e:
    print(f"Classification failed: {e.message}")
```

### Text Summarization

**Before:**
```python
# ❌ String return or None
summary = await ai_client.summarize_text(
    text=long_article,
    model="facebook/bart-large-cnn",
    max_length=130,
    min_length=30
)
if summary is None:
    handle_error()
```

**After:**
```python
# ✅ Pydantic-based
from core.integrations.huggingface import (
    SummarizationRequest,
    SummarizationResponse
)

request = SummarizationRequest(
    text=long_article,
    max_length=130,
    min_length=30
)

try:
    response: SummarizationResponse = await ai_client.summarize_text(request)
    
    print(response.summary)
    print(f"Original: {response.original_length} chars")
    print(f"Summary: {response.summary_length} chars")
    print(f"Compression: {response.summary_length / response.original_length:.1%}")
except AIServiceError as e:
    print(f"Summarization failed: {e.message}")
```

---

## Validation Examples

### Automatic Validation

```python
from core.services.auth import LoginRequest
from pydantic import ValidationError

# ✅ Valid request
request = LoginRequest(
    username="user@example.com",
    password="SecurePass123!"
)

# ❌ Invalid - will raise ValidationError
try:
    request = LoginRequest(
        username="invalid-email",  # Not a valid email
        password="weak"  # Too short, no uppercase/digit
    )
except ValidationError as e:
    print(e.errors())
    # [
    #   {'loc': ('password',), 'msg': 'Password must be at least 8 characters', ...},
    #   {'loc': ('password',), 'msg': 'Password must contain at least one uppercase letter', ...},
    #   ...
    # ]
```

### Field Constraints

```python
from core.integrations.storage import UploadUrlRequest

# ✅ Valid
request = UploadUrlRequest(
    domain="lms",
    level=StorageLevel.USER,
    filename="document.pdf",
    content_type="application/pdf",
    expires_in=3600  # 1 hour
)

# ❌ Invalid - expires_in out of range
try:
    request = UploadUrlRequest(
        domain="lms",
        level=StorageLevel.USER,
        filename="document.pdf",
        content_type="application/pdf",
        expires_in=100000  # > 86400 (24 hours)
    )
except ValidationError as e:
    print(e.errors())
    # [{'loc': ('expires_in',), 'msg': 'ensure this value is less than or equal to 86400', ...}]
```

---

## API Endpoint Examples

### FastAPI Integration

```python
from fastapi import APIRouter, Depends
from core.services.auth import AuthService, LoginRequest, LoginResponse

router = APIRouter()

@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,  # Automatic validation!
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login endpoint with automatic request validation.
    
    FastAPI will:
    - Validate request body against LoginRequest model
    - Return 422 if validation fails
    - Provide clear error messages
    """
    return await auth_service.login(request)
```

### Error Handling

```python
from fastapi import HTTPException
from core.exceptions import InvalidCredentialsError, InvalidTokenError

@router.post("/auth/login")
async def login(request: LoginRequest):
    try:
        response = await auth_service.login(request)
        return response
    except InvalidCredentialsError as e:
        # Middleware handles this automatically
        raise
    except Exception as e:
        # Unexpected error
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Migration Checklist

### For Service Consumers

- [ ] Import Pydantic models from service modules
- [ ] Replace Dict parameters with Pydantic request models
- [ ] Update return type hints to Pydantic response models
- [ ] Remove `Optional` from return types (use exceptions instead)
- [ ] Update error handling to catch specific exceptions
- [ ] Remove `if result is None` checks

### For Service Providers

- [ ] Create Pydantic models for all inputs/outputs
- [ ] Update method signatures to use models
- [ ] Replace `return None` with exceptions
- [ ] Add proper type hints
- [ ] Update docstrings with Raises section
- [ ] Export models from `__init__.py`

---

## Benefits Summary

### Before (Dict-based)
```python
# ❌ No type safety
result = await service.do_something(
    param1="value1",
    param2="value2",
    param3="value3"
)
if result is None:
    # Why did it fail? 🤷
    handle_error()
else:
    value = result.get("field")  # Could be None
```

### After (Pydantic-based)
```python
# ✅ Type safe
request = RequestModel(
    param1="value1",  # Validated automatically
    param2="value2",
    param3="value3"
)

try:
    response: ResponseModel = await service.do_something(request)
    value = response.field  # IDE autocomplete works!
except SpecificError as e:
    # Clear error type and message
    handle_error(e)
```

### Key Improvements

1. ✅ **Type Safety** - IDE knows all fields and types
2. ✅ **Validation** - Automatic input validation
3. ✅ **Clear Errors** - Specific exception types
4. ✅ **Documentation** - Self-documenting APIs
5. ✅ **Serialization** - Easy JSON conversion
6. ✅ **Testing** - Easier to mock and test

---

## Next Steps

1. **Update remaining services** - Apply Pydantic models to other services
2. **Update API routes** - Use models in FastAPI endpoints
3. **Update tests** - Use models in test fixtures
4. **Update documentation** - Document all available models
