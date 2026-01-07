# FileManager Service

The FileManager service provides a unified interface for file operations across all add-ons/domains, integrating caching and storage capabilities.

## Features

- **Unified File Operations**: Single interface for upload, download, delete, and list operations
- **Hybrid Caching**: In-memory + S3 caching for improved performance
- **Domain Isolation**: Separate storage spaces for different domains (blog, commerce, lms, social, etc.)
- **User Isolation**: USER-level storage for per-user files and APP-level for shared files
- **Compression & Encryption**: Optional compression and encryption for file storage
- **Presigned URLs**: Generate URLs for direct client uploads/downloads
- **Cache Invalidation**: Automatic cache management on file operations

## Architecture

```
FileManager (High-level API)
    ↓
HybridCache (In-memory + S3)
    ↓
StorageService (S3/MinIO)
```

## Usage

### Basic Usage

```python
from core.services import FileManager, file_manager
from core.integrations.storage import StorageLevel

# Use global instance
fm = file_manager

# Upload file
result = await fm.upload_file(
    domain="blog",
    level=StorageLevel.APP,
    filename="posts/123/image.jpg",
    file_data=image_bytes,
    content_type="image/jpeg",
    cache_content=True
)

# Download file
file_data = await fm.download_file(
    domain="blog",
    level=StorageLevel.APP,
    filename="posts/123/image.jpg"
)
```

### Domain-Specific Managers

Create domain-specific managers for better organization:

```python
class BlogFileManager:
    def __init__(self, domain="blog"):
        self.domain = domain
        self.fm = file_manager
    
    async def upload_featured_image(self, post_id, image_data, filename):
        return await self.fm.upload_file(
            domain=self.domain,
            level=StorageLevel.APP,
            filename=f"posts/{post_id}/{filename}",
            file_data=image_data,
            content_type="image/jpeg"
        )
```

### Storage Levels

- **APP**: Shared across all users in the domain
  - Use for: Product images, blog posts, course materials
  - Path format: `{domain}/app/{filename}`

- **USER**: Isolated per user in the domain
  - Use for: Profile pictures, user documents, assignments
  - Path format: `{domain}/user/{user_id}/{filename}`

### Convenience Functions

```python
from core.services import upload_file_with_cache, download_file_with_cache

# Quick upload
result = await upload_file_with_cache(
    domain="commerce",
    level=StorageLevel.APP,
    filename="products/123/image.jpg",
    file_data=image_bytes,
    content_type="image/jpeg"
)

# Quick download
file_data = await download_file_with_cache(
    domain="commerce",
    level=StorageLevel.APP,
    filename="products/123/image.jpg"
)
```

## API Reference

### FileManager Methods

#### upload_file()
```python
async def upload_file(
    domain: str,
    level: StorageLevel,
    filename: str,
    file_data: Union[bytes, BinaryIO],
    content_type: str = "application/octet-stream",
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
    compress: bool = False,
    encrypt: bool = True,
    cache_content: bool = True
) -> Dict[str, Any]
```

#### download_file()
```python
async def download_file(
    domain: str,
    level: StorageLevel,
    filename: str,
    user_id: Optional[str] = None,
    use_cache: bool = True
) -> bytes
```

#### delete_file()
```python
async def delete_file(
    domain: str,
    level: StorageLevel,
    filename: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]
```

#### get_file_metadata()
```python
async def get_file_metadata(
    domain: str,
    level: StorageLevel,
    filename: str,
    user_id: Optional[str] = None,
    use_cache: bool = True
) -> Optional[Dict[str, Any]]
```

#### list_files()
```python
async def list_files(
    domain: str,
    level: StorageLevel,
    user_id: Optional[str] = None,
    prefix: str = "",
    max_keys: int = 1000,
    use_cache: bool = True
) -> Dict[str, Any]
```

#### generate_upload_url()
```python
def generate_upload_url(
    domain: str,
    level: StorageLevel,
    filename: str,
    content_type: str,
    user_id: Optional[str] = None,
    expires_in: int = 3600
) -> Dict[str, Any]
```

#### generate_download_url()
```python
def generate_download_url(
    domain: str,
    level: StorageLevel,
    filename: str,
    user_id: Optional[str] = None,
    expires_in: int = 3600
) -> Dict[str, Any]
```

## Environment Variables

Required for storage and cache:

```bash
# Storage (S3/MinIO)
APP_BUCKET=fastapp-dev-assets
S3_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_REGION=us-east-1

# Cache (S3)
S3_CACHE_BUCKET=fastapp-cache

# Encryption
STORAGE_ENCRYPTION_KEY=your-encryption-key
```

## Examples by Domain

### Blog Domain
- Featured images (APP level)
- Post attachments (APP level)
- Author avatars (USER level)

### Commerce Domain
- Product images (APP level)
- Category images (APP level)
- Customer documents (USER level)

### LMS Domain
- Course materials (USER level - instructor)
- Student assignments (USER level - student)
- Course thumbnails (APP level)

### Social Domain
- Profile pictures (USER level)
- Post media (USER level)
- Platform assets (APP level)

## Cache Management

The FileManager automatically manages cache:

- **File Content Cache**: Stores file content in memory + S3
- **Metadata Cache**: Stores file metadata for quick lookups
- **List Cache**: Stores file listings with shorter TTL

Cache invalidation happens automatically on:
- File uploads
- File deletions
- File modifications

## Performance Considerations

1. **Cache TTL**: Default 1 hour for files, 5 minutes for lists
2. **Large Files**: Consider disabling `cache_content` for large files
3. **Compression**: Enable for images and text files
4. **Encryption**: Enable for sensitive data

## Error Handling

The FileManager handles common errors:

- `FileNotFoundError`: File not found in storage
- `FileUploadError`: Upload failed
- `FileDownloadError`: Download failed
- `StorageError`: General storage issues

All methods return structured responses with success/error information.
