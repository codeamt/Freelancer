import json
import secrets
from typing import Optional
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
import redis.asyncio as redis

class RedisSessionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        redis_url: str,
        cookie_name: str = "sid",
        ttl_seconds: int = 60 * 60 * 24,
        cookie_secure: bool = False,
        cookie_samesite: str = "lax",
        cookie_domain: Optional[str] = None,
        cookie_path: str = "/",
    ) -> None:
        self.app = app
        self.r = redis.from_url(redis_url, decode_responses=True)
        self.cookie_name = cookie_name
        self.ttl = ttl_seconds
        self.cookie_secure = cookie_secure
        self.cookie_samesite = cookie_samesite
        self.cookie_domain = cookie_domain
        self.cookie_path = cookie_path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        sid = request.cookies.get(self.cookie_name)
        new_sid = False
        if not sid:
            sid = secrets.token_urlsafe(32)
            new_sid = True

        key = f"sess:{sid}"
        data = await self.r.get(key)
        if data:
            session = json.loads(data)
        else:
            session = {}

        # expose session via scope so `request.session` works
        scope["session"] = session

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # persist session
                await self.r.set(key, json.dumps(scope.get("session", {})), ex=self.ttl)
                headers = []
                if new_sid:
                    from starlette.datastructures import MutableHeaders
                    headers = message.setdefault("headers", [])
                    cookie = (
                        f"{self.cookie_name}={sid}; Path={self.cookie_path}; SameSite={self.cookie_samesite}; HttpOnly"
                    )
                    if self.cookie_secure:
                        cookie += "; Secure"
                    if self.cookie_domain:
                        cookie += f"; Domain={self.cookie_domain}"
                    headers.append((b"set-cookie", cookie.encode("latin-1")))
            await send(message)

        await self.app(scope, receive, send_wrapper)
