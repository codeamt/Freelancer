# Storage/Media Refactor: From Add-on to Service

**Date:** December 2, 2025  
**Status:** ✅ Complete

---

## 🎯 Objective

Refactor storage/media from a standalone add-on with generic routes to a universal service that domains use to implement their own domain-specific media upload/download logic.

---

## 💡 Key Insight

**Problem:** Media add-on had generic upload/download routes, but each domain has different requirements (file types, sizes, permissions, metadata).

**Solution:** Storage should be a **service** (S3/MinIO operations) that domains use to implement their own media handling with domain-specific validation and business logic.

---

## 📊 Before vs After

### **Before (Media as Add-on):**
```
add_ons/media/                   ← Standalone add-on
├── media.py                     ← Generic upload/download routes
│   - /media/upload/process
│   - /media/upload/direct
│   - /media/download/{module}/{user_id}/{filename}
└── __init__.py

add_ons/services/
└── storage_base.py              ← Storage service (misnamed)

Problem:
- Generic routes don't fit domain needs
- No domain-specific validation
- Can't customize per use case
- Confusing naming (storage_base.py)
```

### **After (Storage as Service):**
```
add_ons/services/
└── storage.py                   ← Universal storage service
    - StorageService (S3/MinIO operations)
    - Encryption & compression
    - Presigned URLs
    - Metadata management

add_ons/domains/commerce/
└── media_example.py             ← Commerce-specific media
    - Product image upload
    - Secure data upload
    - Custom validation (types, sizes)
    - Business logic

add_ons/domains/lms/
└── media_example.py             ← LMS-specific media
    - Course material upload
    - Assignment submission
    - Course thumbnails
    - Enrollment validation

Benefits:
✅ Each domain defines its own media logic
✅ Storage service provides infrastructure
✅ Domain-specific validation
✅ Custom business rules
```

---

## 🔧 What Changed

### **1. Renamed Storage Service**
**Before:** `add_ons/services/storage_base.py`  
**After:** `add_ons/services/storage.py`

**Reason:** It's not a "base" class, it's the actual service.

**Provides:**
- `StorageService` class
  - `generate_upload_url()` - Presigned upload URLs
  - `generate_download_url()` - Presigned download URLs
  - `upload_secure_object()` - Encrypted + compressed upload
  - `download_secure_object()` - Decrypted + decompressed download
  - `delete_object()` - Delete files
  - `head_object()` - Get metadata
  - `cleanup_temp_files()` - Cleanup old temp files

**Features:**
- ✅ Supports AWS S3 and MinIO
- ✅ Encryption (Fernet)
- ✅ Compression (gzip)
- ✅ Presigned URLs (secure client uploads)
- ✅ Configurable via environment variables

**Usage:**
```python
from add_ons.services.storage import StorageService

storage = StorageService()

# Generate presigned upload URL
upload_info = storage.generate_upload_url(
    module="commerce",
    user_id=123,
    filename="product.jpg",
    content_type="image/jpeg"
)

# Upload with encryption
storage.upload_secure_object(
    module="lms",
    user_id=456,
    filename="assignment.pdf",
    data=file_content,
    content_type="application/pdf"
)
```

### **2. Removed Media Add-on**
```bash
❌ Deleted: add_ons/media/
   - media.py (generic routes)
   - __init__.py
```

### **3. Created Domain Examples**
```
✅ add_ons/domains/commerce/media_example.py
   - upload_product_image() - Product images
   - upload_secure_product_data() - Encrypted vendor data
   - download_product_image() - Download with auth
   - delete_product_image() - Delete with validation

✅ add_ons/domains/lms/media_example.py
   - upload_course_material() - Course PDFs/videos
   - upload_student_assignment() - Assignment submissions
   - upload_course_thumbnail() - Course images
   - download_course_material() - Download with enrollment check
```

### **4. Updated Services Export**
**File:** `add_ons/services/__init__.py`

**Added:**
```python
from .storage import StorageService

__all__ = [
    "StorageService",
]
```

---

## 🏗️ Architecture Pattern

### **Service Layer (Infrastructure):**
```
add_ons/services/storage.py
├── StorageService
│   ├── S3/MinIO client
│   ├── Encryption (Fernet)
│   ├── Compression (gzip)
│   ├── Presigned URLs
│   └── Metadata operations
```

