# Security Middleware & Helpers (Headers, CSRF, Rate Limit, JWT)
import os
import uuid
import boto3
import watchtower
import logging
from datetime import datetime
import time
import secrets
import jwt
from typing import Callable
from collections import defaultdict
from fastapi import HTTPException, FastAPI # , Request
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from core.ui.utils.security import sanitize_html, sanitize_sql_input
from core.utils.logger import get_logger

JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGO = "HS256"

COOKIE_OPTS = {"httponly": True, "secure": False, "samesite": "lax", "path": "/"}
CSRF_COOKIE = "csrf_token"

# --- JWT helpers -------------------------------------------------------------

def issue_jwt(payload: dict, exp_seconds: int = 3600) -> str:
    payload = {**payload, "exp": int(time.time()) + exp_seconds}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def verify_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")

# --- Security headers --------------------------------------------------------

class SecurityHeaders(BaseHTTPMiddleware):
    """
    Security headers middleware with FastHTML/MonsterUI compatibility
    
    Note: CSP is intentionally permissive for development with CDN resources.
    Tighten in production if needed.
    """
    async def dispatch(self, request: Request, call_next: Callable):
        resp = await call_next(request)
        
        # Only add security headers, skip CSP entirely
        # CSP is incompatible with FastHTML's inline styles and CDN usage
        resp.headers.update({
            "X-Frame-Options": "SAMEORIGIN",  # Changed from DENY to allow iframes if needed
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer-when-downgrade",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            # CSP removed - incompatible with FastHTML/MonsterUI
        })
        
        # Only add HSTS in production
        if os.getenv("ENVIRONMENT") == "production":
            resp.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        
        return resp

# --- CSRF --------------------------------------------------------------------

class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            token_cookie = request.cookies.get(CSRF_COOKIE)
            token_header = request.headers.get("X-CSRF-Token")
            if not token_cookie or not token_header or token_cookie != token_header:
                raise HTTPException(403, "CSRF validation failed")
        resp = await call_next(request)
        # rotate token on GET
        if request.method == "GET":
            token = secrets.token_urlsafe(32)
            resp.set_cookie(CSRF_COOKIE, token, **COOKIE_OPTS)
        return resp

# --- Rate limit --------------------------------------------------------------

_BUCKET = defaultdict(lambda: {"tokens": 60.0, "ts": time.time()})
_CAP = 60.0
_WINDOW = 60.0

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        ip = request.client.host if request.client else "anon"
        now = time.time()
        b = _BUCKET[ip]
        elapsed = now - b["ts"]
        b["tokens"] = min(_CAP, b["tokens"] + elapsed * (_CAP / _WINDOW))
        b["ts"] = now
        if b["tokens"] < 1:
            raise HTTPException(429, "Too Many Requests")
        b["tokens"] -= 1
        return await call_next(request)

# ------------------------------------------------------------------------------
# CloudWatch Logging and Metrics Setup
# ------------------------------------------------------------------------------

def configure_logger():
    logger = get_logger("security_middleware")
    logger.setLevel(logging.INFO)

    # Console handler
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Optional CloudWatch Logs integration
    if os.getenv("AWS_REGION") and os.getenv("AWS_ACCESS_KEY_ID"):
        try:
            session = boto3.Session(region_name=os.getenv("AWS_REGION", "us-east-1"))
            cw_handler = watchtower.CloudWatchLogHandler(
                log_group=os.getenv("CLOUDWATCH_LOG_GROUP", "FastApp/Security"),
                stream_name=os.getenv("CLOUDWATCH_LOG_STREAM", "middleware-events"),
                boto3_session=session,
            )
            cw_formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s"
            )
            cw_handler.setFormatter(cw_formatter)
            logger.addHandler(cw_handler)
            logger.info("✅ CloudWatch Logs initialized.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize CloudWatch Logs: {e}")

    return logger

logger = configure_logger()


# ------------------------------------------------------------------------------
# CloudWatch Logging and Metrics Setup
# ------------------------------------------------------------------------------
try:
    cloudwatch_client = boto3.client("cloudwatch", region_name=os.getenv("AWS_REGION", "us-east-1"))
except Exception as e:
    logger.warning(f"⚠️ CloudWatch Metrics client not initialized: {e}")
    cloudwatch_client = None

