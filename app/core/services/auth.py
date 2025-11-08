# Authentication and Access Control
import jwt
import os
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Request
from functools import wraps
from app.core.utils.security import generate_token
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = 12

class AuthService:
    @staticmethod
    def create_token(data: dict) -> str:
        payload = {
            **data,
            "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        logger.debug(f"JWT created for user {data.get('sub')}")
        return token

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            logger.debug(f"JWT verified for user {payload.get('sub')}")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    def get_current_user(request: Request) -> dict:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing token")
        token = auth_header.split(" ")[1]
        return AuthService.verify_token(token)

# -----------------------------------------------------------------------------
# Access Control Decorators
# -----------------------------------------------------------------------------
def require_role(required_role: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = next((a for a in args if isinstance(a, Request)), None)
            if not request:
                raise HTTPException(status_code=400, detail="Request not found")
            user = AuthService.get_current_user(request)
            if user.get("role") != required_role:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_scope(*scopes):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = next((a for a in args if isinstance(a, Request)), None)
            if not request:
                raise HTTPException(status_code=400, detail="Request not found")
            user = AuthService.get_current_user(request)
            user_scopes = user.get("scopes", [])
            if not all(scope in user_scopes for scope in scopes):
                raise HTTPException(status_code=403, detail="Insufficient scope")
            return await func(*args, **kwargs)
        return wrapper
    return decorator