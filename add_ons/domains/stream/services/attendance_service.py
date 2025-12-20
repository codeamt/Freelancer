from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from core.services import get_db_service


@dataclass
class StreamAttendance:
    id: int
    stream_id: int
    user_id: int
    created_at: datetime


class AttendanceService:
    def __init__(self, use_db: bool = False):
        self.use_db = use_db
        self.db = get_db_service() if use_db else None
        self._mem: Dict[int, List[StreamAttendance]] = {}

    async def is_attending(self, stream_id: int, user_id: int) -> bool:
        if self.use_db:
            doc = await self.db.find_document(
                "stream_attendees",
                {"stream_id": stream_id, "user_id": user_id},
            )
            return bool(doc)

        return any(a.user_id == user_id for a in self._mem.get(stream_id, []))

    async def add_attendee(self, stream_id: int, user_id: int) -> StreamAttendance:
        if self.use_db:
            existing = await self.db.find_document(
                "stream_attendees",
                {"stream_id": stream_id, "user_id": user_id},
            )
            if existing:
                return self._doc_to_attendance(existing)

            all_docs = await self.db.find_documents("stream_attendees", {}, limit=5000)
            new_id = (
                max((int(d.get("id")) for d in all_docs if d.get("id") is not None), default=0) + 1
            )
            now = datetime.utcnow()
            doc = {"id": new_id, "stream_id": stream_id, "user_id": user_id, "created_at": now}
            await self.db.insert_document("stream_attendees", doc)
            return StreamAttendance(id=new_id, stream_id=stream_id, user_id=user_id, created_at=now)

        now = datetime.utcnow()
        if stream_id not in self._mem:
            self._mem[stream_id] = []
        for a in self._mem[stream_id]:
            if a.user_id == user_id:
                return a
        att = StreamAttendance(id=len(self._mem[stream_id]) + 1, stream_id=stream_id, user_id=user_id, created_at=now)
        self._mem[stream_id].append(att)
        return att

    async def list_user_attendances(self, user_id: int, limit: int = 200) -> List[StreamAttendance]:
        if self.use_db:
            docs = await self.db.find_documents(
                "stream_attendees",
                {"user_id": user_id},
                limit=limit,
                sort=[("created_at", -1)],
            )
            return [self._doc_to_attendance(d) for d in docs]

        out: List[StreamAttendance] = []
        for stream_id, items in self._mem.items():
            for a in items:
                if a.user_id == user_id:
                    out.append(a)
        out.sort(key=lambda a: a.created_at, reverse=True)
        return out[:limit]

    async def counts_for_stream_ids(self, stream_ids: List[int]) -> Dict[int, int]:
        if not stream_ids:
            return {}

        if self.use_db:
            docs = await self.db.find_documents(
                "stream_attendees",
                {"stream_id": {"$in": stream_ids}},
                limit=10000,
            )
            counts: Dict[int, int] = {}
            for d in docs:
                sid = int(d.get("stream_id") or 0)
                counts[sid] = counts.get(sid, 0) + 1
            return counts

        return {sid: len(self._mem.get(sid, [])) for sid in stream_ids}

    def _doc_to_attendance(self, doc: dict) -> StreamAttendance:
        created_at = doc.get("created_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.utcnow()

        return StreamAttendance(
            id=int(doc.get("id") or 0),
            stream_id=int(doc.get("stream_id") or 0),
            user_id=int(doc.get("user_id") or 0),
            created_at=created_at,
        )
