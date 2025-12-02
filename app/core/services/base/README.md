# Base Services - Abstract Base Classes

This directory contains abstract base classes (ABCs) for core services that add-ons can extend to implement custom functionality while maintaining a consistent interface.

## Available Base Services

### 1. BaseAuthService (`auth.py`)
Abstract base class for authentication and authorization services.

**Key Methods:**
- `get_user_roles()` - Get user roles
- `get_user_permissions()` - Get user permissions/scopes
- `has_permission()` - Check specific permission
- `has_role()` - Check specific role
- `authenticate_user()` - Authenticate with credentials
- `create_token()` - Create JWT token
- `verify_token()` - Verify JWT token

**Extension Points:**
- Custom role definitions
- Permission scopes specific to add-on
- Custom authentication logic

### 2. BaseDBService (`db.py`)
Abstract base class for database operations.

**Key Methods:**
- `insert_one()` - Insert document
- `find_one()` - Find single document
- `find_many()` - Find multiple documents
- `update_one()` - Update single document
- `update_many()` - Update multiple documents
- `delete_one()` - Delete single document
- `delete_many()` - Delete multiple documents
- `count()` - Count documents
- `aggregate()` - Run aggregation pipeline
- `get_collection_name()` - Get prefixed collection name

**Extension Points:**
- Collection/table naming (e.g., `lms_courses`)
- Domain-specific query helpers
- Custom indexes and schemas

### 3. BaseStorageService (`storage.py`)
Abstract base class for file storage operations.

**Key Methods:**
- `get_module_prefix()` - Get storage namespace
- `generate_upload_url()` - Generate presigned upload URL
- `generate_download_url()` - Generate presigned download URL
- `upload_file()` - Upload file from server
- `download_file()` - Download file to server
- `delete_file()` - Delete file
- `list_files()` - List user files
- `get_file_metadata()` - Get file metadata
- `validate_file_type()` - Validate file extension
- `validate_file_size()` - Validate file size

**Extension Points:**
- Module-specific paths (e.g., `lms/courses/`)
- Custom upload validation
- File processing pipelines
- Retention policies

### 4. BaseEmailService (`email.py`)
Abstract base class for email services.

**Key Methods:**
- `send_email()` - Send plain/HTML email
- `send_template_email()` - Send templated email
- `send_bulk_email()` - Send to multiple recipients
- `render_template()` - Render email template
- `validate_email()` - Validate email format
- `get_template_path()` - Get template file path
- `track_email_sent()` - Track sent emails (optional)
- `track_email_opened()` - Track opens (optional)
- `track_email_clicked()` - Track clicks (optional)

**Extension Points:**
- Custom email templates
- Template organization
- Provider selection (SMTP, SES, SendGrid, etc.)
- Email tracking and analytics

### 5. BaseNotificationService (`notification.py`)
Abstract base class for notification services.

**Key Methods:**
- `send_notification()` - Send notification to user
- `send_bulk_notification()` - Send to multiple users
- `get_user_notifications()` - Get user's notifications
- `mark_as_read()` - Mark notification as read
- `mark_all_as_read()` - Mark all as read
- `delete_notification()` - Delete notification
- `get_unread_count()` - Get unread count
- `get_user_preferences()` - Get notification preferences
- `update_user_preferences()` - Update preferences
- `format_notification()` - Format notification data

**Extension Points:**
- Custom notification types
- Delivery channels (in-app, email, SMS, push)
- User preference management
- Real-time delivery via WebSockets/SSE

## Usage in Add-ons

### Example: LMS Add-on

```python
from core.services.base import BaseDBService, BaseEmailService

class LMSDBService(BaseDBService):
    """LMS-specific database service"""
    
    def get_collection_name(self, entity: str) -> str:
        return f"lms_{entity}"
    
    async def get_course_by_id(self, course_id: str):
        """LMS-specific helper"""
        return await self.find_one("lms_courses", {"_id": course_id})

class LMSEmailService(BaseEmailService):
    """LMS-specific email service"""
    
    def get_template_path(self, template_name: str) -> str:
        return f"add_ons/lms/templates/email/{template_name}.html"
    
    def get_default_from_email(self) -> str:
        return "courses@fastapp.dev"
```

## Benefits

1. **Consistency** - All add-ons follow the same patterns
2. **Type Safety** - Abstract methods enforce implementation
3. **Extensibility** - Add-ons can customize while maintaining interface
4. **Testability** - Easy to mock base services for testing
5. **Documentation** - Clear contract for what methods are required

## Next Steps

1. Refactor existing core services to inherit from these bases
2. Create example implementations in add-ons (LMS, Commerce, Social)
3. Add integration tests for base service contracts
