# Environment Variables Template

Copy this to `.env` and fill in your values.

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fastapp

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=fastapp

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# AWS S3 (Optional - for media storage)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name

# Stripe (Optional - for commerce)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Application Settings
SECRET_KEY=your_secret_key_here
DEBUG=True
ENVIRONMENT=development

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@yourapp.com

# LMS Specific (Optional)
LMS_CERTIFICATE_TEMPLATE_URL=https://your-cdn.com/certificate-template.pdf
LMS_VIDEO_CDN_URL=https://your-cdn.com/videos/
LMS_MAX_UPLOAD_SIZE_MB=500
```

## Required for LMS

The LMS add-on requires:
- ✅ `DATABASE_URL` - PostgreSQL database
- ✅ `REDIS_URL` - For session management
- ⚠️ `MONGO_URI` - For analytics (optional)

## Optional for Enhanced LMS Features

- `AWS_*` - For video hosting and thumbnails
- `STRIPE_*` - For paid courses
- `SMTP_*` - For enrollment notifications
- `LMS_*` - For customization
