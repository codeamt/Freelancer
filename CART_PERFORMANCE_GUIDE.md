# Cart Service Performance Guide

## Current Implementation Analysis

### In-Memory CartService (Development)
**Location:** `app/core/services/cart/cart_service.py`

**Pros:**
- ✓ Fast (O(1) operations)
- ✓ Simple implementation
- ✓ No external dependencies
- ✓ Perfect for development/testing

**Cons:**
- ✗ Not persistent (data lost on restart)
- ✗ Not scalable (single process only)
- ✗ Memory grows unbounded
- ✗ Can't share across multiple servers

**Use Case:** Development, testing, single-server demos

---

## Production-Ready Implementation

### RedisCartService (Production)
**Location:** `app/core/services/cart/redis_cart_service.py`

**Pros:**
- ✓ Persistent (survives restarts)
- ✓ Distributed (works across multiple servers)
- ✓ Auto-expiring (TTL-based cleanup)
- ✓ High performance (Redis is in-memory)
- ✓ Scalable (millions of carts)
- ✓ Fallback to in-memory if Redis unavailable

**Performance Metrics:**
- Read: ~1ms (Redis network + deserialization)
- Write: ~1-2ms (Redis network + serialization)
- Memory: ~1-2KB per cart (JSON serialized)
- Throughput: 10,000+ ops/sec per Redis instance

**Use Case:** Production deployments, multi-server setups

---

## Setup Instructions

### 1. Install Redis

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

### 2. Install Python Redis Client

```bash
pip install redis
```

### 3. Configure Environment

```bash
# .env
REDIS_URL=redis://localhost:6379
# Or for production:
# REDIS_URL=redis://username:password@redis-host:6379/0
```

### 4. Update Service Usage

```python
# Development (in-memory)
from core.services import CartService
cart_service = CartService()

# Production (Redis)
from core.services.cart.redis_cart_service import RedisCartService
cart_service = RedisCartService()

# Or use environment-based selection
import os
if os.getenv('REDIS_URL'):
    from core.services.cart.redis_cart_service import RedisCartService
    cart_service = RedisCartService()
else:
    from core.services import CartService
    cart_service = CartService()
```

---

## Performance Comparison

| Operation | In-Memory | Redis | Database |
|-----------|-----------|-------|----------|
| Get cart | 0.001ms | 1ms | 10-50ms |
| Add item | 0.001ms | 1-2ms | 20-100ms |
| Checkout | 0.001ms | 1-2ms | 50-200ms |
| Scalability | Single server | Horizontal | Horizontal |
| Persistence | None | Yes | Yes |
| Memory usage | Process RAM | Redis RAM | Disk |

---

## Scaling Strategies

### Small Scale (< 1,000 users)
- **Use:** In-memory CartService
- **Why:** Simple, fast, no infrastructure needed
- **Limitation:** Single server only

### Medium Scale (1,000 - 100,000 users)
- **Use:** RedisCartService with single Redis instance
- **Why:** Persistent, distributed, auto-expiring
- **Setup:** Single Redis server (2-4GB RAM)

### Large Scale (100,000+ users)
- **Use:** RedisCartService with Redis Cluster
- **Why:** Horizontal scaling, high availability
- **Setup:** Redis Cluster (3+ nodes) or Redis Sentinel

### Enterprise Scale (Millions of users)
- **Use:** RedisCartService + Database hybrid
- **Why:** Redis for hot data, DB for cold storage
- **Setup:** Redis Cluster + PostgreSQL/MongoDB

---

## Migration Path

### Phase 1: Development (Current)
```python
from core.services import CartService
cart_service = CartService()
```

### Phase 2: Single Server Production
```python
from core.services.cart.redis_cart_service import RedisCartService
cart_service = RedisCartService()
```

### Phase 3: Multi-Server Production
```python
# Same code, just configure Redis URL to point to shared Redis
REDIS_URL=redis://shared-redis:6379
```

### Phase 4: High Availability
```python
# Use Redis Sentinel or Cluster
REDIS_URL=redis://sentinel-host:26379/mymaster
```

---

## Monitoring & Optimization

### Key Metrics to Track
1. **Cart operations/sec** - Monitor throughput
2. **Average cart size** - Track memory usage
3. **Cache hit rate** - Redis performance
4. **Expiration rate** - TTL effectiveness

### Redis Optimization
```bash
# Monitor Redis
redis-cli INFO stats
redis-cli MONITOR

# Check memory usage
redis-cli INFO memory

# Tune eviction policy (if needed)
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Performance Tips
1. **Use connection pooling** - Reuse Redis connections
2. **Batch operations** - Use Redis pipelines for multiple ops
3. **Compress large carts** - Use msgpack instead of JSON
4. **Set appropriate TTL** - Balance memory vs. user experience
5. **Monitor slow queries** - Use Redis SLOWLOG

---

## Conclusion

**Current Status:** ✓ Good for development
**Recommendation:** Migrate to RedisCartService for production

The in-memory implementation is fine for development and single-server demos, but for production deployments with multiple servers or high traffic, RedisCartService provides the performance, persistence, and scalability you need.
