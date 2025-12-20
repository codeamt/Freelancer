import json
import time
from typing import Optional, Dict, Tuple

from core.services import get_db_service
from core.utils.logger import get_logger

logger = get_logger(__name__)


class SignalingService:
    def __init__(self):
        self._db = get_db_service()
        self._mem: Dict[str, Tuple[str, float]] = {}

        # In-memory structures for multi-viewer fallback
        self._mem_pending: Dict[str, list[str]] = {}
        self._mem_pending_set: Dict[str, set[str]] = {}

    async def _ensure_redis(self) -> None:
        redis = getattr(self._db, "redis", None)
        if not redis:
            return
        if not getattr(redis, "client", None):
            await redis.connect()

    async def set_offer(self, room: str, offer: dict, ttl_seconds: int = 600) -> None:
        await self._set_json(f"webrtc:{room}:offer", offer, ttl_seconds)

    async def get_offer(self, room: str) -> Optional[dict]:
        return await self._get_json(f"webrtc:{room}:offer")

    async def set_answer(self, room: str, answer: dict, ttl_seconds: int = 600) -> None:
        await self._set_json(f"webrtc:{room}:answer", answer, ttl_seconds)

    async def get_answer(self, room: str) -> Optional[dict]:
        return await self._get_json(f"webrtc:{room}:answer")

    # ---------------------------------------------------------------------
    # Multi-viewer signaling (viewer offers, broadcaster answers)
    # ---------------------------------------------------------------------

    async def set_viewer_offer(self, room: str, viewer_id: str, offer: dict, ttl_seconds: int = 600) -> None:
        """Viewer posts an offer. We enqueue viewer_id for broadcaster pickup."""
        key = f"webrtc:{room}:offer:{viewer_id}"
        await self._set_json(key, offer, ttl_seconds)

        # Maintain a queue of pending offers without needing key scans
        queue_key = f"webrtc:{room}:pending_queue"
        set_key = f"webrtc:{room}:pending_set"

        try:
            await self._ensure_redis()
            redis = self._db.redis
            already = await redis.sismember(set_key, viewer_id)
            if not already:
                await redis.sadd(set_key, viewer_id)
                await redis.rpush(queue_key, viewer_id)
                await redis.expire(set_key, ttl_seconds)
                await redis.expire(queue_key, ttl_seconds)
            return
        except Exception as e:
            logger.warning(f"Redis multi-viewer signaling unavailable, falling back to memory: {e}")

        # In-memory fallback
        if room not in self._mem_pending:
            self._mem_pending[room] = []
            self._mem_pending_set[room] = set()
        if viewer_id not in self._mem_pending_set[room]:
            self._mem_pending_set[room].add(viewer_id)
            self._mem_pending[room].append(viewer_id)

    async def pop_next_offer(self, room: str) -> Optional[dict]:
        """Broadcaster pops next pending viewer offer."""
        queue_key = f"webrtc:{room}:pending_queue"
        set_key = f"webrtc:{room}:pending_set"

        viewer_id: Optional[str] = None
        try:
            await self._ensure_redis()
            viewer_id = await self._db.redis.lpop(queue_key)
            if viewer_id:
                await self._db.redis.srem(set_key, viewer_id)
        except Exception:
            viewer_id = None

        if not viewer_id:
            # In-memory fallback
            q = self._mem_pending.get(room) or []
            if q:
                viewer_id = q.pop(0)
                self._mem_pending_set.get(room, set()).discard(viewer_id)

        if not viewer_id:
            return None

        offer = await self._get_json(f"webrtc:{room}:offer:{viewer_id}")
        if not offer:
            return None
        return {"viewer_id": viewer_id, "offer": offer}

    async def set_viewer_answer(self, room: str, viewer_id: str, answer: dict, ttl_seconds: int = 600) -> None:
        await self._set_json(f"webrtc:{room}:answer:{viewer_id}", answer, ttl_seconds)

    async def get_viewer_answer(self, room: str, viewer_id: str) -> Optional[dict]:
        return await self._get_json(f"webrtc:{room}:answer:{viewer_id}")

    # ---------------------------------------------------------------------
    # Trickle ICE candidates
    # ---------------------------------------------------------------------

    async def push_viewer_candidate(self, room: str, viewer_id: str, candidate: dict, ttl_seconds: int = 600) -> None:
        """Viewer -> broadcaster candidate queue."""
        key = f"webrtc:{room}:cands_from_viewer:{viewer_id}"
        await self._push_list_item(key, candidate, ttl_seconds)

    async def pop_viewer_candidates(self, room: str, viewer_id: str, max_items: int = 50) -> list[dict]:
        key = f"webrtc:{room}:cands_from_viewer:{viewer_id}"
        return await self._pop_list_items(key, max_items=max_items)

    async def push_broadcaster_candidate(self, room: str, viewer_id: str, candidate: dict, ttl_seconds: int = 600) -> None:
        """Broadcaster -> viewer candidate queue."""
        key = f"webrtc:{room}:cands_from_broadcaster:{viewer_id}"
        await self._push_list_item(key, candidate, ttl_seconds)

    async def pop_broadcaster_candidates(self, room: str, viewer_id: str, max_items: int = 50) -> list[dict]:
        key = f"webrtc:{room}:cands_from_broadcaster:{viewer_id}"
        return await self._pop_list_items(key, max_items=max_items)

    async def cleanup_viewer(self, room: str, viewer_id: str) -> None:
        """Delete viewer-specific signaling keys and remove from pending set."""
        keys = [
            f"webrtc:{room}:offer:{viewer_id}",
            f"webrtc:{room}:answer:{viewer_id}",
            f"webrtc:{room}:cands_from_viewer:{viewer_id}",
            f"webrtc:{room}:cands_from_broadcaster:{viewer_id}",
        ]

        set_key = f"webrtc:{room}:pending_set"

        try:
            await self._ensure_redis()
            await self._db.redis.delete(*keys)
            await self._db.redis.srem(set_key, viewer_id)
            return
        except Exception as e:
            logger.warning(f"Redis cleanup unavailable, falling back to memory: {e}")

        for k in keys:
            self._mem.pop(k, None)

    async def _push_list_item(self, key: str, payload: dict, ttl_seconds: int) -> None:
        raw = json.dumps(payload)
        try:
            await self._ensure_redis()
            await self._db.redis.rpush(key, raw)
            await self._db.redis.expire(key, ttl_seconds)
            return
        except Exception as e:
            logger.warning(f"Redis list unavailable, falling back to memory: {e}")

        # In-memory fallback: store as a JSON-lines list under a synthetic key
        mem_key = f"list:{key}"
        existing = self._mem.get(mem_key)
        if not existing or time.time() > existing[1]:
            self._mem[mem_key] = (json.dumps([raw]), time.time() + ttl_seconds)
            return
        try:
            arr = json.loads(existing[0])
        except Exception:
            arr = []
        arr.append(raw)
        self._mem[mem_key] = (json.dumps(arr), existing[1])

    async def _pop_list_items(self, key: str, max_items: int = 50) -> list[dict]:
        items: list[dict] = []
        try:
            await self._ensure_redis()
            for _ in range(max_items):
                raw = await self._db.redis.lpop(key)
                if not raw:
                    break
                try:
                    items.append(json.loads(raw))
                except Exception:
                    continue
            return items
        except Exception:
            pass

        mem_key = f"list:{key}"
        existing = self._mem.get(mem_key)
        if not existing or time.time() > existing[1]:
            self._mem.pop(mem_key, None)
            return []
        try:
            arr = json.loads(existing[0])
        except Exception:
            arr = []
        popped = arr[:max_items]
        remaining = arr[max_items:]
        self._mem[mem_key] = (json.dumps(remaining), existing[1])
        out: list[dict] = []
        for raw in popped:
            try:
                out.append(json.loads(raw))
            except Exception:
                continue
        return out

    async def _set_json(self, key: str, payload: dict, ttl_seconds: int) -> None:
        raw = json.dumps(payload)
        try:
            await self._db.cache_set(key, raw, ttl=ttl_seconds)
            return
        except Exception as e:
            logger.warning(f"Redis signaling unavailable, falling back to memory: {e}")

        self._mem[key] = (raw, time.time() + ttl_seconds)

    async def _get_json(self, key: str) -> Optional[dict]:
        try:
            raw = await self._db.cache_get(key)
            if raw:
                return json.loads(raw)
        except Exception:
            pass

        item = self._mem.get(key)
        if not item:
            return None

        raw, expires_at = item
        if time.time() > expires_at:
            self._mem.pop(key, None)
            return None

        try:
            return json.loads(raw)
        except Exception:
            return None