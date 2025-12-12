# Stream Module Database Migration Guide

## Overview

The stream module services have been updated to support **both demo mode (in-memory) and database mode (DBService)** with minimal refactoring. This allows gradual migration from demo data to persistent database storage.

## What Changed

### Services Updated

1. **StreamService** - Stream management
2. **MembershipService** - Channel subscriptions
3. **PurchaseService** - Pay-per-view purchases

### Key Features

- ✅ **Backward compatible** - Demo mode still works by default
- ✅ **Opt-in database** - Enable with `use_db=True` parameter
- ✅ **State system integration** - Automatic audit trails via UserContext
- ✅ **Minimal refactoring** - Services maintain same interface

---

## Usage

### Demo Mode (Default - No Changes Required)

```python
# Existing code continues to work
service = StreamService()
streams = service.list_all_streams()  # Uses DEMO_STREAMS
```

### Database Mode (Opt-in)

```python
# Enable database persistence
service = StreamService(use_db=True)
streams = await service.list_all_streams()  # Uses DBService
```

---

## Migration Path

### Phase 1: Test Database Mode (Current)

Services support both modes. Test database operations:

```python
# In routes or services
stream_service = StreamService(use_db=True)
membership_service = MembershipService(use_db=True)
purchase_service = PurchaseService(use_db=True)

# All methods now async when use_db=True
streams = await stream_service.list_all_streams()
memberships = await membership_service.get_user_memberships(user_id)
purchases = await purchase_service.get_user_purchases(user_id)
```

### Phase 2: Update Routes (Gradual)

Update routes to use async/await:

```python
# Before (demo mode)
@router_streams.get("/stream")
async def list_streams(request: Request):
    service = StreamService()
    streams = service.list_all_streams()  # Sync
    return streams_list_page(streams, user)

# After (database mode)
@router_streams.get("/stream")
async def list_streams(request: Request):
    service = StreamService(use_db=True)
    streams = await service.list_all_streams()  # Async
    return streams_list_page(streams, user)
```

### Phase 3: Switch Default (Future)

Once tested, change service defaults:

```python
class StreamService:
    def __init__(self, use_db: bool = True):  # Changed default
        # Now uses database by default
```

---

## Database Schema

### Required Tables

#### `streams`
```sql
CREATE TABLE streams (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    visibility VARCHAR(50) DEFAULT 'public',
    price DECIMAL(10, 2) DEFAULT 0.00,
    is_live BOOLEAN DEFAULT FALSE,
    viewer_count INTEGER DEFAULT 0,
    thumbnail_url VARCHAR(500),
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `memberships`
```sql
CREATE TABLE memberships (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    channel_owner_id INTEGER NOT NULL,
    tier VARCHAR(50) NOT NULL,  -- 'basic', 'premium', 'vip'
    stripe_subscription_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    current_period_end TIMESTAMP,
    canceled_at TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, channel_owner_id)
);
```

#### `stream_purchases`
```sql
CREATE TABLE stream_purchases (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    stream_id INTEGER NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    stripe_payment_intent_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'completed',
    access_expires_at TIMESTAMP,  -- NULL for lifetime access
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Service API Changes

### StreamService

| Method | Demo Mode | Database Mode | Returns |
|--------|-----------|---------------|---------|
| `list_live_streams()` | Sync | **Async** | List[dict] |
| `list_all_streams()` | Sync | **Async** | List[dict] |
| `get_stream(id)` | Sync | **Async** | Optional[dict] |
| `create_stream(...)` | Sync | **Async** | dict |

### MembershipService

| Method | Demo Mode | Database Mode | Returns |
|--------|-----------|---------------|---------|
| `get_user_memberships(user_id)` | Sync | **Async** | List[Membership] |
| `get_membership(user_id, channel_id)` | Sync | **Async** | Optional[Membership] |
| `create_membership(...)` | Sync | **Async** | Membership |

### PurchaseService

| Method | Demo Mode | Database Mode | Returns |
|--------|-----------|---------------|---------|
| `has_purchased(user_id, stream_id)` | Sync | **Async** | bool |
| `get_user_purchases(user_id)` | Sync | **Async** | List[StreamPurchase] |
| `create_purchase(...)` | Sync | **Async** | StreamPurchase |

---

## Benefits

### 1. **State System Integration**

All database operations automatically include:
- `created_by` - User ID from UserContext
- `updated_by` - User ID from UserContext
- `metadata.user_role` - User role
- `metadata.ip_address` - Request IP

### 2. **Transaction Support**

```python
from core.services import get_db_service

db = get_db_service()

async with db.transaction() as tm:
    # Create stream
    stream = await db.insert("streams", {...}, transaction_manager=tm)
    
    # Create initial membership
    await db.insert("memberships", {...}, transaction_manager=tm)
    
    # Auto-commits on success, auto-rollbacks on error
```

### 3. **Multi-Database Support**

```python
# PostgreSQL for relational data
await db.insert("streams", {...})

# MongoDB for analytics/logs
await db.insert_document("stream_analytics", {...})

# Redis for caching
await db.cache_set(f"stream:{stream_id}", stream_data, ttl=300)
```

---

## Testing Strategy

### 1. Unit Tests

```python
# Test both modes
def test_stream_service_demo():
    service = StreamService(use_db=False)
    streams = service.list_all_streams()
    assert len(streams) > 0

async def test_stream_service_db():
    service = StreamService(use_db=True)
    streams = await service.list_all_streams()
    assert len(streams) >= 0
```

### 2. Integration Tests

```python
async def test_create_stream_with_db():
    service = StreamService(use_db=True)
    
    stream = await service.create_stream(
        owner_id=1,
        title="Test Stream",
        description="Test",
        visibility="public",
        price=0.00
    )
    
    assert stream["id"] is not None
    assert stream["title"] == "Test Stream"
```

### 3. Route Tests

```python
async def test_list_streams_endpoint():
    response = await client.get("/stream")
    assert response.status_code == 200
```

---

## Rollback Plan

If issues arise, simply revert to demo mode:

```python
# Change this
service = StreamService(use_db=True)

# Back to this
service = StreamService()  # or use_db=False
```

No database changes needed - demo data still works!

---

## Next Steps

1. ✅ **Services updated** - StreamService, MembershipService, PurchaseService
2. ⏳ **Create database migrations** - Add tables to schema
3. ⏳ **Update routes** - Add async/await where needed
4. ⏳ **Test database mode** - Verify all operations work
5. ⏳ **Migrate demo data** - Seed database with DEMO_STREAMS
6. ⏳ **Switch default** - Change `use_db=True` as default

---

## Example: Full Migration

### Before (Demo Mode)
```python
@router_streams.get("/stream")
async def list_streams(request: Request):
    user = get_current_user_from_context()
    service = StreamService()
    streams = service.list_all_streams()
    return streams_list_page(streams, user)
```

### After (Database Mode)
```python
@router_streams.get("/stream")
async def list_streams(request: Request):
    user = get_current_user_from_context()
    service = StreamService(use_db=True)
    streams = await service.list_all_streams()
    return streams_list_page(streams, user)
```

**That's it!** Minimal changes, maximum compatibility.
