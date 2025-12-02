# Settings System Guide

## Overview

FastApp uses a secure, type-safe settings system built on **Pydantic Settings** that:

✅ Loads configuration from environment variables and `.env` files  
✅ Validates all settings with type checking  
✅ Masks secrets in logs and error messages  
✅ Integrates with the add-on system  
✅ Provides production safety checks  

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      .env File                               │
│  (Environment Variables - Not in version control)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  app/settings.py                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Settings Class (Pydantic BaseSettings)             │    │
│  │  - Loads & validates environment variables          │    │
│  │  - Provides type-safe access                        │    │
│  │  - Masks secrets (SecretStr)                        │    │
│  │  - Validates production requirements                │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              app/config/addons.py                            │
│  - Defines which add-ons are enabled                         │
│  - Resolves add-on dependencies                              │
│  - Specifies mount points                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 Add-ons & Application                        │
│  - Get add-on-specific configuration                         │
│  - Validate requirements before loading                      │
│  - Use settings throughout the app                           │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Basic Usage

```python
from settings import settings, get_settings

# Access settings
if settings.is_production():
    print("Running in production mode")

# Get database URI
db_uri = settings.get_database_uri()

# Check if email is configured
if settings.has_email_configured():
    # Send email
    pass
```

### Add-on Specific Configuration

```python
from settings import get_addon_settings

# Get auth add-on configuration
auth_config = get_addon_settings("auth")
jwt_secret = auth_config["jwt_secret"]
enable_oauth = auth_config["enable_oauth"]

# Get commerce add-on configuration
commerce_config = get_addon_settings("commerce")
stripe_key = commerce_config["stripe_api_key"]
```

### Validate Add-on Requirements

```python
from settings import settings

# Check if add-on can be loaded
is_valid, error_msg = settings.validate_addon_requirements("commerce")
if not is_valid:
    print(f"Cannot load commerce add-on: {error_msg}")
```

### Production Validation

```python
from settings import validate_production_config

# Get list of warnings/errors
warnings = validate_production_config()
for warning in warnings:
    print(warning)
```

## Security Features

### 1. Secret Masking

Secrets are stored as `SecretStr` and masked in logs:

```python
# In settings.py
jwt_secret: SecretStr = Field(default=SecretStr("..."))

# Access the actual value
actual_secret = settings.jwt_secret.get_secret_value()

# Logging/printing shows: SecretStr('**********')
print(settings.jwt_secret)  # SecretStr('**********')
```

### 2. Production Validation

Settings are validated when loading in production:

```python
@validator("jwt_secret")
def validate_jwt_secret_in_production(cls, v, values):
    if values.get("app_env") == "production":
        if v.get_secret_value() == "change-this-secret-key-in-production":
            raise ValueError("JWT secret must be changed in production!")
    return v
```

### 3. Environment-Specific Defaults

```python
# Development: Debug enabled, relaxed security
if settings.is_development():
    # Allow all origins, verbose logging, etc.
    pass

# Production: Strict security
if settings.is_production():
    # Enforce HTTPS, strict CORS, etc.
    pass
```

## Configuration Sections

### Core Settings

```python
app_name: str                    # Application name
app_env: str                     # Environment (development/staging/production)
debug: bool                      # Debug mode
host: str                        # Server host
port: int                        # Server port
```

### Security Settings

```python
jwt_secret: SecretStr            # JWT signing key
jwt_algorithm: str               # JWT algorithm (HS256)
jwt_expiration_minutes: int      # Token expiration
password_min_length: int         # Minimum password length
cors_origins: List[str]          # Allowed CORS origins
```

### Database Settings

```python
mongo_uri: Optional[str]         # MongoDB connection string
mongo_db_name: str               # Database name
postgres_uri: Optional[str]      # PostgreSQL connection string
redis_uri: Optional[str]         # Redis connection string
```

### Add-on Settings

#### Auth Add-on
```python
email_provider: Optional[str]    # Email service (smtp/sendgrid/mailgun)
smtp_host: Optional[str]         # SMTP server
sendgrid_api_key: Optional[SecretStr]  # SendGrid key
google_client_id: Optional[str]  # Google OAuth
github_client_id: Optional[str]  # GitHub OAuth
```

#### Commerce Add-on
```python
stripe_api_key: Optional[SecretStr]     # Stripe secret key
stripe_webhook_secret: Optional[SecretStr]  # Webhook secret
paypal_client_id: Optional[str]         # PayPal client ID
```

#### Media Add-on
```python
storage_provider: Optional[str]          # Storage (local/s3/gcs)
aws_access_key_id: Optional[str]         # AWS credentials
aws_s3_bucket: Optional[str]             # S3 bucket name
```

