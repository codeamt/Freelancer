# ==============================================================

# FILE: app/add_ons/streaming/__init__.py

# ==============================================================

"""Streaming Add-on Module
WebRTC live streaming with real-time chat, video archive, optional paywall,
and first-class YouTube Live integration.
Integrates with DuckDB analytics, Celery tasks, global health registry, core theming & auth.
"""

from app.add_ons.streaming import models, services, graphql, routes, tasks, ui, turn_config

__all__ = ["models", "services", "graphql", "routes", "tasks", "ui", "turn_config"]

# ==============================================================

# FILE: app/add_ons/streaming/models.py

# ==============================================================

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.db import Base

class Stream(Base):
    __tablename__ = "streaming_streams"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    is_live = Column(Boolean, default=False)
    visibility = Column(String(20), default="public")  # public | private | paid
    # Playback/HLS or external platform
    playback_url = Column(String(1024), nullable=True)

    # YouTube Live integration fields
    yt_stream_id = Column(String(255), nullable=True)
    yt_broadcast_id = Column(String(255), nullable=True)
    yt_ingest_url = Column(String(1024), nullable=True)
    yt_stream_key = Column(String(255), nullable=True)
    yt_live_url = Column(String(1024), nullable=True)  # watch URL / embed URL

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("ChatMessage", back_populates="stream", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "streaming_messages"

    id = Column(Integer, primary_key=True)
    stream_id = Column(Integer, ForeignKey("streaming_streams.id"))
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    stream = relationship("Stream", back_populates="messages")

class ViewerSession(Base):
    __tablename__ = "streaming_viewers"

    id = Column(Integer, primary_key=True)
    stream_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

class Paywall(Base):
    __tablename__ = "streaming_paywall"

    id = Column(Integer, primary_key=True)
    stream_id = Column(Integer, nullable=False)
    price_cents = Column(Integer, default=0)
    currency = Column(String(3), default="USD")
    product_sku = Column(String(64), nullable=True)  # map to eshop product if desired

# ==============================================================

# FILE: app/add_ons/streaming/schemas.py

# ==============================================================

from pydantic import BaseModel
from typing import Optional

class StreamCreate(BaseModel):
    title: str
    description: Optional[str] = None
    visibility: str = "public"  # public | private | paid

class StreamOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    is_live: bool
    visibility: str
    playback_url: Optional[str]
    yt_live_url: Optional[str]

    class Config:
        from_attributes = True

class ChatMessageIn(BaseModel):
    content: str

class WebRTCOffer(BaseModel):
    sdp: str
    type: str

class WebRTCAnswer(BaseModel):
    sdp: str
    type: str

# ==============================================================

# FILE: app/add_ons/streaming/turn_config.py

# ==============================================================

"""TURN/STUN configuration helpers for WebRTC clients."""
import os
from typing import List, Dict

def get_ice_servers() -> List[Dict[str, str]]:
    stun_list = os.getenv("STUN_SERVERS", "stun:stun.l.google.com:19302").split(",")
    ice = [{"urls": s.strip()} for s in stun_list if s.strip()]

    turn_url = os.getenv("TURN_URL")
    turn_user = os.getenv("TURN_USERNAME")
    turn_pass = os.getenv("TURN_PASSWORD")
    if turn_url and turn_user and turn_pass:
        ice.append({
            "urls": turn_url,
            "username": turn_user,
            "credential": turn_pass,
        })
    return ice

# ==============================================================

# FILE: app/add_ons/streaming/services.py

# ==============================================================

import os
import json
import asyncio
from typing import Optional, List, Tuple

import aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.add_ons.streaming.models import Stream, ChatMessage, ViewerSession, Paywall
from app.add_ons.streaming.schemas import StreamCreate
from app.core.analytics.duckdb_service import analytics
from app.core.utils import get_logger, S3Storage

logger = get_logger("streaming.services")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
YOUTUBE_CLIENT_SECRET_FILE = os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "")
YOUTUBE_CREDENTIALS_PATH = os.getenv("YOUTUBE_CREDENTIALS_PATH", ".youtube-oauth.json")
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube",  # full control as needed for create/bind/transition
]
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")
S3_ACCESS = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET = os.getenv("S3_SECRET_KEY", "")
S3_BUCKET = os.getenv("S3_BUCKET", "fastapp-streams")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
S3_URL_EXPIRY_SECONDS = int(os.getenv("S3_URL_EXPIRY_SECONDS", "900"))
S3_USE_PATH_STYLE = os.getenv("S3_USE_PATH_STYLE", "true").lower() == "true"

class StreamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_stream(self, owner_id: int, data: StreamCreate) -> Stream:
        stream = Stream(owner_id=owner_id, **data.model_dump())
        self.db.add(stream)
        await self.db.commit()
        await self.db.refresh(stream)
        analytics.log_event("streaming", "create_stream", owner_id, {"stream_id": stream.id})
        return stream

    async def list_live_streams(self) -> List[Stream]:
        res = await self.db.execute(select(Stream).where(Stream.is_live == True))
        streams = res.scalars().all()
        analytics.log_event("streaming", "list_live_streams")
        return streams

    async def start_stream(self, stream_id: int) -> Optional[Stream]:
        res = await self.db.execute(select(Stream).where(Stream.id == stream_id))
        stream = res.scalars().first()
        if not stream:
            return None
        stream.is_live = True
        await self.db.commit()
        await self.db.refresh(stream)
        analytics.log_event("streaming", "start_stream", metadata={"stream_id": stream_id})
        return stream

    async def stop_stream(self, stream_id: int) -> Optional[Stream]:
        res = await self.db.execute(select(Stream).where(Stream.id == stream_id))
        stream = res.scalars().first()
        if not stream:
            return None
        stream.is_live = False
        await self.db.commit()
        await self.db.refresh(stream)
        analytics.log_event("streaming", "stop_stream", metadata={"stream_id": stream_id})
        return stream

class SignalingService:
    """Very simple Redis-backed signaling channel for WebRTC offers/answers."""
    def __init__(self):
        self.redis = aioredis.from_url(REDIS_URL)

    async def set_offer(self, room: str, offer: dict):
        await (await self.redis).set(f"webrtc:{room}:offer", json.dumps(offer), ex=600)

    async def get_offer(self, room: str) -> Optional[dict]:
        val = await (await self.redis).get(f"webrtc:{room}:offer")
        return json.loads(val) if val else None

    async def set_answer(self, room: str, answer: dict):
        await (await self.redis).set(f"webrtc:{room}:answer", json.dumps(answer), ex=600)

    async def get_answer(self, room: str) -> Optional[dict]:
        val = await (await self.redis).get(f"webrtc:{room}:answer")
        return json.loads(val) if val else None

class ArchiveService:
    def __init__(self):
        self.s3 = None
        if S3_ENDPOINT and S3_ACCESS and S3_SECRET:
            self.s3 = S3Storage(S3_ENDPOINT, S3_ACCESS, S3_SECRET, S3_BUCKET)

    async def store_recording(self, filename: str, data: bytes, content_type: str = "video/mp4") -> str:
        if not self.s3:
            raise RuntimeError("S3 is not configured")
        return await self.s3.upload_file(filename, data, content_type)

    def generate_presigned_url(self, filename: str, method: str = "put") -> Tuple[str, dict]:
        """Return a presigned URL (and headers) for PUT (upload) or GET (download)."""
        try:
            import boto3  # type: ignore
            session = boto3.session.Session()
            client = session.client(
                "s3",
                endpoint_url=S3_ENDPOINT or None,
                aws_access_key_id=S3_ACCESS or None,
                aws_secret_access_key=S3_SECRET or None,
                region_name=S3_REGION or None,
                config=boto3.session.Config(s3={"addressing_style": "path" if S3_USE_PATH_STYLE else "virtual"}),
            )
            operation = "put_object" if method.lower() == "put" else "get_object"
            url = client.generate_presigned_url(
                ClientMethod=operation,
                Params={"Bucket": S3_BUCKET, "Key": filename},
                ExpiresIn=S3_URL_EXPIRY_SECONDS,
            )
            headers = {"Content-Type": "application/octet-stream"} if operation == "put_object" else {}
            return url, headers
        except Exception:
            base = (S3_ENDPOINT.rstrip("/") + f"/{S3_BUCKET}/{filename}") if S3_ENDPOINT else f"/{filename}"
            return base, {}