# ------------------------------------------------------------------------------
# Middleware Definition
# ------------------------------------------------------------------------------

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware that sanitizes requests, logs to CloudWatch, and emits security metrics."""

    async def dispatch(self, request: Request, call_next):
        trace_id = str(uuid.uuid4())
        suspicious_inputs = 0
        sanitization_failures = 0

        # -----------------------------
        # Sanitize Query Parameters
        # -----------------------------
        clean_query = {}
        for k, v in request.query_params.items():
            safe_v = sanitize_sql_input(sanitize_html(v))
            if v != safe_v:
                suspicious_inputs += 1
            clean_query[k] = safe_v
        request.state.sanitized_query = clean_query

        # -----------------------------
        # Sanitize Form Data
        # -----------------------------
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                form = await request.form()
                clean_form = {}
                for k, v in form.items():
                    safe_v = sanitize_sql_input(sanitize_html(v))
                    if v != safe_v:
                        suspicious_inputs += 1
                    clean_form[k] = safe_v
                request.state.sanitized_form = clean_form
            except Exception:
                sanitization_failures += 1
                request.state.sanitized_form = {}

        # -----------------------------
        # Sanitize Path Parameters
        # -----------------------------
        if hasattr(request, "path_params"):
            request.state.sanitized_path_params = {
                k: sanitize_sql_input(sanitize_html(str(v))) for k, v in getattr(request, "path_params", {}).items()
            }

        # -----------------------------
        # Sanitize Headers
        # -----------------------------
        clean_headers = {}
        for key, value in request.headers.items():
            if key.lower().startswith(("authorization", "cookie", "x-api-key")):
                clean_headers[key] = "[REDACTED]"
            else:
                clean_headers[key] = sanitize_html(value)
        request.state.sanitized_headers = clean_headers

        # -----------------------------
        # Log Request Metadata
        # -----------------------------
        logger.info(
            f"TRACE {trace_id} — {request.method} {request.url.path} | IP: {request.client.host} | Agent: {clean_headers.get('user-agent', 'n/a')}"
        )

        # -----------------------------
        # Process Request
        # -----------------------------
        response: Response = await call_next(request)

        # -----------------------------
        # Log Response Metadata
        # -----------------------------
        logger.info(
            f"TRACE {trace_id} — Response: {response.status_code} | Suspicious Inputs: {suspicious_inputs} | Sanitization Failures: {sanitization_failures}"
        )

        # -----------------------------
        # Emit Metrics to CloudWatch
        # -----------------------------
        if cloudwatch_client:
            try:
                metrics = [
                    {
                        'MetricName': 'SanitizedRequests',
                        'Timestamp': datetime.utcnow(),
                        'Value': 1,
                        'Unit': 'Count'
                    }
                ]

                if suspicious_inputs > 0:
                    metrics.append({
                        'MetricName': 'SuspiciousInputs',
                        'Timestamp': datetime.utcnow(),
                        'Value': suspicious_inputs,
                        'Unit': 'Count'
                    })

                if sanitization_failures > 0:
                    metrics.append({
                        'MetricName': 'SanitizationFailures',
                        'Timestamp': datetime.utcnow(),
                        'Value': sanitization_failures,
                        'Unit': 'Count'
                    })

                if 400 <= response.status_code < 500:
                    metrics.append({
                        'MetricName': 'Response4xx',
                        'Timestamp': datetime.utcnow(),
                        'Value': 1,
                        'Unit': 'Count'
                    })
                elif response.status_code >= 500:
                    metrics.append({
                        'MetricName': 'Response5xx',
                        'Timestamp': datetime.utcnow(),
                        'Value': 1,
                        'Unit': 'Count'
                    })

                cloudwatch_client.put_metric_data(
                    Namespace='FastApp/Security',
                    MetricData=metrics
                )

            except Exception as e:
                logger.warning(f"⚠️ Failed to publish metrics: {e}")

        return response

# --- Apply to app ------------------------------------------------------------

def apply_security(app: FastAPI):
    app.add_middleware(SecurityHeaders)
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityMiddleware)
    return app

# ------------------------------------------------------------------------------
# Example Usage (in main.py)
# ------------------------------------------------------------------------------
"""
from fastapi import FastAPI, Request
from app.middleware.security_middleware import apply_security

app = FastAPI()
apply_security(app)

@app.get("/status")
async def status(request: Request):
    return {"message": "OK", "trace_id": request.headers.get('x-trace-id', 'n/a')}
"""
