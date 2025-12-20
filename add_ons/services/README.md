# Base Service Classes

This directory contains abstract base classes (ABCs) for common services that can be implemented by specific add-ons or customized for client projects.

## Available Base Services

### 📧 `email_base.py` - Email Service
Abstract base class for email service implementations.

**Implementations can use:**
- AWS SES
- SendGrid
- Mailgun
- SMTP
- Custom solutions

**Methods:**
- `send_email()` - Send basic email
- `send_template_email()` - Send templated email
- `verify_email()` - Verify email address

---

### 📊 `analytics_base.py` - Analytics Service
Abstract base class for analytics and metrics tracking.

**Implementations can use:**
- Google Analytics (GA4)
- Mixpanel
- Segment
- DuckDB (included example)
- Custom solutions

**Methods:**
- `init_db()` - Initialize analytics storage
- `log_metric()` - Log a metric
- `summarize_metrics()` - Get metric summaries

---

### 🔐 `auth_base.py` - Authentication Service
Base authentication service patterns (moved from core).

**Note:** The working auth implementation is in `app/add_ons/auth/services/auth_service.py`

---

### 🔗 `oauth_base.py` - OAuth Service
OAuth provider integration base class.

**Implementations can use:**
- Google OAuth
- GitHub OAuth
- Facebook OAuth
- Custom OAuth providers

---

### 🔔 `notifications_base.py` - Notifications Service
Push notifications and in-app notifications.

**Implementations can use:**
- Firebase Cloud Messaging
- OneSignal
- Pusher
- Custom WebSocket solutions

---

### 🎯 `recommender_base.py` - Recommendation Engine
Content and product recommendation system.

**Implementations can use:**
- Collaborative filtering
- Content-based filtering
- Hybrid approaches
- ML-based recommendations

---

### 💳 `stripe_base.py` - Payment Processing
Payment gateway integration.

**Implementations can use:**
- Stripe
- PayPal
- Square
- Custom payment processors

---

### 📦 `storage_base.py` - File Storage
File upload and storage management.

**Implementations can use:**
- AWS S3
- Google Cloud Storage
- Azure Blob Storage
- Local filesystem
- CDN integration

---

### 🔄 `event_bus_base.py` - Event Bus
Event-driven architecture for decoupled services.

**Implementations can use:**
- Redis Pub/Sub
- RabbitMQ
- AWS SNS/SQS
- Custom event systems

---

## Usage

### For Client Projects

1. **Choose a base service** that matches your needs
2. **Create an implementation** in your add-on or project
3. **Extend the base class** and implement required methods
4. **Configure** with environment variables or config files

### Example: Implementing Email Service

```python
from add_ons.services.email_base import EmailServiceBase
import sendgrid
from sendgrid.helpers.mail import Mail

class SendGridEmailService(EmailServiceBase):
    def __init__(self, api_key: str):
        self.client = sendgrid.SendGridAPIClient(api_key)
    
    def send_email(self, to_email: str, subject: str, body: str, **kwargs) -> bool:
        message = Mail(
            from_email='noreply@yourapp.com',
            to_emails=to_email,
            subject=subject,
            html_content=body
        )
        try:
            response = self.client.send(message)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return False
    
    # Implement other abstract methods...
```

### Example: Using in Your Add-on

```python
from add_ons.services.email_base import EmailServiceBase
from your_implementation import SendGridEmailService

# Initialize your implementation
email_service: EmailServiceBase = SendGridEmailService(api_key=os.getenv('SENDGRID_API_KEY'))

# Use it
email_service.send_email(
    to_email="user@example.com",
    subject="Welcome!",
    body="<h1>Welcome to our platform</h1>"
)
```

## Benefits

✅ **Type Safety** - Abstract base classes ensure consistent interfaces
✅ **Flexibility** - Swap implementations without changing code
✅ **Testing** - Easy to mock for unit tests
✅ **Documentation** - Clear contracts for what methods are needed
✅ **Client Customization** - Clients can bring their own implementations

## Adding New Base Services

1. Create a new `*_base.py` file in this directory
2. Define an ABC with `@abstractmethod` decorators
3. Document the interface and example implementations
4. Update this README

---

**Note:** These are base classes only. Actual implementations should be created in specific add-ons or client projects based on requirements.
