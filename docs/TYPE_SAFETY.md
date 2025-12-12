# Type Safety with Pydantic Models

This document describes the Pydantic models available for type-safe service interactions.

## Overview

Pydantic models provide:
- ✅ **Type validation** - Automatic validation of input data
- ✅ **IDE support** - Autocomplete and type hints
- ✅ **Documentation** - Self-documenting API contracts
- ✅ **Serialization** - Easy JSON conversion
- ✅ **Error messages** - Clear validation errors

---

## Auth Service Models

**Location:** `core/services/auth/models.py`

### User Models

```python
from core.services.auth import User, UserCreate, UserUpdate, UserRole

# Creating a new user
new_user = UserCreate(
    email="user@example.com",
    username="johndoe",
    password="SecurePass123!",
    roles=[UserRole.USER]
)

# Updating a user
update_data = UserUpdate(
    full_name="John Doe",
    roles=[UserRole.USER, UserRole.INSTRUCTOR]
)

# Type-safe user object
user: User = await auth_service.get_user(user_id)
print(user.email)  # IDE autocomplete works!
```

### Authentication Models

```python
from core.services.auth import LoginRequest, LoginResponse

# Login request
login_req = LoginRequest(
    username="johndoe",
    password="SecurePass123!",
    remember_me=True
)

# Login response (type-safe)
response: LoginResponse = await auth_service.login(login_req)
print(response.access_token)
print(response.user.email)
```

### Available Auth Models

- `User` - Complete user object (without password)
- `UserCreate` - Create new user (with password validation)
- `UserUpdate` - Update user information
- `LoginRequest` / `LoginResponse` - Authentication
- `TokenPayload` - JWT token data
- `TokenRefreshRequest` / `TokenRefreshResponse` - Token refresh
- `PasswordChangeRequest` - Password change
- `PasswordResetRequest` / `PasswordResetConfirm` - Password reset
- `PermissionCheck` / `PermissionCheckResponse` - Permission checks
- `RoleAssignment` - Role management
- `SessionInfo` - Session data
- `UserRole` (Enum) - User roles
- `UserStatus` (Enum) - Account status

---

## Storage Service Models

**Location:** `core/integrations/storage/models.py`

### File Upload

```python
from core.integrations.storage import (
    UploadUrlRequest,
    UploadUrlResponse,
    StorageLevel
)

# Request presigned upload URL
request = UploadUrlRequest(
    domain="lms",
    level=StorageLevel.USER,
    filename="course-material.pdf",
    content_type="application/pdf",
    user_id="user123",
    expires_in=3600
)

# Get upload URL (type-safe response)
response: UploadUrlResponse = storage.generate_upload_url(request)
print(response.url)
print(response.fields)
```

### File Metadata

```python
from core.integrations.storage import FileMetadata, FileListResponse

# List files (type-safe)
files: FileListResponse = await storage.list_files(
    domain="lms",
    level=StorageLevel.USER,
    user_id="user123"
)

for file in files.files:
    metadata: FileMetadata = file
    print(f"{metadata.filename}: {metadata.size} bytes")
```

### Available Storage Models

- `FileMetadata` - File information
- `UploadUrlRequest` / `UploadUrlResponse` - Upload URL generation
- `DownloadUrlRequest` / `DownloadUrlResponse` - Download URL generation
- `FileUploadRequest` / `FileUploadResponse` - Direct file upload
- `FileDownloadRequest` - File download
- `FileDeleteRequest` / `FileDeleteResponse` - File deletion
- `FileListRequest` / `FileListResponse` - File listing
- `StoragePath` - Storage path builder
- `StorageLevel` (Enum) - Storage isolation levels

---

## HuggingFace Service Models

**Location:** `core/integrations/huggingface/models.py`

### Text Generation

```python
from core.integrations.huggingface import (
    TextGenerationRequest,
    TextGenerationResponse
)

# Create request
request = TextGenerationRequest(
    prompt="Write a story about a robot",
    max_length=200,
    temperature=0.8,
    num_return_sequences=1
)

# Get response (type-safe)
response: TextGenerationResponse = await ai_client.generate_text(request)
print(response.generated_text)
```

### Text Classification

