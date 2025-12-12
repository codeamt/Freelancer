# Base Services - Abstract Base Classes for Add-on Extensibility

This directory contains abstract base classes (ABCs) for services where **add-ons might provide custom implementations**.

## Philosophy: Hybrid Approach

**✅ Base classes are provided for:**
- Services where add-ons need custom implementations (storage, email, notifications)
- External integrations that vary by client (payment processors, analytics)

**❌ Base classes are NOT provided for:**
- Core platform services (auth, database) - these are not extensible
- Internal-only services that add-ons don't customize

## Available Base Services

### 1. BaseStorageService (`storage.py`)
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

### 2. BaseEmailService (`email.py`)
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

### 3. BaseNotificationService (`notification.py`)
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
from core.services.base import BaseStorageService, BaseEmailService

class LMSStorageService(BaseStorageService):
    """LMS-specific storage service"""
    
    def get_module_prefix(self) -> str:
        return "lms"
    
    def upload_file(self, user_id: int, filename: str, data: bytes, **kwargs) -> bool:
        """Upload with LMS-specific validation"""
        # Custom validation for course materials
        if not self.validate_file_type(filename, ['.pdf', '.mp4', '.zip']):
            raise ValueError("Invalid file type for course materials")
        return super().upload_file(user_id, filename, data, **kwargs)

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

## Implementation Status

**✅ Implemented:**
- `StorageService` in `core/integrations/storage/s3_client.py` implements `BaseStorageService`

**📝 To Do:**
- Create example email service implementations in add-ons
- Create example notification service implementations in add-ons
- Add integration tests for base service contracts

## Notes

- **Auth and DB services** do not have base classes as they are core platform services, not extensible by add-ons
- Add-ons should extend base classes when they need custom implementations
- Core implementations (like `StorageService`) serve as reference implementations
