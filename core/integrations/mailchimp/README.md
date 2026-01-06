# Mailchimp Integration

## Overview

Provides Mailchimp API integration for email marketing campaigns, audience management, and automation.

## Setup

### 1. Mailchimp Account Configuration

1. Log in to [Mailchimp](https://mailchimp.com/)
2. Go to Account > Extras > API Keys
3. Generate a new API key
4. Note your server prefix (e.g., 'us1', 'us2')

### 2. Environment Variables

```bash
MAILCHIMP_API_KEY=your_api_key_here-us1
MAILCHIMP_SERVER_PREFIX=us1
```

### 3. Usage

```python
from core.integrations.mailchimp import MailchimpClient, MailchimpConfig, Contact

# Initialize client
config = MailchimpConfig(
    api_key=os.getenv("MAILCHIMP_API_KEY"),
    server_prefix=os.getenv("MAILCHIMP_SERVER_PREFIX")
)

client = MailchimpClient(config)

# Get audiences
audiences = await client.get_audiences()

# Add contact
contact = Contact(
    email_address="user@example.com",
    first_name="John",
    last_name="Doe"
)
await client.add_contact(audience_id, contact)

# Create campaign
campaign_data = {
    "type": "regular",
    "recipients": {"list_id": audience_id},
    "settings": {
        "subject_line": "Test Campaign",
        "from_name": "Your Company",
        "reply_to": "contact@yourcompany.com"
    }
}
campaign = await client.create_campaign(campaign_data)
```

## Features

- **Audience Management**: Create, retrieve, and manage email lists
- **Contact Management**: Add, update, and remove subscribers
- **Campaign Management**: Create and send email campaigns
- **Template Management**: Access email templates
- **Analytics**: Campaign reports and audience growth
- **Automation**: Manage automated email workflows

## API Limits

- **Rate Limit**: 10-50 requests per second (varies by plan)
- **Concurrent Connections**: 10 simultaneous connections
- **Batch Operations**: Up to 500 operations per batch

## Data Models

### Contact
```python
@dataclass
class Contact:
    email_address: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    tags: Optional[List[str]] = None
```

### Campaign
```python
@dataclass
class Campaign:
    id: str
    title: str
    subject_line: str
    preview_text: str
    status: str
    emails_sent: int
    send_time: Optional[str] = None
```

### Audience
```python
@dataclass
class Audience:
    id: str
    name: str
    member_count: int
    unsubscribe_count: int
    cleaned_count: int
```

## Health Check

```python
# Test API connection
is_healthy = await client.ping()
```

## Troubleshooting

### Common Issues

1. **Invalid API Key**: Ensure API key format is `key-string-server_prefix`
2. **Wrong Server Prefix**: Check your Mailchimp account URL for correct prefix
3. **Invalid List ID**: Use `get_audiences()` to get correct list IDs
4. **Contact Already Exists**: Use `update_contact()` instead of `add_contact()`

### Error Codes

- `400` - Bad Request (invalid data)
- `401` - Unauthorized (invalid API key)
- `404` - Not Found (invalid resource ID)
- `422` - Unprocessable Entity (validation errors)
- `429` - Too Many Requests (rate limit exceeded)

## Best Practices

1. **Batch Operations**: Use batch endpoints for multiple contacts
2. **Error Handling**: Implement retry logic for rate limits
3. **Data Validation**: Validate email addresses before adding
4. **Status Tracking**: Monitor campaign send status
5. **Clean Data**: Regularly clean bounced and unsubscribed addresses

## References

- [Mailchimp API Documentation](https://mailchimp.com/developer/marketing/api/)
- [API Reference](https://mailchimp.com/developer/marketing/api/reference/)
- [Rate Limits](https://mailchimp.com/developer/marketing/docs/fundamentals/#rate-limits)