```python
from core.integrations.huggingface import (
    TextClassificationRequest,
    TextClassificationResponse,
    ClassificationResult
)

# Classify text
request = TextClassificationRequest(
    text="This product is amazing!",
    labels=["positive", "negative", "neutral"]
)

response: TextClassificationResponse = await ai_client.classify_text(request)
for result in response.results:
    print(f"{result.label}: {result.score:.2%}")
```

### Available HuggingFace Models

- `TextGenerationRequest` / `TextGenerationResponse` - Text generation
- `TextClassificationRequest` / `TextClassificationResponse` - Classification
- `SentimentAnalysisRequest` / `SentimentAnalysisResponse` - Sentiment
- `QuestionAnsweringRequest` / `QuestionAnsweringResponse` - Q&A
- `SummarizationRequest` / `SummarizationResponse` - Summarization
- `ImageGenerationRequest` / `ImageGenerationResponse` - Image generation
- `ImageClassificationRequest` / `ImageClassificationResponse` - Image classification
- `EmbeddingsRequest` / `EmbeddingsResponse` - Embeddings
- `TranslationRequest` / `TranslationResponse` - Translation
- `APIError` - Error responses
- `ModelType` (Enum) - Model types

---

## Benefits

### 1. Validation

```python
# Automatic validation
try:
    user = UserCreate(
        email="invalid-email",  # ❌ Will raise ValidationError
        username="ab",          # ❌ Too short (min 3 chars)
        password="weak"         # ❌ Doesn't meet requirements
    )
except ValidationError as e:
    print(e.errors())  # Clear error messages
```

### 2. Type Safety

```python
# IDE knows the types!
user: User = await get_user(user_id)
user.email  # ✅ Autocomplete works
user.invalid_field  # ❌ IDE error before runtime
```

### 3. Documentation

```python
# Models are self-documenting
print(UserCreate.schema_json(indent=2))
# Shows all fields, types, and validation rules
```

### 4. Serialization

```python
# Easy JSON conversion
user_dict = user.dict()
user_json = user.json()

# Parse from dict/JSON
user = User.parse_obj(user_dict)
user = User.parse_raw(user_json)
```

---

## Migration Guide

### Before (Dict-based)

```python
# ❌ No type safety
def create_user(data: Dict[str, Any]) -> Dict[str, Any]:
    # What fields does data have? 🤷
    # What does the return value contain? 🤷
    user = {
        "email": data["email"],  # Could be missing
        "username": data.get("username"),  # Could be None
        # ...
    }
    return user
```

### After (Pydantic-based)

```python
# ✅ Type safe
def create_user(data: UserCreate) -> User:
    # IDE knows exactly what fields exist
    # Validation happens automatically
    user = User(
        id=generate_id(),
        email=data.email,  # Guaranteed to be valid email
        username=data.username,  # Guaranteed to be 3-50 chars
        # ...
    )
    return user
```

---

## Best Practices

### 1. Use Models for Service Boundaries

```python
# ✅ Good - Type-safe service interface
async def register_user(self, user_data: UserCreate) -> User:
    # Validation already done by Pydantic
    ...

# ❌ Bad - Dict-based interface
async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
    # Manual validation needed
    ...
```

### 2. Validate Early

```python
# Validate at the API boundary
@router.post("/users")
async def create_user_endpoint(user_data: UserCreate):
    # user_data is already validated
    user = await user_service.create(user_data)
    return user
```

### 3. Use Enums for Constants

```python
# ✅ Good - Type-safe enum
user.roles = [UserRole.ADMIN, UserRole.INSTRUCTOR]

# ❌ Bad - String literals (typo-prone)
user.roles = ["admin", "instrctor"]  # Typo!
```

### 4. Leverage IDE Support

```python
# IDE autocomplete shows all available fields
user.  # <-- IDE shows: email, username, roles, etc.

# IDE shows type errors before runtime
user.email = 123  # ❌ IDE error: expected str, got int
```

---

## Next Steps

1. **Gradual Migration**: Start using Pydantic models in new code
2. **Update Existing Services**: Refactor high-value services to use models
3. **API Documentation**: Models auto-generate OpenAPI/Swagger docs
4. **Testing**: Models make mocking and testing easier

---

## Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI + Pydantic](https://fastapi.tiangolo.com/tutorial/body/)
- [Type Hints in Python](https://docs.python.org/3/library/typing.html)
