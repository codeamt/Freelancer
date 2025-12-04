# app/core/services/auth/providers/jwt.py
import os
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from core.utils.logger import get_logger

logger = get_logger(__name__)

class JWTProvider:
    def __init__(self):
        self.secret = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.exp_hours = 24

    def create(self, payload: Dict) -> str:
        """Create JWT token with expiration"""
        return jwt.encode(
            {**payload, "exp": datetime.utcnow() + timedelta(hours=self.exp_hours)},
            self.secret,
            algorithm=self.algorithm
        )

    def verify(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            return jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None