class YouTubeService:
    """YouTube Live/Upload integration using Google API client libraries.
    Requires OAuth2 credentials JSON (YOUTUBE_CLIENT_SECRET_FILE) and a writable token file (YOUTUBE_CREDENTIALS_PATH).
    """

    def _get_client(self):
        try:
            # Lazy import to avoid hard dep when not used
            from googleapiclient.discovery import build  # type: ignore
            from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
            from google.oauth2.credentials import Credentials  # type: ignore
        except Exception as e:
            raise RuntimeError("YouTube client libraries not installed: pip install google-api-python-client google-auth-oauthlib") from e

    creds = None
        if os.path.exists(YOUTUBE_CREDENTIALS_PATH):
            creds = Credentials.from_authorized_user_file(YOUTUBE_CREDENTIALS_PATH, YOUTUBE_SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request)  # type: ignore
                except Exception:
                    pass
            if not creds or not creds.valid:
                if not os.path.exists(YOUTUBE_CLIENT_SECRET_FILE):
                    raise RuntimeError("Missing YOUTUBE_CLIENT_SECRET_FILE for OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(YOUTUBE_CLIENT_SECRET_FILE, YOUTUBE_SCOPES)
                creds = flow.run_local_server(port=0)
                with open(YOUTUBE_CREDENTIALS_PATH, "w") as token:
                    token.write(creds.to_json())
        service = build("youtube", "v3", credentials=creds)
        return service

    async def create_live(self, db: AsyncSession, stream_id: int, title: str, description: str) -> Stream:
        service = self._get_client()
        # 1) Create the liveStream (ingestion info)
        stream_insert = service.liveStreams().insert(
            part="snippet,cdn",
            body={
                "snippet": {"title": title},
                "cdn": {"frameRate": "variable", "ingestionType": "rtmp", "resolution": "variable"},
            },
        ).execute()
        yt_stream_id = stream_insert["id"]
        ingest = stream_insert["cdn"]["ingestionInfo"]
        ingest_url = ingest.get("ingestionAddress")
        stream_key = ingest.get("streamName")

    # 2) Create the liveBroadcast
        broadcast_insert = service.liveBroadcasts().insert(
            part="snippet,status,contentDetails",
            body={
                "snippet": {"title": title, "description": description},
                "status": {"privacyStatus": "public"},
                "contentDetails": {"enableAutoStart": True, "enableAutoStop": True},
            },
        ).execute()
        yt_broadcast_id = broadcast_insert["id"]

    # 3) Bind stream to broadcast
        service.liveBroadcasts().bind(id=yt_broadcast_id, part="id,contentDetails", streamId=yt_stream_id).execute()

    # 4) Persist to DB
        res = await db.execute(select(Stream).where(Stream.id == stream_id))
        stream = res.scalars().first()
        if not stream:
            raise RuntimeError("Stream not found")
        stream.yt_stream_id = yt_stream_id
        stream.yt_broadcast_id = yt_broadcast_id
        stream.yt_ingest_url = ingest_url
        stream.yt_stream_key = stream_key
        stream.yt_live_url = f"https://www.youtube.com/watch?v={yt_broadcast_id}"
        await db.commit()
        await db.refresh(stream)
        return stream

    async def transition(self, broadcast_id: str, status: str):
        service = self._get_client()
        service.liveBroadcasts().transition(broadcastStatus=status, id=broadcast_id, part="status").execute()
        return True

# ==============================================================

# FILE: app/add_ons/streaming/routes.py

# ==============================================================

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Form, HTTPException, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse

from app.core.db import get_db
from app.add_ons.streaming.schemas import StreamCreate, WebRTCOffer, WebRTCAnswer
from app.add_ons.streaming.services import StreamService, SignalingService, ArchiveService, YouTubeService
from app.add_ons.streaming.turn_config import get_ice_servers
from app.add_ons.streaming.ui.watch import watch_page
from app.core.utils.health_registry import register_health_check
import os, smtplib, aioredis

router = APIRouter(prefix="/streaming", tags=["Streaming"])

# ---- REST: Streams ----

@router.post("/streams")
async def create_stream(request: Request, title: str = Form(...), description: str = Form(""), visibility: str = Form("public"), db=Depends(get_db)):
    user_id = request.state.user_id or 1
    service = StreamService(db)
    stream = await service.create_stream(user_id, StreamCreate(title=title, description=description, visibility=visibility))
    return JSONResponse({"id": stream.id, "title": stream.title})

@router.post("/streams/{stream_id}/start")
async def start_stream(stream_id: int, db=Depends(get_db)):
    service = StreamService(db)
    stream = await service.start_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    return {"status": "ok", "stream_id": stream.id}

@router.post("/streams/{stream_id}/stop")
async def stop_stream(stream_id: int, db=Depends(get_db)):
    service = StreamService(db)
    stream = await service.stop_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    return {"status": "ok", "stream_id": stream.id}

# ---- REST: WebRTC Signaling ----

@router.get("/webrtc/config")
async def webrtc_config():
    return {"iceServers": get_ice_servers()}

@router.post("/webrtc/{room}/offer")
async def post_offer(room: str, payload: WebRTCOffer):
    sig = SignalingService()
    await sig.set_offer(room, payload.model_dump())
    return {"status": "ok"}

@router.get("/webrtc/{room}/offer")
async def get_offer(room: str):
    sig = SignalingService()
    offer = await sig.get_offer(room)
    return offer or {}

@router.post("/webrtc/{room}/answer")
async def post_answer(room: str, payload: WebRTCAnswer):
    sig = SignalingService()
    await sig.set_answer(room, payload.model_dump())
    return {"status": "ok"}

@router.get("/webrtc/{room}/answer")
async def get_answer(room: str):
    sig = SignalingService()
    answer = await sig.get_answer(room)
    return answer or {}

# ---- Presigned Upload/Download URLs ----

@router.get("/upload-url")
async def get_presigned_url(filename: str = Query(...), method: str = Query("put")):
    arch = ArchiveService()
    url, headers = arch.generate_presigned_url(filename, method)
    return {"url": url, "headers": headers, "method": method}

# ---- YouTube Live integration ----

@router.post("/youtube/create/{stream_id}")
async def youtube_create(stream_id: int, title: str = Form(...), description: str = Form(""), db=Depends(get_db)):
    svc = YouTubeService()
    stream = await svc.create_live(db, stream_id, title, description)
    return {
        "stream_id": stream.id,
        "ingest_url": stream.yt_ingest_url,
        "stream_key": stream.yt_stream_key,
        "broadcast_id": stream.yt_broadcast_id,
        "watch_url": stream.yt_live_url,
    }

@router.post("/youtube/start/{broadcast_id}")
async def youtube_start(broadcast_id: str):
    svc = YouTubeService()
    await svc.transition(broadcast_id, "live")
    return {"status": "ok", "broadcast_id": broadcast_id}

@router.post("/youtube/end/{broadcast_id}")
async def youtube_end(broadcast_id: str):
    svc = YouTubeService()
    await svc.transition(broadcast_id, "complete")
    return {"status": "ok", "broadcast_id": broadcast_id}

# ---- WebSocket: Chat ----

active_connections: dict[int, list[WebSocket]] = {}

@router.websocket("/ws/chat/{stream_id}")
async def chat_socket(websocket: WebSocket, stream_id: int):
    await websocket.accept()
    active_connections.setdefault(stream_id, []).append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for ws in list(active_connections.get(stream_id, [])):
                try:
                    await ws.send_text(data)
                except WebSocketDisconnect:
                    active_connections[stream_id].remove(ws)
    except WebSocketDisconnect:
        active_connections[stream_id].remove(websocket)

# ---- Watch Page ----

@router.get("/watch/{stream_id}", response_class=HTMLResponse)
async def watch_stream(stream_id: int, db=Depends(get_db)):
    # In a real app: fetch stream, decide between WebRTC or YouTube playback
    ice = get_ice_servers()
    html = watch_page(stream_id=stream_id, ice_servers=ice)
    return HTMLResponse(html.render())

# ---- Health Registration for Global /healthz ----

async def get_streaming_health() -> bool:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    smtp_host = os.getenv("SMTP_HOST", "localhost")
    smtp_port = int(os.getenv("SMTP_PORT", "1025"))

    ok = True
    try:
        redis = await aioredis.from_url(redis_url)
        await redis.ping()
        await redis.close()
    except Exception:
        ok = False

    try:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=3)
        server.noop()
        server.quit()
    except Exception:
        ok = False

    return ok