#### Analytics Add-on
```python
google_analytics_id: Optional[str]       # GA tracking ID
mixpanel_token: Optional[SecretStr]      # Mixpanel token
```

### Feature Flags

```python
enable_registration: bool        # Allow new registrations
enable_oauth: bool               # Enable OAuth login
enable_email_verification: bool  # Require email verification
enable_2fa: bool                 # Two-factor authentication
enable_rate_limiting: bool       # Rate limiting
```

## Helper Methods

### Environment Checks

```python
settings.is_production()         # True if APP_ENV=production
settings.is_development()        # True if APP_ENV=development
```

### Service Configuration Checks

```python
settings.has_email_configured()           # Email service ready?
settings.has_oauth_configured("google")   # Google OAuth ready?
settings.has_payment_configured("stripe") # Stripe ready?
```

### Database

```python
settings.get_database_uri()      # Get primary DB URI
```

### Add-on Configuration

```python
settings.get_addon_config("auth")           # Get auth settings
settings.validate_addon_requirements("commerce")  # Validate requirements
```

## Best Practices

### 1. Never Hardcode Secrets

❌ **Bad:**
```python
JWT_SECRET = "my-secret-key"
```

✅ **Good:**
```python
from settings import settings
jwt_secret = settings.jwt_secret.get_secret_value()
```

### 2. Use Type-Safe Access

❌ **Bad:**
```python
import os
port = int(os.getenv("PORT", "5001"))
```

✅ **Good:**
```python
from settings import settings
port = settings.port  # Already validated as int
```

### 3. Check Configuration Before Use

❌ **Bad:**
```python
# Assume email is configured
send_email(...)  # May fail
```

✅ **Good:**
```python
if settings.has_email_configured():
    send_email(...)
else:
    logger.warning("Email not configured")
```

### 4. Validate Add-on Requirements

❌ **Bad:**
```python
# Load add-on without checking
load_commerce_addon()  # May fail if Stripe not configured
```

✅ **Good:**
```python
is_valid, error = settings.validate_addon_requirements("commerce")
if is_valid:
    load_commerce_addon()
else:
    logger.error(f"Cannot load commerce: {error}")
```

### 5. Environment-Specific Behavior

```python
if settings.is_production():
    # Strict security, HTTPS only, etc.
    enforce_https()
    strict_cors()
else:
    # Development conveniences
    allow_all_origins()
    verbose_logging()
```

## Integration with Add-ons

### In Add-on Code

```python
# app/add_ons/auth/services/auth_service.py
from settings import get_addon_settings

class AuthService:
    def __init__(self):
        config = get_addon_settings("auth")
        self.jwt_secret = config["jwt_secret"]
        self.jwt_algorithm = config["jwt_algorithm"]
        self.enable_oauth = config["enable_oauth"]
```

### In Add-on Loader

```python
# app/core/addon_loader.py
from settings import settings
from config.addons import get_enabled_addons

def load_addons(app):
    enabled_addons = get_enabled_addons()
    
    for addon_name in enabled_addons:
        # Validate requirements
        is_valid, error = settings.validate_addon_requirements(addon_name)
        if not is_valid:
            logger.error(f"Skipping {addon_name}: {error}")
            continue
        
        # Load add-on
        load_addon(app, addon_name)
```

## Testing

### Unit Tests

```python
from settings import Settings

def test_settings():
    # Override settings for testing
    test_settings = Settings(
        app_env="development",
        jwt_secret="test-secret",
        debug=True
    )
    
    assert test_settings.is_development()
    assert test_settings.debug
```

### Integration Tests

```python
import os
os.environ["APP_ENV"] = "development"
os.environ["JWT_SECRET"] = "test-secret"

from settings import settings

def test_with_env():
    assert settings.app_env == "development"
```

## Troubleshooting

### "JWT secret must be changed in production"

**Cause:** Using default JWT secret in production  
**Fix:** Set `JWT_SECRET` environment variable

```bash
export JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### "Validation error for Settings"

**Cause:** Invalid environment variable type or value  
**Fix:** Check `.env` file for typos, ensure types match (e.g., `PORT=5001` not `PORT=abc`)

### "Cannot load add-on: requires X configuration"

**Cause:** Add-on enabled but required settings missing  
**Fix:** Either configure the required settings or disable the add-on in `config/addons.py`

## Reference

- **Settings File:** `app/settings.py`
- **Add-on Config:** `app/config/addons.py`
- **Environment Template:** `ENV_TEMPLATE.md`
- **Pydantic Settings Docs:** https://docs.pydantic.dev/latest/concepts/pydantic_settings/

---

**Pro Tip:** Use `validate_production_config()` in your deployment scripts to catch configuration issues before they reach production!
