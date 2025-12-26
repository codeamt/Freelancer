"""Simple cookie-based session middleware for development"""
import json
import secrets
import base64
from typing import Optional, Dict, Any
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import Response


class CookieSessionMiddleware:
    """Simple cookie-based session middleware for development/testing"""
    
    def __init__(
        self,
        app: ASGIApp,
        cookie_name: str = "session",
        cookie_secure: bool = False,
        cookie_samesite: str = "lax",
        cookie_domain: Optional[str] = None,
        cookie_path: str = "/",
    ) -> None:
        self.app = app
        self.cookie_name = cookie_name
        self.cookie_secure = cookie_secure
        self.cookie_samesite = cookie_samesite
        self.cookie_domain = cookie_domain
        self.cookie_path = cookie_path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        session_data = request.cookies.get(self.cookie_name)
        
        # Decode session from cookie
        session: Dict[str, Any] = {}
        if session_data:
            try:
                # Decode base64 and parse JSON
                decoded = base64.b64decode(session_data.encode()).decode()
                session = json.loads(decoded)
            except (ValueError, json.JSONDecodeError):
                session = {}

        # Store session in scope
        scope["session"] = session
        
        # Capture response to add session cookie
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Check if session was modified
                if scope.get("_session_modified", False):
                    # Encode session data
                    session_json = json.dumps(session)
                    encoded = base64.b64encode(session_json.encode()).decode()
                    
                    # Add session cookie
                    headers = dict(message.get("headers", []))
                    cookie_value = f"{self.cookie_name}={encoded}"
                    cookie_value += f"; Path={self.cookie_path}"
                    if self.cookie_secure:
                        cookie_value += "; Secure"
                    if self.cookie_samesite:
                        cookie_value += f"; SameSite={self.cookie_samesite}"
                    if self.cookie_domain:
                        cookie_value += f"; Domain={self.cookie_domain}"
                    
                    headers[b"set-cookie"] = cookie_value.encode()
                    message["headers"] = list(headers.items())
            
            await send(message)

        # Wrap the request to detect session modifications
        class SessionRequest(Request):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._session = session
                self._scope = scope
            
            @property
            def session(self) -> Dict[str, Any]:
                return self._session
            
            def __setitem__(self, key, value):
                self._session[key] = value
                self._scope["_session_modified"] = True

        # Replace request in scope
        scope["_request_class"] = SessionRequest
        
        await self.app(scope, receive, send_wrapper)


def add_session_methods(request: Request):
    """Add session methods to request object"""
    session = scope.get("session", {})
    
    def get_session():
        return session
    
    def set_session(key: str, value: Any):
        session[key] = value
        scope["_session_modified"] = True
    
    request.session = session