register_health_check("streaming", get_streaming_health)

# ==============================================================

# FILE: app/add_ons/streaming/graphql.py

# ==============================================================

import strawberry
from strawberry.types import Info
from typing import List

from app.add_ons.streaming.services import StreamService

@strawberry.type
class StreamType:
    id: int
    title: str
    description: str | None
    is_live: bool
    visibility: str
    playback_url: str | None
    yt_live_url: str | None

@strawberry.type
class StreamingQuery:
    @strawberry.field
    async def live_streams(self, info: Info) -> List[StreamType]:
        db = info.context["db"]
        service = StreamService(db)
        items = await service.list_live_streams()
        return [StreamType(id=s.id, title=s.title, description=s.description, is_live=s.is_live, visibility=s.visibility, playback_url=s.playback_url, yt_live_url=s.yt_live_url) for s in items]

schema = strawberry.Schema(StreamingQuery)

# ==============================================================

# FILE: app/add_ons/streaming/tasks.py

# ==============================================================

from app.core.tasks.celery_app import celery_app
from app.core.utils import get_logger

logger = get_logger("streaming.tasks")

@celery_app.task(name="streaming.ping")
def ping_task():
    logger.info("Streaming ping task ok")
    return "pong"

@celery_app.task(name="streaming.archive.process")
def process_archive(stream_id: int, object_key: str):
    logger.info(f"Archive processing for stream {stream_id} -> {object_key}")
    # TODO: transcode, thumbnail, etc.
    return True

