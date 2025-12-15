import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

import anyio
import requests

from core.utils.logger import get_logger

logger = get_logger(__name__)


class YouTubeService:
    def __init__(self):
        self.access_token = os.getenv("YOUTUBE_ACCESS_TOKEN")
        self.mock = os.getenv("YOUTUBE_MOCK", "").lower() in ("1", "true", "yes")
        self.enabled = os.getenv("YOUTUBE_ENABLED", "").lower() in ("1", "true", "yes")

    def is_configured(self) -> bool:
        if self.mock:
            return True
        if not self.enabled:
            return False
        return bool(self.access_token)

    async def create_and_bind_broadcast(
        self,
        title: str,
        description: str = "",
        privacy_status: str = "public",
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise RuntimeError("YouTube integration not configured")

        if self.mock:
            broadcast_id = uuid.uuid4().hex[:16]
            stream_id = uuid.uuid4().hex[:16]
            ingest_url = "rtmp://a.rtmp.youtube.com/live2"
            stream_key = uuid.uuid4().hex
            watch_url = f"https://www.youtube.com/watch?v={broadcast_id}"
            return {
                "broadcast_id": broadcast_id,
                "stream_id": stream_id,
                "ingest_url": ingest_url,
                "stream_key": stream_key,
                "watch_url": watch_url,
            }

        return await anyio.to_thread.run_sync(
            self._create_and_bind_broadcast_sync,
            title,
            description,
            privacy_status,
        )

    async def start_broadcast(self, broadcast_id: str) -> Dict[str, Any]:
        if not self.is_configured():
            raise RuntimeError("YouTube integration not configured")
        if self.mock:
            return {"broadcast_id": broadcast_id, "status": "live"}
        return await anyio.to_thread.run_sync(self._transition_sync, broadcast_id, "live")

    async def end_broadcast(self, broadcast_id: str) -> Dict[str, Any]:
        if not self.is_configured():
            raise RuntimeError("YouTube integration not configured")
        if self.mock:
            return {"broadcast_id": broadcast_id, "status": "complete"}
        return await anyio.to_thread.run_sync(self._transition_sync, broadcast_id, "complete")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _create_and_bind_broadcast_sync(self, title: str, description: str, privacy_status: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        started_at = now.replace(microsecond=0).isoformat()

        broadcast = self._post_json(
            "https://www.googleapis.com/youtube/v3/liveBroadcasts?part=snippet,status,contentDetails",
            {
                "snippet": {
                    "title": title,
                    "description": description,
                    "scheduledStartTime": started_at,
                },
                "status": {"privacyStatus": privacy_status},
                "contentDetails": {
                    "enableAutoStart": True,
                    "enableAutoStop": True,
                },
            },
        )

        broadcast_id = broadcast.get("id")
        if not broadcast_id:
            raise RuntimeError("Failed to create YouTube broadcast")

        stream = self._post_json(
            "https://www.googleapis.com/youtube/v3/liveStreams?part=snippet,cdn,contentDetails,status",
            {
                "snippet": {"title": title},
                "cdn": {
                    "frameRate": "variable",
                    "resolution": "variable",
                    "ingestionType": "rtmp",
                },
            },
        )
        stream_id = stream.get("id")
        if not stream_id:
            raise RuntimeError("Failed to create YouTube stream")

        self._post_json(
            f"https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?part=snippet&id={broadcast_id}&streamId={stream_id}",
            {},
        )

        ingestion_info = ((stream.get("cdn") or {}).get("ingestionInfo") or {})
        ingest_url = ingestion_info.get("ingestionAddress")
        stream_key = ingestion_info.get("streamName")
        watch_url = f"https://www.youtube.com/watch?v={broadcast_id}"

        return {
            "broadcast_id": broadcast_id,
            "stream_id": stream_id,
            "ingest_url": ingest_url,
            "stream_key": stream_key,
            "watch_url": watch_url,
        }

    def _transition_sync(self, broadcast_id: str, status: str) -> Dict[str, Any]:
        data = self._post_json(
            f"https://www.googleapis.com/youtube/v3/liveBroadcasts/transition?part=status&id={broadcast_id}&broadcastStatus={status}",
            {},
        )
        return {
            "broadcast_id": broadcast_id,
            "status": ((data.get("status") or {}).get("lifeCycleStatus") or status),
        }

    def _post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            resp = requests.post(url, headers=self._headers(), json=payload, timeout=20)
        except Exception as e:
            logger.error(f"YouTube request failed: {e}")
            raise

        if resp.status_code >= 400:
            raise RuntimeError(f"YouTube API error {resp.status_code}: {resp.text}")

        return resp.json() if resp.content else {}