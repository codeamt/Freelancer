# Environment Variables Template

Copy this file to `.env` in your project root and configure the values for your deployment.

## Core Application Settings

```bash
# Application Configuration
APP_NAME=FastApp
APP_ENV=development  # Options: development, staging, production
DEBUG=true
HOST=0.0.0.0
PORT=5001
```

## Security Settings (REQUIRED for Production)

```bash
# JWT Configuration - CHANGE THIS IN PRODUCTION!
JWT_SECRET=your-super-secret-jwt-key-here-min-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440  # 24 hours

# Password Requirements
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=false
PASSWORD_REQUIRE_LOWERCASE=false
PASSWORD_REQUIRE_NUMBERS=false
PASSWORD_REQUIRE_SPECIAL=false

# CORS Settings
CORS_ORIGINS=http://localhost:5001,http://127.0.0.1:5001,https://yourdomain.com
CORS_ALLOW_CREDENTIALS=true
```

## Database Settings (Optional - for Production)

```bash
# MongoDB (Recommended)
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=fastapp
MONGO_MAX_POOL_SIZE=10

# PostgreSQL (Alternative)
# POSTGRES_URI=postgresql://user:password@localhost:5432/fastapp

# Redis (Optional - for caching/sessions)
# REDIS_URI=redis://localhost:6379/0
```

## Auth Add-on Settings

### Email Service Configuration

Choose ONE email provider:

```bash
# Email Provider Selection
EMAIL_PROVIDER=smtp  # Options: smtp, sendgrid, ses, mailgun
FROM_EMAIL=noreply@yourdomain.com

# Option 1: SMTP (Local or service like Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Option 2: SendGrid
# SENDGRID_API_KEY=SG.your-sendgrid-api-key

# Option 3: Mailgun
# MAILGUN_API_KEY=your-mailgun-api-key
# MAILGUN_DOMAIN=mg.yourdomain.com
```

### OAuth Providers (Optional)

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

## Commerce Add-on Settings

### Payment Processing

Choose ONE payment provider:

```bash
# Stripe (Recommended)
STRIPE_API_KEY=sk_test_your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# PayPal (Alternative)
# PAYPAL_CLIENT_ID=your-paypal-client-id
# PAYPAL_CLIENT_SECRET=your-paypal-client-secret
```

## Media Add-on Settings

### File Storage

```bash
# Storage Provider
STORAGE_PROVIDER=local  # Options: local, s3, gcs, azure

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1
```

## Analytics Add-on Settings

```bash
# Google Analytics
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX

# Mixpanel
MIXPANEL_TOKEN=your-mixpanel-project-token
```

## Feature Flags

```bash
# Authentication Features
ENABLE_REGISTRATION=true
ENABLE_OAUTH=false
ENABLE_EMAIL_VERIFICATION=false
ENABLE_2FA=false

# General Features
ENABLE_RATE_LIMITING=true
```

---

## Quick Start Configurations

### Development (Minimal)

```bash
APP_ENV=development
DEBUG=true
JWT_SECRET=dev-secret-key-change-in-production
```

### Production (Full)

```bash
APP_ENV=production
DEBUG=false
JWT_SECRET=your-production-secret-min-32-chars
MONGO_URI=mongodb://user:pass@your-mongo-host:27017
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.your-key
STRIPE_API_KEY=sk_live_your-key
CORS_ORIGINS=https://yourdomain.com
```

---

## Security Best Practices

### ⚠️ CRITICAL

1. **Never commit `.env` to version control** - It's in `.gitignore` for a reason
2. **Change JWT_SECRET in production** - Use a strong, random 32+ character string
3. **Use environment-specific secrets** - Different keys for dev/staging/prod
4. **Rotate secrets regularly** - Especially after team member changes

### 🔒 Recommended

1. **Use secret management** - AWS Secrets Manager, HashiCorp Vault, etc.
2. **Enable HTTPS** - Always use TLS in production
3. **Restrict CORS origins** - Only allow your actual domains
4. **Enable rate limiting** - Protect against abuse
5. **Monitor failed auth attempts** - Set up alerts

### 🛡️ Password Security

For production, enable stricter password requirements:

```bash
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=true
```

---

## Testing Configuration

### Unit Tests

```bash
APP_ENV=development
DEBUG=true
JWT_SECRET=test-secret-key
# No database needed - uses in-memory storage
```

### Integration Tests

```bash
APP_ENV=development
MONGO_URI=mongodb://localhost:27017/fastapp_test
JWT_SECRET=test-secret-key
```

---

## Troubleshooting

### "JWT secret must be changed in production"
- Set `JWT_SECRET` environment variable to a strong random string
- Generate one: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### "Email sending failed"
- Check `EMAIL_PROVIDER` is set correctly
- Verify credentials for your chosen provider
- For Gmail SMTP, use an "App Password", not your regular password

### "Database connection failed"
- Verify `MONGO_URI` or `POSTGRES_URI` is correct
- Check database server is running and accessible
- Ensure firewall allows connections

### "OAuth redirect mismatch"
- Add your callback URL to OAuth provider settings
- Format: `https://yourdomain.com/auth/google/callback`
- For development: `http://localhost:5001/auth/google/callback`

---

## Need Help?

- Check `app/settings.py` for all available settings
- See `app/config/addons.py` for add-on configuration
- Review `CLEANUP_SUMMARY.md` for architecture overview