### **Domain Layer (Business Logic):**
```
domains/commerce/media_example.py
├── Product images
│   ├── Validate: JPEG/PNG/WebP only
│   ├── Max size: 5MB
│   └── Store metadata in DB
│
└── Secure data
    ├── Admin only
    ├── Encrypted upload
    └── Vendor contracts, pricing

domains/lms/media_example.py
├── Course materials
│   ├── Instructor only
│   ├── PDF/Video/ZIP
│   └── Store in course DB
│
├── Assignments
│   ├── Student enrolled check
│   ├── Deadline validation
│   └── Encrypted submission
│
└── Thumbnails
    ├── Images only
    ├── Max 2MB
    └── Update course record
```

### **Benefits:**
1. **Separation of Concerns**
   - Service = S3/MinIO operations
   - Domain = Business validation & logic

2. **Customization**
   - Each domain controls file types
   - Custom size limits
   - Domain-specific permissions

3. **Security**
   - Domain validates auth
   - Service handles encryption
   - Presigned URLs (no server upload)

4. **Flexibility**
   - Different workflows per domain
   - Custom metadata storage
   - Domain-specific analytics

---

## 📝 Usage Examples

### **Commerce: Product Image Upload**
```python
from add_ons.services.storage import StorageService
from add_ons.services.auth import get_current_user

async def upload_product_image(request: Request, file: UploadFile):
    # Get current user
    user = await get_current_user(request)
    if not user:
        return {"error": "Not authenticated"}, 401
    
    # Validate file type (domain-specific)
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        return {"error": "Invalid file type"}, 400
    
    # Validate file size (domain-specific)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:  # 5MB
        return {"error": "File too large"}, 400
    
    # Use storage service
    storage = StorageService()
    upload_info = storage.generate_upload_url(
        module="commerce",
        user_id=int(user["_id"]),
        filename=f"products/{file.filename}",
        content_type=file.content_type
    )
    
    # Store metadata in domain database
    await db.insert_one("product_images", {
        "user_id": user["_id"],
        "filename": file.filename,
        "uploaded_at": datetime.utcnow()
    })
    
    return {"upload_info": upload_info}
```

### **LMS: Assignment Submission**
```python
async def upload_student_assignment(
    request: Request,
    course_id: str,
    assignment_id: str,
    file: UploadFile
):
    # Get current user
    user = await get_current_user(request)
    
    # Validate enrollment (domain-specific)
    enrollment = await db.find_one("enrollments", {
        "course_id": course_id,
        "user_id": user["_id"]
    })
    if not enrollment:
        return {"error": "Not enrolled"}, 403
    
    # Check deadline (domain-specific)
    assignment = await db.find_one("assignments", {"_id": assignment_id})
    if datetime.utcnow() > assignment["deadline"]:
        return {"error": "Deadline passed"}, 400
    
    # Upload with encryption (sensitive student data)
    storage = StorageService()
    file_content = await file.read()
    
    success = storage.upload_secure_object(
        module="lms",
        user_id=int(user["_id"]),
        filename=f"assignments/{course_id}/{assignment_id}/{file.filename}",
        data=file_content,
        content_type=file.content_type
    )
    
    # Store submission in domain database
    await db.insert_one("submissions", {
        "course_id": course_id,
        "assignment_id": assignment_id,
        "student_id": user["_id"],
        "submitted_at": datetime.utcnow()
    })
    
    return {"message": "Assignment submitted"}
```

---

## 🔒 Storage Service Features

### **1. Presigned URLs (Recommended)**
```python
# Generate upload URL
upload_info = storage.generate_upload_url(
    module="commerce",
    user_id=123,
    filename="product.jpg",
    content_type="image/jpeg",
    expires_in=3600  # 1 hour
)

# Client uploads directly to S3/MinIO
# No server bandwidth used
# Faster uploads
```

### **2. Encrypted Upload (Sensitive Data)**
```python
# Upload with encryption + compression
success = storage.upload_secure_object(
    module="lms",
    user_id=456,
    filename="assignment.pdf",
    data=file_content,
    content_type="application/pdf"
)

# File is encrypted with Fernet
# Compressed with gzip
# Metadata stored: {"encrypted": "true", "compressed": "true"}
```