# ==============================================================

# FILE: app/add_ons/streaming/ui/__init__.py

# ==============================================================

from fasthtml.common import *
from monsterui.all import *
from app.core.ui import app_layout

def streaming_page(streams):
    return app_layout(
        Div(
            H1("Live Streams", cls="text-3xl font-bold mb-6"),
            Div([
                Card(
                    H3(s.title, cls="font-semibold"),
                    P(s.description or "", cls="text-gray-600"),
                    A("Watch", href=f"/streaming/watch/{s.id}", cls="mt-2 inline-block bg-primary text-white px-4 py-2 rounded"),
                    A("Broadcast", href=f"/streaming/broadcast/{s.id}", cls="mt-2 inline-block ml-2 bg-secondary text-white px-4 py-2 rounded"),
                ) for s in streams
            ], cls="grid grid-cols-1 md:grid-cols-3 gap-4"),
        )
    )

# ==============================================================

# FILE: app/add_ons/streaming/ui/broadcaster.py

# ==============================================================

from fasthtml.common import *
from app.core.ui import app_layout

def broadcaster_page(stream_id: int, ice_servers: list[dict]):
    return app_layout(
        Div(
            H1(f"Broadcast Stream #{stream_id}", cls="text-2xl font-semibold mb-4"),

    # Controls
            Div(
                Button("🎙️ Go Live (WebRTC)", id="btn-webrtc", cls="bg-primary text-white px-4 py-2 rounded mr-2"),
                Button("📺 Go Live on YouTube", id="btn-youtube", cls="bg-rose-600 text-white px-4 py-2 rounded"),
                cls="controls mb-4"
            ),

    # Ingest info (YouTube)
            Div(
                H3("YouTube Ingest Info", cls="font-semibold mb-2"),
                P("RTMP URL: ", Span(id="yt-ingest", cls="font-mono")),
                Br(),
                P("Stream Key: ", Span(id="yt-key", cls="font-mono")),
                P("Watch URL: ", A(id="yt-watch", href="#", children=["(pending)"])) ,
                cls="widget-card mb-6"
            ),

    # Video preview
            Div(
                Video(id="preview", cls="video-container", autoplay=True, playsinline=True, muted=True, controls=True),
                cls="mb-6"
            ),

    # Widgets
            Div(
                Div(id="analytics-widget", **{"hx-get": "/streaming/mock-metrics", "hx-trigger": "load, every 5s", "hx-target": "#analytics-widget", "hx-swap": "outerHTML"}),
                Div(id="engagement-widget", **{"hx-get": "/streaming/mock-engagement", "hx-trigger": "load, every 10s", "hx-target": "#engagement-widget", "hx-swap": "outerHTML"}),
                cls="dashboard-widgets grid gap-4 md:grid-cols-2"
            ),

    # Assets
            Link(rel="stylesheet", href="/streaming-static/css/streaming.css"),
            Script(src="https://unpkg.com/htmx.org@1.9.12"),
            Script(src="/streaming-static/js/webrtc.js"),
            Script(
                f"""
                window.ICE_SERVERS = {ice_servers};
                const streamId = {stream_id};
                document.getElementById('btn-webrtc').addEventListener('click', () => startLocalStream(`stream-${streamId}`));
                document.getElementById('btn-youtube').addEventListener('click', () => startYouTubeStream(streamId));
                """
            ),
        )
    )

