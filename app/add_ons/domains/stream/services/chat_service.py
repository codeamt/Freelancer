from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from core.services import get_db_service
from core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ChatMessage:
    id: int
    stream_id: int
    user_id: int
    username: str
    content: str
    created_at: datetime


class ChatService:
    def __init__(self, use_db: bool = False):
        self.use_db = use_db
        self.db = get_db_service() if use_db else None
        self._mem: Dict[int, List[ChatMessage]] = {}

    async def list_messages(self, stream_id: int, limit: int = 50) -> List[ChatMessage]:
        if self.use_db:
            docs = await self.db.find_documents(
                "stream_messages",
                {"stream_id": stream_id},
                limit=limit,
                sort=[("created_at", 1)],
            )
            return [self._doc_to_message(d) for d in docs]

        return list(self._mem.get(stream_id, [])[-limit:])

    async def add_message(self, stream_id: int, user_id: int, username: str, content: str) -> ChatMessage:
        msg = ChatMessage(
            id=0,
            stream_id=stream_id,
            user_id=user_id,
            username=username,
            content=content,
            created_at=datetime.utcnow(),
        )

        if self.use_db:
            existing = await self.db.find_documents("stream_messages", {"stream_id": stream_id}, limit=5000)
            new_id = (
                max((int(m.get("id")) for m in existing if m.get("id") is not None), default=0) + 1
            )
            doc = {
                "id": new_id,
                "stream_id": stream_id,
                "user_id": user_id,
                "username": username,
                "content": content,
                "created_at": msg.created_at,
            }
            await self.db.insert_document("stream_messages", doc)
            msg.id = new_id
            return msg

        # Demo/in-memory
        if stream_id not in self._mem:
            self._mem[stream_id] = []
        msg.id = len(self._mem[stream_id]) + 1
        self._mem[stream_id].append(msg)
        return msg

    def _doc_to_message(self, doc: dict) -> ChatMessage:
        created_at = doc.get("created_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.utcnow()

        return ChatMessage(
            id=int(doc.get("id") or 0),
            stream_id=int(doc.get("stream_id") or 0),
            user_id=int(doc.get("user_id") or 0),
            username=str(doc.get("username") or "User"),
            content=str(doc.get("content") or ""),
            created_at=created_at,
        )
