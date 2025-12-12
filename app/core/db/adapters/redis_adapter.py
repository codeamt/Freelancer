"""Redis Adapter - Handles caching and session data"""
from typing import Any, Dict, Optional
import redis.asyncio as redis
from core.utils.logger import get_logger

logger = get_logger(__name__)


class RedisAdapter:
    """
    Redis adapter for caching, sessions, and real-time data.
    
    Use for: Caching, session storage, pub/sub, rate limiting, temporary data
    """
    
    def __init__(self, connection_string: str, decode_responses: bool = True):
        self.connection_string = connection_string
        self.decode_responses = decode_responses
        self.client: Optional[redis.Redis] = None
        
    async def connect(self):
        """Connect to Redis"""
        if not self.client:
            self.client = await redis.from_url(
                self.connection_string,
                decode_responses=self.decode_responses,
                encoding="utf-8"
            )
            logger.info(f"Redis connected: {self.connection_string}")
            
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self.client = None
            
    # Key-Value operations
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        return await self.client.get(key)
        
    async def set(
        self, 
        key: str, 
        value: Any, 
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        Set key-value pair
        
        Args:
            key: Key name
            value: Value to store
            ex: Expiration in seconds
            px: Expiration in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists
        """
        return await self.client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        return await self.client.delete(*keys)
        
    async def exists(self, *keys: str) -> int:
        """Check if keys exist"""
        return await self.client.exists(*keys)
        
    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration"""
        return await self.client.expire(key, seconds)
        
    async def ttl(self, key: str) -> int:
        """Get time to live for key"""
        return await self.client.ttl(key)
        
    # Hash operations
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value"""
        return await self.client.hget(name, key)
        
    async def hset(self, name: str, key: str, value: Any) -> int:
        """Set hash field value"""
        return await self.client.hset(name, key, value)
        
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields"""
        return await self.client.hgetall(name)
        
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields"""
        return await self.client.hdel(name, *keys)
        
    # List operations
    async def lpush(self, name: str, *values: Any) -> int:
        """Push values to list head"""
        return await self.client.lpush(name, *values)
        
    async def rpush(self, name: str, *values: Any) -> int:
        """Push values to list tail"""
        return await self.client.rpush(name, *values)
        
    async def lpop(self, name: str) -> Optional[str]:
        """Pop value from list head"""
        return await self.client.lpop(name)
        
    async def rpop(self, name: str) -> Optional[str]:
        """Pop value from list tail"""
        return await self.client.rpop(name)
        
    async def lrange(self, name: str, start: int, end: int) -> list:
        """Get list range"""
        return await self.client.lrange(name, start, end)
        
    # Set operations
    async def sadd(self, name: str, *values: Any) -> int:
        """Add members to set"""
        return await self.client.sadd(name, *values)
        
    async def srem(self, name: str, *values: Any) -> int:
        """Remove members from set"""
        return await self.client.srem(name, *values)
        
    async def smembers(self, name: str) -> set:
        """Get all set members"""
        return await self.client.smembers(name)
        
    async def sismember(self, name: str, value: Any) -> bool:
        """Check if value is set member"""
        return await self.client.sismember(name, value)
        
    # Sorted set operations
    async def zadd(self, name: str, mapping: Dict[Any, float]) -> int:
        """Add members to sorted set"""
        return await self.client.zadd(name, mapping)
        
    async def zrange(
        self, 
        name: str, 
        start: int, 
        end: int, 
        withscores: bool = False
    ) -> list:
        """Get sorted set range"""
        return await self.client.zrange(name, start, end, withscores=withscores)
        
    async def zrem(self, name: str, *values: Any) -> int:
        """Remove members from sorted set"""
        return await self.client.zrem(name, *values)
        
    # Pub/Sub operations
    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel"""
        return await self.client.publish(channel, message)
        
    # Transaction support (basic)
    async def prepare_transaction(self, transaction_id: str):
        """Redis doesn't support 2PC, but we can use MULTI/EXEC"""
        pass
        
    async def commit_transaction(self, transaction_id: str):
        """Commit is handled by EXEC in Redis pipeline"""
        pass
        
    async def rollback_transaction(self, transaction_id: str):
        """Redis MULTI/EXEC doesn't support rollback"""
        pass
        
    # Utility operations
    async def ping(self) -> bool:
        """Check Redis connection"""
        return await self.client.ping()
        
    async def flushdb(self) -> bool:
        """Clear current database"""
        return await self.client.flushdb()