# ==============================================================

# FILE: app/add_ons/streaming/ui/widgets/analytics_widget.py

# ==============================================================

from fasthtml.common import *

def render(metrics: dict):
    def fmt_dur(sec: int):
        m, s = divmod(int(sec), 60)
        return f"{m:02d}:{s:02d}"

    return Div(
        Div(
            H3("Live Analytics", cls="font-semibold mb-2"),
            Div(
                Div(Span("Viewers", cls="metric-label"), Span(str(metrics.get("viewers", 0)), cls="metric-value"), cls="metric"),
                Div(Span("Likes", cls="metric-label"), Span(str(metrics.get("likes", 0)), cls="metric-value"), cls="metric"),
                Div(Span("Chat Msgs", cls="metric-label"), Span(str(metrics.get("chat_messages", 0)), cls="metric-value"), cls="metric"),
                Div(Span("Avg Watch", cls="metric-label"), Span(fmt_dur(metrics.get("avg_watch_duration", 0)), cls="metric-value"), cls="metric"),
                Div(Span("Sentiment", cls="metric-label"), Span(f"{metrics.get('sentiment_score', 0):.2f}", cls="metric-value"), cls="metric"),
                cls="metric-grid"
            ),
        ),
        cls="widget-card",
        id="analytics-widget"
    )

# ==============================================================

# FILE: app/add_ons/streaming/ui/widgets/engagement_widget.py

# ==============================================================

from fasthtml.common import *

def render(payload: dict):
    reactions = payload.get("reactions", ["❤️", "🔥", "👏"])[:5]
    poll = payload.get("poll", {"question": "Favorite topic?", "options": [{"text": "A", "pct": 40}, {"text": "B", "pct": 60}]})

    return Div(
        H3("Audience Engagement", cls="font-semibold mb-2"),
        Div(
            Span("Reactions: ", cls="mr-2"),
            *[Span(r, cls="reaction") for r in reactions],
            cls="mb-4"
        ),
        Div(
            P(poll.get("question", "Poll"), cls="mb-2"),
            *[Div(Span(o["text"]) , Div(cls="bar", style=f"width:{o['pct']}%"), cls="poll-item") for o in poll.get("options", [])],
        ),
        cls="widget-card",
        id="engagement-widget"
    )

# ==============================================================

# FILE: app/add_ons/streaming/static/js/webrtc.js

# ==============================================================

(async function(){
  async function getICE(){
    const res = await fetch('/streaming/webrtc/config');
    const data = await res.json();
    return data.iceServers || [];
  }

  async function publishOffer(room, pc){
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    await fetch(`/streaming/webrtc/${room}/offer`, {
      method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(offer)
    });
  }

  async function pollForAnswer(room){
    for(let i=0;i<20;i++){
      const res = await fetch(`/streaming/webrtc/${room}/answer`);
      if(res.ok){
        const data = await res.json();
        if(data && data.type && data.sdp){ return data; }
      }
      await new Promise(r=>setTimeout(r,1500));
    }
    return null;
  }

  window.startLocalStream = async function(room){
    const video = document.getElementById('preview');
    const ice = window.ICE_SERVERS || await getICE();
    const pc = new RTCPeerConnection({iceServers: ice});
    pc.onicecandidate = (e)=>{ if(e.candidate){ /* optionally send via signaling */ } };
    pc.onconnectionstatechange = ()=> console.log('pc state', pc.connectionState);
    pc.ontrack = (ev)=>{ if(video.srcObject !== ev.streams[0]) video.srcObject = ev.streams[0]; };

    const media = await navigator.mediaDevices.getUserMedia({audio:true, video:true});
    media.getTracks().forEach(t=> pc.addTrack(t, media));
    video.srcObject = media;

    await publishOffer(room, pc);
    const answer = await pollForAnswer(room);
    if(!answer){ console.warn('No answer received'); return; }
    await pc.setRemoteDescription(new RTCSessionDescription(answer));
  }

  window.startYouTubeStream = async function(streamId){
    const form = new FormData();
    form.append('title', `Live Stream #${streamId}`);
    form.append('description', 'Streaming via YouTube Live (demo)');
    const createRes = await fetch(`/streaming/youtube/create/${streamId}`, {method:'POST', body: form});
    const info = await createRes.json();
    document.getElementById('yt-ingest').textContent = info.ingest_url || '';
    document.getElementById('yt-key').textContent = info.stream_key || '';
    const watch = document.getElementById('yt-watch');
    if(info.watch_url){ watch.href = info.watch_url; watch.textContent = info.watch_url; }

    if(info.broadcast_id){
      const startRes = await fetch(`/streaming/youtube/start/${info.broadcast_id}`, {method:'POST'});
      if(!startRes.ok){ console.warn('Failed to start YouTube broadcast'); }
    }
  }
})();

