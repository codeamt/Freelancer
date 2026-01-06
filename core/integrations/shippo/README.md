# Shippo Integration

## Overview

Provides Shippo API integration for shipping, tracking, and logistics management.

## Setup

### 1. Shippo Account Configuration

1. Sign up at [Shippo](https://goshippo.com/)
2. Get your API token from Account > Settings > API
3. Choose between Test and Live modes

### 2. Environment Variables

```bash
SHIPPO_API_KEY=your_shippo_api_token
SHIPPO_TEST_MODE=true  # Set to false for production
```

### 3. Usage

```python
from core.integrations.shippo import ShippoClient, ShippoConfig, Address, Parcel

# Initialize client
config = ShippoConfig(
    api_key=os.getenv("SHIPPO_API_KEY"),
    test_mode=os.getenv("SHIPPO_TEST_MODE", "true").lower() == "true"
)

client = ShippoClient(config)

# Create addresses
from_address = Address(
    name="Sender",
    street1="123 Main St",
    city="San Francisco",
    state="CA",
    zip="94105",
    country="US"
)

to_address = Address(
    name="Recipient",
    street1="456 Oak Ave",
    city="New York",
    state="NY", 
    zip="10001",
    country="US"
)

# Create parcel
parcel = Parcel(
    length=10.0,
    width=8.0,
    height=4.0,
    distance_unit="in",
    weight=16.0,
    mass_unit="oz"
)

# Get shipping rates
rates = await client.get_shipping_rates(from_address, to_address, parcel)

# Purchase label
label = await client.purchase_shipping_label(rate_object_id)

# Track shipment
tracking_info = await client.track_shipment(tracking_number)
```

## Features

- **Address Validation**: Validate and standardize addresses
- **Rate Comparison**: Get rates from multiple carriers
- **Label Generation**: Create and print shipping labels
- **Tracking**: Real-time shipment tracking
- **Manifests**: Generate end-of-day manifests
- **Refunds**: Request refunds for unused labels

## Supported Carriers

- **USPS**: United States Postal Service
- **UPS**: United Parcel Service
- **FedEx**: Federal Express
- **DHL**: DHL Express
- **Canada Post**: Canadian postal service
- **And many more...**

## API Limits

- **Rate Limit**: 1000 requests per hour
- **Label Generation**: 100 labels per hour
- **Tracking Updates**: Real-time via webhooks

## Data Models

### Address
```python
@dataclass
class Address:
    name: str
    street1: str
    city: str
    state: Optional[str] = None
    zip: str
    country: str
    street2: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    validate: bool = True
```

### Parcel
```python
@dataclass
class Parcel:
    length: float
    width: float
    height: float
    distance_unit: str  # "in" or "cm"
    weight: float
    mass_unit: str  # "oz" or "g"
```

## Health Check

```python
# Test API connection
is_healthy = await client.ping()
```

## Troubleshooting

### Common Issues

1. **Invalid Address**: Use address validation before shipping
2. **Insufficient Funds**: Check Shippo account balance
3. **Carrier Restrictions**: Verify carrier service availability
4. **Label Errors**: Check parcel dimensions and weight

### Error Codes

- `400` - Bad Request (invalid data)
- `401` - Unauthorized (invalid API key)
- `402` - Payment Required (insufficient funds)
- `422` - Unprocessable Entity (validation errors)
- `429` - Too Many Requests (rate limit exceeded)

## Best Practices

1. **Address Validation**: Always validate addresses before shipping
2. **Rate Comparison**: Compare rates across carriers
2. **Insurance**: Add insurance for valuable packages
3. **Tracking**: Set up webhooks for tracking updates
4. **Test Mode**: Use test mode for development

## Webhooks

Configure webhooks for real-time updates:

- **Track Updates**: Shipment status changes
- **Label Events**: Label creation and refunds
- **Account Events**: Balance and billing notifications

## References

- [Shippo API Documentation](https://goshippo.com/docs/reference)
- [Carrier List](https://goshippo.com/docs/carriers)
- [Webhook Guide](https://goshippo.com/docs/webhooks)