### **3. Presigned Download URLs**
```python
# Generate download URL
download_url = storage.generate_download_url(
    module="commerce",
    user_id=123,
    filename="product.jpg",
    expires_in=3600  # 1 hour
)

# Time-limited access
# No server bandwidth
# Secure
```

### **4. Metadata & Cleanup**
```python
# Get file metadata
metadata = storage.head_object(
    module="commerce",
    user_id=123,
    filename="product.jpg"
)
# Returns: size, mime_type, last_modified, metadata

# Delete file
storage.delete_object(
    module="commerce",
    user_id=123,
    filename="product.jpg"
)

# Cleanup old temp files
storage.cleanup_temp_files(
    module="commerce",
    user_id=123,
    older_than_hours=24
)
```

---

## 🎯 Domain-Specific Logic

### **Commerce Domain:**
| Feature | Validation | Logic |
|---------|-----------|-------|
| Product Images | JPEG/PNG/WebP, 5MB max | Store in product DB |
| Secure Data | Admin only | Encrypted, vendor contracts |
| Downloads | User auth | Presigned URLs |

### **LMS Domain:**
| Feature | Validation | Logic |
|---------|-----------|-------|
| Course Materials | Instructor only, PDF/Video | Store in course DB |
| Assignments | Enrolled + deadline | Encrypted submission |
| Thumbnails | Images, 2MB max | Update course record |
| Downloads | Enrolled or instructor | Log access for analytics |

### **Social Domain (Future):**
| Feature | Validation | Logic |
|---------|-----------|-------|
| Profile Photos | Images, 1MB max | Public access |
| Post Media | Images/Videos | Privacy settings |
| Messages | Any file, 10MB max | Encrypted, private |

---

## 🔧 Configuration

### **Environment Variables:**
```bash
# S3/MinIO Configuration
APP_BUCKET=fastapp-dev-assets
S3_URL=http://localhost:9000  # or https://s3.amazonaws.com
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin

# Encryption Key (auto-generated if not set)
APP_MEDIA_KEY=your-fernet-key-here
```

### **Provider Detection:**
```python
# Automatically detects provider
provider = "aws" if "amazonaws.com" in endpoint else "minio"
```

---

## 📊 Comparison: Generic vs Domain-Specific

### **Generic Media Add-on (Before):**
```python
# One-size-fits-all route
@router.post("/media/upload/process")
async def process_upload(module: str, user_id: int, file: UploadFile):
    # No validation
    # No business logic
    # No domain context
    storage.upload(module, user_id, file)
```

**Problems:**
- ❌ No file type validation
- ❌ No size limits
- ❌ No permission checks
- ❌ No domain-specific metadata

### **Domain-Specific (After):**
```python
# Commerce-specific route
@app.post("/commerce/media/upload/product-image")
async def upload_product_image(request: Request, file: UploadFile):
    # Domain validation
    if file.content_type not in ["image/jpeg", "image/png"]:
        return {"error": "Invalid type"}
    
    # Domain business logic
    user = await get_current_user(request)
    if "seller" not in user["roles"]:
        return {"error": "Not authorized"}
    
    # Domain metadata
    await db.insert_one("product_images", {...})
    
    # Use storage service
    storage.generate_upload_url(...)
```

**Benefits:**
- ✅ File type validation
- ✅ Size limits
- ✅ Permission checks
- ✅ Domain-specific metadata
- ✅ Business logic

---

## ✅ Summary

### **What We Did:**
1. ✅ Renamed `storage_base.py` to `storage.py`
2. ✅ Removed generic media add-on
3. ✅ Created domain-specific media examples
4. ✅ Updated services exports
5. ✅ Established pattern for media handling

### **Benefits:**
- 🎨 **Custom Validation** - Each domain controls file types/sizes
- 🔧 **Universal Service** - Storage operations are reusable
- 📦 **Better Organization** - Clear service/domain separation
- 🚀 **Flexibility** - Domains implement their own logic

### **Architecture:**
```
Services (Infrastructure)  →  Domains (Business Logic)
   storage.py              →  commerce/media_example.py
   (S3/MinIO ops)          →  (Product images, validation)
```

### **Pattern:**
Same as Auth and GraphQL - infrastructure provides tools, domains implement business logic.

---

**Status:** ✅ Complete  
**Pattern:** ⭐ Consistent with Auth & GraphQL  
**Encryption:** 🔒 Fernet + gzip  
**Providers:** ☁️ AWS S3 & MinIO
