# Redis Pub/Sub Event Bus (async) For Modules that include messaging/chat features
import os
import json
from typing import Awaitable, Callable, Any, Optional
from core.utils.logger import get_logger

# Use redis-py asyncio client
import redis.asyncio as redis

logger = get_logger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class EventBus:
    """A minimal async Pub/Sub wrapper around Redis.

    Usage:
        bus = EventBus()
        await bus.publish("order.created", {"order_id": "123"})
        await bus.subscribe("order.*", handler)
    """

    def __init__(self, url: str = REDIS_URL):
        self.url = url
        self._r: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        if not self._r:
            self._r = redis.from_url(self.url, decode_responses=True)
        return self._r

    async def publish(self, channel: str, payload: Any) -> int:
        message = json.dumps({"channel": channel, "data": payload})
        logger.debug(f"Publishing to {channel}: {payload}")
        return await self.client.publish(channel, message)

    async def subscribe(self, pattern: str, handler: Callable[[str, Any], Awaitable[None]]):
        """Pattern-subscribe (supports wildcards). Calls handler(channel, data)."""
        psub = self.client.pubsub()
        await psub.psubscribe(pattern)
        logger.info(f"Subscribed to pattern: {pattern}")
        async for raw in psub.listen():
            if raw.get("type") == "pmessage":
                channel = raw.get("channel")
                try:
                    payload = json.loads(raw.get("data", "{}"))
                    await handler(channel, payload.get("data"))
                except Exception as e:
                    logger.error(f"Event handler error for {channel}: {e}")

# Singleton
bus = EventBus()