# ==============================================================

# FILE: app/add_ons/streaming/static/css/streaming.css

# ==============================================================

.video-container{ width:100%; max-width:960px; aspect-ratio:16/9; background:#000; border-radius:1rem; }
.controls button{ margin-right:.5rem }
.widget-card{ border:1px solid #e5e7eb; border-radius:1rem; padding:1rem; background:#fff }
.metric-grid{ display:grid; grid-template-columns: repeat(5, minmax(0,1fr)); gap:.5rem }
.metric{ display:flex; flex-direction:column; align-items:flex-start; padding:.25rem .5rem; background:#f9fafb; border-radius:.5rem }
.metric-label{ font-size:.75rem; color:#6b7280 }
.metric-value{ font-weight:600 }
.reaction{ font-size:1.25rem; margin-right:.25rem }
.poll-item{ display:flex; align-items:center; gap:.5rem; margin:.25rem 0 }
.poll-item .bar{ height:.5rem; background:#60a5fa; border-radius:.25rem }
.dashboard-widgets{ margin-top:1rem }

# ==============================================================

# FILE: app/add_ons/streaming/routes.py (ADDITIONS)

# ==============================================================

# (Append to existing routes file)

from fastapi.staticfiles import StaticFiles
from app.add_ons.streaming.ui.broadcaster import broadcaster_page
from app.add_ons.streaming.ui.widgets import analytics_widget, engagement_widget
import random, time

# Static mount for streaming module assets

STREAMING_STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')

# Provide a helper to mount from main app

def mount_streaming_static(app):
    if os.path.isdir(STREAMING_STATIC_DIR):
        app.mount('/streaming-static', StaticFiles(directory=STREAMING_STATIC_DIR), name='streaming-static')

@router.get("/broadcast/{stream_id}", response_class=HTMLResponse)
async def broadcast(stream_id: int):
    ice = get_ice_servers()
    html = broadcaster_page(stream_id=stream_id, ice_servers=ice)
    return HTMLResponse(html.render())

@router.get("/mock-metrics", response_class=HTMLResponse)
async def mock_metrics():
    payload = {
        "viewers": random.randint(50, 200),
        "likes": random.randint(100, 600),
        "chat_messages": random.randint(10, 120),
        "avg_watch_duration": random.randint(60, 1200),
        "sentiment_score": round(min(1, max(0, random.gauss(0.75, 0.1))), 2),
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }
    return HTMLResponse(analytics_widget.render(payload).render())

@router.get("/mock-engagement", response_class=HTMLResponse)
async def mock_engagement():
    reactions = random.choices(["❤️", "🔥", "👏", "🎉", "👍"], k=random.randint(3, 5))
    poll = {
        "question": "What should we cover next?",
        "options": [
            {"text": "Q&A", "pct": random.randint(20, 60)},
            {"text": "Demo", "pct": random.randint(20, 60)},
            {"text": "Deep Dive", "pct": random.randint(20, 60)},
        ],
    }
    payload = {"reactions": reactions, "poll": poll}
    return HTMLResponse(engagement_widget.render(payload).render())

# ==============================================================

# END OF FILES

# ==============================================================
