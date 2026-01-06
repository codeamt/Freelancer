# Instagram Integration

## Overview

Provides Instagram Basic Display API and Graph API integration for media management, user data, and business features.

## Setup

### 1. Instagram App Configuration

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app or select existing one
3. Add "Instagram Basic Display" product
4. Configure OAuth redirect URI
5. Note your App ID and App Secret

### 2. Environment Variables

```bash
INSTAGRAM_CLIENT_ID=your_app_id
INSTAGRAM_CLIENT_SECRET=your_app_secret
INSTAGRAM_REDIRECT_URI=https://yourdomain.com/auth/instagram/callback
```

### 3. Usage

```python
from core.integrations.instagram import InstagramClient, InstagramConfig

# Initialize client
config = InstagramConfig(
    app_id=os.getenv("INSTAGRAM_CLIENT_ID"),
    app_secret=os.getenv("INSTAGRAM_CLIENT_SECRET"),
    redirect_uri=os.getenv("INSTAGRAM_REDIRECT_URI")
)

client = InstagramClient(config)

# Get authorization URL
auth_url = client.get_authorization_url()

# Exchange code for token
token_data = await client.exchange_code_for_token(code)

# Get user profile
profile = await client.get_user_profile()

# Get user media
media_items = await client.get_user_media()
```

## Features

- **Authentication**: OAuth flow with short-lived and long-lived tokens
- **User Profile**: Get user information and account type
- **Media Management**: Upload, retrieve, and manage media
- **Insights**: Analytics for business/creator accounts
- **Hashtag Search**: Search and get hashtag media
- **Comments**: Manage media comments

## API Limits

- **Rate Limit**: 200 requests per hour per user
- **Media Upload**: 25 posts per 24 hour period
- **Token Refresh**: Long-lived tokens expire in 60 days

## Required Permissions

- `user_profile` - Basic profile information
- `user_media` - Access to user's media
- `instagram_graph_basic` - Graph API access (business accounts)

## Health Check

```python
# Test API connection
is_healthy = await client.ping()
```

## Troubleshooting

### Common Issues

1. **Invalid Redirect URI**: Ensure redirect URI matches exactly in Facebook Developers
2. **Token Expired**: Use `refresh_long_lived_token()` to refresh tokens
3. **Insufficient Permissions**: Request required scopes during authorization
4. **Rate Limits**: Implement exponential backoff for failed requests

### Error Codes

- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Server Error (Instagram API issue)

## References

- [Instagram Basic Display API](https://developers.facebook.com/docs/instagram-basic-display-api)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)
- [OAuth Documentation](https://developers.facebook.com/docs/facebook-login/oauth)
